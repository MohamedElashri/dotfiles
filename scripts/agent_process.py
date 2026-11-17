"""Bounded POSIX subprocesses and conservative filesystem helpers (Python 3.9+).

Process groups and polling are resource controls, not a security sandbox.
"""
import os
from pathlib import Path
import selectors
import signal
import stat
import subprocess
import tempfile
import time
import resource


class SafetyError(ValueError):
    pass


def real_directory(path, create=False, private=False):
    path = Path(path).expanduser()
    if not path.is_absolute():
        raise SafetyError('Use an absolute directory path.')
    for part in reversed((path,) + tuple(path.parents)):
        if part.is_symlink():
            raise SafetyError('Symlinked directory paths are not supported.')
        if part.exists() and not part.is_dir():
            raise SafetyError('A directory path is occupied by a file.')
    if create:
        path.mkdir(parents=True, exist_ok=True, mode=0o700 if private else 0o755)
    if not path.is_dir():
        raise SafetyError('Directory does not exist.')
    if private:
        info = path.stat()
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise SafetyError('State directories must be user-owned with mode 0700.')
    return path


def files(path, max_bytes=4 * 1024 * 1024, max_files=256, ignore_git=True):
    """Read bounded regular UTF-8 files without traversing links or special files."""
    root = real_directory(path)
    result = {}
    size = 0
    count = 0
    for directory, dirs, names in os.walk(root, followlinks=False):
        if ignore_git and Path(directory) == root and '.git' in dirs:
            dirs.remove('.git')
        for name in dirs + names:
            item = Path(directory) / name
            if ignore_git and item == root / '.git':
                continue
            info = item.lstat()
            count += 1
            if count > max_files or stat.S_ISLNK(info.st_mode):
                raise SafetyError('Candidate contains too many paths or a symlink.')
            if stat.S_ISDIR(info.st_mode):
                continue
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise SafetyError('Candidate contains a special file or hard link.')
            size += info.st_size
            if size > max_bytes:
                raise SafetyError('Candidate exceeds the size limit.')
            result[item.relative_to(root).as_posix()] = item.read_text(encoding='utf-8')
    return result


def environment(home, path=None):
    """No inherited credentials, proxies, user shell profiles, Git config or tools."""
    home = Path(home)
    env = {'HOME': str(home), 'PATH': path or '/usr/bin:/bin', 'LANG': 'C.UTF-8',
           'LC_ALL': 'C', 'TERM': 'dumb', 'SHELL': '/bin/sh',
           'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
           'GIT_TERMINAL_PROMPT': '0', 'GIT_SSH_COMMAND': '/usr/bin/false',
           'PYTHONDONTWRITEBYTECODE': '1'}
    for key, relative in [('XDG_CONFIG_HOME', 'config'), ('XDG_STATE_HOME', 'state'),
                          ('XDG_DATA_HOME', 'data'), ('XDG_CACHE_HOME', 'cache'),
                          ('XDG_RUNTIME_DIR', 'runtime'), ('TMPDIR', 'tmp'),
                          ('CODEX_HOME', 'codex'), ('CLAUDE_CONFIG_DIR', 'claude'),
                          ('PI_CODING_AGENT_DIR', 'pi')]:
        directory = home / relative
        directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        env[key] = str(directory)
    env['PI_OFFLINE'] = '1'
    env['PI_TELEMETRY'] = '0'
    env['OPENCODE_DISABLE_AUTOUPDATE'] = '1'
    return env


def _disk_usage(root):
    count = size = 0
    for directory, dirs, names in os.walk(root, followlinks=False):
        count += len(dirs) + len(names)
        if count > 4096:
            return float('inf')
        for name in names:
            try:
                size += (Path(directory) / name).lstat().st_size
            except FileNotFoundError:
                pass
    return size


def bounded(argv, *, cwd, env, timeout=30, output_limit=1024 * 1024,
            disk_root=None, disk_limit=32 * 1024 * 1024, input_text=None):
    if not 0 < timeout <= 300 or not 1024 <= output_limit <= 1024 * 1024:
        raise SafetyError('Runtime must be 1–300 seconds; output 1 KiB–1 MiB.')
    started = time.monotonic()
    process = None
    selector = selectors.DefaultSelector()
    captured = bytearray()
    total = 0
    reason = None
    interrupted = False
    handlers = {}
    def cancel(signum, frame):
        raise KeyboardInterrupt
    def limits():
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_FSIZE, (disk_limit, disk_limit))
    # A regular temporary stdin avoids a pipe write that can block before polling.
    with tempfile.TemporaryFile(dir=env.get('TMPDIR')) as stdin:
        if input_text is not None:
            data = input_text.encode()
            if len(data) > 64 * 1024:
                raise SafetyError('Input exceeds 64 KiB.')
            stdin.write(data)
        stdin.seek(0)
        try:
            for signum in (signal.SIGINT, signal.SIGTERM):
                handlers[signum] = signal.signal(signum, cancel)
            process = subprocess.Popen([str(arg) for arg in argv], cwd=cwd, env=env,
                                       stdin=stdin, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, start_new_session=True,
                                       preexec_fn=limits)
            os.set_blocking(process.stdout.fileno(), False)
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                if time.monotonic() - started >= timeout:
                    reason = 'timeout'
                    break
                if disk_root and _disk_usage(disk_root) > disk_limit:
                    reason = 'disk_limit'
                    break
                for key, _ in selector.select(0.05):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    total += len(chunk)
                    captured.extend(chunk[:max(0, output_limit - len(captured))])
                    if total > output_limit:
                        reason = 'output_limit'
                        break
                if reason or (process.poll() is not None and not selector.get_map()):
                    break
        except KeyboardInterrupt:
            reason, interrupted = 'cancelled', True
        except OSError:
            reason = 'spawn_error'
        finally:
            if process is not None:
                # Kill same-session descendants even when the leader has exited.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                process.stdout.close()
            selector.close()
            for signum, handler in handlers.items():
                signal.signal(signum, handler)
    return {'exit_code': process.returncode if process is not None else None,
            'reason': reason, 'duration_seconds': round(time.monotonic() - started, 6),
            'output_bytes': total, 'output': captured.decode('utf-8', 'replace'),
            'interrupted': interrupted}
