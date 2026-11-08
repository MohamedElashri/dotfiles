"""Exercise updates against a local remote without network or user Git settings."""
from pathlib import Path
import shutil
import json
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='dotfiles update test ')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.home = self.base / 'home'
        self.home.mkdir()
        self.env = dict(HOME=str(self.home), PATH='/usr/bin:/bin',
                        GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0')
        self.remote = self.base / 'remote.git'
        self.source = self.base / 'source'
        self.checkout = self.base / 'installed checkout'
        self.git(self.base, 'init', '--bare', '-q', str(self.remote))
        self.git(self.base, 'init', '-q', str(self.source))
        self.git(self.source, 'checkout', '-qb', 'main')
        (self.source / 'bin').mkdir()
        (self.source / 'scripts').mkdir()
        (self.source / 'setup/profiles').mkdir(parents=True)
        (self.source / 'setup/profiles/personal').write_text('personal\n')
        shutil.copy2(ROOT / 'bin/dotfiles', self.source / 'bin/dotfiles')
        shutil.copy2(ROOT / 'scripts/update.py', self.source / 'scripts/update.py')
        self.write_installer('original')
        self.commit(self.source, 'Initial configuration')
        self.git(self.source, 'remote', 'add', 'origin', str(self.remote))
        self.git(self.source, 'push', '-qu', 'origin', 'main')
        self.git(self.base, 'clone', '-q', '-b', 'main', str(self.remote), str(self.checkout))
        profile = self.home / '.config/dotfiles/profile'
        profile.parent.mkdir(parents=True)
        profile.symlink_to(self.checkout / 'setup/profiles/personal')
        # Deliberately conflicting personal defaults must not rebase or stash.
        (self.home / '.gitconfig').write_text(
            '[pull]\n rebase = true\n[rebase]\n autoStash = true\n'
            '[merge]\n autoStash = true\n')

    def git(self, directory, *args):
        result = subprocess.run(['git', '-C', str(directory), *args],
                                env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def commit(self, directory, message):
        self.git(directory, 'add', '.')
        self.git(directory, '-c', 'user.name=Test', '-c', 'user.email=test@example.com',
                 '-c', 'commit.gpgsign=false', 'commit', '-qm', message)

    def write_installer(self, version, *, extra='', paths=(), links=()):
        # A small installer implementing the same read-only manifest/status contract.
        # Failure injection can distinguish disposable validation from the live home.
        plan = ''.join(f'printf "change\\0%s\\0" "$HOME/{name}"\n' for name in paths)
        plan += ''.join(f'printf "link\\0%s\\0" "$HOME/{name}"\n' for name in links)
        apply_links = ''.join(
            f'ln -sfn "$root/setup/profiles/personal" "$HOME/{name}"\n' for name in links)
        (self.source / 'install.sh').write_text(
            '#!/usr/bin/env bash\nset -eu\n'
            'root=$(cd "$(dirname "$0")" && pwd -P)\n'
            'mode=install\n'
            'while [ "$#" -gt 0 ]; do\n'
            ' case "$1" in\n'
            ' --profile) shift ;;\n'
            ' --manifest) mode=manifest ;;\n'
            ' --status) mode=status ;;\n'
            ' --dry-run) mode=preview ;;\n'
            ' esac\n shift\ndone\n'
            'case "$mode" in\n'
            ' manifest)\n'
            '  printf "link\\0%s\\0" "$HOME/.config/dotfiles/profile"\n'
            '  printf "change\\0%s\\0" "$HOME/install-ran"\n'
            '  printf "mode\\0%s\\0" "$HOME/.ssh"\n'
            + plan + '  exit 0 ;;\n'
            ' status)\n'
            '  if [ ! -L "$HOME/.config/dotfiles/profile" ] || '
            '[ "$(readlink "$HOME/.config/dotfiles/profile")" != "$root/setup/profiles/personal" ]; then\n'
            '   echo "Detached: $HOME/.config/dotfiles/profile"; exit 1\n'
            '  fi\n exit 0 ;;\n'
            ' preview) exit 0 ;;\n'
            'esac\n'
            'mkdir -p "$HOME/.config/dotfiles"\n'
            'ln -sfn "$root/setup/profiles/personal" "$HOME/.config/dotfiles/profile"\n'
            'mkdir -p "$HOME/.ssh"\nchmod 700 "$HOME/.ssh"\n'
            f'printf "%s\\n" "{version}" > "$HOME/install-ran"\n'
            + apply_links + extra)

    def publish(self):
        self.write_installer('updated')
        self.commit(self.source, 'Update configuration')
        self.git(self.source, 'push', '-q')

    def push_installer(self):
        self.commit(self.source, 'Change installer')
        self.git(self.source, 'push', '-q')

    def update(self, *args, executable=None):
        return subprocess.run([str(executable or self.checkout / 'bin/dotfiles'),
                               'update', *args], cwd=self.home,
                              env=self.env, text=True, capture_output=True)

    def rollback(self):
        return subprocess.run([str(self.checkout / 'bin/dotfiles'), 'rollback'],
                              cwd=self.home, env=self.env, text=True, capture_output=True)

    def states(self):
        return [json.loads(path.read_text())
                for path in (self.checkout / '.git/dotfiles-updates').glob('*/state.json')]

    def assert_not_installed(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / 'install-ran').exists())

    def test_pull_and_run_updated_installer_from_another_directory(self):
        self.publish()
        result = self.update()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / 'install-ran').read_text(), 'updated\n')
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'),
                         self.git(self.source, 'rev-parse', 'HEAD'))
        self.assertEqual(self.git(self.checkout, 'status', '--porcelain'), '')
        # Updating when already current still reapplies configuration.
        self.assertEqual(self.update().returncode, 0)

    def test_dirty_updates_preserve_staged_unstaged_and_untracked_files(self):
        self.publish()
        for kind in ('unstaged', 'staged', 'untracked'):
            with self.subTest(kind=kind):
                target = self.checkout / ('local.txt' if kind == 'untracked' else 'install.sh')
                original = target.read_text() if target.exists() else None
                target.write_text('local edits\n')
                if kind == 'staged':
                    self.git(self.checkout, 'add', 'install.sh')
                before_head = self.git(self.checkout, 'rev-parse', 'HEAD')
                before_status = self.git(self.checkout, 'status', '--porcelain')
                result = self.update()
                self.assert_not_installed(result)
                self.assertIn('commit or stash', result.stderr)
                self.assertEqual(target.read_text(), 'local edits\n')
                self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), before_head)
                self.assertEqual(self.git(self.checkout, 'status', '--porcelain'), before_status)
                self.assertEqual(self.git(self.checkout, 'stash', 'list'), '')
                if kind == 'staged':
                    self.git(self.checkout, 'restore', '--staged', 'install.sh')
                if original is None:
                    target.unlink()
                else:
                    target.write_text(original)

    def test_divergence_does_not_rebase_merge_or_install(self):
        (self.checkout / 'local.txt').write_text('local commit\n')
        self.commit(self.checkout, 'Local configuration')
        before = self.git(self.checkout, 'rev-parse', 'HEAD')
        self.publish()
        result = self.update()
        self.assert_not_installed(result)
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), before)
        self.assertEqual(self.git(self.checkout, 'status', '--porcelain'), '')
        self.assertFalse((self.checkout / '.git/rebase-merge').exists())
        self.assertFalse((self.checkout / '.git/MERGE_HEAD').exists())

    def test_failed_pull_does_not_install(self):
        self.git(self.checkout, 'remote', 'set-url', 'origin', str(self.base / 'missing.git'))
        self.assert_not_installed(self.update())

    def test_detached_head_does_not_install(self):
        self.git(self.checkout, 'checkout', '-q', '--detach')
        result = self.update()
        self.assert_not_installed(result)
        self.assertIn('HEAD is detached', result.stderr)

    def test_missing_upstream_does_not_install(self):
        self.git(self.checkout, 'branch', '--unset-upstream')
        result = self.update()
        self.assert_not_installed(result)
        self.assertIn('no upstream', result.stderr)

    def test_relative_symlink_to_command(self):
        link = self.base / 'dotfiles'
        link.symlink_to('installed checkout/bin/dotfiles')
        self.publish()
        result = self.update(executable=link)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / 'install-ran').read_text(), 'updated\n')

    def test_incoming_internal_symlink_is_supported(self):
        (self.source / 'install').symlink_to('install.sh')
        (self.source / 'install-alias').symlink_to('install')
        self.push_installer()
        result = self.update()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.checkout / 'install').readlink(), Path('install.sh'))

    def test_incoming_external_symlink_stops_before_live_changes(self):
        (self.source / 'external').symlink_to('../../outside')
        self.push_installer()
        before = self.git(self.checkout, 'rev-parse', 'HEAD')
        self.assert_not_installed(self.update())
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), before)

    def test_incoming_absolute_or_cyclic_symlink_stops_before_live_changes(self):
        for target in ('/etc/passwd', 'unsafe'):
            with self.subTest(target=target):
                path = self.source / 'unsafe'
                if path.is_symlink():
                    path.unlink()
                path.symlink_to(target)
                self.push_installer()
                before = self.git(self.checkout, 'rev-parse', 'HEAD')
                self.assert_not_installed(self.update())
                self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), before)

    def test_invalid_update_options_do_not_pull_or_install(self):
        self.publish()
        before = self.git(self.checkout, 'rev-parse', 'HEAD')
        self.assert_not_installed(self.update('--dry-run'))
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), before)

    def test_preview_validates_without_changing_checkout_or_home(self):
        self.publish()
        before = self.git(self.checkout, 'rev-parse', 'HEAD')
        result = self.update('--check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), before)
        self.assertFalse((self.home / 'install-ran').exists())
        self.assertEqual(self.states(), [])

    def test_detached_home_configuration_stops_before_fetch(self):
        self.publish()
        profile = self.home / '.config/dotfiles/profile'
        profile.unlink()
        profile.write_text('personal\n')
        before = self.git(self.checkout, 'rev-parse', 'origin/main')
        result = self.update()
        self.assert_not_installed(result)
        self.assertIn('Detached:', result.stderr)
        self.assertEqual(profile.read_text(), 'personal\n')
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'origin/main'), before)

    def test_invalid_incoming_shell_stops_before_live_changes(self):
        self.publish()
        (self.source / 'broken.sh').write_text('if true; then\n')
        self.push_installer()
        before = self.git(self.checkout, 'rev-parse', 'HEAD')
        self.assert_not_installed(self.update())
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), before)

    def test_shell_startup_error_stops_before_live_changes(self):
        (self.source / 'bashrc').write_text('not_a_real_dotfiles_command\n')
        self.write_installer('updated', paths=('.bashrc',),
                             extra='ln -s "$root/bashrc" "$HOME/.bashrc"\n')
        self.push_installer()
        before = self.git(self.checkout, 'rev-parse', 'HEAD')
        result = self.update()
        self.assert_not_installed(result)
        self.assertIn('Incoming shell startup failed', result.stderr)
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), before)

    def test_invalid_platform_git_config_stops_before_live_changes(self):
        (self.source / 'linux.gitconfig').write_text('[broken\n')
        self.push_installer()
        before = self.git(self.checkout, 'rev-parse', 'HEAD')
        self.assert_not_installed(self.update())
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), before)

    def test_missing_incoming_source_stops_before_live_changes(self):
        self.write_installer('updated', extra='test -f "$root/missing-config"\n')
        self.push_installer()
        before = self.git(self.checkout, 'rev-parse', 'HEAD')
        self.assert_not_installed(self.update())
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), before)

    def test_failed_install_restores_commit_files_links_and_new_paths(self):
        before = self.git(self.checkout, 'rev-parse', 'HEAD')
        existing = self.home / 'existing.conf'
        existing.write_text('keep my settings\n')
        existing.chmod(0o640)
        link = self.home / 'custom-link'
        link.symlink_to('existing.conf')
        ssh = self.home / '.ssh'
        ssh.mkdir(mode=0o750)
        condition = shlex.quote(str(self.home))
        self.write_installer('updated', paths=('existing.conf', 'custom-link', 'new-dir/new.conf'), extra=(
            'printf changed > "$HOME/existing.conf"\n'
            'chmod 600 "$HOME/existing.conf"\n'
            'rm -f "$HOME/custom-link"\n'
            'ln -s new-location "$HOME/custom-link"\n'
            'mkdir -p "$HOME/new-dir"\n'
            'printf new > "$HOME/new-dir/new.conf"\n'
            f'if [ "$HOME" = {condition} ]; then exit 42; fi\n'))
        self.push_installer()
        result = self.update()
        self.assert_not_installed(result)
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), before)
        self.assertEqual(existing.read_text(), 'keep my settings\n')
        self.assertEqual(existing.stat().st_mode & 0o777, 0o640)
        self.assertEqual(link.readlink(), Path('existing.conf'))
        self.assertEqual(ssh.stat().st_mode & 0o777, 0o750)
        self.assertFalse((self.home / 'new-dir').exists())
        self.assertEqual(self.states()[-1]['status'], 'rolled-back')
        self.assertIn('Restored previous commit', result.stdout)

    def test_explicit_rollback_restores_last_successful_update(self):
        before = self.git(self.checkout, 'rev-parse', 'HEAD')
        self.publish()
        result = self.update()
        self.assertEqual(result.returncode, 0, result.stderr)
        state = self.states()[-1]
        self.assertEqual(state['previous'], before)
        self.assertEqual(state['status'], 'complete')
        # A no-op update must keep the useful rollback point.
        self.assertEqual(self.update().returncode, 0)
        self.assertEqual(len(self.states()), 1)
        result = self.rollback()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), before)
        self.assertFalse((self.home / 'install-ran').exists())
        self.assertFalse((self.home / '.ssh').exists())
        self.assertEqual(self.states()[-1]['status'], 'rolled-back')

    def test_rollback_preserves_subsequent_home_edits(self):
        self.publish()
        result = self.update()
        self.assertEqual(result.returncode, 0, result.stderr)
        marker = self.home / 'install-ran'
        marker.write_text('new local settings\n')
        after = self.git(self.checkout, 'rev-parse', 'HEAD')
        result = self.rollback()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('changed since the update', result.stderr)
        self.assertEqual(marker.read_text(), 'new local settings\n')
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), after)

    def test_rollback_preserves_subsequent_tracked_edits(self):
        self.publish()
        result = self.update()
        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.checkout / 'install.sh'
        target.write_text('# local edits\n')
        result = self.rollback()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(target.read_text(), '# local edits\n')

    def test_rollback_preserves_ignored_file_created_after_update(self):
        (self.source / 'AGENTS.md').write_text('old shared instructions\n')
        self.push_installer()
        self.git(self.checkout, 'pull', '--ff-only')
        (self.source / 'AGENTS.md').unlink()
        self.push_installer()
        self.git(self.checkout, 'config', 'core.excludesFile', str(ROOT / 'config/git/ignore'))
        result = self.update()
        self.assertEqual(result.returncode, 0, result.stderr)
        local = self.checkout / 'AGENTS.md'
        local.write_text('new local instructions\n')
        after = self.git(self.checkout, 'rev-parse', 'HEAD')
        result = self.rollback()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Rollback would replace an untracked file', result.stderr)
        self.assertEqual(local.read_text(), 'new local instructions\n')
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), after)

    def test_ignored_incoming_file_collision_is_preserved(self):
        self.git(self.checkout, 'config', 'core.excludesFile', str(ROOT / 'config/git/ignore'))
        local = self.checkout / 'AGENTS.md'
        local.write_text('local instructions\n')
        (self.source / 'AGENTS.md').write_text('shared instructions\n')
        self.push_installer()
        before = self.git(self.checkout, 'rev-parse', 'HEAD')
        result = self.update()
        self.assert_not_installed(result)
        self.assertEqual(local.read_text(), 'local instructions\n')
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), before)

    def test_concurrent_updates_are_rejected(self):
        import fcntl
        state_root = self.checkout / '.git/dotfiles-updates'
        state_root.mkdir()
        with (state_root / 'lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.update()
        self.assert_not_installed(result)
        self.assertIn('Another dotfiles update', result.stderr)

    def test_existing_new_managed_target_is_preserved(self):
        target = self.home / 'new-managed-config'
        target.write_text('local configuration\n')
        self.write_installer('updated', links=('new-managed-config',))
        self.push_installer()
        before = self.git(self.checkout, 'rev-parse', 'HEAD')
        result = self.update()
        self.assert_not_installed(result)
        self.assertIn('New managed path already exists', result.stderr)
        self.assertEqual(target.read_text(), 'local configuration\n')
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), before)

    def test_real_installer_update_and_rollback(self):
        # Use the real config tree and installer, with disposable Git/home paths.
        shutil.copytree(ROOT, self.source, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('.git', 'fonts', '__pycache__'))
        self.commit(self.source, 'Use complete configuration')
        self.git(self.source, 'push', '-q')
        self.git(self.checkout, 'pull', '--ff-only')
        result = subprocess.run(['bash', str(self.checkout / 'install.sh')],
                                env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        before = self.git(self.checkout, 'rev-parse', 'HEAD')
        aliases = self.source / 'shell/aliases.sh'
        aliases.write_text(aliases.read_text() + "\nalias update_test='echo updated'\n")
        self.push_installer()
        result = self.update()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        live_aliases = self.home / '.bashrc'
        result = subprocess.run(['bash', '--noprofile', '--rcfile', str(live_aliases),
                                 '-ic', 'alias update_test'], env=self.env,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('echo updated', result.stdout)
        result = self.rollback()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), before)
        self.assertNotIn('update_test', (self.checkout / 'shell/aliases.sh').read_text())
        self.assertTrue((self.home / '.bashrc').is_symlink())

    def test_interrupted_update_journal_blocks_further_updates(self):
        journal = self.checkout / '.git/dotfiles-updates/interrupted'
        journal.mkdir(parents=True)
        (journal / 'state.json').write_text(json.dumps({'status': 'applying'}))
        result = self.update()
        self.assert_not_installed(result)
        self.assertIn('interrupted update needs recovery', result.stderr)


if __name__ == '__main__':
    unittest.main()
