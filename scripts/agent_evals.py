"""Metadata-only synthetic evaluation runner; stdlib, offline scoring by default."""
import contextlib
import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
import uuid

from agent_grading import digest, load_cases, populate, score
from agent_grading import validate_case
from agent_process import SafetyError, bounded, environment, files, real_directory

SCHEMA_VERSION = 1
APP = 'dotfiles-agent-evals-v1'
STATUSES = ('pass', 'fail', 'blocked', 'error', 'unknown')
RUN_ID = re.compile(r'[0-9]{8}T[0-9]{6}Z-[a-f0-9]{12}')
REASONS = (None, 'pending', 'live_opt_in_required', 'unsupported_profile',
           'unsupported_harness', 'harness_unavailable', 'unsupported_cli',
           'sandbox_unavailable', 'auth_unavailable', 'timeout', 'output_limit',
           'disk_limit', 'cancelled', 'spawn_error', 'harness_failed',
           'candidate_invalid', 'git_metadata_changed', 'grader_failed', 'internal_error', 'agent_activity_unconfirmed', 'cleanup_failed')


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def state_root():
    base = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))).expanduser()
    return base / 'dotfiles/agent-evals'


def ensure_state(path=None, create=True):
    root = real_directory(path or state_root(), create=create, private=True)
    marker = root / '.owner.json'
    if marker.is_symlink():
        raise SafetyError('State ownership marker cannot be a symlink.')
    if not marker.exists():
        if not create:
            raise SafetyError('State directory is not runner-owned.')
        if any(root.iterdir()):
            raise SafetyError('Refusing to claim a nonempty, unmanaged state directory.')
        descriptor = os.open(str(marker), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, 'w') as stream:
            json.dump({'app': APP, 'uid': os.getuid()}, stream)
    if not marker.is_file() or marker.stat().st_size > 1024 or json.loads(marker.read_text()) != {'app': APP, 'uid': os.getuid()}:
        raise SafetyError('Invalid state ownership marker.')
    for name in ('runs', 'work'):
        real_directory(root / name, create=create, private=True)
    return root


def validate_result(record):
    keys = {'schema_version', 'run_id', 'kind', 'case_id', 'case_version', 'case_hash',
            'fixture_hash', 'grader_hash', 'runner_hash', 'limits', 'base_commit', 'harness', 'harness_version',
            'model', 'policy_hash', 'policy_mode', 'platform', 'execution_mode',
            'started_at', 'finished_at', 'duration_seconds', 'status', 'reason',
            'agent_executed', 'process', 'checks', 'retry_count', 'usage', 'cost_usd'}
    if not isinstance(record, dict) or set(record) != keys or type(record['schema_version']) is not int or record['schema_version'] != 1:
        raise SafetyError('Invalid result schema.')
    if not isinstance(record['run_id'], str) or not RUN_ID.fullmatch(record['run_id']):
        raise SafetyError('Invalid run ID.')
    if record['kind'] not in ('grader', 'live') or record['status'] not in STATUSES or record['reason'] not in REASONS:
        raise SafetyError('Invalid result outcome.')
    if not isinstance(record['case_id'], str) or not re.fullmatch('[A-Z][0-9]{2}', record['case_id']) or type(record['case_version']) is not int or record['case_version'] < 1:
        raise SafetyError('Invalid result case.')
    for key in ('case_hash', 'fixture_hash', 'grader_hash', 'runner_hash', 'policy_hash'):
        if not isinstance(record[key], str) or not re.fullmatch('[a-f0-9]{64}', record[key]):
            raise SafetyError('Invalid provenance hash.')
    limits = record['limits']
    if not isinstance(limits, dict) or set(limits) != {'timeout_seconds', 'output_bytes', 'disk_bytes'} or any(type(v) is not int or v <= 0 for v in limits.values()):
        raise SafetyError('Invalid resource limits.')
    if record['kind'] == 'live' and record['status'] == 'pass' and not record['agent_executed']:
        raise SafetyError('A live pass requires observed agent activity.')
    if record['base_commit'] is not None and (not isinstance(record['base_commit'], str) or not re.fullmatch('[a-f0-9]{40,64}', record['base_commit'])):
        raise SafetyError('Invalid base commit.')
    if record['harness'] not in (None, 'codex', 'claude', 'opencode', 'pi') or record['execution_mode'] not in ('offline-trusted', 'trusted-native-gated'):
        raise SafetyError('Invalid harness or execution mode.')
    for key in ('harness_version', 'model'):
        value = record[key]
        if value is not None and (not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._:/()-]{0,99}', value)):
            raise SafetyError('Invalid harness metadata.')
        if value is not None:
            from check_private import check_content
            if check_content(value.encode()):
                raise SafetyError('Sensitive-looking harness metadata is not allowed.')
    if record['policy_mode'] not in ('current', 'baseline') or record['platform'] not in ('linux', 'darwin'):
        raise SafetyError('Invalid run configuration.')
    for key in ('started_at', 'finished_at'):
        if record[key] is not None:
            try:
                date = datetime.datetime.fromisoformat(record[key])
            except (ValueError, TypeError):
                raise SafetyError('Invalid result timestamp.') from None
            if date.tzinfo is None:
                raise SafetyError('Result timestamps must include a timezone.')
    for key in ('duration_seconds', 'cost_usd'):
        value = record[key]
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
            raise SafetyError('Invalid numeric metric.')
    if type(record['agent_executed']) is not bool or type(record['retry_count']) is not int or record['retry_count'] != 0:
        raise SafetyError('Invalid invocation metadata.')
    proc = record['process']
    if not isinstance(proc, dict) or set(proc) != {'exit_code', 'reason', 'output_bytes'}:
        raise SafetyError('Invalid process metadata.')
    if proc['reason'] not in REASONS or (proc['exit_code'] is not None and type(proc['exit_code']) is not int):
        raise SafetyError('Invalid process outcome.')
    if type(proc['output_bytes']) is not int or proc['output_bytes'] < 0:
        raise SafetyError('Invalid output metric.')
    if not isinstance(record['checks'], list) or len(record['checks']) > 16:
        raise SafetyError('Invalid check list.')
    for check in record['checks']:
        if (not isinstance(check, dict) or set(check) != {'id', 'status', 'exit_code'} or
                not isinstance(check['id'], str) or not re.fullmatch('[a-z_]{1,32}', check['id']) or
                check['status'] not in STATUSES or
                (check['exit_code'] is not None and type(check['exit_code']) is not int)):
            raise SafetyError('Invalid check result.')
    usage = record['usage']
    if usage is not None and (not isinstance(usage, dict) or
            any(key not in ('input_tokens', 'output_tokens', 'cached_input_tokens') or type(value) is not int or value < 0 for key, value in usage.items())):
        raise SafetyError('Invalid usage metrics.')
    return record


def new_record(root, case, kind, policy_mode='current'):
    policy = (Path(root) / 'agent-workflow/AGENTS.md').read_bytes() if policy_mode == 'current' else b''
    grader = (Path(__file__).with_name('agent_grading.py')).read_bytes()
    runner = b''.join(Path(__file__).with_name(name).read_bytes() for name in ('agent_evals.py', 'agent_process.py', 'agent_tools.py'))
    return {'schema_version': 1,
            'run_id': datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:12],
            'kind': kind, 'case_id': case['id'], 'case_version': case['version'],
            'case_hash': digest(case), 'fixture_hash': case['fixture']['sha256'],
            'grader_hash': hashlib.sha256(grader).hexdigest(), 'runner_hash': hashlib.sha256(runner).hexdigest(),
            'limits': {'timeout_seconds': case['timeout_seconds'], 'output_bytes': 1048576, 'disk_bytes': 33554432}, 'base_commit': None,
            'harness': 'codex' if kind == 'live' else None, 'harness_version': None,
            'model': None, 'policy_hash': hashlib.sha256(policy).hexdigest(),
            'policy_mode': policy_mode, 'platform': sys.platform,
            'execution_mode': 'trusted-native-gated' if kind == 'live' else 'offline-trusted',
            'started_at': utcnow(), 'finished_at': None, 'duration_seconds': None,
            'status': 'unknown', 'reason': 'pending', 'agent_executed': False,
            'process': {'exit_code': None, 'reason': None, 'output_bytes': 0},
            'checks': [], 'retry_count': 0, 'usage': None, 'cost_usd': None}


def text_report(record):
    validate_result(record)
    return ('{run_id}: {kind} {case_id} {status}\n'
            'harness={harness} version={harness_version} model={model}\n'
            'agent_executed={agent_executed} mode={execution_mode} reason={reason}\n'
            'duration_seconds={duration_seconds} cost_usd={cost_usd}\n').format(**record)


def save_result(state, record):
    validate_result(record)
    state = ensure_state(state)
    for suffix, content in (('.json', json.dumps(record, indent=2, allow_nan=False) + '\n'),
                            ('.txt', text_report(record))):
        target = state / 'runs' / (record['run_id'] + suffix)
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise SafetyError('Result path is occupied by a non-regular file.')
        descriptor, temporary = tempfile.mkstemp(prefix='.record-', dir=target.parent)
        try:
            with os.fdopen(descriptor, 'w') as stream:
                stream.write(content)
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return state / 'runs' / (record['run_id'] + '.json')


def read_results(state, run_id=None):
    state = ensure_state(state, create=False)
    directory = real_directory(state / 'runs')
    if run_id is not None and not RUN_ID.fullmatch(run_id):
        raise SafetyError('Invalid run ID.')
    paths = [directory / (run_id + '.json')] if run_id else sorted(directory.glob('*.json'))
    if len(paths) > 10000:
        raise SafetyError('Too many result files; prune old owned results.')
    result = []
    for path in paths:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > 65536:
            raise SafetyError('Result file must be bounded, regular and unlinked.')
        record = validate_result(json.loads(path.read_text()))
        if path.stem != record['run_id']:
            raise SafetyError('Run ID does not match its result filename.')
        result.append(record)
    return result


def aggregate(records):
    groups = {}
    fields = ('kind', 'case_hash', 'fixture_hash', 'grader_hash', 'harness', 'harness_version',
              'model', 'policy_hash', 'policy_mode', 'platform', 'execution_mode', 'runner_hash', 'limits')
    for record in records:
        validate_result(record)
        configuration = {field: record[field] for field in fields}
        if record['kind'] == 'live' and record['model'] is None:
            configuration['unresolved_model_run'] = record['run_id']
        key = digest(configuration)
        group = groups.setdefault(key, {'configuration': configuration,
                                       'sample_size': 0, 'outcomes': {s: 0 for s in STATUSES},
                                       'duration_seconds': [], 'retry_count': 0,
                                       'known_cost_usd': 0, 'unknown_cost_count': 0,
                                       'failing_checks': {}, 'agent_execution_count': 0,
                                       'known_usage_totals': {name: 0 for name in ('input_tokens', 'output_tokens', 'cached_input_tokens')},
                                       'unknown_usage_counts': {name: 0 for name in ('input_tokens', 'output_tokens', 'cached_input_tokens')}})
        group['sample_size'] += 1
        group['outcomes'][record['status']] += 1
        group['agent_execution_count'] += int(record['agent_executed'])
        group['retry_count'] += record['retry_count']
        if record['duration_seconds'] is not None:
            group['duration_seconds'].append(record['duration_seconds'])
        if record['cost_usd'] is None:
            group['unknown_cost_count'] += 1
        else:
            group['known_cost_usd'] += record['cost_usd']
        for name in group['known_usage_totals']:
            if record['usage'] is None or name not in record['usage']:
                group['unknown_usage_counts'][name] += 1
            else:
                group['known_usage_totals'][name] += record['usage'][name]
        for check in record['checks']:
            if check['status'] in ('fail', 'error'):
                group['failing_checks'][check['id']] = group['failing_checks'].get(check['id'], 0) + 1
    for group in groups.values():
        values = group.pop('duration_seconds')
        group['mean_duration_seconds'] = sum(values) / len(values) if values else None
        complete = group['outcomes']['pass'] + group['outcomes']['fail']
        group['observed_success_fraction'] = group['outcomes']['pass'] / complete if complete else None
    return {'schema_version': 1, 'groups': list(groups.values()),
            'comparison_note': 'Groups differ by recorded configuration; small samples do not establish reliability or causal policy effects.'}


@contextlib.contextmanager
def run_lock(state):
    descriptor = os.open(str(state / '.lock'), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise SafetyError('Unsafe evaluation lock.')
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SafetyError('Another evaluation is running; concurrency is limited to one.')
        yield
    finally:
        os.close(descriptor)


def owned_workspace(state, run_id):
    if not RUN_ID.fullmatch(run_id):
        raise SafetyError('Invalid owned run ID.')
    path = state / 'work' / run_id
    path.mkdir(mode=0o700)
    token = uuid.uuid4().hex
    marker = path / '.owner.json'
    marker.write_text(json.dumps({'app': APP, 'token': token, 'run_id': run_id, 'uid': os.getuid()}))
    marker.chmod(0o600)
    return path, token


def cleanup_owned(state, path, token):
    state = real_directory(state)
    path = real_directory(path, private=True)
    if path.parent != state / 'work' or not RUN_ID.fullmatch(path.name):
        raise SafetyError('Refusing cleanup outside runner-owned work roots.')
    marker = path / '.owner.json'
    info = marker.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > 1024:
        raise SafetyError('Invalid ownership marker.')
    expected = {'app': APP, 'token': token, 'run_id': path.name, 'uid': os.getuid()}
    if json.loads(marker.read_text()) != expected or not getattr(shutil.rmtree, 'avoids_symlink_attacks', False):
        raise SafetyError('Ownership or symlink-safe deletion could not be established.')
    shutil.rmtree(path)


def codex_config(env, workspace):
    # Keep native scratch state in one runner-owned directory, never all /tmp.
    runtime = Path(env['HOME']).parent / 'tool-runtime'
    runtime.mkdir(mode=0o700, exist_ok=True)
    env['TMPDIR'] = str(runtime)
    env['XDG_RUNTIME_DIR'] = str(runtime)
    # Current named permissions, not legacy sandbox/profile compatibility flags.
    config = '''approval_policy = "never"
default_permissions = "eval"
web_search = "disabled"
[permissions.eval]
extends = ":workspace"
[permissions.eval.filesystem]
":root" = "deny"
":slash_tmp" = "deny"
":minimal" = "read"
":workspace_roots" = "write"
[permissions.eval.network]
enabled = false
[features]
hooks = false
memories = false
multi_agent = false
goals = false
apps = false
[plugins._default]
enabled = false
[shell_environment_policy]
inherit = "none"
[shell_environment_policy.set]
HOME = "/nonexistent"
PATH = "/usr/bin:/bin"
PYTHONDONTWRITEBYTECODE = "1"
GIT_CONFIG_NOSYSTEM = "1"
GIT_CONFIG_GLOBAL = "/dev/null"
GIT_TERMINAL_PROMPT = "0"
'''
    # Deny tools access to profile credentials and all sibling runner artifacts.
    # Tables cannot be reopened. Put additional direct path grants before network.
    tool_roots = set()
    for executable in (sys.executable, shutil.which('codex')):
        if executable:
            resolved = Path(executable).resolve()
            prefix = next((Path(item) for item in ('/home/linuxbrew/.linuxbrew', '/opt/homebrew')
                           if resolved == Path(item) or Path(item) in resolved.parents), resolved.parent)
            tool_roots.add(str(prefix))
    extra = '\n' + ''.join(json.dumps(item) + ' = "read"\n' for item in sorted(tool_roots))
    extra += (json.dumps(str(workspace.parent)) + ' = "read"\n' +
              json.dumps(str(runtime)) + ' = "write"\n' +
              json.dumps(str(workspace / '.git')) + ' = "read"\n')
    config = config.replace('[permissions.eval.network]', extra + '[permissions.eval.network]')
    path = Path(env['CODEX_HOME']) / 'config.toml'
    path.write_text(config)
    path.chmod(0o600)
    return path


def native_probe(executable, workspace, env):
    """Offline all-or-nothing gate; no model or authentication is used."""
    canary_directory = tempfile.TemporaryDirectory(prefix='dotfiles-outside-canary-', dir=workspace.parent.parent)
    outside = Path(canary_directory.name) / 'canary'
    outside.write_text('synthetic private canary')
    (workspace / 'probe-link').symlink_to(outside)
    server = socket.socket()
    server.bind(('127.0.0.1', 0))
    server.listen(2)
    # Establish that this local endpoint is reachable outside the native sandbox.
    with socket.create_connection(server.getsockname(), timeout=1):
        pass
    probe = '''import pathlib, socket, sys
root, outside, home = map(pathlib.Path, sys.argv[1:4])
(root / "probe-write").write_text("ok")
for path in (outside, root / "probe-link", home / "config.toml"):
    try:
        path.read_text()
    except OSError:
        pass
    else:
        raise SystemExit(41)
try:
    outside.write_text("changed")
except OSError:
    pass
else:
    raise SystemExit(42)
config = root / ".git/config"
if config.exists():
    try:
        config.write_text("unexpected metadata change")
    except OSError:
        pass
    else:
        raise SystemExit(43)
try:
    connection = socket.create_connection(("127.0.0.1", int(sys.argv[4])), timeout=1)
except OSError:
    pass
else:
    connection.close()
    raise SystemExit(44)
'''
    try:
        outcome = bounded([executable, '--no-daemon', 'sandbox', '-P', 'eval', '-C', workspace,
                           '--', sys.executable, '-I', '-c', probe, workspace, outside, env['CODEX_HOME'], str(server.getsockname()[1])],
                          cwd=workspace, env=env, timeout=10, output_limit=65536)
        passed = outcome['exit_code'] == 0 and outcome['reason'] is None and outside.read_text() == 'synthetic private canary'
        # No protected/adversarial live mode is exposed: this native-command
        # probe does not prove that every model tool has identical coverage.
        return passed, outcome
    finally:
        for name in ('probe-link', 'probe-write'):
            path = workspace / name
            if path.exists() or path.is_symlink():
                path.unlink()
        outside.unlink()
        canary_directory.cleanup()
        server.close()


def native_grader(executable):
    """Sandbox submitted Python too; model output is not implicitly trusted."""
    def execute(argv, **kwargs):
        # The new grading context contains checker + copied submission; neither
        # existed in the original agent-visible checkout during model execution.
        grading_context = Path(kwargs['cwd']).parent
        codex_config(kwargs['env'], grading_context)
        command = [executable, '--no-daemon', 'sandbox', '-P', 'eval', '-C', grading_context, '--', *argv]
        return bounded(command, **kwargs)
    return execute


def run_live(root, case, *, live=False, harness='codex', timeout=180, output_limit=1048576,
             profile='trusted', policy_mode='current', auth_file=None, model=None, state=None, disk_limit=134217728):
    validate_case(case)
    if policy_mode not in ('current', 'baseline') or harness not in ('codex', 'claude', 'opencode', 'pi'):
        raise SafetyError('Unsupported policy or harness name.')
    if type(disk_limit) is not int or not 1048576 <= disk_limit <= 268435456:
        raise SafetyError('Live disk limit must be 1–256 MiB.')
    if not 1 <= timeout <= 180 or not 1024 <= output_limit <= 1048576:
        raise SafetyError('Live limits must be 1–180 seconds and 1 KiB–1 MiB output.')
    if model is not None and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,99}', model):
        raise SafetyError('Invalid model identifier.')
    state = ensure_state(state)
    record = new_record(root, case, 'live', policy_mode)
    record['harness'] = harness
    record['model'] = model
    record['limits'] = {'timeout_seconds': timeout, 'output_bytes': output_limit, 'disk_bytes': disk_limit}
    started = time.monotonic()
    base = token = None
    with run_lock(state):
        save_result(state, record)
        try:
            if not live:
                record.update(status='blocked', reason='live_opt_in_required')
            elif profile != 'trusted':
                record.update(status='blocked', reason='unsupported_profile')
            elif harness != 'codex':
                record.update(status='blocked', reason='unsupported_harness')
            else:
                executable = shutil.which('codex')
                if not executable:
                    record.update(status='blocked', reason='harness_unavailable')
                else:
                    base, token = owned_workspace(state, record['run_id'])
                    work = base / 'workspace/repo'
                    work.mkdir(parents=True)
                    populate(work, case['fixture']['files'])
                    env = environment(base / 'home')
                    codex_config(env, work)
                    version = bounded([executable, '--version'], cwd=work, env=env, timeout=5, output_limit=65536)
                    match = re.search(r'codex-cli (0\.169\.[0-9]+)', version['output'])
                    if not match:
                        record.update(status='blocked', reason='unsupported_cli')
                    else:
                        record['harness_version'] = match.group(1)
                        for args in (['init', '-q', '--template='], ['config', 'user.name', 'Synthetic Eval'],
                                     ['config', 'user.email', 'eval@example.invalid'], ['config', 'core.hooksPath', '/dev/null'],
                                     ['add', '.'], ['-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture']):
                            result = bounded(['git', *args], cwd=work, env=env, timeout=5)
                            if result['exit_code'] != 0 or result['reason']:
                                raise SafetyError('Could not create independent fixture Git metadata.')
                        result = bounded(['git', 'rev-parse', 'HEAD'], cwd=work, env=env, timeout=5)
                        commit = result['output'].strip()
                        if not re.fullmatch('[a-f0-9]{40,64}', commit):
                            raise SafetyError('Could not inspect the fixture base commit.')
                        record['base_commit'] = commit
                        git_config = (work / '.git/config').read_bytes()
                        passed, probe = native_probe(executable, work, env)
                        record['checks'].append({'id': 'native_filesystem_probe', 'status': 'pass' if passed else 'error', 'exit_code': probe['exit_code']})
                        if not passed:
                            record.update(status='blocked', reason='sandbox_unavailable')
                            record['process'] = {key: probe[key] for key in ('exit_code', 'reason', 'output_bytes')}
                        elif auth_file is None:
                            record.update(status='blocked', reason='auth_unavailable')
                        else:
                            auth = Path(auth_file).expanduser()
                            info = auth.lstat()
                            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_size > 256 * 1024 or info.st_nlink != 1:
                                raise SafetyError('Authentication must be a bounded regular file.')
                            destination = Path(env['CODEX_HOME']) / 'auth.json'
                            descriptor = os.open(str(destination), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                            with os.fdopen(descriptor, 'wb') as stream:
                                stream.write(auth.read_bytes())
                            if policy_mode == 'current':
                                (Path(env['CODEX_HOME']) / 'AGENTS.md').write_bytes((Path(root) / 'agent-workflow/AGENTS.md').read_bytes())
                            argv = [executable, '--no-daemon', 'exec', '--strict-config', '--ephemeral',
                                    '--ignore-rules', '--color', 'never', '--json', '-C', work]
                            if model:
                                argv += ['--model', model]
                            argv += ['-']
                            outcome = bounded(argv, cwd=work, env=env, timeout=timeout,
                                              output_limit=output_limit, disk_root=base, disk_limit=disk_limit,
                                              input_text=case['task'] + '\nDo not commit, add remotes, use network tools, or modify Git metadata.\n')
                            record['process'] = {key: outcome[key] for key in ('exit_code', 'reason', 'output_bytes')}
                            for line in outcome['output'].splitlines():
                                try:
                                    event = json.loads(line)
                                except ValueError:
                                    continue
                                if isinstance(event, dict) and (event.get('type') == 'turn.completed' or
                                        (event.get('type') == 'item.completed' and isinstance(event.get('item'), dict) and
                                         event['item'].get('type') in ('agent_message', 'command_execution', 'file_change'))):
                                    record['agent_executed'] = True
                                usage = event.get('usage') if isinstance(event, dict) and event.get('type') == 'turn.completed' else None
                                if isinstance(usage, dict):
                                    record['usage'] = {key: value for key, value in usage.items() if key in ('input_tokens', 'output_tokens', 'cached_input_tokens') and type(value) is int and value >= 0}
                            if outcome['reason']:
                                record.update(status='error', reason=outcome['reason'])
                            elif outcome['exit_code'] != 0:
                                record.update(status='error', reason='harness_failed')
                            elif not record['agent_executed']:
                                record.update(status='unknown', reason='agent_activity_unconfirmed')
                            elif (work / '.git/config').read_bytes() != git_config:
                                record.update(status='fail', reason='git_metadata_changed')
                            else:
                                graded = score(case, work, executor=native_grader(executable))
                                record['status'] = graded['status']
                                record['reason'] = None if graded['status'] == 'pass' else 'grader_failed'
                                record['checks'] += graded['checks']
        except KeyboardInterrupt:
            record.update(status='error', reason='cancelled')
        except (OSError, ValueError, subprocess.SubprocessError):
            record.update(status='error', reason='internal_error')
        finally:
            record['finished_at'] = utcnow()
            record['duration_seconds'] = round(time.monotonic() - started, 6)
            try:
                if base is not None:
                    cleanup_owned(state, base, token)
            except (OSError, ValueError):
                record.update(status='error', reason='cleanup_failed')
            finally:
                save_result(state, record)
    return record


def prune(state, days=30, apply=False):
    if type(days) is not int or days < 1:
        raise SafetyError('Retention must be at least one day.')
    if not Path(state).exists() and not apply:
        return []
    state = ensure_state(state, create=apply)
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    selected = []
    with run_lock(state) if apply else contextlib.nullcontext():
        for record in read_results(state):
            if datetime.datetime.fromisoformat(record['finished_at'] or record['started_at']) < cutoff:
                selected.append(record['run_id'])
                if apply:
                    for suffix in ('.json', '.txt'):
                        path = state / 'runs' / (record['run_id'] + suffix)
                        if path.is_symlink() or (path.exists() and not path.is_file()):
                            raise SafetyError('Refusing to prune a non-regular report.')
                    for suffix in ('.json', '.txt'):
                        (state / 'runs' / (record['run_id'] + suffix)).unlink(missing_ok=True)
        # Stale work trees are considered only while the runner lock is held.
        for path in (state / 'work').iterdir():
            if path.is_symlink() or not path.is_dir() or not RUN_ID.fullmatch(path.name):
                continue
            marker = path / '.owner.json'
            if marker.is_symlink() or not marker.is_file() or marker.stat().st_size > 1024:
                continue
            if datetime.datetime.fromtimestamp(marker.stat().st_mtime, datetime.timezone.utc) >= cutoff:
                continue
            owner = json.loads(marker.read_text())
            if owner.get('app') == APP and owner.get('uid') == os.getuid():
                if apply:
                    cleanup_owned(state, path, owner.get('token'))
    return selected
