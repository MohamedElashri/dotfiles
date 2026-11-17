"""Small agent CLI: local diagnostics, non-destructive onboarding and evaluations."""
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time

import agent_evals as evaluations
from agent_grading import load_cases, score
from agent_process import SafetyError, bounded, environment, real_directory

HARNESSES = {
    'codex': {'file': '.codex/AGENTS.md', 'adapter': 'trusted-only',
              'limitation': '0.169.x adapter; native command probe required. Protected/all-tool isolation unverified.'},
    'claude': {'file': '.claude/CLAUDE.md', 'adapter': 'unsupported',
               'limitation': 'Documented Bash sandbox does not by itself cover every tool; no live adapter.'},
    'opencode': {'file': '.config/opencode/AGENTS.md', 'adapter': 'unsupported',
                 'limitation': 'Tool permissions require version-specific configuration; no verified OS boundary or live adapter.'},
    'pi': {'file': '.pi/agent/AGENTS.md', 'adapter': 'unsupported',
           'limitation': 'Extensions can add controls; no verified default all-tool sandbox or live adapter.'},
}


def doctor(root):
    result = []
    expected = Path(root) / 'agent-workflow/AGENTS.md'
    for name, capability in HARNESSES.items():
        target = Path.home() / capability['file']
        executable = shutil.which(name)
        version = None
        code = None
        if executable:
            with tempfile.TemporaryDirectory(prefix='dotfiles-agent-doctor-') as temp:
                home = Path(temp).resolve()
                env = environment(home, path=os.pathsep.join([str(Path(executable).parent), '/usr/bin', '/bin']))
                outcome = bounded([executable, '--version'], cwd=home, env=env, timeout=5, output_limit=32768)
                code = outcome['exit_code']
                if code == 0 and outcome['reason'] is None:
                    for line in outcome['output'].splitlines():
                        if re.fullmatch(r'(codex-cli )?[0-9]+\.[0-9]+\.[0-9]+(?: \(Claude Code\))?', line.strip()):
                            version = line.strip()
                            break
        override = target.with_name('AGENTS.override.md') if name in ('codex', 'pi') else None
        result.append({'harness': name, 'installed': executable is not None, 'version': version,
                       'version_exit_code': code, 'global_file': str(target),
                       'link': 'correct' if target.is_symlink() and target.resolve() == expected else
                               'unmanaged' if target.exists() or target.is_symlink() else 'missing',
                       'override_present': bool(override and override.exists()),
                       'adapter': capability['adapter'], 'protected': 'unsupported',
                       'native_enforcement': 'not tested', 'limitation': capability['limitation']})
    return result


def project_context(target):
    name = target.name
    readme = target / 'README.md'
    if readme.is_file() and not readme.is_symlink() and readme.stat().st_size <= 256 * 1024:
        for line in readme.read_text(errors='replace').splitlines():
            if line.startswith('# '):
                name = line[2:100].strip()
                break
    entries = sorted(item.name for item in target.iterdir() if not item.name.startswith('.'))[:30]
    commands = []
    package = target / 'package.json'
    if package.is_file() and not package.is_symlink() and package.stat().st_size <= 256 * 1024:
        config = json.loads(package.read_text())
        if not isinstance(config, dict):
            raise SafetyError('package.json must contain an object; fix it before initialization.')
        scripts = config.get('scripts', {})
        if isinstance(scripts, dict):
            manager = 'pnpm' if (target / 'pnpm-lock.yaml').is_file() else 'npm'
            for script in ('build', 'test', 'lint', 'format', 'dev'):
                if isinstance(scripts.get(script), str):
                    commands.append(manager + ' run ' + script)
    tests = target / 'tests'
    if tests.is_dir() and not tests.is_symlink():
        for test in list(tests.glob('test*.py'))[:20]:
            if not test.is_symlink() and test.stat().st_size < 128 * 1024 and 'import unittest' in test.read_text(errors='replace'):
                commands.append('python3 -m unittest discover -s tests -v')
                break
    return ('\n## Observed project context\n\nName: ' + name + '\n\nTop-level paths: ' +
            (', '.join('`' + item.replace('`', '') + '`' for item in entries) or '(empty project)') +
            '\n\nExisting command interfaces: ' + (', '.join('`' + command + '`' for command in commands) or
            'not detected; inspect project documentation before choosing commands') +
            '. These interfaces were discovered, not executed.\n')


def initialize(root, target, *, dry=False, with_plan=False):
    target = real_directory(target)
    guidance = [target / 'AGENTS.md', target / 'CLAUDE.md', target / '.claude/CLAUDE.md']
    existing = any(path.exists() or path.is_symlink() for path in guidance)
    proposals = []
    if not existing:
        text = (Path(root) / 'agent-workflow/templates/AGENTS.md').read_text() + project_context(target)
        proposals.append(('AGENTS.md', text))
    if with_plan and not (target / 'plan.md').exists() and not (target / 'plan.md').is_symlink():
        proposals.append(('plan.md', (Path(root) / 'agent-workflow/templates/plan.md').read_text()))
    created = []
    try:
        for name, text in proposals:
            if not dry:
                descriptor, temporary = tempfile.mkstemp(prefix='.agent-init-', dir=target)
                try:
                    with os.fdopen(descriptor, 'w') as stream:
                        stream.write(text)
                        stream.flush()
                        os.fchmod(stream.fileno(), 0o644)
                    # Publish exclusively only after the complete write succeeds.
                    os.link(temporary, target / name, follow_symlinks=False)
                    created.append((name, text))
                finally:
                    os.unlink(temporary)
    except OSError:
        # Roll back only files still containing our exact newly-created content.
        for name, text in created:
            path = target / name
            if not path.is_symlink() and path.is_file() and path.read_text() == text:
                path.unlink()
        raise
    return {'existing_guidance_preserved': existing, 'dry_run': dry,
            'files': [{'path': name, 'content': text} for name, text in proposals]}


def add_parser(commands):
    parser = commands.add_parser('agents', help='Local agent setup and opt-in synthetic evaluations')
    sub = parser.add_subparsers(dest='agent_command', required=True)
    command = sub.add_parser('doctor', help='Offline installed harness and instruction diagnostics')
    command.add_argument('--format', choices=('text', 'json'), default='text')
    command = sub.add_parser('init', help='Prepare project instructions without overwriting existing guidance')
    command.add_argument('--target', required=True, type=Path)
    command.add_argument('--dry-run', action='store_true')
    command.add_argument('--with-plan', action='store_true')
    command = sub.add_parser('eval', help='Offline graders, metadata reports and explicitly opt-in live runs')
    ev = command.add_subparsers(dest='eval_command', required=True)
    ev.add_parser('list')
    score_parser = ev.add_parser('score', help='Score a submitted candidate; never invokes a model')
    score_parser.add_argument('--case', required=True)
    score_parser.add_argument('--candidate', required=True, type=Path)
    score_parser.add_argument('--trusted-candidate', action='store_true', help='Consent to execute supplied synthetic Python code without hostile-code sandbox guarantees')
    run_parser = ev.add_parser('run', help='One bounded live Codex invocation; never runs in ordinary tests/CI')
    run_parser.add_argument('--case', required=True)
    run_parser.add_argument('--harness', choices=tuple(HARNESSES), required=True)
    run_parser.add_argument('--live', action='store_true')
    run_parser.add_argument('--timeout', type=int, required=True)
    run_parser.add_argument('--output-limit', type=int, required=True)
    run_parser.add_argument('--profile', choices=('trusted', 'read-only', 'workspace-write'), required=True)
    run_parser.add_argument('--policy', choices=('current', 'baseline'), default='current')
    run_parser.add_argument('--auth-file', type=Path, help='Explicit existing Codex authentication file; copied only after the native probe passes')
    run_parser.add_argument('--model')
    run_parser.add_argument('--disk-limit', type=int, default=134217728, help='Private temporary disk budget in bytes (default: 128 MiB; maximum: 256 MiB)')
    report = ev.add_parser('report', help='Metadata only; no session-history ingestion')
    report.add_argument('--run')
    report.add_argument('--format', choices=('text', 'json'), default='text')
    prune = ev.add_parser('prune', help='Preview deletion of old runner-owned records/workspaces')
    prune.add_argument('--days', type=int, default=30)
    prune.add_argument('--apply', action='store_true', help='Explicitly authorize deleting only old runner-owned state')
    for item in (score_parser, run_parser, report, prune):
        item.add_argument('--state', type=Path, help='Absolute private state directory (default: XDG_STATE_HOME/dotfiles/agent-evals)')
    return parser


def main(args, root):
    if args.agent_command == 'doctor':
        data = doctor(root)
        if args.format == 'json':
            print(json.dumps(data, indent=2))
        else:
            for row in data:
                print('{harness}: installed={installed} version={version} global={link} override={override_present}; adapter={adapter}; protected={protected}; native={native_enforcement}'.format(**row))
                print('  ' + row['limitation'])
        return 0
    if args.agent_command == 'init':
        data = initialize(root, args.target, dry=args.dry_run, with_plan=args.with_plan)
        if data['existing_guidance_preserved']:
            print('Existing project guidance preserved; no duplicate instruction file created.')
        for item in data['files']:
            print(('Would create: ' if args.dry_run else 'Created: ') + item['path'])
            if args.dry_run:
                print(item['content'])
        return 0
    cases = load_cases(root)
    if args.eval_command == 'list':
        for case in cases.values():
            print('{id} v{version}: {title} [{trust}]'.format(**case))
        return 0
    state = args.state or evaluations.state_root()
    if args.eval_command == 'report':
        records = evaluations.read_results(state, args.run) if state.exists() else []
        if args.run and not records:
            raise SafetyError('Requested result does not exist.')
        data = records[0] if args.run else evaluations.aggregate(records)
        if args.format == 'json':
            print(json.dumps(data, indent=2))
        elif args.run:
            print(evaluations.text_report(data), end='')
        else:
            for group in data['groups']:
                print(json.dumps(group, sort_keys=True))
            print(data['comparison_note'])
        return 0
    if args.eval_command == 'prune':
        print(json.dumps({'apply': args.apply, 'run_ids': evaluations.prune(state, args.days, args.apply)}))
        return 0
    if args.case not in cases:
        raise SafetyError('Unknown evaluation case; use agents eval list.')
    case = cases[args.case]
    if args.eval_command == 'run':
        record = evaluations.run_live(root, case, live=args.live, harness=args.harness,
                                      timeout=args.timeout, output_limit=args.output_limit,
                                      profile=args.profile, policy_mode=args.policy,
                                      auth_file=args.auth_file, model=args.model, state=state, disk_limit=args.disk_limit)
    else:
        started = time.monotonic()
        record = evaluations.new_record(root, case, 'grader')
        try:
            outcome = score(case, args.candidate, args.trusted_candidate)
            record['status'] = outcome['status']
            record['checks'] = outcome['checks']
            record['reason'] = None if outcome['status'] == 'pass' else 'grader_failed'
        except (OSError, ValueError):
            record.update(status='error', reason='candidate_invalid')
        record.update(finished_at=evaluations.utcnow(), duration_seconds=round(time.monotonic() - started, 6))
        evaluations.save_result(state, record)
    print(evaluations.text_report(record), end='')
    return 0 if record['status'] == 'pass' else 1 if record['status'] == 'fail' else 2
