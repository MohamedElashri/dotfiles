"""Offline agent tooling contracts; fake CLIs are not live model evidence."""
import argparse
import copy
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import agent_evals as evaluations
import agent_grading as grading
import agent_process as processes
import agent_tools
import workflow

ROOT = Path(__file__).resolve().parents[1]


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='dotfiles eval tests ')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.cases = grading.load_cases(ROOT)
        self.state = self.base / 'state'

    def candidate(self, case_id='E03', variant='pass'):
        case = self.cases[case_id]
        path = self.base / ('candidate-' + case_id + '-' + variant)
        path.mkdir()
        grading.populate(path, dict(case['fixture']['files'], **case['examples'][variant]))
        return path

    def test_good_and_bad_candidates_for_all_cases(self):
        self.assertEqual(set(self.cases), {'E01', 'E02', 'E03', 'E04', 'E05', 'R01', 'D01'})
        for case_id, case in self.cases.items():
            for variant in ('pass', 'fail'):
                with self.subTest(case=case_id, variant=variant):
                    result = grading.score(case, self.candidate(case_id, variant), trusted=True)
                    self.assertEqual(result['status'], variant)
                    if case_id in ('E01', 'E02'):
                        self.assertEqual(result['semantic_review'], 'unknown')

    def test_review_evidence_is_reproduced_against_actual_seeded_code(self):
        case = copy.deepcopy(self.cases['R01'])
        case['fixture']['files']['solution.py'] = case['fixture']['files']['solution.py'].replace('//', '/')
        case['fixture']['sha256'] = grading.digest(case['fixture']['files'])
        path = self.base / 'fixed-seed'
        path.mkdir()
        grading.populate(path, dict(case['fixture']['files'], **case['examples']['pass']))
        self.assertEqual(grading.score(case, path)['status'], 'fail')

    def test_functional_score_requires_explicit_trust(self):
        path = self.candidate()
        with mock.patch.object(grading, 'bounded') as execute:
            self.assertEqual(grading.score(self.cases['E03'], path)['status'], 'blocked')
        execute.assert_not_called()

    def test_invalid_manifests_and_paths_fail_before_execution(self):
        for mutation in ('version', 'hash', 'traversal', 'absolute', 'backslash', 'git', 'command', 'timeout'):
            case = copy.deepcopy(self.cases['E03'])
            if mutation == 'version':
                case['schema_version'] = 2
            elif mutation == 'hash':
                case['fixture']['sha256'] = '0' * 64
            elif mutation in ('traversal', 'absolute', 'backslash', 'git'):
                name = {'traversal': '../escape', 'absolute': '/escape', 'backslash': 'a\\b', 'git': '.git/config'}[mutation]
                case['fixture']['files'][name] = 'invalid'
                case['fixture']['sha256'] = grading.digest(case['fixture']['files'])
            elif mutation == 'command':
                case['acceptance_checks'][0] = 'arbitrary shell command'
            else:
                case['timeout_seconds'] = 999999
            with self.subTest(mutation=mutation), self.assertRaises(processes.SafetyError):
                grading.validate_case(case)
        with self.assertRaises(processes.SafetyError):
            grading.relative_name('.')

    def test_text_graders_handle_filename_dots_and_plain_test_headings(self):
        commit = self.candidate('E01')
        (commit / 'message.txt').write_text('fix(cache): invalidate stale cache.py entries\n')
        self.assertEqual(grading.score(self.cases['E01'], commit)['status'], 'pass')
        pr = self.candidate('E02')
        for heading in ('Testing\n-------', '**Testing:**', 'Validation:'):
            (pr / 'pr.md').write_text('Invalidate stale cache entries after writes.\n\n' + heading + '\nVerified locally.\n')
            self.assertEqual(grading.score(self.cases['E02'], pr)['status'], 'fail')
        review = self.candidate('R01')
        (review / 'finding.json').write_text('[]')
        self.assertEqual(grading.score(self.cases['R01'], review)['status'], 'fail')

    def test_symlinks_hardlinks_special_files_and_oversize_inputs_are_rejected(self):
        outside = self.base / 'outside'
        outside.write_text('untouched')
        for kind in ('symlink', 'hardlink', 'fifo', 'large'):
            path = self.base / kind
            path.mkdir()
            item = path / 'solution.py'
            if kind == 'symlink':
                item.symlink_to(outside)
            elif kind == 'hardlink':
                os.link(outside, item)
            elif kind == 'fifo':
                os.mkfifo(item)
            else:
                with item.open('wb') as stream:
                    stream.truncate(5 * 1024 * 1024)
            with self.subTest(kind=kind), self.assertRaises(processes.SafetyError):
                processes.files(path)
            item.unlink()
        self.assertEqual(outside.read_text(), 'untouched')

    def test_unrelated_edits_and_test_weakening_fail_scope(self):
        for case_id in ('E04', 'E05'):
            result = grading.score(self.cases[case_id], self.candidate(case_id, 'fail'), trusted=True)
            self.assertEqual(result['checks'][0]['status'], 'fail')
            self.assertEqual(result['status'], 'fail')

    def test_hidden_checks_are_outside_candidate_checkout(self):
        path = self.candidate()
        calls = []
        original = grading.bounded
        def execute(argv, **kwargs):
            calls.append(argv)
            self.assertFalse(Path(argv[2]).is_relative_to(path))
            self.assertNotEqual(Path(argv[3]), path)
            return original(argv, **kwargs)
        with mock.patch.object(grading, 'bounded', side_effect=execute):
            self.assertEqual(grading.score(self.cases['E03'], path, trusted=True)['status'], 'pass')
        self.assertEqual(len(calls), 1)
        self.assertFalse((path / '__pycache__').exists())

    def test_init_is_idempotent_preview_only_and_respects_existing_guidance(self):
        project = self.base / 'project'
        project.mkdir()
        (project / 'README.md').write_text('# Example project\n')
        (project / 'package.json').write_text('{"scripts":{"test":"node test.js","build":"node build.js"}}')
        before = sorted(p.name for p in project.iterdir())
        preview = agent_tools.initialize(ROOT, project, dry=True, with_plan=True)
        self.assertEqual([item['path'] for item in preview['files']], ['AGENTS.md', 'plan.md'])
        self.assertEqual(sorted(p.name for p in project.iterdir()), before)
        self.assertIn('npm run test', preview['files'][0]['content'])
        self.assertNotIn('just ', preview['files'][0]['content'])
        agent_tools.initialize(ROOT, project, with_plan=True)
        snapshot = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in project.iterdir()}
        self.assertEqual(agent_tools.initialize(ROOT, project, with_plan=True)['files'], [])
        self.assertEqual({p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in project.iterdir()}, snapshot)
        existing = self.base / 'existing'
        existing.mkdir()
        (existing / 'CLAUDE.md').write_text('authoritative project guidance')
        self.assertTrue(agent_tools.initialize(ROOT, existing)['existing_guidance_preserved'])
        self.assertFalse((existing / 'AGENTS.md').exists())
        self.assertFalse((existing / '.gitignore').exists())

    def test_init_refuses_symlinked_target(self):
        target = self.base / 'target'
        target.mkdir()
        link = self.base / 'link'
        link.symlink_to(target, target_is_directory=True)
        with self.assertRaises(processes.SafetyError):
            agent_tools.initialize(ROOT, link)
        self.assertEqual(list(target.iterdir()), [])

    def test_init_rolls_back_own_files_and_preserves_a_concurrent_user_file(self):
        project = self.base / 'racing-project'
        project.mkdir()
        original_link = os.link
        def publish(source, destination, **kwargs):
            if Path(destination).name == 'plan.md':
                Path(destination).write_text('user-owned concurrent plan')
                raise FileExistsError('concurrent file')
            return original_link(source, destination, **kwargs)
        with mock.patch.object(agent_tools.os, 'link', side_effect=publish), self.assertRaises(FileExistsError):
            agent_tools.initialize(ROOT, project, with_plan=True)
        self.assertEqual(sorted(path.name for path in project.iterdir()), ['plan.md'])
        self.assertEqual((project / 'plan.md').read_text(), 'user-owned concurrent plan')

    def test_doctor_missing_harnesses_is_offline_and_honest(self):
        with mock.patch.dict(os.environ, {'HOME': str(self.base)}, clear=True), \
                mock.patch.object(agent_tools.shutil, 'which', return_value=None), \
                mock.patch.object(agent_tools, 'bounded') as execute:
            rows = agent_tools.doctor(ROOT)
        execute.assert_not_called()
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row['version'] is None and not row['installed'] for row in rows))
        self.assertTrue(all(row['protected'] == 'unsupported' for row in rows))
        self.assertEqual(list(self.base.iterdir()), [])

    def test_minimal_environment_drops_credentials_and_network_settings(self):
        with mock.patch.dict(os.environ, {'SERVICE_TOKEN': 'synthetic example canary',
                                         'HTTP_PROXY': 'http://invalid', 'GIT_CONFIG_COUNT': '9'}):
            env = processes.environment(self.base / 'home')
        for name in ('SERVICE_TOKEN', 'HTTP_PROXY', 'GIT_CONFIG_COUNT', 'SSH_AUTH_SOCK', 'OPENAI_API_KEY'):
            self.assertNotIn(name, env)
        self.assertEqual(env['GIT_CONFIG_GLOBAL'], '/dev/null')
        self.assertEqual(env['PI_OFFLINE'], '1')

    def test_subprocess_limits_and_failure_codes(self):
        env = processes.environment(self.base / 'home')
        for source, reason in [('import time; time.sleep(10)', 'timeout'),
                               ('import os\nwhile True: os.write(1, b"x" * 65536)', 'output_limit')]:
            with self.subTest(reason=reason):
                result = processes.bounded([sys.executable, '-I', '-c', source], cwd=self.base,
                                           env=env, timeout=0.2 if reason == 'timeout' else 3, output_limit=1024)
                self.assertEqual(result['reason'], reason)
                self.assertLessEqual(len(result['output'].encode()), 1024)
                self.assertLess(result['duration_seconds'], 4)
        result = processes.bounded([sys.executable, '-I', '-c', 'raise SystemExit(7)'],
                                   cwd=self.base, env=env, timeout=5)
        self.assertEqual(result['exit_code'], 7)
        self.assertIsNone(result['reason'])

    def test_disk_limit_and_cancellation(self):
        env = processes.environment(self.base / 'home')
        result = processes.bounded([sys.executable, '-I', '-c', 'import pathlib,time; pathlib.Path("large").write_bytes(b"x"*20000); time.sleep(10)'],
                                   cwd=self.base, env=env, timeout=5, disk_root=self.base, disk_limit=10000)
        self.assertTrue(result['reason'] == 'disk_limit' or
                        (result['exit_code'] != 0 and ('File too large' in result['output'] or result['exit_code'] == -signal.SIGXFSZ)))
        with mock.patch.object(processes.selectors.DefaultSelector, 'select', side_effect=KeyboardInterrupt):
            result = processes.bounded([sys.executable, '-I', '-c', 'import time; time.sleep(10)'], cwd=self.base, env=env, timeout=5)
        self.assertEqual(result['reason'], 'cancelled')
        self.assertTrue(result['interrupted'])

    def test_explicit_budget_allows_a_bounded_harness_cache(self):
        env = processes.environment(self.base / 'home')
        source = 'import pathlib,time; f=pathlib.Path("cache").open("wb"); f.truncate(40*1024*1024); f.close(); time.sleep(0.1)'
        result = processes.bounded([sys.executable, '-I', '-c', source], cwd=self.base,
                                   env=env, timeout=5, disk_root=self.base, disk_limit=128 * 1024 * 1024)
        self.assertEqual(result['exit_code'], 0, result['output'])
        self.assertIsNone(result['reason'])
        for limit in (0, 1024 * 1024 * 1024):
            with self.subTest(limit=limit), self.assertRaises(processes.SafetyError):
                evaluations.run_live(ROOT, self.cases['E03'], disk_limit=limit, state=self.state)

    def test_same_session_descendants_are_terminated(self):
        env = processes.environment(self.base / 'home')
        code = 'import subprocess,sys,time; p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"]); print(p.pid,flush=True); time.sleep(30)'
        result = processes.bounded([sys.executable, '-I', '-c', code], cwd=self.base, env=env, timeout=0.4)
        pid = int(result['output'].strip())
        self.assertEqual(result['reason'], 'timeout')
        # SIGKILL delivery is asynchronous; allow exit/reaping to be observed.
        # A reparented zombie is stopped even if the host has not reaped it.
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            try:
                if sys.platform == 'linux' and Path('/proc/' + str(pid) + '/stat').read_text().split()[2] == 'Z':
                    return
                os.kill(pid, 0)
            except (ProcessLookupError, FileNotFoundError):
                return
            time.sleep(0.01)
        self.fail('Subprocess descendant remained alive after process-group termination')

    def test_sigterm_stops_the_worker_and_its_process_group(self):
        ready = self.base / 'ready'
        child = 'import pathlib, time, os; pathlib.Path(' + repr(str(ready)) + ').write_text(str(os.getpid())); time.sleep(30)'
        worker = ('import sys,json; sys.path.insert(0,' + repr(str(ROOT / 'scripts')) + '); '
                  'from agent_process import bounded, environment; from pathlib import Path; '
                  'env=environment(Path(' + repr(str(self.base / 'worker-home')) + ')); '
                  'print(json.dumps(bounded([sys.executable,"-I","-c",' + repr(child) + '],'
                  'cwd=' + repr(str(self.base)) + ',env=env,timeout=20)),flush=True)')
        process = subprocess.Popen([sys.executable, '-I', '-c', worker], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 5
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(ready.exists())
            process.send_signal(signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(json.loads(stdout)['reason'], 'cancelled')
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

    def test_state_permissions_unmanaged_state_and_symlink_paths(self):
        state = evaluations.ensure_state(self.state)
        self.assertEqual(state.stat().st_mode & 0o777, 0o700)
        self.assertEqual((state / '.owner.json').stat().st_mode & 0o777, 0o600)
        foreign = self.base / 'foreign'
        foreign.mkdir(mode=0o700)
        (foreign / 'notes').write_text('user data')
        with self.assertRaises(processes.SafetyError):
            evaluations.ensure_state(foreign)
        self.assertEqual(sorted(p.name for p in foreign.iterdir()), ['notes'])
        link = self.base / 'state-link'
        link.symlink_to(state, target_is_directory=True)
        with self.assertRaises(processes.SafetyError):
            evaluations.ensure_state(link)

    def test_owned_cleanup_never_follows_links_or_deletes_unowned_data(self):
        state = evaluations.ensure_state(self.state)
        record = evaluations.new_record(ROOT, self.cases['E03'], 'live')
        work, token = evaluations.owned_workspace(state, record['run_id'])
        unrelated = self.base / 'user-data'
        unrelated.mkdir()
        (unrelated / 'keep').write_text('keep')
        (work / 'link').symlink_to(unrelated, target_is_directory=True)
        with self.assertRaises(processes.SafetyError):
            evaluations.cleanup_owned(state, work, 'wrong-token')
        with self.assertRaises(processes.SafetyError):
            evaluations.cleanup_owned(state, unrelated, token)
        evaluations.cleanup_owned(state, work, token)
        self.assertEqual((unrelated / 'keep').read_text(), 'keep')
        self.assertFalse(work.exists())

    def test_result_contract_privacy_grouping_and_retention(self):
        record = evaluations.new_record(ROOT, self.cases['E03'], 'grader')
        record.update(status='pass', reason=None, duration_seconds=1, finished_at='2020-01-01T00:00:00+00:00')
        evaluations.save_result(self.state, record)
        result_path = self.state / 'runs' / (record['run_id'] + '.json')
        self.assertEqual(result_path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(evaluations.read_results(self.state), [record])
        changed = copy.deepcopy(record)
        changed['policy_hash'] = '0' * 64
        changed['cost_usd'] = 0
        data = evaluations.aggregate([record, changed])
        self.assertEqual(len(data['groups']), 2)
        self.assertEqual(data['groups'][0]['unknown_cost_count'], 1)
        self.assertEqual(data['groups'][1]['unknown_cost_count'], 0)
        for key, value in [('transcript', 'synthetic sensitive canary'), ('model', 'sk-' + 'X' * 40), ('cost_usd', float('nan')), ('started_at', 'synthetic sensitive canary'), ('reason', {})]:
            invalid = copy.deepcopy(record)
            invalid[key] = value
            with self.subTest(key=key), self.assertRaises(processes.SafetyError):
                evaluations.validate_result(invalid)
        (self.state / 'runs/notes.txt').write_text('unrelated notes')
        before = sorted(p.name for p in (self.state / 'runs').iterdir())
        self.assertEqual(evaluations.prune(self.state, 1), [record['run_id']])
        self.assertEqual(sorted(p.name for p in (self.state / 'runs').iterdir()), before)
        evaluations.prune(self.state, 1, apply=True)
        self.assertEqual((self.state / 'runs/notes.txt').read_text(), 'unrelated notes')
        self.assertFalse(result_path.exists())

    def test_live_is_explicit_and_protected_modes_fail_closed(self):
        for live, profile, harness, expected in [(False, 'trusted', 'codex', 'live_opt_in_required'),
                (True, 'read-only', 'codex', 'unsupported_profile'),
                (True, 'workspace-write', 'codex', 'unsupported_profile'),
                (True, 'trusted', 'claude', 'unsupported_harness')]:
            with self.subTest(expected=expected), mock.patch.object(evaluations, 'bounded') as execute:
                record = evaluations.run_live(ROOT, self.cases['E03'], live=live, profile=profile,
                                              harness=harness, state=self.state)
                self.assertEqual(record['status'], 'blocked')
                self.assertEqual(record['reason'], expected)
                self.assertFalse(record['agent_executed'])
                execute.assert_not_called()

    def fake_codex(self, body):
        path = self.base / 'codex'
        path.write_text('#!' + sys.executable + '\nimport sys, pathlib, json\nif "--version" in sys.argv:\n print("codex-cli 0.169.0"); sys.exit()\n' + body)
        path.chmod(0o755)
        return path

    def test_native_probe_failure_persists_blocker_without_reading_auth(self):
        fake = self.fake_codex('raise SystemExit(9)\n')
        outcome = {'exit_code': 1, 'reason': None, 'output_bytes': 34}
        with mock.patch.object(evaluations.shutil, 'which', return_value=str(fake)), \
                mock.patch.object(evaluations, 'native_probe', return_value=(False, outcome)):
            record = evaluations.run_live(ROOT, self.cases['E03'], live=True,
                                         auth_file=self.base / 'does-not-exist', state=self.state)
        self.assertEqual(record['reason'], 'sandbox_unavailable')
        self.assertFalse(record['agent_executed'])
        self.assertEqual(list((self.state / 'work').iterdir()), [])
        self.assertEqual(evaluations.read_results(self.state), [record])

    def test_fake_live_runner_scores_diff_and_discards_raw_output(self):
        good = self.cases['E03']['examples']['pass']['solution.py']
        fake = self.fake_codex('pathlib.Path("solution.py").write_text(' + repr(good) + ')\nprint(json.dumps({"type":"turn.completed","usage":{"input_tokens":12,"output_tokens":8},"message":"synthetic sensitive canary"}))\n')
        auth = self.base / 'auth-file'
        auth.write_text('{"synthetic":"test authentication"}')
        with mock.patch.object(evaluations.shutil, 'which', return_value=str(fake)), \
                mock.patch.object(evaluations, 'native_probe', return_value=(True, {'exit_code': 0})), \
                mock.patch.object(evaluations, 'native_grader', return_value=processes.bounded):
            record = evaluations.run_live(ROOT, self.cases['E03'], live=True, auth_file=auth, state=self.state)
        self.assertEqual(record['status'], 'pass')
        self.assertTrue(record['agent_executed'])
        self.assertEqual(record['usage']['input_tokens'], 12)
        self.assertIsNone(record['cost_usd'])
        self.assertEqual(list((self.state / 'work').iterdir()), [])
        for path in (self.state / 'runs').iterdir():
            self.assertNotIn('synthetic sensitive canary', path.read_text())
            self.assertNotIn('test authentication', path.read_text())
        self.assertEqual(auth.read_text(), '{"synthetic":"test authentication"}')

    def test_cli_parser_offline_commands_do_not_invoke_models(self):
        parser = workflow.parser(include_agents=True)
        for argv in (['agents', 'doctor'], ['agents', 'init', '--target', str(self.base), '--dry-run'],
                     ['agents', 'eval', 'list'], ['agents', 'eval', 'report', '--format', 'json']):
            args = parser.parse_args(argv)
            self.assertTrue(callable(args.func))
        with self.assertRaises(SystemExit):
            parser.parse_args(['agents', 'eval', 'run', '--case', 'E03', '--harness', 'codex'])


if __name__ == '__main__':
    unittest.main()
