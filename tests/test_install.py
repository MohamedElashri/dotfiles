"""Integration checks using disposable homes; never source the user's startup files."""
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest

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

    def run_cmd(self, *args, env=None):
        return subprocess.run(args, env=env or self.env, cwd=ROOT, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def install(self, *args):
        result = self.run_cmd('bash', str(ROOT/'install.sh'), *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_dry_run_all_profiles(self):
        for args in [(), ('--platform', 'mac'), ('--profile', 'hep')]:
            self.install(*args, '--dry-run')
            self.assertEqual(list(self.home.iterdir()), [])

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
        self.assertEqual(result.stderr, '')
        result = self.run_cmd('zsh', '-c', 'echo noninteractive')
        self.assertEqual(result.stdout, 'noninteractive\n')
        self.assertEqual(result.stderr, '')

    def test_mac_links_and_login_preservation(self):
        (self.home/'.bash_profile').write_text('# site login\n')
        self.install('--platform', 'mac')
        self.assertEqual((self.home/'.bash_profile').read_text(), '# site login\n')
        self.assertFalse((self.home/'.profile').exists())
        self.assertTrue((self.home/'Library/Application Support/Code/User/settings.json').is_file())
        for p in self.home.rglob('*'):
            if p.is_symlink(): self.assertTrue(p.exists(), str(p))

    def test_hep_runtime_selection_shared_home(self):
        self.install('--profile', 'hep')
        self.assertFalse((self.home/'.zshrc').exists())
        self.assertFalse((self.home/'.gitconfig').exists())
        for host, command in [('lxplus901', 'alias afs >/dev/null && declare -F ktmux >/dev/null'),
                              ('unknown', '! alias afs >/dev/null 2>&1'),
                              ('sneezy', 'alias mydata >/dev/null'),
                              ('sleepy', 'alias b_data >/dev/null'),
                              ('gpu_farm', 'alias run_pvfinder_gpu >/dev/null')]:
            env = dict(self.env, DOTFILES_MACHINE=host)
            result = self.run_cmd('bash', '--noprofile', '--rcfile', str(self.home/'.bashrc'), '-ic', command, env=env)
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
        fake.mkdir()
        uname = fake/'uname'
        uname.write_text('#!/bin/sh\necho Darwin\n')
        uname.chmod(0o755)
        env = dict(self.env, PATH=str(fake)+':/usr/bin:/bin')
        self.install('--platform', 'mac')
        result = self.run_cmd('zsh', '-ic', "[[ ${aliases[ports]} == 'lsof -nP -iTCP -sTCP:LISTEN' ]]", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')

    def test_saved_hep_profile_is_reused(self):
        self.install('--profile', 'hep')
        self.install()
        self.assertEqual((self.home/'.config/dotfiles/profile').read_text(), 'hep\n')
        self.assertFalse((self.home/'.zshrc').exists())

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

    def test_get_size_preserves_linux_apparent_size(self):
        self.install()
        target = self.home/'sparse file'
        with target.open('wb') as stream:
            stream.truncate(2 * 1024 * 1024)
        result = self.run_cmd('zsh', '-ic', 'get_size "$HOME/sparse file"')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertEqual(result.stdout.strip(), f"Size of '{target}': 2.00 MB")

    def test_bash_listing_shortcuts_are_preserved(self):
        self.install()
        result = self.run_cmd('bash', '--noprofile', '--rcfile', str(self.home/'.bashrc'), '-ic', 'alias ll; alias la')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "alias ll='ls -alF'\nalias la='ls -A'\n")

    def test_saved_profile_without_final_newline(self):
        config = self.home/'.config/dotfiles'
        config.mkdir(parents=True)
        (config/'profile').write_text('hep')
        self.install()
        self.assertEqual((config/'profile').read_text(), 'hep\n')
        self.assertFalse((self.home/'.zshrc').exists())

    def test_reinstall_after_checkout_moves(self):
        for profile in ['personal', 'hep']:
            with self.subTest(profile=profile):
                original = self.home/f'original checkout {profile}'
                moved = self.home/f'moved checkout {profile}'
                target_home = self.home/f'home {profile}'
                target_home.mkdir()
                shutil.copytree(ROOT, original, ignore=shutil.ignore_patterns('.git', '.claude', 'fonts', '__pycache__'))
                env = dict(self.env, HOME=str(target_home), ZDOTDIR=str(target_home))
                result = self.run_cmd('bash', str(original/'install.sh'), '--profile', profile, env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                original.rename(moved)
                result = self.run_cmd('bash', str(moved/'install.sh'), env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((target_home/'.config/dotfiles/profile').read_text().strip(), profile)
                self.assertEqual((target_home/'.profile').resolve(), moved/'shell/.profile')
                self.assertEqual((target_home/'.bashrc').resolve(), moved/'bash/.bashrc')
                self.assertFalse((target_home/'.config/dotfiles/site.bash').exists())
                result = self.run_cmd('sh', '-c', '. "$HOME/.profile"; command -v terminal_quran.sh', env=env)
                self.assertEqual(result.stdout.strip(), str(moved/'bin/terminal_quran.sh'))
                self.assertEqual(result.stderr, '')

    def test_invalid_arguments_make_no_changes(self):
        for args in [('--profile', '../other'), ('--profile',), ('--copy',), ('--platform','mac','--profile','hep')]:
            result = self.run_cmd('bash', str(ROOT/'install.sh'), *args)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(self.home.iterdir()), [])

if __name__ == '__main__':
    unittest.main()
