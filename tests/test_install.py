"""Integration checks using disposable homes; never source the user's startup files."""
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]

class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='dotfiles test ')
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.env = dict(HOME=str(self.home), ZDOTDIR=str(self.home),
                        PATH='/usr/bin:/bin', TERM='dumb', USER='dotfiles-test',
                        LOGNAME='dotfiles-test', SHELL='/bin/zsh',
                        RUN_QURAN_VERSE_ON_STARTUP='false')
        fake = self.home/'test-bin'
        fake.mkdir()
        # Keep shell auto-discovery from loading this host's Homebrew tools
        # and starting real history hooks in the disposable test home.
        self.env['HOMEBREW_PREFIX'] = str(fake)
        uname = fake/'uname'
        uname.write_text('#!/bin/sh\necho Linux\n')
        uname.chmod(0o755)
        self.env['PATH'] = str(fake) + ':' + self.env['PATH']

    def run_cmd(self, *args, env=None):
        return subprocess.run(args, env=env or self.env, cwd=ROOT, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def install(self, *args):
        result = self.run_cmd('bash', str(ROOT/'install.sh'), *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_dry_run_all_platforms(self):
        for args in [(), ('--platform', 'mac'), ('--profile', 'personal')]:
            self.install(*args, '--dry-run')
            self.assertEqual([p.name for p in self.home.iterdir()], ['test-bin'])

    def test_backup_and_idempotence(self):
        (self.home/'.zshrc').write_text('# previous settings\n')
        (self.home/'.bashrc').write_text('export SITE_PRESERVED=yes\n')
        self.install()
        backups = list(self.home.glob('.dotfiles-backup/*/.zshrc'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), '# previous settings\n')
        self.assertEqual((self.home/'.config/dotfiles/site.bash').read_text(), 'export SITE_PRESERVED=yes\n')
        before = sorted(str(p) for p in self.home.glob('.dotfiles-backup/**/*'))
        self.install()
        self.assertEqual(before, sorted(str(p) for p in self.home.glob('.dotfiles-backup/**/*')))
        result = self.run_cmd('bash', '--noprofile', '--rcfile', str(self.home/'.bashrc'), '-ic', 'test "$SITE_PRESERVED" = yes')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_shell_startup_and_local_overrides(self):
        self.install()
        (self.home/'.config/dotfiles/local.zsh').write_text('alias ll="echo local-wins"\n')
        result = self.run_cmd('zsh', '-ic', '[[ ${aliases[ll]} == "echo local-wins" ]] && (( $+functions[nvims] )) && (( $+functions[extract] ))')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('command not found', result.stderr)
        result = self.run_cmd('zsh', '-c', 'echo noninteractive')
        self.assertEqual(result.stdout, 'noninteractive\n')
        self.assertNotIn('command not found', result.stderr)

    def test_mac_links_and_login_preservation(self):
        (self.home/'.bash_profile').write_text('# site login\n')
        self.install('--platform', 'mac')
        backups = sorted(str(p) for p in self.home.glob('.dotfiles-backup/**/*'))
        self.install('--platform', 'mac')
        self.assertEqual(backups, sorted(str(p) for p in self.home.glob('.dotfiles-backup/**/*')))
        self.assertEqual((self.home/'.bash_profile').read_text(), '# site login\n')
        self.assertFalse((self.home/'.profile').exists())
        self.assertFalse((self.home/'Library/Application Support/Code/User/settings.json').exists())
        self.assertEqual((self.home/'.ssh/config').resolve(), ROOT/'config/mac/ssh/config')
        self.assertIn('Include ~/.ssh/config.local', (self.home/'.ssh/config').read_text())
        self.assertEqual((self.home/'.config/gh/config.yml').resolve(), ROOT/'config/cli/gh/config.yml')
        self.assertEqual((self.home/'.config/micro/settings.json').resolve(), ROOT/'config/cli/micro/settings.json')
        self.assertEqual((self.home/'.config/karabiner/karabiner.json').resolve(), ROOT/'config/mac/karabiner/karabiner.json')
        self.assertEqual((self.home/'.warp/settings.toml').resolve(), ROOT/'config/mac/warp/settings.toml')
        for p in self.home.rglob('*'):
            if p.is_symlink(): self.assertTrue(p.exists(), str(p))

    def test_local_ssh_fragment_precedes_shared_defaults(self):
        ssh_dir = self.home/'.ssh'
        ssh_dir.mkdir()
        local = ssh_dir/'config.local'
        fragment = ssh_dir/'config.hep.local'
        fragment.write_text('Host local-compute\n'
                            ' HostName compute.example.invalid\n'
                            ' User local-user\n'
                            ' Port 2222\n'
                            ' ProxyJump local-gateway\n'
                            ' IdentityAgent none\n'
                            ' ForwardAgent no\n'
                            ' ControlMaster no\n'
                            ' ServerAliveInterval 600\n')
        local.write_text(f'Include "{fragment}"\n\nHost *\n')
        for platform, source in [('linux', 'config/ssh/config'), ('mac', 'config/mac/ssh/config')]:
            with self.subTest(platform=platform):
                managed = self.home/f'ssh-{platform}.config'
                managed.write_text((ROOT/source).read_text().replace(
                    'Include ~/.ssh/config.local', f'Include "{local}"'))
                result = self.run_cmd('ssh', '-G', '-F', str(managed), 'local-compute')
                self.assertEqual(result.returncode, 0, result.stderr)
                values = dict(line.split(' ', 1) for line in result.stdout.splitlines() if ' ' in line)
                self.assertEqual(values['hostname'], 'compute.example.invalid')
                self.assertEqual(values['user'], 'local-user')
                self.assertEqual(values['port'], '2222')
                self.assertEqual(values['proxyjump'], 'local-gateway')
                self.assertEqual(values['identityagent'], 'none')
                self.assertEqual(values['forwardagent'], 'no')
                self.assertIn(values['controlmaster'], ('no', 'false'))
                self.assertEqual(values['serveraliveinterval'], '600')
        fragment.unlink()
        result = self.run_cmd('ssh', '-G', '-F', str(self.home/'ssh-linux.config'), 'local-compute')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('hostname local-compute\n', result.stdout)

    def test_mac_profile_loads_linked_bash_config(self):
        self.install('--platform', 'mac')
        self.assertEqual((self.home/'.profile').resolve(), ROOT/'config/mac/shell/.profile')
        result = self.run_cmd('bash', '--noprofile', '-ic', '. "$HOME/.profile"; test "$DOTFILES_ROOT" = "'+str(ROOT)+'" && alias ll >/dev/null')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_mac_preserves_an_unmanaged_profile(self):
        profile = self.home/'.profile'
        profile.write_text('export DEVICE_LOGIN_SETTING=preserved\n')
        self.install('--platform', 'mac')
        self.install('--platform', 'mac')
        self.assertFalse(profile.is_symlink())
        self.assertEqual(profile.read_text(), 'export DEVICE_LOGIN_SETTING=preserved\n')
        self.assertFalse(list(self.home.glob('.dotfiles-backup/*/.profile')))

    def test_custom_prompt_is_linked_outside_framework_sources(self):
        (self.home/'.oh-my-zsh/.git').mkdir(parents=True)
        self.install()
        theme = self.home/'.oh-my-zsh/custom/themes/dracula-pro.zsh-theme'
        self.assertTrue(theme.is_symlink())
        self.assertEqual(theme.resolve(), ROOT/'config/zsh/themes/dracula-pro.zsh-theme')
        self.assertFalse((self.home/'.oh-my-zsh/themes/dracula-pro.zsh-theme').exists())

    def test_status_detects_app_replacing_a_link(self):
        self.install('--platform', 'mac')
        self.assertEqual(self.run_cmd('bash', str(ROOT/'install.sh'), '--platform', 'mac', '--status').returncode, 0)
        config = self.home/'.config/gh/config.yml'
        config.unlink()
        config.write_text('editor: micro\n')
        result = self.run_cmd('bash', str(ROOT/'install.sh'), '--platform', 'mac', '--status')
        self.assertEqual(result.returncode, 1)
        self.assertIn('Detached: '+str(config), result.stdout)
        self.assertEqual(config.read_text(), 'editor: micro\n')

    def test_retired_environment_does_not_load_cluster_settings(self):
        self.install()
        env = dict(self.env, DOTFILES_PROFILE='hep', DOTFILES_MACHINE='lxplus901')
        command = 'for name in lhcb cern mount_gpu afs proxy; do if alias "$name" >/dev/null 2>&1; then exit 1; fi; done'
        for shell_args in [('bash', '--noprofile', '--rcfile', str(self.home/'.bashrc'), '-ic'),
                           ('zsh', '-ic')]:
            result = self.run_cmd(*shell_args, command, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('command not found', result.stderr)
            self.assertNotIn('syntax error', result.stderr)

    def test_legacy_cleanup_preserves_unmanaged_files(self):
        (self.home/'config.zsh').symlink_to(ROOT/'zsh/config.zsh')
        (self.home/'plugins.zsh').write_text('# mine\n')
        self.install()
        self.assertFalse((self.home/'config.zsh').is_symlink())
        self.assertEqual((self.home/'plugins.zsh').read_text(), '# mine\n')
        self.assertEqual(len(list(self.home.glob('.dotfiles-backup/*/config.zsh'))), 1)

    def test_mac_shell_startup_with_mock_os(self):
        fake = self.home/'test-bin'
        uname = fake/'uname'
        uname.write_text('#!/bin/sh\necho Darwin\n')
        uname.chmod(0o755)
        env = dict(self.env, PATH=str(fake)+':/usr/bin:/bin', ATUIN_CONFIG_DIR='/legacy/atuin')
        self.install('--platform', 'mac')
        result = self.run_cmd('zsh', '-ic', "[[ ${aliases[ports]} == 'lsof -nP -iTCP -sTCP:LISTEN' && -z ${ATUIN_CONFIG_DIR-} ]]", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('command not found', result.stderr)

    def test_retired_profile_link_migrates_to_personal(self):
        config = self.home/'.config/dotfiles'
        config.mkdir(parents=True)
        (config/'profile').symlink_to(ROOT/'setup/profiles/hep')
        self.install('--dry-run')
        self.assertEqual((config/'profile').readlink(), ROOT/'setup/profiles/hep')
        self.install()
        self.assertEqual((config/'profile').read_text(), 'personal\n')
        self.assertTrue((self.home/'.zshrc').is_symlink())
        self.assertTrue(list(self.home.glob('.dotfiles-backup/*/.config/dotfiles/profile')))
        self.assertEqual(self.run_cmd('bash', str(ROOT/'install.sh'), '--status').returncode, 0)

    def test_local_override_migration_and_early_environment(self):
        config = self.home/'.config/dotfiles'
        config.mkdir(parents=True)
        old = config/'environment.local.zsh'
        old.write_text('export ZSH_THEME=custom-test\n')
        (config/'zshrc.local.zsh').write_text('alias ll="echo old"\n')
        (config/'local.zsh').write_text('alias ll="echo current"\n')
        self.install('--dry-run')
        self.assertTrue(old.exists())
        self.assertFalse((config/'local.env.zsh').exists())
        self.install()
        self.assertFalse(old.exists())
        self.assertTrue(list(self.home.glob('.dotfiles-backup/*/.config/dotfiles/environment.local.zsh')))
        result = self.run_cmd('zsh', '-ic', '[[ $ZSH_THEME == custom-test && ${aliases[ll]} == "echo current" ]]')
        self.assertEqual(result.returncode, 0, result.stderr)
        current = (config/'local.zsh').read_text()
        self.install()
        self.assertEqual((config/'local.zsh').read_text(), current)

    def test_lazy_nvm_without_completion_script(self):
        nvm = self.home/'.nvm'
        nvm.mkdir()
        (nvm/'nvm.sh').write_text('nvm() { echo nvm-loaded; }\n')
        self.install()
        result = self.run_cmd('zsh', '-ic', 'nvm --version')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'nvm-loaded\n')

    def test_posix_login_profile_loads_shared_environment(self):
        self.install()
        result = self.run_cmd('sh', '-c', '. "$HOME/.profile"; command -v terminal_quran.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(ROOT/'bin/terminal_quran.sh'))
        self.assertEqual(result.stderr, '')

    def test_existing_dangling_profile_is_migrated(self):
        (self.home/'.profile').symlink_to(ROOT/'sh/.profile')
        (self.home/'cli').symlink_to(ROOT/'cli')
        self.install()
        self.assertEqual((self.home/'.profile').resolve(), ROOT/'shell/.profile')
        self.assertFalse((self.home/'cli').is_symlink())

    def test_get_size_preserves_apparent_file_size(self):
        self.install()
        if sys.platform == 'darwin':
            uname = self.home/'test-bin/uname'
            uname.write_text('#!/bin/sh\necho Darwin\n')
        target = self.home/'sparse file'
        with target.open('wb') as stream:
            stream.truncate(2 * 1024 * 1024)
        result = self.run_cmd('zsh', '-ic', 'get_size "$HOME/sparse file"')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('Parse error', result.stderr)
        self.assertEqual(result.stdout.strip(), f"Size of '{target}': 2.00 MB")
        small = self.home/'small file'
        small.write_bytes(b'x' * 512)
        result = self.run_cmd('zsh', '-ic', 'get_size "$HOME/small file"')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), f"Size of '{small}': 512 B")

    def test_bash_listing_shortcuts_are_preserved(self):
        self.install()
        (self.home/'.sudo_as_admin_successful').touch()
        result = self.run_cmd('bash', '--noprofile', '--rcfile', str(self.home/'.bashrc'), '-ic', 'alias ll; alias la')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "alias ll='ls -alF'\nalias la='ls -A'\n")

    def test_get_size_requires_no_bc_dependency(self):
        commands = self.home/'size-commands'
        commands.mkdir()
        for name in ('uname', 'du', 'stat', 'awk'):
            (commands/name).symlink_to(shutil.which(name))
        env = dict(self.env, PATH=str(commands), LC_ALL='C')
        target = self.home/'size sample'
        for size, expected in [(1536, '1.50 KB'), (1572864, '1.50 MB'), (1610612736, '1.50 GB')]:
            with self.subTest(size=size):
                with target.open('wb') as stream:
                    stream.truncate(size)
                result = self.run_cmd(shutil.which('zsh'), '-f', '-c',
                                      'source "$1"; get_size "$2"', 'size-check',
                                      str(ROOT/'zsh/functions.zsh'), str(target), env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, '')
                self.assertEqual(result.stdout.strip(), f"Size of '{target}': {expected}")

    def test_saved_profile_without_final_newline(self):
        config = self.home/'.config/dotfiles'
        config.mkdir(parents=True)
        (config/'profile').write_text('hep')
        result = self.run_cmd('bash', str(ROOT/'install.sh'), '--check-existing')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.install()
        self.assertEqual((config/'profile').read_text(), 'personal\n')
        self.assertTrue((self.home/'.zshrc').is_symlink())

    def test_reinstall_after_checkout_moves(self):
        scenarios = [('personal', 'linux', False), ('retired', 'linux', False),
                     ('personal', 'mac', False), ('personal', 'linux', True)]
        for profile, platform, aliased in scenarios:
            with self.subTest(previous_profile=profile, platform=platform, aliased=aliased):
                base = self.home
                label = f'{profile} {platform} {aliased}'
                if aliased:
                    base = self.home/'home alias'
                    base.symlink_to(self.home, target_is_directory=True)
                original = base/f'original checkout {label}'
                moved = base/f'moved checkout {label}'
                target_home = base/f'home {label}'
                target_home.mkdir()
                shutil.copytree(ROOT, original, ignore=shutil.ignore_patterns('.git', '.claude', '.cache', 'fonts', '__pycache__'))
                env = dict(self.env, HOME=str(target_home), ZDOTDIR=str(target_home))
                result = self.run_cmd('bash', str(original/'install.sh'), '--platform', platform, env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                if profile == 'retired':
                    marker = target_home/'.config/dotfiles/profile'
                    marker.unlink()
                    marker.symlink_to(original/'setup/profiles/hep')
                original.rename(moved)
                result = self.run_cmd('bash', str(moved/'install.sh'), '--platform', platform, '--check-existing', env=env)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                result = self.run_cmd('bash', str(moved/'install.sh'), '--platform', platform, env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((target_home/'.config/dotfiles/profile').read_text().strip(), 'personal')
                expected_profile = moved/('config/mac/shell/.profile' if platform == 'mac' else 'shell/.profile')
                self.assertEqual((target_home/'.profile').resolve(), expected_profile.resolve())
                self.assertEqual((target_home/'.bashrc').resolve(), (moved/'bash/.bashrc').resolve())
                for target, source in [('.codex/AGENTS.md', 'agent-workflow/global.md'),
                                       ('.agents/skills/research-audit/SKILL.md', 'agent-workflow/skills/research-audit/SKILL.md'),
                                       ('.agents/skills/engineering-audit/SKILL.md', 'agent-workflow/skills/engineering-audit/SKILL.md')]:
                    self.assertEqual((target_home/target).resolve(strict=True), (moved/source).resolve(strict=True))
                for name in ('research-audit', 'engineering-audit'):
                    self.assertEqual((target_home/'.claude/skills'/name/'SKILL.md').resolve(strict=True),
                                     (moved/'agent-workflow/skills'/name/'SKILL.md').resolve(strict=True))
                result = self.run_cmd('bash', str(moved/'install.sh'), '--platform', platform, '--status', env=env)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertFalse((target_home/'.config/dotfiles/site.bash').exists())
                result = self.run_cmd('sh', '-c', '. "$HOME/.profile"; command -v terminal_quran.sh', env=env)
                self.assertEqual(Path(result.stdout.strip()).resolve(), (moved/'bin/terminal_quran.sh').resolve())
                self.assertEqual(result.stderr, '')

    def test_invalid_arguments_make_no_changes(self):
        for args in [('--profile', '../other'), ('--profile',), ('--profile', 'hep'), ('--copy',), ('--platform','mac','--profile','hep')]:
            result = self.run_cmd('bash', str(ROOT/'install.sh'), *args)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual([p.name for p in self.home.iterdir()], ['test-bin'])

if __name__ == '__main__':
    unittest.main()
