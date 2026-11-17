"""Validate workstation provisioning without sudo, downloads or real app changes."""
import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import workflow


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dotfiles-bootstrap-')
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.environment = mock.patch.dict(os.environ, {'HOME': str(self.home)})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def args(self, *options):
        return workflow.parser().parse_args(['bootstrap', *options])

    def test_full_defaults_and_partial_setup_flags(self):
        args = self.args()
        self.assertTrue(args.dev)
        self.assertFalse(any((args.skip_apps, args.skip_assets, args.skip_fonts, args.skip_packages, args.skip_shell)))
        args = self.args('--skip-dev', '--skip-apps', '--skip-fonts', '--skip-shell')
        self.assertFalse(args.dev)
        self.assertTrue(args.skip_apps and args.skip_fonts and args.skip_shell)
        for options in [('--fonts', 'meslo', '--skip-fonts'), ('--fonts',),
                        ('--unknown',), ('--apps',), ('--dev',)]:
            with self.subTest(options=options), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                self.args(*options)

    def test_distro_identification_uses_id_like_without_executing_content(self):
        release = self.home / 'os-release'
        for source, expected in [('ID=zorin\nID_LIKE="ubuntu debian"\n', 'apt'),
                                 ('ID=debian\n', 'apt'), ('ID=fedora\n', 'dnf')]:
            release.write_text(source)
            self.assertEqual(workflow.linux_manager(release), expected)
        release.write_text('ID=arch\nID_LIKE="$(touch unexpected)"\n')
        with self.assertRaisesRegex(RuntimeError, 'supports Debian/Ubuntu'):
            workflow.linux_manager(release)
        self.assertFalse((self.home / 'unexpected').exists())

    def test_invalid_asset_settings_fail_before_provisioning(self):
        marker = self.home / '.config/dotfiles/features.json'
        marker.parent.mkdir(parents=True)
        marker.write_text('{"assets": ["unknown"]}\n')
        with mock.patch.object(workflow, 'run') as execute, \
                self.assertRaisesRegex(RuntimeError, 'Invalid enabled asset groups'):
            workflow.bootstrap(self.args('--dry-run', '--skip-apps'))
        execute.assert_not_called()

    def test_wrong_platform_root_and_incompatible_flags_fail_before_commands(self):
        for options, uid, actual, message in [
                (['--platform', 'mac'], 1000, 'Linux', 'another OS'),
                ([], 0, 'Linux', 'normal user'),
                (['--skip-packages'], 1000, 'Linux', '--skip-apps')]:
            with self.subTest(options=options, uid=uid), mock.patch.object(workflow.os, 'getuid', return_value=uid), \
                    mock.patch.object(workflow.platform, 'system', return_value=actual), \
                    mock.patch.object(workflow, 'run') as execute, self.assertRaisesRegex(RuntimeError, message):
                workflow.bootstrap(self.args(*options))
            execute.assert_not_called()

    def test_linux_arm_apps_fail_before_commands(self):
        with mock.patch.object(workflow.os, 'getuid', return_value=1000), \
                mock.patch.object(workflow.platform, 'system', return_value='Linux'), \
                mock.patch.object(workflow.platform, 'machine', return_value='aarch64'), \
                mock.patch.object(workflow, 'linux_manager', return_value='apt'), \
                mock.patch.object(workflow, 'run') as execute, self.assertRaisesRegex(RuntimeError, 'x86_64'):
            workflow.bootstrap(self.args())
        execute.assert_not_called()

    def test_zed_conflict_is_detected_before_any_provisioning(self):
        target = self.home / '.local/zed.app'
        target.mkdir(parents=True)
        (target / 'personal.txt').write_text('keep')
        with mock.patch.object(workflow.shutil, 'which', return_value=None), \
                mock.patch.object(workflow.platform, 'system', return_value='Linux'), \
                mock.patch.object(workflow, 'linux_manager', return_value='apt'), \
                mock.patch.object(workflow, 'run') as execute, self.assertRaisesRegex(RuntimeError, 'Zed destination'):
            workflow.bootstrap(self.args('--dry-run'))
        execute.assert_not_called()
        self.assertEqual((target / 'personal.txt').read_text(), 'keep')

    def test_link_conflict_blocks_packages_before_prerequisites(self):
        def execute(argv, **kwargs):
            if '--dry-run' in argv:
                return subprocess.CompletedProcess(argv, 1, '', 'blocked skill path')
            return subprocess.CompletedProcess(argv, 0, '', '')
        with mock.patch.object(workflow, 'check_rendered'), \
                mock.patch.object(workflow, 'run', side_effect=execute) as commands, \
                self.assertRaisesRegex(RuntimeError, 'blocked skill path'):
            workflow.bootstrap(self.args('--platform', 'mac', '--dry-run'))
        self.assertEqual(commands.call_count, 1)
        self.assertIn('install.sh', str(commands.call_args.args[0]))

    def test_mac_full_bootstrap_keeps_installed_apps_and_provisions_all_stages(self):
        commands = []
        def execute(argv, **kwargs):
            commands.append([str(item) for item in argv])
            output = ''
            if argv[1:] == ['list', '--formula', '-1']:
                output = '\n'.join(workflow.packages('setup/packages.txt') + workflow.packages('setup/dev-packages.txt'))
            if argv[1:] == ['list', '--cask', '-1']:
                output = 'kitty\nzed\n'
            return subprocess.CompletedProcess(argv, 0, output, '')
        with mock.patch.object(workflow, 'run', side_effect=execute), \
                mock.patch.object(workflow.platform, 'system', return_value='Darwin'), \
                mock.patch.object(workflow, 'brew_command', return_value='brew'), \
                mock.patch.object(workflow, 'configure_path'), \
                mock.patch.object(workflow, 'check_rendered'), \
                mock.patch.object(workflow, 'assets') as assets, \
                mock.patch.object(workflow, 'fonts') as fonts, \
                mock.patch.object(workflow, 'login_shell') as shell, \
                mock.patch.object(workflow, 'enable_hooks') as hooks, \
                contextlib.redirect_stdout(io.StringIO()):
            workflow.bootstrap(self.args('--platform', 'mac', '--dry-run'))
        casks = [args for args in commands if '--cask' in args and 'install' in args]
        self.assertEqual(casks, [['brew', 'install', '--cask', '1password', 'ghostty', 'visual-studio-code', 'warp', 'wave']])
        self.assertFalse(any('install' in args and '--cask' not in args for args in commands))
        self.assertEqual(set(fonts.call_args.args[0].families), set(workflow.read_json('setup/fonts.json')))
        self.assertEqual(assets.call_args.args[0].group, ['shell', 'editors'])
        shell.assert_called_once_with(True)
        hooks.assert_called_once_with(True)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_linux_vendor_packages_use_native_format_and_signature_checks(self):
        for manager in ('apt', 'dnf'):
            with self.subTest(manager=manager), mock.patch.object(workflow, 'linux_manager', return_value=manager), \
                    mock.patch.object(workflow.platform, 'system', return_value='Linux'), \
                    mock.patch.object(workflow, 'native_app_present', return_value=False), \
                    mock.patch.object(workflow.shutil, 'which', side_effect=lambda command: '/bin/zed' if command == 'zed' else None), \
                    mock.patch.object(workflow, 'run', return_value=subprocess.CompletedProcess([], 1, '', '')) as execute:
                workflow.linux_apps(dry=True)
            calls = execute.call_args_list
            argv = [[str(item) for item in call.args[0]] for call in calls]
            downloads = [args[-1] for args in argv if args[0] == 'curl']
            self.assertEqual(len(downloads), 2 if manager == 'apt' else 4)
            if manager == 'apt':
                self.assertTrue(any('debconf-set-selections' in args for args in argv))
                self.assertIn('boolean true', next(call.kwargs['input_data'] for call in calls if 'input_data' in call.kwargs))
            else:
                installs = [args for args in argv if '--setopt=localpkg_gpgcheck=1' in args]
                self.assertEqual(len(installs), 2)
                self.assertEqual(sum('--import' in args for args in argv), 2)
            self.assertTrue(all(call.kwargs.get('dry') for call in calls))
        self.assertEqual(list(self.home.iterdir()), [])

    def test_linux_apps_rerun_does_not_download_or_upgrade_installed_apps(self):
        with mock.patch.object(workflow, 'linux_manager', return_value='dnf'), \
                mock.patch.object(workflow, 'native_app_present', return_value=True), \
                mock.patch.object(workflow.shutil, 'which', return_value='/bin/zed'), \
                mock.patch.object(workflow, 'run') as execute, contextlib.redirect_stdout(io.StringIO()):
            workflow.linux_apps()
        execute.assert_not_called()

    def test_zed_checksum_failure_prevents_script_execution(self):
        def download(url, target, dry=False):
            target.write_text('corrupt installer')
        with mock.patch.object(workflow, 'linux_manager', return_value='dnf'), \
                mock.patch.object(workflow, 'native_app_present', return_value=True), \
                mock.patch.object(workflow.shutil, 'which', return_value=None), \
                mock.patch.object(workflow, 'download', side_effect=download), \
                mock.patch.object(workflow, 'run') as execute, contextlib.redirect_stdout(io.StringIO()), \
                self.assertRaisesRegex(RuntimeError, 'checksum mismatch'):
            workflow.linux_apps()
        execute.assert_not_called()

    def test_login_shell_only_changes_when_needed_and_targets_real_account(self):
        account = mock.Mock(pw_shell='/bin/bash', pw_name='real-user')
        with mock.patch.object(workflow.pwd, 'getpwuid', return_value=account), \
                mock.patch.object(workflow.shutil, 'which', return_value='/opt/homebrew/bin/zsh'), \
                mock.patch.object(Path, 'read_text', return_value='/bin/bash\n'), \
                mock.patch.object(workflow, 'run') as execute:
            workflow.login_shell()
            self.assertEqual(execute.call_args_list[0].kwargs['input_data'], '\n/opt/homebrew/bin/zsh\n')
            self.assertEqual(execute.call_args_list[1].args[0], ['sudo', 'chsh', '-s', '/opt/homebrew/bin/zsh', 'real-user'])
            execute.reset_mock()
            account.pw_shell = '/opt/homebrew/bin/zsh'
            with contextlib.redirect_stdout(io.StringIO()):
                workflow.login_shell()
            execute.assert_not_called()

    def test_archive_setup_skips_hooks_without_git_commands(self):
        with mock.patch.object(workflow, 'ROOT', self.home), mock.patch.object(workflow, 'run') as execute, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            workflow.enable_hooks()
        self.assertIn('Archive checkout', output.getvalue())
        execute.assert_not_called()

    def test_shared_shell_environment_preserves_existing_brew_selection(self):
        commands = self.home / 'selected/bin'
        commands.mkdir(parents=True)
        brew = commands / 'brew'
        brew.write_text('#!/bin/sh\nexit 0\n')
        brew.chmod(0o755)
        environment = {**os.environ, 'DOTFILES_ROOT': str(ROOT), 'HOMEBREW_PREFIX': '', 'PATH': str(commands) + ':/usr/bin:/bin'}
        result = subprocess.run(['/bin/bash', '-c', '. "$DOTFILES_ROOT/shell/env.sh"; command -v brew'],
                                env=environment, text=True, capture_output=True, check=True)
        self.assertEqual(result.stdout.strip(), str(brew))

    def test_shared_environment_respects_an_explicit_brew_prefix(self):
        environment = {**os.environ, 'DOTFILES_ROOT': str(ROOT), 'HOMEBREW_PREFIX': str(self.home / 'isolated'),
                       'PATH': '/usr/bin:/bin'}
        result = subprocess.run(['/bin/bash', '-c', '. "$DOTFILES_ROOT/shell/env.sh"; printf "%s" "$PATH"'],
                                env=environment, text=True, capture_output=True, check=True)
        for prefix in ('/home/linuxbrew/.linuxbrew', '/opt/homebrew', '/usr/local'):
            self.assertNotIn(prefix + '/bin', result.stdout.split(':'))


class ColdStartTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dotfiles-cold-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bin = self.base / 'bin'
        self.bin.mkdir()
        self.log = self.base / 'commands'
        self.ready = self.base / 'python-ready'
        self.env = {**os.environ, 'HOME': str(self.base), 'PATH': str(self.bin) + ':/usr/bin:/bin',
                    'COMMAND_LOG': str(self.log), 'PYTHON_READY': str(self.ready)}
        for command, body in {
            'uname': 'if [ "$1" = -m ]; then echo x86_64; else echo Linux; fi',
            'id': 'echo 1000',
            'python3': 'if [ "$1" = -c ]; then test -f "$PYTHON_READY"; else printf "python %s\\n" "$*" >> "$COMMAND_LOG"; fi',
            'brew': 'printf "brew %s\\n" "$*" >> "$COMMAND_LOG"; if [ "$*" = "install python" ]; then touch "$PYTHON_READY"; fi',
            'sudo': 'printf "sudo %s\\n" "$*" >> "$COMMAND_LOG"',
            'curl': 'echo "Unexpected network operation" >&2; exit 99',
        }.items():
            self.fake(command, body)

    def fake(self, name, body):
        target = self.bin / name
        target.write_text('#!/bin/sh\n' + body + '\n')
        target.chmod(0o755)

    def call(self, *args):
        return subprocess.run(['/bin/bash', str(ROOT / 'bin/dotfiles'), *args], env=self.env,
                              text=True, capture_output=True, timeout=20)

    def test_no_python_preview_and_help_do_not_provision(self):
        for args in [('bootstrap', '--dry-run', '--skip-apps'), ('bootstrap', '--help')]:
            result = self.call(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(self.log.exists())
            self.assertFalse(self.ready.exists())

    def test_no_python_rejects_bad_arguments_before_privileged_commands(self):
        for options in [('--unknown',), ('--fonts', 'bogus'), ('--fonts', 'sha256'), ('--fonts',), ('--platform', 'bogus'),
                        ('--fonts', 'meslo', '--skip-fonts'), ('--skip-packages',)]:
            with self.subTest(options=options):
                result = self.call('bootstrap', *options)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.log.exists())

    def test_no_python_installs_prerequisites_and_resumes_exact_arguments(self):
        result = self.call('bootstrap', '--skip-apps', '--fonts', 'meslo', '--skip-shell')
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = self.log.read_text()
        self.assertIn('apt-get install -y', commands)
        self.assertIn('brew install python', commands)
        self.assertIn('scripts/workflow.py bootstrap --skip-apps --fonts meslo --skip-shell', commands)

    def test_no_python_link_conflict_prevents_prerequisite_changes(self):
        target = self.base / '.agents'
        target.symlink_to(self.base / 'missing-parent')
        result = self.call('bootstrap')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.log.exists())

    def test_mac_clt_install_is_automated_without_invoking_python_stub(self):
        self.fake('uname', 'if [ "$1" = -m ]; then echo arm64; else echo Darwin; fi')
        self.fake('xcode-select', 'exit 1')
        self.fake('softwareupdate', 'printf "* Label: Command Line Tools for Xcode 27\\n* Label: Command Line Tools for Xcode 16\\n"')
        result = subprocess.run(['/bin/bash', str(ROOT / 'scripts/prerequisites.sh')], env=self.env,
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = self.log.read_text()
        self.assertIn('softwareupdate --install Command Line Tools for Xcode 27', commands)
        self.assertNotIn('softwareupdate --install Command Line Tools for Xcode 16', commands)
        self.assertIn('xcode-select --switch /Library/Developer/CommandLineTools', commands)
        self.assertNotIn('brew install', commands)
        self.assertNotIn('python', commands)

    def test_root_prerequisites_fail_without_any_sudo_command(self):
        self.fake('id', 'echo 0')
        result = self.call('bootstrap')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('normal user', result.stderr)
        self.assertFalse(self.log.exists())

    def test_linux_prerequisite_preview_never_launches_python(self):
        self.fake('python3', 'mkdir -p "$HOME/Library"; echo python >> "$COMMAND_LOG"; exit 1')
        for system in ('Linux', 'Darwin'):
            with self.subTest(host=system):
                self.fake('uname', f'echo {system}')
                result = subprocess.run(['/bin/bash', str(ROOT / 'scripts/prerequisites.sh'),
                                         '--platform', 'linux', '--dry-run'], env=self.env,
                                        text=True, capture_output=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('apt-get install', result.stdout)
                self.assertFalse(self.log.exists())
                self.assertFalse((self.base / 'Library').exists())


if __name__ == '__main__':
    unittest.main()
