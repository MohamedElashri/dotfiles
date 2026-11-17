"""Exercise provisioning and sync using temporary homes and local Git remotes."""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / 'scripts'))
import workflow


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dotfiles workflow ')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.home = self.base / 'home'
        self.home.mkdir()
        self.root = self.base / 'checkout'
        def ignore_local(directory, names):
            ignored = set(shutil.ignore_patterns('.git', '.cache', '.claude', '.agents',
                                                '.codex', '.aws', '__pycache__')(directory, names))
            # Machine-local links into ignored caches are not part
            # of a fresh checkout and must not become dangling fixture links.
            for name in names:
                path = Path(directory) / name
                if path.is_symlink() and path.resolve().is_relative_to(REPOSITORY / '.cache'):
                    ignored.add(name)
            return ignored
        shutil.copytree(REPOSITORY, self.root, symlinks=True, ignore=ignore_local)
        self.environment = mock.patch.dict(os.environ, {
            'HOME': str(self.home), 'ZDOTDIR': str(self.home),
            'PATH': '/usr/bin:/bin', 'TERM': 'dumb', 'USER': 'dotfiles-test',
            'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
            'RUN_QURAN_VERSE_ON_STARTUP': 'false',
        }, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.patch_root = mock.patch.object(workflow, 'ROOT', self.root)
        self.patch_root.start()
        self.addCleanup(self.patch_root.stop)
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Dotfiles Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'commit.gpgsign', 'false')
        self.git('add', '.')
        self.git('commit', '-qm', 'Initial test configuration')

    def git(self, *args, cwd=None):
        return subprocess.run(['git', '-C', str(cwd or self.root), *args], check=True,
                              text=True, capture_output=True).stdout.strip()

    def install(self, *args):
        return subprocess.run(['bash', str(self.root / 'install.sh'), '--platform', 'linux', *args],
                              check=True, text=True, capture_output=True)

    def sync_args(self, **kwargs):
        return argparse.Namespace(**dict({'platform': 'linux', 'check': False,
                                         'dry_run': False, 'with_agents': False}, **kwargs))

    def configure_remote(self):
        remote = self.base / 'remote.git'
        subprocess.run(['git', 'init', '-q', '--bare', '--initial-branch=main', str(remote)], check=True)
        self.git('remote', 'add', 'origin', str(remote))
        self.git('push', '-qu', 'origin', 'main')
        peer = self.base / 'second device'
        subprocess.run(['git', 'clone', '-q', str(remote), str(peer)], check=True)
        self.git('config', 'user.name', 'Other Device', cwd=peer)
        self.git('config', 'user.email', 'other@example.invalid', cwd=peer)
        self.git('config', 'commit.gpgsign', 'false', cwd=peer)
        return peer

    def advance_remote(self, peer):
        (peer / 'shell/aliases.sh').write_text((peer / 'shell/aliases.sh').read_text() + '\nalias synced="echo synced"\n')
        self.git('add', 'shell/aliases.sh', cwd=peer)
        self.git('commit', '-qm', 'Update from other device', cwd=peer)
        self.git('push', '-q', cwd=peer)

    def test_same_portable_configs_are_linked_on_both_platforms(self):
        for platform in ('linux', 'mac'):
            result = subprocess.run(['bash', str(self.root / 'install.sh'), '--platform', platform],
                                    check=True, text=True, capture_output=True)
            self.assertIn('Done.', result.stdout)
            for target, source in [('.config/atuin/config.toml', 'config/cli/atuin/config.toml'),
                                   ('.config/gh/config.yml', 'config/cli/gh/config.yml'),
                                   ('.config/micro/settings.json', 'config/cli/micro/settings.json'),
                                   ('.config/zed/settings.json', 'config/editors/zed/settings.json'),
                                   ('.tmux.conf', 'config/tmux/.tmux.conf')]:
                self.assertEqual((self.home / target).resolve(), self.root / source)

    def test_classic_install_and_cli_work_without_agent_workflow_files(self):
        shutil.rmtree(self.root / 'agent-workflow')
        for path in (self.root / 'scripts').glob('agent_*.py'):
            path.unlink()
        self.git('add', '-u')
        self.git('commit', '-qm', 'Remove optional agent workflow from fixture')
        self.configure_remote()
        # Occupied harness parents must not affect classic setup or diagnostics.
        external = self.base / 'private harness state'
        external.mkdir()
        sentinel = external / 'keep'
        sentinel.write_text('preserve private harness state')
        for name in ('.codex', '.claude', '.agents', '.pi'):
            (self.home / name).symlink_to(external, target_is_directory=True)
        for platform in ('linux', 'mac'):
            for option in ('--list', '--dry-run', '', '--status', '--check-existing'):
                result = subprocess.run(['bash', str(self.root / 'install.sh'), '--platform', platform,
                                         *([option] if option else [])], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn('agent-workflow', result.stdout)
        # CLI maintenance uses the host platform after the cross-platform matrix.
        subprocess.run(['bash', str(self.root / 'install.sh'), '--platform', workflow.os_name()],
                       check=True, text=True, capture_output=True)
        commands = [(['--help'], 0), (['fonts', '--list'], 0), (['render'], 0),
                    (['bootstrap', '--dry-run', '--skip-packages', '--skip-apps',
                      '--skip-assets', '--skip-fonts', '--skip-shell'], 0),
                    (['doctor', '--strict'], 1), (['sync', '--check'], 0), (['sync'], 0)]
        for arguments, expected in commands:
            result = subprocess.run([str(self.root / 'bin/dotfiles'), *arguments],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, expected, (arguments, result.stdout, result.stderr))
            self.assertNotIn('Traceback', result.stderr)
            self.assertNotIn('agent-workflow', result.stdout)
        unavailable = subprocess.run([str(self.root / 'bin/dotfiles'), 'agents', 'eval', 'list'],
                                     text=True, capture_output=True)
        self.assertEqual(unavailable.returncode, 1)
        self.assertIn('Optional agent workflow files are unavailable', unavailable.stderr)
        self.assertEqual(list(external.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_text(), 'preserve private harness state')

    def test_bootstrap_with_agents_checks_conflicts_before_provisioning(self):
        (self.home / '.codex').write_text('private harness state')
        args = workflow.parser().parse_args(['bootstrap', '--with-agents', '--dry-run', '--skip-apps'])
        with mock.patch.object(workflow, 'assets') as assets, self.assertRaisesRegex(RuntimeError, 'Blocked configuration parent'):
            workflow.bootstrap(args)
        assets.assert_not_called()
        self.assertEqual((self.home / '.codex').read_text(), 'private harness state')
        self.assertFalse((self.home / '.bashrc').exists())

    def test_symlinked_application_parents_are_refused_without_writes(self):
        for target, source in [('.waveterm/config', 'config/terminals/waveterm/config'),
                               ('.config/ghostty', 'config/terminals/ghostty'),
                               ('.config/micro', 'config/cli/micro')]:
            with self.subTest(target=target):
                parent = self.home / target
                parent.parent.mkdir(parents=True, exist_ok=True)
                parent.symlink_to(self.root / source, target_is_directory=True)
                for option in ('--dry-run', '--status', '--check-existing', ''):
                    args = ['bash', str(self.root / 'install.sh'), '--platform', 'linux']
                    if option:
                        args.append(option)
                    result = subprocess.run(args, text=True, capture_output=True)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn('Blocked configuration parent: ' + str(parent), result.stderr)
                    self.assertTrue(parent.is_symlink())
                    self.assertFalse((self.home / '.bashrc').exists())
                    self.assertFalse((self.home / '.dotfiles-backup').exists())
                    self.assertEqual(self.git('status', '--porcelain'), '')
                parent.unlink()

    def test_render_preserves_platform_preferences_and_detects_direct_edits(self):
        common = self.root / 'config/terminals/waveterm/settings.common.json'
        settings = json.loads(common.read_text())
        settings['term:fontsize'] = 19
        common.write_text(json.dumps(settings))
        with self.assertRaises(RuntimeError):
            workflow.check_rendered()
        subprocess.run([sys.executable, str(self.root / 'scripts/render_configs.py')], check=True, capture_output=True)
        for platform, relative in [('linux', 'config/terminals/waveterm/config/settings.json'),
                                   ('mac', 'config/mac/waveterm/config/settings.json')]:
            rendered = json.loads((self.root / relative).read_text())
            overrides = json.loads((common.parent / f'settings.{platform}.json').read_text())
            self.assertEqual(rendered['term:fontsize'], 19)
            for key, value in overrides.items():
                self.assertEqual(rendered[key], value)
        workflow.check_rendered()
        output = self.root / 'config/terminals/waveterm/config/settings.json'
        output.write_text('{}\n')
        with self.assertRaises(RuntimeError):
            workflow.check_rendered()
        self.assertEqual(output.read_text(), '{}\n')

    def test_bootstrap_dry_run_changes_neither_home_nor_repository(self):
        args = workflow.parser().parse_args(['bootstrap', '--platform', 'linux', '--dry-run', '--skip-apps', '--fonts', 'meslo'])
        head = self.git('rev-parse', 'HEAD')
        with mock.patch.object(workflow, 'brew_command', return_value=None), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(workflow.bootstrap(args), 0)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertEqual(self.git('status', '--porcelain'), '')
        self.assertEqual(self.git('rev-parse', 'HEAD'), head)
        self.assertIn('brew install', output.getvalue())
        # Classic setup never installs AI application packages or instructions.
        self.assertNotIn('agent-workflow', output.getvalue())
        package_commands = [shlex.split(line.removeprefix('Would run: '))
                            for line in output.getvalue().splitlines()
                            if line.startswith('Would run: brew install ')]
        self.assertTrue(package_commands)
        for command in package_commands:
            self.assertTrue({'claude', 'codex', 'opencode'}.isdisjoint(command[2:]))
        self.assertIn('Would download and verify meslo', output.getvalue())

    def test_invalid_font_option_fails_before_packages_change(self):
        args = workflow.parser().parse_args(['bootstrap', '--platform', workflow.os_name(), '--fonts', 'unknown'])
        with mock.patch.object(workflow, 'run') as execute, self.assertRaisesRegex(RuntimeError, 'Unknown font'):
            workflow.bootstrap(args)
        execute.assert_not_called()

    def test_bootstrap_links_custom_theme_after_provisioning_framework(self):
        args = workflow.parser().parse_args(['bootstrap', '--platform', workflow.os_name(), '--skip-packages', '--skip-apps', '--skip-fonts', '--skip-shell'])
        def provision(_args):
            (self.home / '.oh-my-zsh/.git').mkdir(parents=True)
            return 0
        with mock.patch.object(workflow, 'assets', side_effect=provision), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(workflow.bootstrap(args), 0)
        self.assertTrue((self.home / '.oh-my-zsh/custom/themes/dracula-pro.zsh-theme').is_symlink())
        self.assertEqual(workflow.enabled_assets(), ['editors', 'shell'])

    def test_hooks_preserve_custom_hook_configuration(self):
        self.git('config', 'core.hooksPath', '/custom/hooks')
        with contextlib.redirect_stdout(io.StringIO()):
            workflow.enable_hooks()
        self.assertEqual(self.git('config', 'core.hooksPath'), '/custom/hooks')

    def test_hooks_are_enabled_without_changing_tracked_files(self):
        workflow.enable_hooks()
        self.assertEqual(self.git('config', 'core.hooksPath'), '.githooks')
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_sync_fast_forwards_from_other_device_and_relinks_missing_files(self):
        peer = self.configure_remote()
        self.install('--with-agents')
        (self.home / '.config/gh/config.yml').unlink()
        agent_targets = ['.codex/AGENTS.md', '.claude/CLAUDE.md',
                         '.config/opencode/AGENTS.md', '.pi/agent/AGENTS.md',
                         '.agents/skills/research-audit',
                         '.agents/skills/engineering-audit', '.claude/skills/research-audit',
                         '.claude/skills/engineering-audit']
        for target in agent_targets:
            (self.home / target).unlink()
        self.advance_remote(peer)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(workflow.sync(self.sync_args(with_agents=True)), 0)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.git('rev-parse', 'HEAD', cwd=peer))
        self.assertTrue((self.home / '.config/gh/config.yml').is_symlink())
        for target in agent_targets:
            self.assertTrue((self.home / target).is_symlink())
        self.assertIn('alias synced=', (self.home / '.bashrc').resolve().parent.parent.joinpath('shell/aliases.sh').read_text())
        self.install('--status')
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_sync_refuses_dirty_checkout_before_fetch(self):
        peer = self.configure_remote()
        self.install()
        old_remote = self.git('rev-parse', 'origin/main')
        self.advance_remote(peer)
        (self.root / 'README.md').write_text('local work\n')
        with self.assertRaisesRegex(RuntimeError, 'local edits'):
            workflow.sync(self.sync_args())
        self.assertEqual(self.git('rev-parse', 'origin/main'), old_remote)
        self.assertEqual((self.root / 'README.md').read_text(), 'local work\n')

    def test_sync_reconciles_only_the_enabled_asset_groups(self):
        self.configure_remote()
        self.install()
        workflow.remember_assets(['editors', 'shell'])
        with mock.patch.object(workflow, 'assets', return_value=0) as provision, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(workflow.sync(self.sync_args()), 0)
        chosen = provision.call_args.args[0]
        self.assertEqual(chosen.group, ['editors', 'shell'])
        self.assertTrue(chosen.update)
        self.assertEqual(workflow.enabled_assets(), ['editors', 'shell'])

    def test_sync_preserves_app_replaced_configuration_before_fetch(self):
        peer = self.configure_remote()
        self.install()
        target = self.home / '.config/gh/config.yml'
        target.unlink()
        target.write_text('editor: custom-editor\n')
        old_remote = self.git('rev-parse', 'origin/main')
        self.advance_remote(peer)
        with self.assertRaisesRegex(RuntimeError, 'Existing files need review'):
            workflow.sync(self.sync_args())
        self.assertEqual(target.read_text(), 'editor: custom-editor\n')
        self.assertEqual(self.git('rev-parse', 'origin/main'), old_remote)

    def test_sync_rejects_link_to_the_wrong_repository_file(self):
        self.install()
        target = self.home / '.config/gh/config.yml'
        target.unlink()
        unrelated = self.root / 'config/cli/micro/settings.json'
        target.symlink_to(unrelated)
        with self.assertRaisesRegex(RuntimeError, 'Existing files need review'):
            workflow.check_existing('linux')
        self.assertEqual(target.readlink(), unrelated)

    def test_sync_preserves_replaced_agent_instructions_before_fetch(self):
        peer = self.configure_remote()
        self.install('--with-agents')
        target = self.home / '.codex/AGENTS.md'
        target.unlink()
        target.write_text('Device-owned instructions\n')
        old_remote = self.git('rev-parse', 'origin/main')
        self.advance_remote(peer)
        with self.assertRaisesRegex(RuntimeError, 'Existing files need review'):
            workflow.sync(self.sync_args(with_agents=True))
        self.assertEqual(target.read_text(), 'Device-owned instructions\n')
        self.assertEqual(self.git('rev-parse', 'origin/main'), old_remote)
        self.assertFalse((self.home / '.dotfiles-backup').exists())

    def test_sync_refuses_symlinked_agent_parent_before_fetch(self):
        peer = self.configure_remote()
        self.install('--with-agents')
        parent = self.home / '.agents/skills'
        external = self.base / 'shared skills'
        shutil.move(str(parent), external)
        parent.symlink_to(external, target_is_directory=True)
        source = self.root / 'agent-workflow/skills/research-audit/SKILL.md'
        original = source.read_bytes()
        old_remote = self.git('rev-parse', 'origin/main')
        self.advance_remote(peer)
        with self.assertRaisesRegex(RuntimeError, 'Blocked configuration parent'):
            workflow.sync(self.sync_args(with_agents=True))
        self.assertEqual(self.git('rev-parse', 'origin/main'), old_remote)
        self.assertEqual(source.read_bytes(), original)
        self.assertTrue(parent.is_symlink())
        self.assertEqual((external / 'research-audit/SKILL.md').read_bytes(), original)
        self.assertFalse((self.home / '.dotfiles-backup').exists())

    def test_sync_refuses_divergence_without_rewriting_local_commit(self):
        peer = self.configure_remote()
        self.install()
        (self.root / 'README.md').write_text('committed local work\n')
        self.git('add', 'README.md')
        self.git('commit', '-qm', 'Local commit')
        local_head = self.git('rev-parse', 'HEAD')
        self.advance_remote(peer)
        with self.assertRaises(subprocess.CalledProcessError):
            workflow.sync(self.sync_args())
        self.assertEqual(self.git('rev-parse', 'HEAD'), local_head)
        self.assertEqual((self.root / 'README.md').read_text(), 'committed local work\n')

    def test_sync_check_and_dry_run_do_not_pull_or_install(self):
        peer = self.configure_remote()
        self.install()
        self.advance_remote(peer)
        old_head = self.git('rev-parse', 'HEAD')
        old_remote = self.git('rev-parse', 'origin/main')
        for check, dry in [(True, False), (False, True)]:
            with contextlib.redirect_stdout(io.StringIO()):
                workflow.sync(argparse.Namespace(platform='linux', check=check, dry_run=dry, with_agents=False))
        self.assertEqual(self.git('rev-parse', 'HEAD'), old_head)
        self.assertEqual(self.git('rev-parse', 'origin/main'), old_remote)
        self.assertFalse((self.home / '.dotfiles-backup').exists())

    def test_new_source_paths_are_listed_without_home_changes(self):
        result = self.install('--list')
        self.assertIn(str(self.root / 'config/cli/gh/config.yml'), result.stdout)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_invalid_skill_manifests_stop_installation_before_writes(self):
        source = self.root / 'agent-workflow/skills/research-audit/SKILL.md'
        original = source.read_bytes()
        for kind in ('missing', 'symlink'):
            with self.subTest(kind=kind):
                source.unlink()
                if kind == 'symlink':
                    fixture = self.base / 'regular-skill.md'
                    fixture.write_bytes(original)
                    source.symlink_to(fixture)
                result = subprocess.run(['bash', str(self.root / 'install.sh'), '--platform', 'linux', '--with-agents'],
                                        text=True, capture_output=True)
                self.assertEqual(result.returncode, 1)
                self.assertIn('Skill source must contain a regular manifest', result.stderr)
                self.assertEqual(list(self.home.iterdir()), [])
                if source.is_symlink():
                    source.unlink()
                source.write_bytes(original)

    def test_installer_preserves_external_assistant_configuration(self):
        external = ['.claude/settings.json', '.codex/config.toml', '.config/opencode/opencode.json',
                    '.agents/skills/personal/SKILL.md']
        for relative in external:
            path = self.home / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('device-owned configuration\n')
        for platform in ('linux', 'mac'):
            subprocess.run(['bash', str(self.root / 'install.sh'), '--platform', platform],
                           check=True, text=True, capture_output=True)
            for relative in external:
                path = self.home / relative
                self.assertFalse(path.is_symlink())
                self.assertEqual(path.read_text(), 'device-owned configuration\n')

    def test_invalid_asset_groups_are_rejected_without_rewriting_settings(self):
        marker = self.home / '.config/dotfiles/features.json'
        marker.parent.mkdir(parents=True)
        marker.write_text(json.dumps({'assets': ['shell', 'ai', 'editors']}))
        with self.assertRaisesRegex(RuntimeError, 'Invalid enabled asset groups'):
            workflow.enabled_assets()
        self.assertEqual(json.loads(marker.read_text())['assets'], ['shell', 'ai', 'editors'])

    def test_unknown_provisioning_options_are_rejected(self):
        for arguments in [('bootstrap', '--apps'), ('bootstrap', '--dev'),
                          ('sync', '--assets'), ('assets', '--group', 'ai')]:
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                workflow.parser().parse_args(arguments)
            self.assertEqual(error.exception.code, 2)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_git_assets_are_pinned_and_dirty_updates_are_preserved(self):
        source = self.base / 'plugin source'
        source.mkdir()
        self.git('init', '-q', cwd=source)
        self.git('config', 'user.name', 'Asset Test', cwd=source)
        self.git('config', 'user.email', 'asset@example.invalid', cwd=source)
        (source / 'plugin.zsh').write_text('# initial\n')
        self.git('add', '.', cwd=source)
        self.git('commit', '-qm', 'Initial asset', cwd=source)
        asset = {'path': '.local/share/test-plugin', 'repo': str(source),
                 'revision': self.git('rev-parse', 'HEAD', cwd=source)}
        workflow.install_git_asset(asset, self.home)
        target = self.home / asset['path']
        self.assertEqual(self.git('rev-parse', 'HEAD', cwd=target), asset['revision'])
        (target / 'plugin.zsh').write_text('# local edits\n')
        asset['revision'] = '0' * 40
        with self.assertRaisesRegex(RuntimeError, 'local edits'):
            workflow.install_git_asset(asset, self.home, update=True)
        self.assertEqual((target / 'plugin.zsh').read_text(), '# local edits\n')





    def test_doctor_reports_missing_tools_without_reading_external_settings(self):
        self.install('--with-agents')
        (self.home / '.agents/skills/engineering-audit').unlink()
        state = self.home / '.claude/plugins/installed_plugins.json'
        state.parent.mkdir(parents=True)
        state.write_text('External state is deliberately not JSON: DO_NOT_DISPLAY_TEST_VALUE')
        with mock.patch.object(workflow.shutil, 'which', return_value=None), contextlib.redirect_stdout(io.StringIO()) as output:
            result = workflow.doctor(argparse.Namespace(platform='linux', online=False, strict=False, with_agents=True))
        self.assertEqual(result, 1)
        self.assertIn('Missing tool: nvim', output.getvalue())
        self.assertIn('Missing tool: rg', output.getvalue())
        self.assertNotIn('Missing tool: neovim', output.getvalue())
        self.assertNotIn('DO_NOT_DISPLAY_TEST_VALUE', output.getvalue())
        self.assertIn('Missing: ' + str(self.home / '.agents/skills/engineering-audit'), output.getvalue())

    def font_archive(self, entries):
        archive = self.base / 'fonts.zip'
        with zipfile.ZipFile(archive, 'w') as bundle:
            for name, content in entries:
                bundle.writestr(name, content)
        return archive

    def test_fonts_install_only_font_files_and_back_up_changed_files(self):
        archive = self.font_archive([('nested/Example.ttf', b'new font'), ('README.txt', b'not a font')])
        destination = self.home / '.local/share/fonts'
        destination.mkdir(parents=True)
        (destination / 'Example.ttf').write_bytes(b'previous font')
        workflow.archive_fonts(archive, destination)
        self.assertEqual((destination / 'Example.ttf').read_bytes(), b'new font')
        self.assertFalse((destination / 'README.txt').exists())
        backups = list(self.home.glob('.dotfiles-backup/fonts-*/Example.ttf'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), b'previous font')
        workflow.archive_fonts(archive, destination)
        self.assertEqual(len(list(self.home.glob('.dotfiles-backup/fonts-*/Example.ttf'))), 1)

    def test_fonts_reject_traversal_before_installing_any_files(self):
        archive = self.font_archive([('safe.ttf', b'font'), ('../escape.ttf', b'bad')])
        destination = self.home / '.local/share/fonts'
        with self.assertRaisesRegex(RuntimeError, 'Unsafe'):
            workflow.archive_fonts(archive, destination)
        self.assertFalse(destination.exists())

    def test_fonts_reject_duplicate_names(self):
        archive = self.font_archive([('a/Example.ttf', b'first'), ('b/Example.ttf', b'second')])
        with self.assertRaisesRegex(RuntimeError, 'duplicate'):
            workflow.archive_fonts(archive, self.home / 'fonts')

    def test_font_checksum_mismatch_never_installs_fonts(self):
        source = self.font_archive([('Example.ttf', b'font')])
        (self.root / 'setup/fonts.json').write_text(json.dumps({'test': {
            'url': 'https://example.invalid/font.zip', 'sha256': '0' * 64}}))

        def fake_download(args, **kwargs):
            shutil.copy2(source, args[args.index('--output') + 1])
            return subprocess.CompletedProcess(args, 0)

        with mock.patch.object(workflow, 'run', side_effect=fake_download), self.assertRaisesRegex(RuntimeError, 'Checksum mismatch'):
            workflow.fonts(argparse.Namespace(platform='linux', families=['test'], list=False, dry_run=False))
        self.assertFalse((self.home / '.local/share/fonts').exists())

    def test_font_dry_run_and_unknown_names_leave_home_untouched(self):
        with contextlib.redirect_stdout(io.StringIO()):
            workflow.fonts(argparse.Namespace(platform='linux', families=['meslo'], list=False, dry_run=True))
        with self.assertRaisesRegex(RuntimeError, 'Unknown font'):
            workflow.fonts(argparse.Namespace(platform='linux', families=['unknown'], list=False, dry_run=False))
        self.assertEqual(list(self.home.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
