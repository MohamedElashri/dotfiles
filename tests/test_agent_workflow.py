"""Offline agent integration checks; all installed targets use disposable homes."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LINKS = {
    '.codex/AGENTS.md': 'agent-workflow/global.md',
    '.agents/skills/research-audit': 'agent-workflow/skills/research-audit',
    '.agents/skills/engineering-audit': 'agent-workflow/skills/engineering-audit',
    '.claude/skills/research-audit': 'agent-workflow/skills/research-audit',
    '.claude/skills/engineering-audit': 'agent-workflow/skills/engineering-audit',
}
SKILL_TARGETS = [target for target in LINKS if target != '.codex/AGENTS.md']


def manifest(path):
    return path / 'SKILL.md' if path.is_dir() else path


def snapshot(root):
    """Capture paths, content, and mtimes without following directory symlinks."""
    result = {}
    for directory, directories, files in os.walk(root, followlinks=False):
        for name in directories + files:
            path = Path(directory) / name
            content = str(path.readlink()) if path.is_symlink() else path.read_bytes() if path.is_file() else None
            result[str(path.relative_to(root))] = (content, path.lstat().st_mtime_ns)
    return result


class AgentWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dotfiles agents ')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()

    def home(self, name):
        home = self.base / name
        home.mkdir()
        return home

    def run_command(self, home, *args, check=True):
        env = dict(HOME=str(home), PATH='/usr/bin:/bin',
                   GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=str(home / '.gitconfig'))
        result = subprocess.run(args, cwd=ROOT, env=env, text=True, capture_output=True)
        if check:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def install(self, home, platform, *args, check=True):
        return self.run_command(home, 'bash', str(ROOT / 'install.sh'),
                                '--profile', 'personal', '--platform', platform, *args, check=check)

    def assert_links(self, home):
        self.assertFalse((home / '.codex').is_symlink())
        self.assertFalse((home / '.agents').is_symlink())
        self.assertFalse((home / '.claude').is_symlink())
        for target, source in LINKS.items():
            path = home / target
            self.assertTrue(path.is_symlink(), str(path))
            self.assertEqual(path.resolve(strict=True), ROOT / source)
            if path.is_dir():
                self.assertFalse((path / 'SKILL.md').is_symlink())
            self.assertEqual(manifest(path).read_bytes(), manifest(ROOT / source).read_bytes())

    def test_personal_platform_matrix(self):
        source_before = {source: manifest(ROOT / source).read_bytes() for source in LINKS.values()}
        for platform in ('linux', 'mac'):
            with self.subTest(platform=platform):
                home = self.home(platform)
                before = snapshot(home)
                listing = self.install(home, platform, '--list').stdout
                self.assertEqual(listing, self.install(home, platform, '--manifest').stdout)
                rows = {tuple(line.split('\t')) for line in listing.splitlines()}
                for target, source in LINKS.items():
                    self.assertIn((str(ROOT / source), str(home / target)), rows)
                agent_rows = [tuple(line.split('\t')) for line in listing.splitlines()
                              if line.startswith(str(ROOT / 'agent-workflow') + '/')]
                self.assertEqual(len(agent_rows), len(LINKS))
                self.assertEqual(set(agent_rows), {(str(ROOT / source), str(home / target))
                                                  for target, source in LINKS.items()})
                self.install(home, platform, '--check-existing')
                self.install(home, platform, '--dry-run')
                self.assertEqual(snapshot(home), before)
                self.install(home, platform)
                self.assert_links(home)
                self.install(home, platform, '--status')
                self.install(home, platform, '--check-existing')
                installed = snapshot(home)
                self.install(home, platform)
                self.assertEqual(snapshot(home), installed)
                self.assertFalse((home / '.dotfiles-backup').exists())
        self.assertEqual(source_before, {source: manifest(ROOT / source).read_bytes() for source in LINKS.values()})

    def test_unmanaged_files_are_backed_up_and_siblings_survive(self):
        for platform in ('linux', 'mac'):
            with self.subTest(platform=platform):
                home = self.home(platform)
                originals = {'.codex/AGENTS.md': b'Previous global instructions\n',
                             '.agents/skills/research-audit/SKILL.md': b'Previous research skill\n',
                             '.claude/skills/research-audit/SKILL.md': b'Previous Claude research skill\n'}
                siblings = {'.codex/config.toml': b'# local provider settings\n',
                            '.codex/AGENTS.override.md': b'Local override\n',
                            '.agents/skills/other/SKILL.md': b'Unrelated skill\n',
                            '.claude/settings.json': b'{"privateSettings": true}\n',
                            '.claude/CLAUDE.md': b'Private global instructions\n',
                            '.claude/skills/other/SKILL.md': b'Unrelated Claude skill\n',
                            '.claude/plugins/local.txt': b'Private plugin state\n'}
                for target, content in {**originals, **siblings}.items():
                    path = home / target
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(content)
                before = snapshot(home)
                self.install(home, platform, '--dry-run')
                self.assertEqual(snapshot(home), before)
                existing = self.install(home, platform, '--check-existing', check=False)
                self.assertEqual(existing.returncode, 1)
                self.assertIn('Detached: ' + str(home / '.codex/AGENTS.md'), existing.stdout)
                self.assertIn('Detached: ' + str(home / '.agents/skills/research-audit'), existing.stdout)
                self.assertIn('Detached: ' + str(home / '.claude/skills/research-audit'), existing.stdout)
                self.assertEqual(snapshot(home), before)
                self.install(home, platform)
                self.assert_links(home)
                for target, content in originals.items():
                    backups = list(home.glob('.dotfiles-backup/*/' + target))
                    self.assertEqual(len(backups), 1)
                    self.assertEqual(backups[0].read_bytes(), content)
                for target, content in siblings.items():
                    self.assertFalse((home / target).is_symlink())
                    self.assertEqual((home / target).read_bytes(), content)
                installed = snapshot(home)
                self.install(home, platform)
                self.assertEqual(snapshot(home), installed)

    def test_diagnostics_detect_drift_without_writes(self):
        for platform in ('linux', 'mac'):
            home = self.home(platform)
            self.install(home, platform)
            for target, source in LINKS.items():
                for state in ('replaced', 'missing', 'wrong-link', 'dangling-link'):
                    with self.subTest(platform=platform, target=target, state=state):
                        path = home / target
                        path.unlink()
                        if state == 'replaced':
                            path.write_text('Unmanaged replacement\n')
                        elif state == 'wrong-link':
                            path.symlink_to(ROOT / 'README.md')
                        elif state == 'dangling-link':
                            path.symlink_to(home / 'absent-source')
                        before = snapshot(home)
                        status = self.install(home, platform, '--status', check=False)
                        self.assertEqual(status.returncode, 1)
                        self.assertIn(('Missing: ' if state == 'missing' else 'Detached: ') + str(path), status.stdout)
                        existing = self.install(home, platform, '--check-existing', check=False)
                        # Missing targets are recoverable on sync; existing conflicts stop it.
                        self.assertEqual(existing.returncode, 0 if state == 'missing' else 1)
                        if state != 'missing':
                            self.assertIn('Detached: ' + str(path), existing.stdout)
                        self.assertEqual(snapshot(home), before)
                        if state != 'missing':
                            path.unlink()
                        path.symlink_to(ROOT / source)

    def test_legacy_manifest_links_migrate_with_backups(self):
        for platform in ('linux', 'mac'):
            home = self.home(platform)
            for target, source in LINKS.items():
                if source == 'agent-workflow/global.md':
                    continue
                folder = home / target
                folder.mkdir(parents=True)
                (folder / 'SKILL.md').symlink_to(ROOT / source / 'SKILL.md')
            before = snapshot(home)
            self.install(home, platform, '--check-existing')
            self.install(home, platform, '--dry-run')
            self.assertEqual(snapshot(home), before)
            self.install(home, platform)
            self.assert_links(home)
            for target, source in LINKS.items():
                if source == 'agent-workflow/global.md':
                    continue
                backups = list(home.glob('.dotfiles-backup/*/' + target + '/SKILL.md'))
                self.assertEqual(len(backups), 1)
                self.assertEqual(backups[0].readlink(), ROOT / source / 'SKILL.md')
            installed = snapshot(home)
            self.install(home, platform)
            self.assertEqual(snapshot(home), installed)

    def test_skill_sidecars_are_preserved_by_refusing_directory_replacement(self):
        for platform in ('linux', 'mac'):
            for target in SKILL_TARGETS:
                for sidecar in ('notes.txt', '.hidden-notes', 'subdirectory', 'dangling-link'):
                    with self.subTest(platform=platform, skill=target, sidecar=sidecar):
                        home = self.home(f'{platform}-{target.replace("/", "-")}-{sidecar}')
                        folder = home / target
                        folder.mkdir(parents=True)
                        (folder / 'SKILL.md').write_text('User-owned skill\n')
                        extra = folder / sidecar
                        if sidecar == 'subdirectory':
                            extra.mkdir()
                        elif sidecar == 'dangling-link':
                            extra.symlink_to(home / 'absent')
                        else:
                            extra.write_text('Keep these notes in place\n')
                        before = snapshot(home)
                        for option in ('--dry-run', '--status', '--check-existing', ''):
                            result = self.install(home, platform, *([option] if option else []), check=False)
                            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                            self.assertIn('Unmanaged skill contents: ' + str(extra), result.stderr)
                            self.assertEqual(snapshot(home), before)

    def test_replaced_skill_directory_links_preserve_the_external_directory(self):
        home = self.home('home')
        external = self.home('external')
        (external / 'SKILL.md').write_text('External skill\n')
        (external / 'private-notes').write_text('Keep external notes\n')
        folder = home / '.agents/skills/research-audit'
        folder.parent.mkdir(parents=True)
        folder.symlink_to(external, target_is_directory=True)
        before = snapshot(external)
        self.assertEqual(self.install(home, 'linux', '--check-existing', check=False).returncode, 1)
        self.install(home, 'linux')
        backups = list(home.glob('.dotfiles-backup/*/.agents/skills/research-audit'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].readlink(), external)
        self.assertEqual(snapshot(external), before)
        self.assert_links(home)

    def test_unsupported_minimal_profile_makes_no_changes(self):
        for platform in ('linux', 'mac'):
            home = self.home(platform)
            for option in ('--dry-run', '--list', '--manifest', '--status', '--check-existing', ''):
                args = ('--profile', 'minimal', *([option] if option else []))
                result = self.install(home, platform, *args, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertIn('only personal is supported', result.stderr)
                self.assertEqual(snapshot(home), {})

    def test_unsafe_agent_parents_are_refused_before_any_installation(self):
        parents = ['.codex', '.agents', '.agents/skills', '.claude', '.claude/skills']
        for platform in ('linux', 'mac'):
            for relative in parents:
                for kind in ('symlink', 'dangling-symlink', 'file'):
                    with self.subTest(platform=platform, parent=relative, kind=kind):
                        home = self.home(f'{platform}-{relative.replace("/", "-")}-{kind}')
                        external = self.base / (home.name + '-external')
                        external.mkdir()
                        (external / 'SKILL.md').write_text('External skill contents\n')
                        parent = home / relative
                        parent.parent.mkdir(parents=True, exist_ok=True)
                        if kind == 'file':
                            parent.write_text('User-owned file\n')
                        else:
                            parent.symlink_to(external if kind == 'symlink' else external / 'absent',
                                              target_is_directory=True)
                        before = snapshot(home)
                        external_before = snapshot(external)
                        # Lists remain inspectable, while diagnostics and installation
                        # must stop before writing even unrelated configuration links.
                        for option in ('--list', '--manifest'):
                            self.install(home, platform, option)
                        for option in ('--dry-run', '--status', '--check-existing', ''):
                            args = [option] if option else []
                            result = self.install(home, platform, *args, check=False)
                            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                            self.assertIn('Blocked agent parent: ' + str(parent), result.stderr)
                            self.assertEqual(snapshot(home), before)
                            self.assertEqual(snapshot(external), external_before)

    def test_agent_parent_checks_allow_home_aliases_and_trailing_slashes(self):
        for platform in ('linux', 'mac'):
            home = self.home(platform)
            alias = self.base / (platform + '-home-alias')
            alias.symlink_to(home, target_is_directory=True)
            for location in (str(home) + '/', str(alias), str(alias) + '/'):
                with self.subTest(platform=platform, home=location):
                    env = dict(HOME=location, PATH='/usr/bin:/bin')
                    result = subprocess.run(['bash', str(ROOT / 'install.sh'), '--platform', platform],
                                            env=env, text=True, capture_output=True, timeout=15)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assert_links(home)

    @unittest.skipIf(os.geteuid() == 0, 'Permission-denial behavior requires an unprivileged user')
    def test_inaccessible_skill_directories_are_refused_without_partial_installation(self):
        for platform in ('linux', 'mac'):
            for target in SKILL_TARGETS:
                for mode in (0, 0o100, 0o400):
                    with self.subTest(platform=platform, target=target, mode=oct(mode)):
                        home = self.home(f'{platform}-{target.replace("/", "-")}-{mode}')
                        folder = home / target
                        folder.mkdir(parents=True)
                        (folder / 'SKILL.md').write_text('Original skill\n')
                        (folder / 'private-notes').write_text('Keep notes in place\n')
                        before = snapshot(home)
                        folder.chmod(mode)
                        try:
                            for option in ('--dry-run', '--status', '--check-existing', ''):
                                result = self.install(home, platform, *([option] if option else []), check=False)
                                self.assertEqual(result.returncode, 1)
                                self.assertIn('Cannot inspect skill directory: ' + str(folder), result.stderr)
                                self.assertFalse((home / '.bashrc').exists())
                                self.assertFalse((home / '.dotfiles-backup').exists())
                        finally:
                            folder.chmod(0o755)
                        self.assertEqual(snapshot(home), before)

    @unittest.skipIf(os.geteuid() == 0, 'Permission-denial behavior requires an unprivileged user')
    def test_unsearchable_agent_parents_are_refused_without_writes(self):
        for relative in ('.codex', '.agents', '.agents/skills', '.claude', '.claude/skills'):
            with self.subTest(parent=relative):
                home = self.home(relative.replace('/', '-'))
                parent = home / relative
                parent.mkdir(parents=True)
                before = snapshot(home)
                parent.chmod(0o600)
                try:
                    result = self.install(home, 'linux', check=False)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn('Blocked agent parent: ' + str(parent), result.stderr)
                    self.assertFalse((home / '.bashrc').exists())
                finally:
                    parent.chmod(0o755)
                self.assertEqual(snapshot(home), before)

    def test_installed_git_ignore_exposes_project_guidance_only(self):
        home = self.home('home')
        self.install(home, 'linux')
        repo = self.home('project')
        self.run_command(home, 'git', 'init', '-q', str(repo))
        visible = ['AGENTS.md', 'nested/AGENTS.md', 'CLAUDE.md', '.claude/skills/verify/SKILL.md',
                   '.agents/skills/verify/SKILL.md', '.env.example',
                   'fixtures/example.sqlite', 'fixtures/example.sqlite3', 'config/hosts.yml']
        hidden = ['.codex/config.toml', 'nested/.codex/config.toml', 'AGENTS.override.md',
                  'nested/AGENTS.override.md', '.env', '.env.local', 'keys/id_ed25519',
                  'service/auth.json', '.claude/settings.local.json', '.DS_Store']
        for relative in visible + hidden:
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Synthetic fixture\n')
            result = self.run_command(home, 'git', '-C', str(repo), 'check-ignore', '-q', relative, check=False)
            self.assertEqual(result.returncode, 1 if relative in visible else 0, relative)
        status = self.run_command(home, 'git', '-C', str(repo), 'ls-files', '--others', '--exclude-standard').stdout.splitlines()
        self.assertEqual(set(status), set(visible))
        self.assertEqual(self.run_command(home, 'git', '-C', str(repo), 'diff', '--cached', '--name-only').stdout, '')

    def test_skill_packaging_and_frontmatter(self):
        expected = {str(manifest(ROOT / source).relative_to(ROOT)) for source in LINKS.values()}
        files = {str(p.relative_to(ROOT)) for p in (ROOT / 'agent-workflow').rglob('*') if p.is_file()}
        self.assertEqual(files, expected)
        names = set()
        descriptions = set()
        for source in sorted(expected - {'agent-workflow/global.md'}):
            path = ROOT / source
            self.assertFalse(path.is_symlink())
            lines = path.read_text().splitlines()
            self.assertEqual(lines[0], '---')
            end = lines.index('---', 1)
            metadata = {}
            # Deliberately support only the simple two-key YAML scalar schema
            # used here, avoiding an additional YAML dependency in offline CI.
            for line in lines[1:end]:
                key, value = line.split(': ', 1)
                self.assertNotIn(key, metadata)
                self.assertNotIn(': ', value)
                self.assertFalse(any(c in value for c in '#\n{}[]'))
                metadata[key] = value
            self.assertEqual(set(metadata), {'name', 'description'})
            self.assertEqual(metadata['name'], path.parent.name)
            self.assertNotIn(metadata['name'], names)
            names.add(metadata['name'])
            self.assertTrue(metadata['description'].strip())
            self.assertLessEqual(len(metadata['description']), 1024)
            descriptions.add(metadata['description'])
            self.assertTrue('\n'.join(lines[end + 1:]).strip())
        self.assertEqual(len(descriptions), 2)


if __name__ == '__main__':
    unittest.main()
