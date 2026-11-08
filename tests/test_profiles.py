"""Fresh-home coverage for minimal machines, offline diagnostics, and standalone HEP."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='dotfiles profiles ')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.home = self.base / 'home'
        self.home.mkdir()
        self.fake = self.base / 'tools'
        self.fake.mkdir()
        (self.fake / 'uname').write_text('#!/bin/sh\necho Linux\n')
        (self.fake / 'uname').chmod(0o755)
        self.env = dict(HOME=str(self.home), ZDOTDIR=str(self.home),
                        PATH=str(self.fake) + ':/usr/bin:/bin', TERM='dumb',
                        USER='dotfiles-test', LOGNAME='dotfiles-test',
                        GIT_CONFIG_NOSYSTEM='1', RUN_QURAN_VERSE_ON_STARTUP='false')

    def run_cmd(self, *args, env=None):
        return subprocess.run([str(arg) for arg in args], cwd=ROOT, env=env or self.env,
                              text=True, capture_output=True)

    def install(self, profile='minimal', platform='linux'):
        result = self.run_cmd('bash', ROOT / 'install.sh', '--profile', profile, '--platform', platform)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def doctor(self, env=None):
        return self.run_cmd('bash', ROOT / 'bin/dotfiles', 'doctor', env=env)

    def test_minimal_install_both_platforms_without_desktop_links(self):
        for platform in ('linux', 'mac'):
            with self.subTest(platform=platform):
                self.install(platform=platform)
                self.assertEqual((self.home / '.config/dotfiles/profile').read_text(), 'minimal\n')
                self.assertEqual((self.home / '.gitconfig').resolve(), ROOT / 'config/git/minimal.gitconfig')
                for name in ('.zshrc', '.zprofile', '.zshenv', '.ssh', '.claude', '.waveterm', '.config/ghostty'):
                    self.assertFalse(os.path.lexists(self.home / name), name)
                result = self.run_cmd('bash', ROOT / 'install.sh', '--platform', platform, '--status')
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_minimal_git_commits_without_desktop_or_signing_tools(self):
        self.install()
        repo = self.base / 'project'
        repo.mkdir()
        for args in (('init', '-q', str(repo)),):
            result = self.run_cmd('git', *args)
            self.assertEqual(result.returncode, 0, result.stderr)
        (repo / 'README.md').write_text('fresh VM\n')
        for args in (('add', 'README.md'), ('commit', '-qm', 'First commit')):
            result = self.run_cmd('git', '-C', repo, *args)
            self.assertEqual(result.returncode, 0, result.stderr)
        for key, expected in (('core.editor', 'vi'), ('core.pager', 'less'), ('commit.gpgsign', 'false')):
            result = self.run_cmd('git', 'config', '--get', key)
            self.assertEqual(result.stdout.strip(), expected)
        for key in ('gpg.ssh.program', 'credential.https://github.com.helper', 'filter.lfs.required'):
            result = self.run_cmd('git', 'config', '--get', key)
            self.assertEqual(result.returncode, 1, key)
        (repo / '.codex').mkdir()
        (repo / '.codex/config.toml').write_text('# private preferences\n')
        result = self.run_cmd('git', '-C', repo, 'status', '--porcelain')
        self.assertEqual(result.stdout, '')

    def test_minimal_local_git_override_wins(self):
        self.install()
        override = self.home / '.config/dotfiles/local.gitconfig'
        override.write_text('[core]\n editor = custom-editor\n[commit]\n gpgsign = true\n')
        result = self.run_cmd('git', 'config', '--get', 'core.editor')
        self.assertEqual(result.stdout.strip(), 'custom-editor')

    def test_doctor_minimal_is_offline_and_read_only(self):
        self.install()
        before = self.snapshot_home()
        result = self.doctor()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('0 failure(s)', result.stdout)
        self.assertIn('Commit signing is optional', result.stdout)
        self.assertIn('authentication was not contacted', result.stdout)
        self.assertEqual(self.snapshot_home(), before)

    def snapshot_home(self):
        return {str(path.relative_to(self.home)): os.readlink(path) if path.is_symlink()
                else path.read_bytes() for path in self.home.rglob('*')
                if path.is_symlink() or path.is_file()}

    def test_doctor_reports_missing_python_without_requiring_python(self):
        self.install()
        for tool in ('bash', 'dirname', 'readlink', 'git', 'vi', 'less'):
            (self.fake / tool).symlink_to(shutil.which(tool, path='/usr/bin:/bin'))
        result = self.doctor(env=dict(self.env, PATH=str(self.fake)))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('python3 missing', result.stdout)
        self.assertNotIn('git missing', result.stdout)

    def test_doctor_reports_detached_config_without_replacing_it(self):
        self.install()
        path = self.home / '.bashrc'
        path.unlink()
        path.write_text('# application replaced my link\n')
        before = self.snapshot_home()
        result = self.doctor()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Managed links need attention', result.stdout)
        self.assertEqual(self.snapshot_home(), before)

    def test_doctor_reports_missing_editor_and_signer_without_execution(self):
        self.install()
        local = self.home / '.config/dotfiles/local.gitconfig'
        local.write_text('[core]\n editor = missing-editor\n[commit]\n gpgsign = true\n'
                         '[gpg]\n format = ssh\n[gpg "ssh"]\n program = missing-signer\n'
                         '[user]\n signingkey = example-public-key\n')
        result = self.doctor()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Git editor unavailable (missing-editor)', result.stdout)
        self.assertIn('Commit signing program unavailable (missing-signer)', result.stdout)
        # Configured shell snippets must never be evaluated by diagnostics.
        local.write_text('[core]\n editor = "sh -c \'touch ' + str(self.home / 'executed') + '\'"\n')
        self.doctor()
        self.assertFalse((self.home / 'executed').exists())

    def test_doctor_reports_uninstalled_profile(self):
        result = self.doctor()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Profile not installed', result.stdout)

    def test_copied_hep_folder_installs_and_moves_independently(self):
        standalone = self.base / 'cluster config'
        shutil.copytree(ROOT / 'hep', standalone)
        (self.home / '.bashrc').write_text('export SITE_KEPT=yes\n')
        (self.home / '.gitconfig').write_text('# existing cluster Git settings\n')
        for target in (standalone, self.base / 'moved cluster config'):
            if target != standalone:
                standalone.rename(target)
            result = self.run_cmd('bash', target / 'install.sh')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = self.run_cmd('bash', target / 'install.sh', '--status')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = self.run_cmd('bash', '--noprofile', '--rcfile', self.home / '.bashrc', '-ic',
                                  'test "$SITE_KEPT" = yes && test -z "${DOTFILES_ROOT-}" && alias afs >/dev/null',
                                  env=dict(self.env, DOTFILES_MACHINE='lxplus900'))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('No such file', result.stderr)
            self.assertEqual((self.home / '.gitconfig').read_text(), '# existing cluster Git settings\n')
            self.assertFalse((self.home / '.zshrc').exists())
            self.assertFalse((self.home / '.ssh').exists())

    def test_hep_install_without_git_python_or_zsh(self):
        standalone = self.base / 'hep-only'
        shutil.copytree(ROOT / 'hep', standalone)
        for tool in ('bash', 'dirname', 'readlink', 'date', 'mkdir', 'ln', 'mv', 'cp', 'cmp', 'dircolors'):
            executable = shutil.which(tool, path='/usr/bin:/bin')
            if executable:
                (self.fake / tool).symlink_to(executable)
        env = dict(self.env, PATH=str(self.fake), DOTFILES_MACHINE='unknown')
        result = self.run_cmd('/bin/bash', standalone / 'install.sh', env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.run_cmd('/bin/bash', '--noprofile', '--rcfile', self.home / '.bashrc', '-ic',
                              'declare -F extract >/dev/null', env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('command not found', result.stderr)

    def test_legacy_hep_layout_migrates_without_capturing_managed_bashrc(self):
        config = self.home / '.config/dotfiles'
        config.mkdir(parents=True)
        (config / 'profile').symlink_to(ROOT / 'setup/profiles/hep')
        (self.home / '.bashrc').symlink_to(ROOT / 'bash/.bashrc')
        (self.home / '.profile').symlink_to(ROOT / 'shell/.profile')
        self.install(profile='hep')
        self.assertFalse((config / 'site.bash').exists())
        self.assertEqual((self.home / '.bashrc').resolve(), ROOT / 'hep/.bashrc')
        self.assertEqual((self.home / '.profile').resolve(), ROOT / 'hep/.profile')

    def test_hep_doctor_does_not_require_personal_tools(self):
        self.install(profile='hep')
        result = self.doctor()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Standalone HEP requires Bash', result.stdout)
        self.assertNotIn('Commit signing', result.stdout)


if __name__ == '__main__':
    unittest.main()
