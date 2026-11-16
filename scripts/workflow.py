#!/usr/bin/env python3
"""Provision, inspect, and update the personal Linux/macOS environment."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def run(args, *, capture=False, check=True, dry=False, cwd=ROOT, timeout=None, env=None):
    args = [str(arg) for arg in args]
    if dry:
        print('Would run: ' + shlex.join(args))
        return subprocess.CompletedProcess(args, 0, '', '')
    return subprocess.run(args, cwd=cwd, text=True, check=check,
                          capture_output=capture, timeout=timeout, env=env)


def git(*args, **kwargs):
    return run(['git', '-C', ROOT, *args], capture=True, **kwargs)


def read_json(relative):
    return json.loads((ROOT / relative).read_text())


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def packages(relative):
    return [line.strip() for line in (ROOT / relative).read_text().splitlines()
            if line.strip() and not line.lstrip().startswith('#')]


def os_name(value=None):
    if value:
        return value
    system = platform.system()
    if system not in ('Linux', 'Darwin'):
        raise RuntimeError(f'Unsupported platform: {system}')
    return 'mac' if system == 'Darwin' else 'linux'


def brew_command():
    found = shutil.which('brew')
    if found:
        return found
    for prefix in ('/opt/homebrew', '/home/linuxbrew/.linuxbrew', '/usr/local'):
        candidate = Path(prefix) / 'bin/brew'
        if candidate.is_file():
            return str(candidate)
    return None


def configure_path():
    paths = [str(Path.home() / '.local/bin')]
    brew = brew_command()
    if brew:
        paths += [str(Path(brew).parent), str(Path(brew).parent.parent / 'sbin')]
    os.environ['PATH'] = os.pathsep.join(dict.fromkeys(paths + os.environ.get('PATH', '').split(os.pathsep)))


def install_args(platform_name, *args):
    return ['bash', ROOT / 'install.sh', '--platform', platform_name, *args]


def enable_hooks(dry=False):
    configured = git('config', '--local', '--get', 'core.hooksPath', check=False).stdout.strip()
    if configured and configured not in ('.githooks', str(ROOT / '.githooks')):
        print('Keeping custom Git hooks; chain .githooks/pre-commit and pre-push manually.')
        return
    run(['git', '-C', ROOT, 'config', '--local', 'core.hooksPath', '.githooks'], dry=dry)


def resource_path(home, relative):
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts:
        raise RuntimeError(f'Asset destination must be relative to HOME: {relative}')
    return home / path


def enabled_assets():
    path = Path.home() / '.config/dotfiles/features.json'
    groups = json.loads(path.read_text()).get('assets', []) if path.is_file() else []
    if not isinstance(groups, list) or any(group not in ('shell', 'editors', 'ai') for group in groups):
        raise RuntimeError('Invalid enabled asset groups in ~/.config/dotfiles/features.json.')
    # Older feature markers may still contain the retired group.
    return [group for group in groups if group != 'ai']


def remember_assets(groups):
    target = Path.home() / '.config/dotfiles/features.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({'assets': sorted(set(groups))}, indent=2) + '\n')
    target.chmod(0o600)


def matching_assets(platform_name, groups):
    return [asset for asset in read_json('setup/assets.json')['git']
            if asset['group'] in groups and asset.get('platform', platform_name) == platform_name]


def install_git_asset(asset, home, dry=False, update=False):
    dest = resource_path(home, asset['path'])
    revision = asset['revision']
    if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise RuntimeError(f'Expected a pinned Git commit for {asset["path"]}')
    exists = dest.exists() or dest.is_symlink()
    if exists:
        if dest.is_symlink() or not (dest / '.git').exists():
            raise RuntimeError(f'Asset path is already occupied: {dest}')
        remote = run(['git', '-C', dest, 'config', '--get', 'remote.origin.url'], capture=True).stdout.strip()
        if remote.removesuffix('.git') != asset['repo'].removesuffix('.git'):
            raise RuntimeError(f'Asset has a different origin: {dest}')
        current = run(['git', '-C', dest, 'rev-parse', 'HEAD'], capture=True).stdout.strip()
        if current == revision:
            print(f'Pinned asset present: {dest}')
            return
        if not update:
            print(f'Keeping existing asset: {dest}; use assets --update to apply the pinned revision.')
            return
        if run(['git', '-C', dest, 'status', '--porcelain'], capture=True).stdout:
            raise RuntimeError(f'Asset has local edits: {dest}')
    if not exists:
        if not dry:
            dest.parent.mkdir(parents=True, exist_ok=True)
        run(['git', 'clone', '--no-checkout', '--filter=blob:none', asset['repo'], dest], dry=dry)
    # Fetch the immutable commit, then detach without resetting local changes.
    run(['git', '-C', dest, 'fetch', '--depth=1', 'origin', revision], dry=dry)
    run(['git', '-C', dest, 'checkout', '--detach', revision], dry=dry)






def assets(args):
    home = Path.home()
    groups = args.group or ['shell', 'editors']
    platform_name = os_name(args.platform)
    for group, executable in [('editors', 'micro')]:
        if group in groups and not args.dry_run and not shutil.which(executable):
            raise RuntimeError(f'Install {executable} before provisioning {group} assets; use dotfiles bootstrap.')
    for asset in matching_assets(platform_name, groups):
        install_git_asset(asset, home, args.dry_run, args.update)
    manifest = read_json('setup/assets.json')
    if 'editors' in groups:
        for plugin in manifest['micro_plugins']:
            if not (home / '.config/micro/plug' / plugin).is_dir():
                run(['micro', '-plugin', 'install', plugin], dry=args.dry_run)
    return 0


def bootstrap(args):
    platform_name = os_name(args.platform)
    if args.apps and platform_name != 'mac':
        raise RuntimeError('--apps supports macOS casks only; Linux GUI apps stay distro-managed.')
    unknown_fonts = set(args.fonts or []) - read_json('setup/fonts.json').keys()
    if unknown_fonts:
        raise RuntimeError('Unknown font families: ' + ', '.join(sorted(unknown_fonts)))
    check_rendered()
    brew = brew_command()
    if not args.skip_packages:
        if not brew and not args.dry_run:
            raise RuntimeError('Install Homebrew first (https://brew.sh), or use --skip-packages with your own package manager.')
        brew = brew or 'brew'
        selected = packages(f'setup/{platform_name}-packages.txt')
        if args.dev:
            selected += packages('setup/dev-packages.txt')
        # Install missing formulae only. Routine package upgrades are separate.
        installed = set()
        if brew_command():
            result = run([brew, 'list', '--formula', '-1'], capture=True, check=False)
            if result.returncode:
                raise RuntimeError('Could not inspect Homebrew formulae; no packages changed.')
            installed = set(result.stdout.splitlines())
        missing = [name for name in dict.fromkeys(selected) if name not in installed]
        if missing:
            run([brew, 'install', *missing], dry=args.dry_run)
        if args.apps:
            run([brew, 'install', '--cask', *packages('setup/mac-apps.txt')], dry=args.dry_run)
    if not args.skip_assets:
        groups = ['shell', 'editors']
        asset_args = argparse.Namespace(platform=platform_name, group=groups,
                                       dry_run=args.dry_run, update=False)
        assets(asset_args)
    # Frameworks exist before linking their custom configuration. This also
    # keeps asset conflicts from occurring after unrelated app files changed.
    run(install_args(platform_name, *(['--dry-run'] if args.dry_run else [])))
    enable_hooks(args.dry_run)
    if args.fonts:
        fonts(argparse.Namespace(families=args.fonts, list=False, dry_run=args.dry_run,
                                 platform=platform_name))
    if not args.dry_run and not args.skip_assets:
        remember_assets(enabled_assets() + groups)
    print('Bootstrap preview complete.' if args.dry_run else
          'Bootstrap complete. Open a new shell, restart apps, and run dotfiles doctor.')
    return 0


def check_rendered():
    result = run([sys.executable, ROOT / 'scripts/render_configs.py', '--check'], capture=True, check=False)
    if result.returncode:
        raise RuntimeError('Generated configuration differs from its source preferences. Review edits, then run dotfiles render.\n' + result.stdout)


def ensure_clean():
    if git('status', '--porcelain', '--untracked-files=normal').stdout:
        raise RuntimeError('Checkout has local edits or untracked files. Review, commit, and push them before syncing.')
    if git('symbolic-ref', '--quiet', 'HEAD', check=False).returncode:
        raise RuntimeError('Checkout is on a detached HEAD; switch to your tracking branch before syncing.')
    if git('rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{upstream}', check=False).returncode:
        raise RuntimeError('This branch has no upstream. Configure its tracking branch before syncing.')


def check_existing(platform_name):
    result = run(install_args(platform_name, '--check-existing'), capture=True, check=False)
    if result.returncode:
        raise RuntimeError('Existing files need review before syncing. Copy desired edits into the checkout first.\n' + result.stdout + result.stderr)


def sync(args):
    platform_name = os_name(args.platform)
    ensure_clean()
    check_rendered()
    check_existing(platform_name)
    groups = enabled_assets()
    if getattr(args, 'assets', False):
        groups += ['shell', 'editors']
    groups = sorted(set(groups))
    if args.check:
        print('Sync preflight passed; no network or installation changes made.')
        return 0
    run(['git', '-C', ROOT, 'pull', '--ff-only'], dry=args.dry_run)
    # A new upstream version can introduce new target paths or generated output.
    check_rendered()
    check_existing(platform_name)
    run(install_args(platform_name, '--dry-run'))
    if not args.dry_run:
        run(install_args(platform_name))
        enable_hooks()
        run(install_args(platform_name, '--status'))
    if groups:
        assets(argparse.Namespace(platform=platform_name, group=groups, dry_run=args.dry_run, update=True))
        if not args.dry_run:
            remember_assets(groups)
    if not args.dry_run:
        print('Sync complete. Open a new shell and restart apps to reload settings.')
    return 0


def configured_git(name):
    result = run(['git', 'config', '--global', '--get', name], capture=True, check=False)
    return result.stdout.strip()


def doctor(args):
    errors = 0
    warnings = 0

    def report(level, message):
        nonlocal errors, warnings
        print(f'{level}: {message}')
        errors += level == 'FAIL'
        warnings += level == 'WARN'

    platform_name = os_name(args.platform)
    status = run(install_args(platform_name, '--status'), capture=True, check=False)
    if status.returncode:
        report('FAIL', 'Managed configuration links need attention.\n' + status.stdout + status.stderr)
    else:
        report('OK', 'Managed configuration links are intact.')
    command_names = {'python': 'python3', 'git-delta': 'delta', 'helix': 'hx',
                     'neovim': 'nvim', 'ripgrep': 'rg'}
    for name in packages(f'setup/{platform_name}-packages.txt'):
        command = command_names.get(name, name)
        if not shutil.which(command) and not (command == 'fd' and shutil.which('fdfind')):
            report('FAIL', f'Missing tool: {command}; install {name} or run dotfiles bootstrap.')
    try:
        check_rendered()
        report('OK', 'Generated app settings and shell plugin selections match their sources.')
    except RuntimeError as error:
        report('FAIL', str(error))
    hooks = git('config', '--local', '--get', 'core.hooksPath', check=False).stdout.strip()
    report('OK' if hooks in ('.githooks', str(ROOT / '.githooks')) else 'WARN',
           'Repository hooks enabled.' if hooks in ('.githooks', str(ROOT / '.githooks')) else
           'Repository hooks are not configured; run dotfiles hooks or chain them into custom hooks.')
    if configured_git('commit.gpgsign') == 'true':
        signing = configured_git('gpg.ssh.program')
        if signing and not Path(signing).expanduser().is_file() and not shutil.which(signing):
            report('FAIL', 'Git SSH signing executable is missing; install 1Password or set local.gitconfig.')
        if not configured_git('user.signingkey'):
            report('FAIL', 'Git commit signing is enabled but user.signingkey is unset.')
        if configured_git('gpg.format') == 'ssh':
            socket = os.environ.get('SSH_AUTH_SOCK')
            if not socket:
                probe = run(['ssh', '-G', 'github.com'], capture=True, check=False, timeout=10)
                socket = next((line.partition(' ')[2] for line in probe.stdout.splitlines()
                               if line.startswith('identityagent ')), '')
            path = Path(os.path.expandvars(socket)).expanduser() if socket and socket != 'none' else None
            report('OK' if path and path.is_socket() else 'WARN',
                   'SSH agent socket is available.' if path and path.is_socket() else
                   'SSH agent socket is unavailable; open/unlock 1Password before signing.')
    if args.online and shutil.which('gh'):
        # Do not print command output: auth status can contain account details.
        probe = run(['gh', 'auth', 'status'], capture=True, check=False, timeout=30)
        report('OK' if probe.returncode == 0 else 'WARN',
               'GitHub authentication verified.' if probe.returncode == 0 else 'GitHub authentication needs attention; run gh auth login.')
    else:
        report('INFO', 'GitHub authentication is not probed offline; use doctor --online to verify it.')
    home = Path.home()
    for asset in matching_assets(platform_name, ['shell', 'editors']):
        dest = resource_path(home, asset['path'])
        if not (dest / '.git').exists():
            report('WARN', f'Missing optional asset: {asset["path"]}; run dotfiles assets.')
        else:
            revision = run(['git', '-C', dest, 'rev-parse', 'HEAD'], capture=True, check=False).stdout.strip()
            if revision != asset['revision']:
                report('WARN', f'Asset differs from pinned revision: {asset["path"]}; review assets --update.')
            if run(['git', '-C', dest, 'status', '--porcelain'], capture=True, check=False).stdout:
                report('WARN', f'Asset has local edits: {asset["path"]}; review them before updating.')
    manifest = read_json('setup/assets.json')
    for plugin in manifest['micro_plugins']:
        if not (home / '.config/micro/plug' / plugin).is_dir():
            report('WARN', f'Missing Micro plugin: {plugin}; run dotfiles assets --group editors.')
    for name in ('local.bash', 'local.zsh', 'local.env.zsh', 'local.gitconfig'):
        if (home / '.config/dotfiles' / name).exists():
            report('INFO', f'Local override present: {name}; its contents stay device-local.')
    if platform_name == 'mac' and not (home / '.ssh/config.local').is_file():
        report('WARN', 'Mac SSH routes are local; restore ~/.ssh/config.local if needed.')
    if git('status', '--porcelain').stdout:
        report('WARN', 'Checkout has local edits; review and commit before syncing.')
    report('INFO', 'Account login and editor cloud sync stay application-owned.')
    print(f'Doctor: {errors} failure(s), {warnings} warning(s).')
    return 1 if errors or (args.strict and warnings) else 0


def archive_fonts(archive, destination):
    """Install font files only; reject traversal, symlinks, and name collisions."""
    with zipfile.ZipFile(archive) as bundle:
        selected = []
        seen = set()
        total_size = 0
        for info in bundle.infolist():
            path = Path(info.filename)
            if path.suffix.lower() not in ('.ttf', '.otf'):
                continue
            if path.is_absolute() or '..' in path.parts or '\\' in info.filename:
                raise RuntimeError('Unsafe font archive path.')
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise RuntimeError('Font archive contains a symlink.')
            if path.name in seen:
                raise RuntimeError('Font archive has duplicate filenames.')
            total_size += info.file_size
            if info.file_size > 32 * 1024 * 1024 or total_size > 1024 * 1024 * 1024:
                raise RuntimeError('Font archive exceeds the supported size limit.')
            seen.add(path.name)
            selected.append((info, path.name))
        if not selected:
            raise RuntimeError('Font archive contains no fonts.')
        destination.mkdir(parents=True, exist_ok=True)
        for info, name in selected:
            content = bundle.read(info)
            target = destination / name
            if target.exists() or target.is_symlink():
                if target.is_file() and target.read_bytes() == content:
                    continue
                stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
                backup = Path.home() / '.dotfiles-backup' / ('fonts-' + stamp) / name
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target), backup)
            target.write_bytes(content)


def fonts(args):
    manifest = read_json('setup/fonts.json')
    if args.list:
        for name in manifest:
            print(name)
        return 0
    if not args.families:
        raise RuntimeError('Select a font family; use dotfiles fonts --list.')
    unknown = set(args.families) - manifest.keys()
    if unknown:
        raise RuntimeError('Unknown font families: ' + ', '.join(sorted(unknown)))
    platform_name = os_name(args.platform)
    destination = Path.home() / ('Library/Fonts' if platform_name == 'mac' else '.local/share/fonts')
    cache = Path.home() / '.cache/dotfiles/fonts'
    for family in args.families:
        asset = manifest[family]
        archive = cache / (asset['sha256'] + '.zip')
        if args.dry_run:
            print(f'Would download and verify {family}: {asset["url"]}')
            print(f'Would install fonts into {destination}')
            continue
        cache.mkdir(parents=True, exist_ok=True)
        if not archive.exists() or file_sha256(archive) != asset['sha256']:
            with tempfile.TemporaryDirectory(dir=cache) as temp:
                downloaded = Path(temp) / 'font.zip'
                run(['curl', '--fail', '--location', '--retry', '2', '--output', downloaded, asset['url']])
                if file_sha256(downloaded) != asset['sha256']:
                    raise RuntimeError(f'Checksum mismatch for {family}; no fonts installed.')
                shutil.move(str(downloaded), archive)
        archive_fonts(archive, destination)
        print(f'Installed {family}: {destination}')
    if platform_name == 'linux' and not args.dry_run and shutil.which('fc-cache'):
        run(['fc-cache', '-f', destination])
    return 0


def parser():
    result = argparse.ArgumentParser(prog='dotfiles', description=__doc__)
    commands = result.add_subparsers(dest='command', required=True)
    for name in ('bootstrap', 'doctor', 'sync', 'assets', 'fonts'):
        command = commands.add_parser(name)
        command.add_argument('--platform', choices=('linux', 'mac'))
        if name != 'doctor':
            command.add_argument('--dry-run', action='store_true')
        if name == 'bootstrap':
            command.add_argument('--skip-packages', action='store_true')
            command.add_argument('--skip-assets', action='store_true')
            command.add_argument('--apps', action='store_true')
            command.add_argument('--dev', action='store_true')
            command.add_argument('--fonts', nargs='+', metavar='FAMILY')
        elif name == 'doctor':
            command.add_argument('--online', action='store_true')
            command.add_argument('--strict', action='store_true')
        elif name == 'sync':
            command.add_argument('--check', action='store_true')
            command.add_argument('--assets', action='store_true', help='Enable shell/editor asset sync on an older installation')
        elif name == 'assets':
            command.add_argument('--group', action='append', choices=('shell', 'editors'))
            command.add_argument('--update', action='store_true')
        elif name == 'fonts':
            command.add_argument('families', nargs='*')
            command.add_argument('--list', action='store_true')
        command.set_defaults(func=globals()[name])
    commands.add_parser('hooks').set_defaults(func=lambda args: enable_hooks() or 0)
    commands.add_parser('render').set_defaults(func=lambda args: run([sys.executable, ROOT / 'scripts/render_configs.py']).returncode)
    return result


def main():
    sys.stdout.reconfigure(line_buffering=True)
    configure_path()
    args = parser().parse_args()
    try:
        return args.func(args)
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        print(f'dotfiles: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
