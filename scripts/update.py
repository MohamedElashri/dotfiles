#!/usr/bin/env python3
"""Validate updates away from live symlinks and journal installer changes.

Only the standard library is required. Incoming configuration must still be
trusted: syntax/smoke checks cannot prove an arbitrary installer is harmless.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
HOME_DIR = Path.home().absolute()


class UpdateError(Exception):
    pass


def run(args, **kwargs):
    return subprocess.run([str(arg) for arg in args], check=True, **kwargs)


def git(*args, capture=True):
    result = run(['git', '-C', ROOT, *args],
                 stdout=subprocess.PIPE if capture else None, text=True)
    return result.stdout.strip() if capture else None


def clean_checkout():
    if Path(git('rev-parse', '--show-toplevel')).resolve() != ROOT:
        raise UpdateError('Update requires a Git checkout of the dotfiles repository.')
    changes = git('status', '--porcelain', '--untracked-files=normal')
    if changes:
        raise UpdateError('Update stopped: commit or stash your dotfiles changes first.\n' + changes)
    result = subprocess.run(['git', '-C', str(ROOT), 'symbolic-ref', '--quiet', 'HEAD'],
                            stdout=subprocess.PIPE, text=True)
    if result.returncode:
        raise UpdateError('Update stopped: check out a branch first (HEAD is detached).')
    # A clean index can still be in the middle of a merge or rebase.
    git_dir = Path(git('rev-parse', '--absolute-git-dir'))
    for name in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply'):
        if (git_dir / name).exists():
            raise UpdateError('Update stopped: finish the active Git operation first.')
    return result.stdout.strip()


def installer(root, *args, env=None, capture=False):
    try:
        return run(['bash', root / 'install.sh', *args], env=env,
                   stdout=subprocess.PIPE if capture else None)
    except subprocess.CalledProcessError as error:
        if error.stdout:
            print(error.stdout.decode('utf-8', 'replace'), file=sys.stderr, end='')
        raise


def manifest(root, profile):
    raw = installer(root, '--profile', profile, '--manifest', capture=True).stdout.split(b'\0')
    if raw[-1:] != [b''] or len(raw) % 2 != 1:
        raise UpdateError('Installer returned an invalid recovery manifest.')
    paths = {}
    for kind, raw_path in zip(raw[0:-1:2], raw[1:-1:2]):
        path = Path(os.fsdecode(raw_path))
        if kind not in (b'link', b'change', b'mode') or not path.is_absolute() or '..' in path.parts:
            raise UpdateError('Installer returned an unsafe recovery path.')
        if HOME_DIR not in path.parents:
            raise UpdateError('Installer recovery paths must be inside the home directory.')
        paths[str(path)] = kind.decode()
    return paths


def fingerprint(path, mode_only=False):
    if not os.path.lexists(path):
        return {'type': 'missing'}
    info = path.lstat()
    if mode_only:
        if not path.is_dir():
            raise UpdateError('Expected a directory: ' + str(path))
        return {'type': 'mode', 'mode': stat.S_IMODE(path.stat().st_mode)}
    if path.is_symlink():
        return {'type': 'symlink', 'target': os.readlink(path)}
    mode = stat.S_IMODE(info.st_mode)
    if path.is_file():
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        return {'type': 'file', 'mode': mode, 'sha256': digest.hexdigest()}
    if path.is_dir():
        return {'type': 'directory', 'mode': mode,
                'children': {child.name: fingerprint(child) for child in sorted(path.iterdir())}}
    raise UpdateError('Unsupported home file type: ' + str(path))


def save_state(directory, state):
    temporary = directory / 'state.json.new'
    with temporary.open('w') as stream:
        json.dump(state, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(directory / 'state.json')


def snapshot(directory, paths):
    entries, parents = [], set()
    for number, (name, kind) in enumerate(paths.items()):
        path = Path(name)
        before = fingerprint(path, kind == 'mode')
        entry = {'path': name, 'kind': kind, 'before': before, 'backup': str(number)}
        backup = directory / str(number)
        if before['type'] == 'symlink':
            backup.symlink_to(before['target'])
        elif before['type'] == 'file':
            shutil.copy2(path, backup)
        elif before['type'] == 'directory':
            shutil.copytree(path, backup, symlinks=True)
        if before['type'] in ('file', 'directory', 'symlink') and fingerprint(backup) != before:
            raise UpdateError('Home configuration changed while making the snapshot: ' + name)
        for parent in path.parents:
            if parent == HOME_DIR:
                break
            if not parent.exists():
                parents.add(str(parent))
        entries.append(entry)
    return entries, sorted(parents, key=lambda name: len(Path(name).parts), reverse=True)


def restore_home(directory, state):
    for entry in reversed(state['entries']):
        path = Path(entry['path'])
        before = entry['before']
        if entry['kind'] == 'mode':
            if before['type'] == 'mode':
                path.chmod(before['mode'])
            continue
        if fingerprint(path) == before:
            continue
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        elif os.path.lexists(path):
            path.unlink()
        if before['type'] != 'missing':
            path.parent.mkdir(parents=True, exist_ok=True)
            backup = directory / entry['backup']
            if before['type'] == 'symlink':
                path.symlink_to(before['target'])
            elif before['type'] == 'directory':
                shutil.copytree(backup, path, symlinks=True)
            else:
                shutil.copy2(backup, path)
    for name in state['created_parents']:
        try:
            Path(name).rmdir()  # Never remove directories containing unrelated files.
        except OSError:
            pass
    for entry in state['entries']:
        if entry['kind'] == 'mode' and entry['before']['type'] == 'missing':
            try:
                Path(entry['path']).rmdir()
            except OSError:
                pass


def export_candidate(commit, destination):
    # Extract regular Git files/directories only, never follow archive symlinks.
    with tempfile.TemporaryFile() as stream:
        run(['git', '-C', ROOT, 'archive', '--format=tar', commit], stdout=stream)
        stream.seek(0)
        with tarfile.open(fileobj=stream) as archive:
            for member in archive:
                relative = Path(member.name)
                if relative.is_absolute() or '..' in relative.parts:
                    raise UpdateError('Unsafe path in incoming configuration.')
                target = destination / relative
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.extractfile(member) as source, target.open('wb') as output:
                        shutil.copyfileobj(source, output)
                    target.chmod(member.mode & 0o777)
                else:
                    raise UpdateError('Incoming source symlinks/submodules need manual review.')


def validate(candidate, profile, scratch):
    print('Checking incoming shell syntax and installation in a temporary home...', flush=True)
    for path in sorted(candidate.rglob('*')):
        if not path.is_file():
            continue
        if path.suffix == '.zsh' or path.name in ('.zshrc', '.zshenv', '.zprofile'):
            shell = shutil.which('zsh')
            if shell:
                run([shell, '-n', path])
        elif path.suffix in ('.sh', '.bash') or path.name in ('.bashrc', '.profile', 'dotfiles'):
            run(['bash', '-n', path])
        elif path.suffix == '.py':
            compile(path.read_bytes(), str(path), 'exec')
        if path.name == '.gitconfig' or path.suffix == '.gitconfig':
            run(['git', 'config', '--file', path, '--list'], stdout=subprocess.DEVNULL)
    test_home = scratch / 'home'
    test_home.mkdir()
    env = dict(os.environ, HOME=str(test_home), ZDOTDIR=str(test_home),
               RUN_QURAN_VERSE_ON_STARTUP='false', TERM='dumb', PATH='/usr/bin:/bin')
    installer(candidate, '--profile', profile, '--dry-run', env=env, capture=True)
    installer(candidate, '--profile', profile, env=env, capture=True)
    installer(candidate, '--profile', profile, '--status', env=env, capture=True)
    if (test_home / '.bashrc').exists():
        smoke_shell(['bash', '--noprofile', '--rcfile', test_home / '.bashrc', '-ic', 'true'], env)
    if (test_home / '.zshrc').exists() and shutil.which('zsh'):
        smoke_shell([shutil.which('zsh'), '-ic', 'true'], env)


def smoke_shell(args, env):
    result = subprocess.run([str(arg) for arg in args], env=env, text=True, capture_output=True)
    # Shells may return success for `true` after reporting startup errors.
    # Ignore normal job-control warnings from a shell without a terminal.
    if result.returncode or re.search(r'command not found|syntax error|parse error|No such file or directory',
                                      result.stderr, re.IGNORECASE):
        raise UpdateError('Incoming shell startup failed:\n' + result.stderr)


def check_unchanged(state):
    for entry in state['entries']:
        if fingerprint(Path(entry['path']), entry['kind'] == 'mode') != entry['before']:
            raise UpdateError('Home configuration changed during validation: ' + entry['path'])


def undo(directory, state):
    # Git status omits ignored files. Protect any untracked path that returning
    # to the old tree would replace, including ignored AI instruction files.
    untracked = run(['git', '-C', ROOT, 'ls-files', '--others', '-z'], stdout=subprocess.PIPE).stdout
    restored = run(['git', '-C', ROOT, 'diff', '--name-only', '--no-renames',
                    '--diff-filter=A', '-z', 'HEAD', state['previous']], stdout=subprocess.PIPE).stdout
    for raw_path in filter(None, restored.split(b'\0')):
        for raw_local in filter(None, untracked.split(b'\0')):
            if (raw_path == raw_local or raw_path.startswith(raw_local + b'/')
                    or raw_local.startswith(raw_path + b'/')):
                raise UpdateError('Rollback would replace an untracked file: ' + os.fsdecode(raw_local))
    # --keep aborts instead of overwriting conflicting edits made during update.
    git('reset', '--keep', state['previous'], capture=False)
    restore_home(directory, state)
    state['status'] = 'rolled-back'
    save_state(directory, state)
    print('Restored previous commit and managed home paths.', flush=True)


def update(state_root, check):
    branch = clean_checkout()
    profile_path = HOME_DIR / '.config/dotfiles/profile'
    if not profile_path.exists():
        raise UpdateError('Install dotfiles first with ./install.sh before updating.')
    profile = profile_path.read_text().strip()
    if profile not in ('personal', 'hep'):
        raise UpdateError('Invalid installed profile.')
    # Detect detached AND missing existing links before fetching or applying anything.
    installer(ROOT, '--status', capture=True)
    old_paths = manifest(ROOT, profile)
    try:
        git('rev-parse', '--verify', '@{upstream}')
    except subprocess.CalledProcessError:
        raise UpdateError('Update stopped: this branch has no upstream. Set its tracking branch first.') from None
    previous = git('rev-parse', 'HEAD')
    print('Fetching upstream without changing live configuration...', flush=True)
    git('fetch', '--no-recurse-submodules', capture=False)
    target = git('rev-parse', '@{upstream}')
    ancestry = subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', previous, target])
    if ancestry.returncode:
        raise UpdateError('Update stopped: upstream is behind or diverged; review/push your local commits first.')
    git('log', '--oneline', previous + '..' + target, capture=False)
    with tempfile.TemporaryDirectory(prefix='dotfiles-validation-') as temporary:
        scratch = Path(temporary)
        candidate = scratch / 'candidate'
        candidate.mkdir()
        export_candidate(target, candidate)
        validate(candidate, profile, scratch)
        incoming = manifest(candidate, profile)
        for name, kind in incoming.items():
            if kind == 'link' and name not in old_paths and os.path.lexists(name):
                raise UpdateError('New managed path already exists; reconcile it first: ' + name)
        if check:
            print('Validation passed. Live checkout and home configuration were not changed.')
            return
        if target == previous:
            print('Already up to date. Managed links are healthy; no recovery snapshot was replaced.')
            return
        # Repeat checks after validation in case an app or another shell made edits.
        if clean_checkout() != branch or git('rev-parse', 'HEAD') != previous:
            raise UpdateError('Checkout changed during validation; update stopped.')
        installer(ROOT, '--status', capture=True)
        directory = Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-'),
                                          dir=state_root))
        paths = dict(old_paths)
        paths.update(incoming)
        entries, parents = snapshot(directory, paths)
        state = dict(status='prepared', previous=previous, target=target, branch=branch,
                     root=str(ROOT), home=str(HOME_DIR), entries=entries, created_parents=parents)
        save_state(directory, state)
        print('Recovery snapshot: ' + str(directory), flush=True)
        check_unchanged(state)
        try:
            state['status'] = 'applying'
            save_state(directory, state)
            # Pin the validated commit; protect ignored local files from replacement.
            git('merge', '--ff-only', '--no-autostash', '--no-overwrite-ignore', target, capture=False)
            installer(ROOT, '--profile', profile)
            installer(ROOT, '--profile', profile, '--status', capture=True)
            for entry in entries:
                entry['after'] = fingerprint(Path(entry['path']), entry['kind'] == 'mode')
            state['status'] = 'complete'
            save_state(directory, state)
        except (Exception, KeyboardInterrupt):
            print('Update failed; attempting to restore the previous configuration...', file=sys.stderr)
            try:
                undo(directory, state)
            except (Exception, KeyboardInterrupt) as recovery_error:
                state['status'] = 'recovery-needed'
                save_state(directory, state)
                print('Automatic recovery failed: ' + str(recovery_error), file=sys.stderr)
                print('Keep this recovery snapshot: ' + str(directory), file=sys.stderr)
            raise
    print('Update complete. Open a new shell. Use dotfiles rollback to undo this update.')


def rollback(state_root):
    branch = clean_checkout()
    records = sorted(state_root.glob('*/state.json'), key=lambda path: path.stat().st_mtime_ns)
    if not records:
        raise UpdateError('No update recovery snapshot exists.')
    record = records[-1]
    state = json.loads(record.read_text())
    if state['status'] != 'complete':
        raise UpdateError('Latest update is not a completed update. Inspect recovery snapshot: ' + str(record.parent))
    if (state['root'], state['home'], state['branch'], state['target']) != (
            str(ROOT), str(HOME_DIR), branch, git('rev-parse', 'HEAD')):
        raise UpdateError('Checkout, home, or branch changed since the update; rollback stopped.')
    for entry in state['entries']:
        if fingerprint(Path(entry['path']), entry['kind'] == 'mode') != entry['after']:
            raise UpdateError('Home configuration changed since the update; rollback stopped: ' + entry['path'])
    undo(record.parent, state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('update', 'rollback'))
    parser.add_argument('--check', action='store_true', help='fetch and validate without applying')
    args = parser.parse_args()
    if args.command == 'rollback' and args.check:
        parser.error('--check is only supported for update')
    clean_checkout()
    git_dir = Path(git('rev-parse', '--absolute-git-dir'))
    state_root = git_dir / 'dotfiles-updates'
    state_root.mkdir(mode=0o700, exist_ok=True)
    state_root.chmod(0o700)
    with (state_root / 'lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise UpdateError('Another dotfiles update or rollback is running.') from None
        pending = [path.parent for path in state_root.glob('*/state.json')
                   if json.loads(path.read_text())['status'] in ('applying', 'recovery-needed')]
        if pending:
            raise UpdateError('An interrupted update needs recovery before continuing: ' + str(pending[-1]))
        if args.command == 'update':
            update(state_root, args.check)
        else:
            rollback(state_root)


def interrupted(signum, frame):
    raise UpdateError('Interrupted by signal ' + str(signum))


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, interrupted)
    try:
        main()
    except (UpdateError, subprocess.CalledProcessError, OSError, SyntaxError, KeyboardInterrupt) as error:
        print('dotfiles: ' + str(error), file=sys.stderr)
        sys.exit(1)
