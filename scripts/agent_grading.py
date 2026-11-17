"""Independent graders for the pinned synthetic cases; no model self-scoring.

Functional checks execute submitted code only with explicit trusted-candidate
consent. A sanitized temporary home is not a sandbox for hostile code.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile

from agent_process import SafetyError, bounded, environment, files

GRADERS = {'commit', 'pr', 'mean', 'normalize', 'percentage', 'review', 'pipeline'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def relative_name(value):
    if not isinstance(value, str) or not value or '\\' in value or '\x00' in value:
        raise SafetyError('Invalid fixture path.')
    path = PurePosixPath(value)
    if not path.parts or path.is_absolute() or '..' in path.parts or path.parts[0] == '.git' or path.as_posix() != value:
        raise SafetyError('Fixture paths must be normalized relative paths outside .git.')
    return value


def file_map(value):
    if not isinstance(value, dict) or not 1 <= len(value) <= 32:
        raise SafetyError('Expected 1–32 fixture files.')
    for name, text in value.items():
        relative_name(name)
        if not isinstance(text, str) or len(text.encode()) > 256 * 1024:
            raise SafetyError('Fixture files must be bounded UTF-8 text.')
    for name in value:
        if any(parent.as_posix() in value for parent in PurePosixPath(name).parents if parent.as_posix() != '.'):
            raise SafetyError('Fixture file/directory paths overlap.')
    return value


def validate_case(case):
    required = {'schema_version', 'id', 'version', 'title', 'task', 'fixture',
                'acceptance_checks', 'timeout_seconds', 'expected_change_scope',
                'required_capabilities', 'examples', 'trust'}
    if not isinstance(case, dict) or set(case) != required:
        raise SafetyError('Invalid case fields.')
    if type(case['schema_version']) is not int or case['schema_version'] != 1:
        raise SafetyError('Unsupported case schema version.')
    if not isinstance(case['id'], str) or not re.fullmatch('[A-Z][0-9]{2}', case['id']):
        raise SafetyError('Invalid case ID.')
    if type(case['version']) is not int or case['version'] < 1:
        raise SafetyError('Invalid case version.')
    for key, limit in [('title', 100), ('task', 8000)]:
        if not isinstance(case[key], str) or not 1 <= len(case[key]) <= limit:
            raise SafetyError('Invalid case text.')
    fixture = case['fixture']
    if not isinstance(fixture, dict) or set(fixture) != {'files', 'sha256'}:
        raise SafetyError('Invalid fixture descriptor.')
    file_map(fixture['files'])
    if fixture['sha256'] != digest(fixture['files']):
        raise SafetyError('Fixture hash mismatch.')
    checks = case['acceptance_checks']
    if not isinstance(checks, list) or len(checks) != 2 or not isinstance(checks[0], str) or checks[0] not in GRADERS or checks[1] != 'scope':
        raise SafetyError('Unsupported acceptance checks; arbitrary grader commands are not allowed.')
    if type(case['timeout_seconds']) is not int or not 1 <= case['timeout_seconds'] <= 60:
        raise SafetyError('Case timeout must be 1–60 seconds.')
    if not isinstance(case['expected_change_scope'], list) or not case['expected_change_scope']:
        raise SafetyError('Expected explicit change scope.')
    for name in case['expected_change_scope']:
        relative_name(name)
    if not isinstance(case['required_capabilities'], list) or any(
            item not in ('python', 'sqlite', 'workspace-write') for item in case['required_capabilities']):
        raise SafetyError('Unsupported case capability.')
    if case['trust'] != 'synthetic-trusted' or not isinstance(case['examples'], dict) or set(case['examples']) != {'pass', 'fail'}:
        raise SafetyError('Only trusted synthetic fixtures are supported.')
    for example in case['examples'].values():
        file_map(example)
        if not set(example) <= set(fixture['files']) | set(case['expected_change_scope']):
            raise SafetyError('Example escapes the fixture.')
    return case


def load_cases(root):
    path = Path(root) / 'agent-workflow/evals/cases.json'
    if path.stat().st_size > 1024 * 1024:
        raise SafetyError('Case registry is too large.')
    cases = json.loads(path.read_text())
    if not isinstance(cases, list) or not 1 <= len(cases) <= 32:
        raise SafetyError('Expected a bounded list of cases.')
    result = {}
    for case in cases:
        validate_case(case)
        if case['id'] in result:
            raise SafetyError('Duplicate case ID.')
        result[case['id']] = case
    return result


def populate(root, mapping):
    for name, text in file_map(mapping).items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8') as stream:
            stream.write(text)


# These checks are run from outside the candidate checkout, with a private copy
# of the submission. The agent sees fixture tests, not this acceptance program.
FUNCTION_CHECKS = {
    'mean': '''
assert solution.mean([1, 2]) == 1.5
assert solution.mean([-3, 0, 2]) == -1 / 3
assert solution.mean([0]) == 0
try:
    solution.mean([])
except ValueError:
    pass
else:
    raise AssertionError("empty input")
''',
    'normalize': '''
assert solution.normalize("  A\\t") == "a"
assert solution.normalize("\\nB  ") == "b"
assert solution.normalize("") == ""
''',
    'percentage': '''
assert solution.percentage(1, 2) == 50
assert solution.percentage(3, 4) == 75
assert solution.percentage(0, 10) == 0
try:
    solution.percentage(1, 0)
except ValueError:
    pass
else:
    raise AssertionError("zero total")
''',
    'pipeline': '''
from pathlib import Path
import sqlite3
source = Path("events.csv")
assert solution.ingest(source, "repeat.db") == (3, 35)
assert solution.ingest(source, "repeat.db") == (3, 35)
try:
    solution.ingest(source, "restart.db", fail_after=2)
except RuntimeError:
    pass
else:
    raise AssertionError("interruption was ignored")
with sqlite3.connect("restart.db") as connection:
    assert connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0
assert solution.ingest(source, "restart.db") == (3, 35)
assert solution.ingest(source, "restart.db") == (3, 35)
''',
}



def run_check(mapping, program, timeout, executor=None):
    with tempfile.TemporaryDirectory(prefix='dotfiles-grader-') as directory:
        base = Path(directory).resolve()
        work = base / 'workspace/submission'
        work.mkdir(parents=True)
        populate(work, mapping)
        env = environment(base / 'home')
        checker = work.parent / 'accept.py'
        checker.write_text('import os, sys\nsys.dont_write_bytecode = True\nsys.path.insert(0, sys.argv[1])\nos.chdir(sys.argv[1])\nimport solution\n' + program)
        execute = executor or bounded
        return execute([sys.executable, '-I', checker, work], cwd=work,
                       env=env, timeout=timeout, disk_root=base)


def score(case, candidate, trusted=False, executor=None):
    validate_case(case)
    submitted = files(candidate)
    baseline = case['fixture']['files']
    changed = {name for name in set(baseline) | set(submitted) if baseline.get(name) != submitted.get(name)}
    checks = [{'id': 'scope', 'status': 'pass' if changed <= set(case['expected_change_scope']) else 'fail',
               'exit_code': None}]
    kind = case['acceptance_checks'][0]
    if checks[0]['status'] == 'fail':
        checks.append({'id': kind, 'status': 'unknown', 'exit_code': None})
        return {'status': 'fail', 'checks': checks, 'semantic_review': None}
    passed = False
    exit_code = None
    status = 'fail'
    try:
        if kind == 'commit':
            text = submitted.get('message.txt', '').rstrip('\r\n')
            passed = (len(text.splitlines()) == 1 and len(text) <= 72 and
                      re.fullmatch(r'(feat|fix|refactor|perf|docs|test|build|ci|chore|revert)(\([a-z0-9-]+\))?!?: [a-z][^\n]*', text) is not None and
                      not text.endswith('.') and
                      'cache' in text and ('stale' in text or 'invalidat' in text))
        elif kind == 'pr':
            text = submitted.get('pr.md', '')
            forbidden_heading = any(line.strip(' #*_:\t').lower() in
                                    ('testing', 'validation', 'verification', 'test plan')
                                    for line in text.splitlines())
            passed = (20 <= len(text) <= 1200 and 'cache' in text.lower() and
                      not forbidden_heading and
                      not re.search(r'(?im)^\s*#{1,6}\s*(testing|validation|verification|test plan)\b', text) and
                      '```' not in text and not re.search(r'(?i)\b(all tests pass|everything passes)\b', text))
        elif kind == 'review':
            finding = json.loads(submitted.get('finding.json', '{}'))
            if not isinstance(finding, dict):
                raise ValueError('Expected a finding object.')
            values = finding.get('trigger', [])
            if (isinstance(values, list) and 1 <= len(values) <= 20 and
                    all(type(v) in (int, float) and abs(v) < 10000 for v in values)):
                observed, expected = sum(values) // len(values), sum(values) / len(values)
                passed = (finding.get('file') == 'solution.py' and finding.get('line') == 3 and
                          finding.get('observed') == observed and finding.get('expected') == expected and
                          observed != expected and isinstance(finding.get('impact'), str) and
                          len(finding['impact']) >= 10)
                if passed:
                    # Execute only the pinned repository fixture, not reviewer code.
                    program = ('import json\nfinding=json.load(open("finding.json"))\n'
                               'values=finding["trigger"]\nobserved=solution.mean(values)\n'
                               'expected=sum(values)/len(values)\n'
                               'assert observed == finding["observed"]\n'
                               'assert expected == finding["expected"] and observed != expected\n')
                    outcome = run_check({'solution.py': baseline['solution.py'],
                                         'finding.json': submitted['finding.json']}, program, case['timeout_seconds'], executor)
                    exit_code = outcome['exit_code']
                    passed = exit_code == 0 and outcome['reason'] is None
                    if outcome['reason']:
                        status = 'error'
        elif not trusted and executor is None:
            status = 'blocked'
        else:
            outcome = run_check(submitted, FUNCTION_CHECKS[kind], case['timeout_seconds'], executor)
            exit_code = outcome['exit_code']
            passed = exit_code == 0 and outcome['reason'] is None
            if outcome['reason']:
                status = 'error'
    except (ValueError, TypeError, ArithmeticError):
        passed = False
    checks.append({'id': kind, 'status': 'pass' if passed else status, 'exit_code': exit_code})
    overall = ('blocked' if status == 'blocked' else 'error' if status == 'error' else
               'pass' if all(item['status'] == 'pass' for item in checks) else 'fail')
    return {'status': overall, 'checks': checks,
            'semantic_review': 'unknown' if kind in ('commit', 'pr') else None}
