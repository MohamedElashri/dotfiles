"""Shared CLI behavior in Bash/Zsh, with mocked Linux/macOS and optional tools."""
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SHELLS = {name: shutil.which(name, path='/usr/bin:/bin') for name in ('bash', 'zsh')}
CORE_ALIASES = ('ll', 'la', 'l', 'l.', 'lt', 'du', 'df', 'cat', 'nano', 'vim', 'vi',
                'cpv', 'ports', 'update', 'upgrade', 'record', 'findgrep', 'grep',
                'process', 'process_user', 'path', 'restart_shell', 'tmux_new')
CORE_FUNCTIONS = ('extract', 'zipf', 'get_size', 'mkd', 'fff', 'ffs', 'ffe', 'fcount',
                  'count_files', 'git_root', 'git_search', 'create_and_push_repo',
                  'crun', 'GrePFind', 'nvims', 'dbash', 'dip', 'dst', 'dstop', 'drm',
                  'drmi', 'open_remote_pdf', 'transfer', 'cheat', 'lk', 'temps',
                  'ii', 'list_commands', 'showdisk', 'mycpu', 'edit_host', 'count', 'myip')


class SharedShellTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dotfiles-shared-cli-')
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.bin = self.home / 'test-bin'
        self.bin.mkdir()
        self.env = {'HOME': str(self.home), 'ZDOTDIR': str(self.home), 'DOTFILES_ROOT': str(ROOT),
                    'PATH': str(self.bin) + ':/usr/bin:/bin', 'HOMEBREW_PREFIX': str(self.bin),
                    'TERM': 'dumb', 'USER': 'dotfiles-test', 'SHELL': '/bin/zsh',
                    'LC_ALL': 'C', 'RUN_QURAN_VERSE_ON_STARTUP': 'false'}
        self.log = self.home / 'operations'
        self.env['OPERATION_LOG'] = str(self.log)
        for name in ('dust', 'duf', 'bat', 'micro', 'nvim', 'rsync', 'brew', 'gh', 'asciinema', 'lsof', 'column'):
            self.fake(name, 'exit 0')
        self.platform('Linux')

    def fake(self, name, body):
        target = self.bin / name
        target.write_text('#!/bin/sh\n' + body + '\n')
        target.chmod(0o755)

    def platform(self, system):
        self.fake('uname', f'if [ "$1" = -m ]; then echo arm64; else echo {system}; fi')

    def run_shell(self, shell, command, *, env=None, input_data=None, startup=False):
        environment = dict(self.env, **(env or {}))
        if startup:
            arguments = ([SHELLS[shell], '--noprofile', '--rcfile', str(self.home / '.bashrc'), '-ic']
                         if shell == 'bash' else [SHELLS[shell], '-ic'])
            script = command
        else:
            arguments = [SHELLS[shell], '-f' if shell == 'zsh' else '--noprofile', '-c']
            script = '. "$DOTFILES_ROOT/shell/interactive.sh"\n' + command
        return subprocess.run([*arguments, script], env=environment, cwd=self.home,
                              input=input_data, text=True, capture_output=True, timeout=20)

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('parse error', result.stderr.lower())
        self.assertNotIn('command not found', result.stderr.lower())

    def test_core_aliases_and_functions_match_in_all_four_environments(self):
        snapshots = []
        for system in ('Linux', 'Darwin'):
            self.platform(system)
            for shell in SHELLS:
                with self.subTest(system=system, shell=shell):
                    command = 'alias ' + ' '.join(shlex.quote(name) for name in CORE_ALIASES)
                    command += '\nfor name in ' + ' '.join(CORE_FUNCTIONS) + '; do typeset -f "$name" >/dev/null || exit 1; done'
                    result = self.run_shell(shell, command)
                    self.assert_success(result)
                    aliases = {}
                    for line in result.stdout.splitlines():
                        key, value = line.removeprefix('alias ').split('=', 1)
                        aliases[key] = ' '.join(shlex.split(value))
                    self.assertEqual(aliases['du'], 'dust')
                    self.assertEqual(aliases['ports'], 'lsof -nP -iTCP -sTCP:LISTEN')
                    self.assertEqual(aliases['ll'], 'ls -alF')
                    snapshots.append(aliases)
        self.assertTrue(all(value == snapshots[0] for value in snapshots))

    def test_alias_execution_preserves_arguments_and_home_paths_with_spaces(self):
        spaced_home = self.home / 'space home'
        spaced_home.mkdir()
        for name in ('ls', 'nvim', 'dust'):
            self.fake(name, 'printf "<%s>\\n" "$@"')
        for system in ('Linux', 'Darwin'):
            self.platform(system)
            for shell in SHELLS:
                result = self.run_shell(shell, 'if [ -n "${BASH_VERSION-}" ]; then shopt -s expand_aliases; fi\neval \'ll "a file"\'\neval edit_zsh\neval \'du "a directory"\'', env={'HOME': str(spaced_home)})
                self.assert_success(result)
                color = '--color=auto' if system == 'Linux' else '-G'
                self.assertEqual(result.stdout.splitlines(), [f'<{color}>', '<-alF>', '<a file>', f'<{spaced_home / ".zshrc"}>', '<a directory>'])

    def test_mkd_ignores_cdpath_and_preserves_the_callers_setting(self):
        elsewhere = self.home / 'elsewhere'
        (elsewhere / 'created').mkdir(parents=True)
        for shell in SHELLS:
            result = self.run_shell(shell, 'mkd created; pwd; printf "cdpath:%s\\n" "$CDPATH"', env={'CDPATH': str(elsewhere)})
            self.assert_success(result)
            self.assertEqual(result.stdout.splitlines(), [str(self.home / 'created'), 'cdpath:' + str(elsewhere)])
            result = self.run_shell(shell, 'mkd ""')
            self.assertEqual(result.returncode, 2)

    def test_privileged_editor_resolves_a_binary_instead_of_a_shell_wrapper(self):
        self.fake('sudo', 'printf "<%s>\\n" "$@"')
        for shell in SHELLS:
            for shadow in ('micro() { :; }', 'alias micro="echo wrapper"'):
                with self.subTest(shell=shell, shadow=shadow):
                    result = self.run_shell(shell, shadow + '\nedit_host')
                    self.assert_success(result)
                    self.assertEqual(result.stdout.splitlines(), [f'<{self.bin / "micro"}>', '</etc/hosts>'])

    def test_function_discovery_does_not_list_heredoc_source_as_functions(self):
        for shell in SHELLS:
            result = self.run_shell(shell, 'list_commands')
            self.assert_success(result)
            names = result.stdout.split('User-defined Functions:\n', 1)[1].splitlines()
            self.assertNotIn('import', names)
            self.assertNotIn('try:', names)
            self.assertIn('_dotfiles_count_entries', names)
            self.assertTrue(set(CORE_FUNCTIONS).issubset(names))

    def test_docker_deduplication_failure_prevents_actions(self):
        self.fake('docker', 'if [ "$1" = ps ]; then echo alpha; else echo MUTATE >> "$OPERATION_LOG"; fi')
        self.fake('awk', 'echo alpha; exit 42')
        for shell in SHELLS:
            self.log.unlink(missing_ok=True)
            result = self.run_shell(shell, 'dstop; result=$?; printf "after:%s\\n" "$result"; exit "$result"')
            self.assertEqual(result.returncode, 42)
            self.assertEqual(result.stdout, 'after:42\n')
            self.assertFalse(self.log.exists())

    def test_weather_alias_propagates_failure_and_preserves_preview_length(self):
        for response, expected in (('exit 40', 40), ("printf '1\\n2\\n3\\n4\\n5\\n6\\n7\\n8\\n'", 0)):
            self.fake('curl', response)
            for shell in SHELLS:
                result = self.run_shell(shell, 'if [ -n "${BASH_VERSION-}" ]; then shopt -s expand_aliases; fi\neval weather_geneva')
                self.assertEqual(result.returncode, expected)
                self.assertEqual(result.stdout, '' if expected else '1\n2\n3\n4\n5\n6\n7\n')

    def test_mac_password_generation_works_with_pipefail_without_tracing_the_value(self):
        self.platform('Darwin')
        self.fake('pbcopy', '/bin/cat > "$HOME/clipboard"')
        for shell in SHELLS:
            result = self.run_shell(shell, 'if [ -n "${BASH_VERSION-}" ]; then shopt -s expand_aliases; fi\nset -o pipefail\nset -x\neval gen_pass')
            self.assert_success(result)
            data = (self.home / 'clipboard').read_bytes()
            self.assertEqual(len(data), 20)
            self.assertTrue(all(character in b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' for character in data))
            self.assertTrue(data.decode() not in result.stdout + result.stderr, 'Generated value leaked into shell output')
            self.assertEqual(result.stdout, '')

    def test_failed_password_generation_does_not_overwrite_the_clipboard(self):
        self.platform('Darwin')
        self.fake('pbcopy', '/bin/cat > "$HOME/clipboard"')
        self.fake('tr', 'exit 43')
        self.fake('python3', 'exit 43')
        for shell in SHELLS:
            (self.home / 'clipboard').write_text('keep existing contents')
            result = self.run_shell(shell, 'if [ -n "${BASH_VERSION-}" ]; then shopt -s expand_aliases; fi\neval gen_pass')
            self.assertEqual(result.returncode, 43)
            self.assertEqual((self.home / 'clipboard').read_text(), 'keep existing contents')
        (self.bin / 'python3').unlink()
        (self.bin / 'tr').unlink()
        self.fake('pbcopy', 'exit 44')
        for shell in SHELLS:
            result = self.run_shell(shell, 'if [ -n "${BASH_VERSION-}" ]; then shopt -s expand_aliases; fi\neval gen_pass')
            self.assertEqual(result.returncode, 44)
            self.assertEqual(result.stdout, '')

    def test_password_generator_does_not_import_modules_from_the_current_project(self):
        self.platform('Darwin')
        self.fake('pbcopy', '/bin/cat > "$HOME/clipboard"')
        (self.home / 'secrets.py').write_text('from pathlib import Path\nPath("shadow-loaded").touch()\ndef choice(values):\n    return values[0]\n')
        for shell in SHELLS:
            result = self.run_shell(shell, 'if [ -n "${BASH_VERSION-}" ]; then shopt -s expand_aliases; fi\neval gen_pass', env={'PYTHONPATH': str(self.home)})
            self.assert_success(result)
            self.assertFalse((self.home / 'shadow-loaded').exists())
            self.assertEqual(len((self.home / 'clipboard').read_bytes()), 20)

    def test_info_helper_tolerates_unset_colors_and_uses_native_hostname(self):
        for name, body in {'hostname': 'echo fixture-host', 'w': 'echo users', 'date': 'echo fixture-date',
                           'uptime': 'echo uptime', 'curl': 'echo 192.0.2.1'}.items():
            self.fake(name, body)
        for shell in SHELLS:
            result = self.run_shell(shell, 'set -u; ii')
            self.assert_success(result)
            self.assertIn('fixture-host', result.stdout)
            self.assertIn('192.0.2.1', result.stdout)

    def test_file_search_usage_errors_return_without_scanning_or_closing_shell(self):
        self.fake('find', 'echo SCAN >> "$OPERATION_LOG"')
        for shell in SHELLS:
            for function in ('fff', 'ffs', 'ffe'):
                self.log.unlink(missing_ok=True)
                result = self.run_shell(shell, f'set -u; {function}; result=$?; printf "after:%s\\n" "$result"; exit "$result"')
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, 'after:2\n')
                self.assertFalse(self.log.exists())

    def test_missing_optional_tools_keep_native_commands_available(self):
        # Only native adapter requirements are visible, never host optional tools.
        minimal = self.home / 'minimal'
        minimal.mkdir()
        (minimal / 'uname').symlink_to(self.bin / 'uname')
        (minimal / 'grep').symlink_to(shutil.which('grep', path='/usr/bin:/bin'))
        for shell in SHELLS:
            with self.subTest(shell=shell):
                result = self.run_shell(shell, "alias du; alias df; for name in cat nano vim vi cpv update upgrade record diff; do if alias \"$name\" >/dev/null 2>&1; then exit 1; fi; done", env={'PATH': str(minimal)})
                self.assert_success(result)
                self.assertIn('du -h', result.stdout)
                self.assertIn('df -h', result.stdout)

    def test_only_platform_adapters_differ(self):
        for system in ('Linux', 'Darwin'):
            self.platform(system)
            for shell in SHELLS:
                with self.subTest(system=system, shell=shell):
                    check = ('alias mac-update; ! typeset -f busywork >/dev/null' if system == 'Darwin' else
                             '! alias mac-update >/dev/null 2>&1; typeset -f busywork >/dev/null')
                    result = self.run_shell(shell, 'alias ls\n' + check)
                    self.assert_success(result)
                    self.assertIn('ls -G' if system == 'Darwin' else 'ls --color=auto', result.stdout)

    def test_common_file_helpers_handle_spaces_hidden_names_and_repeated_options(self):
        directory = self.home / 'files with spaces'
        directory.mkdir()
        for name in ('normal', 'name\nwith newline', '.hidden', '.DS_Store'):
            (directory / name).write_text('x')
        (directory / 'folder').mkdir()
        (directory / '.hidden-dir').mkdir()
        (directory / 'link').symlink_to(directory / 'normal')
        for system in ('Linux', 'Darwin'):
            self.platform(system)
            for shell in SHELLS:
                with self.subTest(system=system, shell=shell):
                    result = self.run_shell(shell, 'fcount -f "$HOME/files with spaces"; fcount -d -a "$HOME/files with spaces"; count_files "$HOME/files with spaces"; mkd "$HOME/new folder"; pwd')
                    self.assert_success(result)
                    self.assertEqual(result.stdout.splitlines(), ['2 files', 'symbolic: 1', '2 dirs', 'symbolic: 1', '3', str(self.home / 'new folder')])

    def test_git_root_failure_does_not_change_directory(self):
        self.fake('git', 'exit 128')
        directory = self.home / 'current'
        directory.mkdir()
        for shell in SHELLS:
            result = self.run_shell(shell, 'cd "$HOME/current"; git_root; result=$?; pwd; test "$result" = 128')
            self.assert_success(result)
            self.assertEqual(result.stdout.strip(), str(directory))

    def test_git_search_accepts_a_query_without_an_empty_path_argument(self):
        self.fake('git', 'printf "<%s>\\n" "$@"')
        for shell in SHELLS:
            result = self.run_shell(shell, 'git_search "two words"')
            self.assert_success(result)
            self.assertEqual(result.stdout.splitlines(), ['<log>', '<-S>', '<two words>', '<--source>', '<--all>'])
            result = self.run_shell(shell, 'git_search needle -- "a file"')
            self.assert_success(result)
            self.assertEqual(result.stdout.splitlines(), ['<log>', '<-S>', '<needle>', '<--source>', '<--all>', '<-->', '<a file>'])

    def test_repository_creation_rejects_unknown_privacy_options_before_writes(self):
        self.fake('git', 'echo GIT >> "$OPERATION_LOG"')
        self.fake('gh', 'printf "GH:%s\\n" "$*" >> "$OPERATION_LOG"')
        for shell in SHELLS:
            for arguments in ('project --privte', 'project --private extra', 'project ""', '""', ''):
                self.log.unlink(missing_ok=True)
                result = self.run_shell(shell, 'create_and_push_repo ' + arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.log.exists())
            for arguments, visibility in (('project', '--public'), ('project --private', '--private'), ('project --public', '--public')):
                self.log.unlink(missing_ok=True)
                result = self.run_shell(shell, 'create_and_push_repo ' + arguments)
                self.assert_success(result)
                self.assertIn('GH:repo create project ' + visibility, self.log.read_text())

    def test_zip_directory_completion_keeps_archive_outside_the_source(self):
        (self.home / 'a directory').mkdir()
        self.fake('zip', 'printf "<%s>\\n" "$@"')
        for shell in SHELLS:
            result = self.run_shell(shell, 'zipf "a directory///"')
            self.assert_success(result)
            self.assertEqual(result.stdout.splitlines(), ['<-r>', '<a directory.zip>', '<a directory>'])
            result = self.run_shell(shell, 'zipf ""')
            self.assertNotEqual(result.returncode, 0)

    def test_recursive_count_handles_newlines_and_native_failure(self):
        (self.home / 'file\nwith newline').write_text('x')
        (self.home / '.hidden').write_text('x')
        for shell in SHELLS:
            result = self.run_shell(shell, 'if [ -n "${BASH_VERSION-}" ]; then shopt -s expand_aliases; fi\neval count')
            self.assert_success(result)
            # Count command-fake files as well as the two files above.
            expected = len(list(self.bin.iterdir())) + 2
            self.assertEqual(int(result.stdout), expected)
        self.fake('find', 'exit 33')
        for shell in SHELLS:
            result = self.run_shell(shell, 'if [ -n "${BASH_VERSION-}" ]; then shopt -s expand_aliases; fi\neval count')
            self.assertEqual(result.returncode, 33)
            self.assertEqual(result.stdout, '')

    def test_compiler_helper_validates_arguments_before_creating_build_files(self):
        self.fake('g++', 'printf "%s\\n" "$*" >> "$OPERATION_LOG"; exit 39')
        for shell in SHELLS:
            self.log.unlink(missing_ok=True)
            for arguments in ('', '""', 'one two'):
                result = self.run_shell(shell, 'crun ' + arguments)
                self.assertEqual(result.returncode, 2)
                self.assertFalse(self.log.exists())
                self.assertFalse((self.home / 'build').exists())
        for shell in SHELLS:
            self.log.unlink(missing_ok=True)
            result = self.run_shell(shell, 'crun -sample')
            self.assertEqual(result.returncode, 39)
            self.assertTrue(self.log.read_text().startswith('./-sample.cpp '))

    def test_failed_editor_selection_does_not_launch_neovim(self):
        (self.home / '.config/LazyVim').mkdir(parents=True)
        self.fake('fzf', 'exit 34')
        self.fake('nvim', 'echo EDITOR >> "$OPERATION_LOG"')
        for shell in SHELLS:
            self.log.unlink(missing_ok=True)
            result = self.run_shell(shell, 'nvims; result=$?; printf "after:%s\\n" "$result"; exit "$result"')
            self.assertEqual(result.returncode, 34, result.stdout + result.stderr)
            self.assertEqual(result.stdout, 'after:34\n')
            self.assertFalse(self.log.exists())

    def test_docker_inspection_and_filtered_stats_propagate_query_failures(self):
        self.fake('docker', 'case "$1" in inspect) test "$*" != "inspect -f {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}} bad" || exit 35 ;; stats) exit 36 ;; esac')
        for shell in SHELLS:
            for command, expected in (('dip bad good', 35), ('dst server', 36)):
                with self.subTest(shell=shell, command=command):
                    result = self.run_shell(shell, command)
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)

    def test_recursive_grep_separates_paths_and_patterns_from_options(self):
        self.fake('grep', 'printf "<%s>\\n" "$@"')
        for shell in SHELLS:
            result = self.run_shell(shell, 'GrePFind "-a path" "-needle"')
            self.assert_success(result)
            # The core color option is allowed, but operands must follow -e/--.
            arguments = result.stdout.splitlines()
            self.assertIn('<-->', arguments)
            self.assertEqual(arguments[-4:], ['<-e>', '<-needle>', '<-->', '<-a path>'])

    def test_failed_function_module_aborts_loading_later_modules(self):
        fixture = self.home / 'checkout'
        (fixture / 'shell/functions').mkdir(parents=True)
        for name in ('interactive.sh', 'functions.sh'):
            shutil.copy2(ROOT / 'shell' / name, fixture / 'shell' / name)
        (fixture / 'shell/aliases.sh').write_text(':\n')
        for group in ('archives', 'files', 'development', 'docker', 'network', 'system'):
            body = 'return 37\n' if group == 'archives' else 'echo LATER >> "$OPERATION_LOG"\n'
            (fixture / 'shell/functions' / (group + '.sh')).write_text(body)
        for shell in SHELLS:
            self.log.unlink(missing_ok=True)
            result = self.run_shell(shell, 'result=$?; printf "after:%s\\n" "$result"; exit "$result"', env={'DOTFILES_ROOT': str(fixture)})
            self.assertEqual(result.returncode, 37, result.stdout + result.stderr)
            self.assertFalse(self.log.exists())

    def test_remote_pdf_checks_for_a_viewer_before_copying(self):
        minimal = self.home / 'pdf-bin'
        minimal.mkdir()
        self.fake('scp', 'echo COPY >> "$OPERATION_LOG"')
        for name in ('uname', 'scp'):
            (minimal / name).symlink_to(self.bin / name)
        for name in ('grep', 'basename', 'mktemp', 'rm', 'rmdir'):
            (minimal / name).symlink_to(shutil.which(name, path='/usr/bin:/bin'))
        temporary = self.home / 'pdf-tmp'
        temporary.mkdir()
        for shell in SHELLS:
            self.log.unlink(missing_ok=True)
            result = self.run_shell(shell, 'open_remote_pdf example.invalid /sample.pdf', env={'PATH': str(minimal), 'TMPDIR': str(temporary)})
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(self.log.exists())

    def test_remote_pdf_copy_failure_cleans_its_temporary_directory(self):
        temporary = self.home / 'pdf-tmp'
        temporary.mkdir()
        self.fake('scp', 'exit 38')
        self.fake('xdg-open', 'echo VIEW >> "$OPERATION_LOG"')
        for shell in SHELLS:
            result = self.run_shell(shell, 'open_remote_pdf example.invalid /sample.pdf', env={'TMPDIR': str(temporary)})
            self.assertEqual(result.returncode, 38, result.stdout + result.stderr)
            self.assertEqual(list(temporary.iterdir()), [])
            self.assertFalse(self.log.exists())

    def test_remote_pdf_success_retains_the_file_for_both_viewers(self):
        self.fake('scp', 'for destination in "$@"; do :; done; printf "pdf fixture" > "$destination"')
        for viewer in ('open', 'xdg-open'):
            self.fake(viewer, 'printf "%s\\n" "$1" >> "$OPERATION_LOG"')
        for system in ('Linux', 'Darwin'):
            self.platform(system)
            for shell in SHELLS:
                self.log.unlink(missing_ok=True)
                temporary = self.home / (system + '-' + shell)
                temporary.mkdir()
                result = self.run_shell(shell, 'open_remote_pdf example.invalid "/a name.pdf" || exit\nif [ "$(uname -s)" = Linux ]; then wait "$!"; fi', env={'TMPDIR': str(temporary)})
                self.assert_success(result)
                self.assertEqual(len(list(temporary.iterdir())), 1)
                downloaded = next(temporary.iterdir()) / 'a name.pdf'
                self.assertEqual(downloaded.read_text(), 'pdf fixture')
                self.assertEqual(self.log.read_text().strip(), str(downloaded))

    def test_size_probe_failure_is_not_reported_as_zero_bytes(self):
        self.fake('du', 'exit 19')
        self.fake('stat', 'exit 19')
        (self.home / 'sample').write_text('x')
        (self.home / 'directory').mkdir()
        for system in ('Linux', 'Darwin'):
            self.platform(system)
            for shell in SHELLS:
                for target in ('sample', 'directory'):
                    result = self.run_shell(shell, f'get_size "$HOME/{target}"')
                    self.assertEqual(result.returncode, 19, result.stdout + result.stderr)
                    self.assertNotIn('0 B', result.stdout)

    def test_optional_aliases_disappear_when_tools_are_removed_before_reload(self):
        minimal = self.home / 'minimal'
        minimal.mkdir()
        for tool in ('uname', 'grep'):
            (minimal / tool).symlink_to(self.bin / tool if tool == 'uname' else shutil.which(tool, path='/usr/bin:/bin'))
        for system in ('Linux', 'Darwin'):
            self.platform(system)
            for shell in SHELLS:
                result = self.run_shell(shell, 'alias cat >/dev/null; alias nano >/dev/null; alias update >/dev/null\nPATH="$HOME/minimal"\n. "$DOTFILES_ROOT/shell/interactive.sh"\nfor name in cat nano vim vi cpv update upgrade record; do if alias "$name" >/dev/null 2>&1; then echo "stale: $name"; exit 1; fi; done')
                self.assert_success(result)

    def test_invalid_archive_input_returns_failure(self):
        (self.home / 'unsupported.data').write_text('fixture')
        for shell in SHELLS:
            for command in ('extract "$HOME/missing.zip"', 'extract "$HOME/unsupported.data"', 'extract', 'zipf'):
                result = self.run_shell(shell, command)
                self.assertNotEqual(result.returncode, 0)

    def test_privileged_editor_shortcut_uses_the_configured_editor(self):
        self.fake('sudo', 'printf "<%s>\\n" "$@"')
        for shell in SHELLS:
            result = self.run_shell(shell, 'if [ -n "${BASH_VERSION-}" ]; then shopt -s expand_aliases; fi\neval edit_host')
            self.assert_success(result)
            self.assertEqual(result.stdout.splitlines(), [f'<{self.bin / "micro"}>', '</etc/hosts>'])

    def test_native_df_is_used_even_with_duf_alias(self):
        self.fake('df', 'printf "Filesystem 1024-blocks Used Available Capacity Mounted on\\nroot 100 20 80 20%% /\\n"')
        self.fake('duf', 'echo WRONG; exit 99')
        for shell in SHELLS:
            result = self.run_shell(shell, 'showdisk')
            self.assert_success(result)
            self.assertEqual(result.stdout, 'The disk usage is: 20%\n')

    def test_mount_helper_forwards_arguments_and_native_failures(self):
        self.fake('mount', 'printf "%s\\n" "$*" >> "$OPERATION_LOG"; test "$1" != fail || exit 17; printf "mount output\\n"')
        self.fake('column', '/bin/cat')
        for shell in SHELLS:
            self.log.unlink(missing_ok=True)
            result = self.run_shell(shell, 'mount "a path"; mount fail')
            self.assertEqual(result.returncode, 17, result.stderr)
            self.assertEqual(result.stdout, 'mount output\n')
            self.assertEqual(self.log.read_text().splitlines(), ['a path', 'fail'])

    def test_upload_eof_refuses_network_and_bypasses_dust(self):
        self.fake('du', 'printf "native-du %s\\n" "$*" >> "$OPERATION_LOG"')
        self.fake('dust', 'echo WRONG; exit 99')
        self.fake('curl', 'echo NETWORK >> "$OPERATION_LOG"; exit 99')
        (self.home / 'sample').write_text('test')
        for shell in SHELLS:
            with self.subTest(shell=shell):
                self.log.unlink(missing_ok=True)
                result = self.run_shell(shell, 'transfer "$HOME/sample"', input_data='')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('native-du -L', self.log.read_text())
                self.assertNotIn('NETWORK', self.log.read_text())

    def test_upload_help_names_the_command_consistently_in_both_shells(self):
        outputs = []
        for shell in SHELLS:
            result = self.run_shell(shell, 'transfer --help')
            self.assert_success(result)
            self.assertTrue(result.stdout.startswith('transfer - Upload'), result.stdout)
            self.assertIn('Usage: transfer ', result.stdout)
            outputs.append(result.stdout)
        self.assertEqual(outputs[0], outputs[1])

    def test_failed_upload_returns_failure_without_a_download_link(self):
        self.fake('du', 'exit 0')
        self.fake('curl', 'printf "HTTP/2 404\\r\\n\\r\\nnot found\\n"; exit 22')
        (self.home / 'sample').write_text('test')
        for shell in SHELLS:
            result = self.run_shell(shell, 'transfer "$HOME/sample"', input_data='y\n')
            self.assertEqual(result.returncode, 22, result.stdout + result.stderr)
            self.assertNotIn('Download link:', result.stdout)

    def test_docker_shell_refuses_multiple_matches_and_query_failures(self):
        for response in (':', 'printf "alpha\\nbeta\\n"', 'exit 23'):
            self.fake('docker', f'if [ "$1" = ps ]; then {response}; else echo EXEC >> "$OPERATION_LOG"; fi')
            for shell in SHELLS:
                self.log.unlink(missing_ok=True)
                result = self.run_shell(shell, 'dbash name')
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.log.exists())
        self.fake('docker', 'if [ "$1" = ps ]; then echo alpha; else printf "<%s>\\n" "$@"; fi')
        for shell in SHELLS:
            result = self.run_shell(shell, 'dbash name')
            self.assert_success(result)
            self.assertEqual(result.stdout.splitlines(), ['<exec>', '<-it>', '<alpha>', '<bash>'])

    def test_bad_docker_filter_fails_before_any_mutation(self):
        self.fake('docker', 'if [ "$1" = ps ]; then printf "alpha\\nbeta\\n"; else echo MUTATE >> "$OPERATION_LOG"; fi')
        for shell in SHELLS:
            self.log.unlink(missing_ok=True)
            result = self.run_shell(shell, 'drm alpha "["')
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(self.log.exists())

    def test_listener_helper_rejects_extra_arguments_and_shows_all_targets(self):
        self.fake('sudo', 'echo "$1" >> "$OPERATION_LOG"; printf "COMMAND PID USER\\nserver 99991 tester\\nworker 99992 tester\\n"')
        for shell in SHELLS:
            self.log.unlink(missing_ok=True)
            result = self.run_shell(shell, 'lk all extra', input_data='n\n')
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(self.log.exists())
            result = self.run_shell(shell, 'lk all', input_data='n\n')
            self.assert_success(result)
            self.assertIn('server 99991 tester', result.stdout)
            self.assertIn('worker 99992 tester', result.stdout)
            self.assertEqual(self.log.read_text().splitlines(), ['lsof'])

    def test_listener_helper_reports_signal_failure_without_sending_real_signals(self):
        self.fake('sudo', 'if [ "$1" = lsof ]; then printf "COMMAND PID USER\\nserver 99991 tester\\n"; else echo FAKE_SIGNAL >> "$OPERATION_LOG"; exit 26; fi')
        for shell in SHELLS:
            self.log.unlink(missing_ok=True)
            result = self.run_shell(shell, 'kill() { return 0; }; lk all; result=$?; printf "after:%s\\n" "$result"; exit "$result"', input_data='y\n')
            self.assertEqual(result.returncode, 26, result.stdout + result.stderr)
            self.assertIn('after:26', result.stdout)
            self.assertNotIn('Done.', result.stdout)
            self.assertEqual(self.log.read_text().strip(), 'FAKE_SIGNAL')

    def test_listener_helper_does_not_mistake_permissions_for_a_missing_pid(self):
        self.fake('sudo', 'if [ "$1" = lsof ]; then printf "COMMAND PID USER\\nserver 99991 root\\n"; else printf "%s\\n" "$*" >> "$OPERATION_LOG"; fi')
        for shell in SHELLS:
            self.log.unlink(missing_ok=True)
            result = self.run_shell(shell, 'kill() { return 1; }; lk all', input_data='y\n')
            self.assert_success(result)
            self.assertTrue(self.log.exists(), result.stdout + result.stderr)
            self.assertEqual(self.log.read_text().strip(), 'kill -15 99991')

    def test_docker_failure_returns_to_the_calling_shell(self):
        self.fake('docker', 'if [ "$1" = ps ]; then echo alpha; else exit 27; fi')
        for shell in SHELLS:
            result = self.run_shell(shell, 'dstop; result=$?; printf "after:%s\\n" "$result"; exit "$result"')
            self.assertEqual(result.returncode, 27, result.stdout + result.stderr)
            self.assertEqual(result.stdout, 'after:27\n')

    def test_dash_prefixed_file_arguments_are_passed_as_paths(self):
        (self.home / '-sample').write_text('x')
        (self.home / '-archive.zip').write_text('fixture')
        self.fake('du', 'printf "%s\\n" "$*" >> "$OPERATION_LOG"; printf "512\\t./-sample\\n"')
        self.fake('zip', 'printf "%s\\n" "$*" >> "$OPERATION_LOG"')
        self.fake('unzip', 'printf "%s\\n" "$*" >> "$OPERATION_LOG"')
        for shell in SHELLS:
            self.log.unlink(missing_ok=True)
            result = self.run_shell(shell, 'get_size -sample; zipf -sample; extract -archive.zip; mkd -folder; pwd')
            self.assert_success(result)
            self.assertIn("Size of '-sample': 512 B", result.stdout)
            self.assertIn(str(self.home / '-folder'), result.stdout)
            self.assertEqual(self.log.read_text().splitlines(), ['-sb ./-sample', '-r ./-sample.zip ./-sample', './-archive.zip'])

    def test_system_metrics_propagate_backend_failures(self):
        self.fake('df', 'exit 24')
        self.fake('ps', 'exit 25')
        for shell in SHELLS:
            for function, expected in (('showdisk', 24), ('mycpu', 25)):
                result = self.run_shell(shell, function)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                self.assertEqual(result.stdout, '')

    def test_docker_ids_are_identical_arguments_in_bash_and_zsh(self):
        self.fake('docker', '''case "$1" in
ps) printf 'alpha\\nbeta\\n' ;;
images) printf 'image-one\\nimage-two\\n' ;;
*) printf '%s:%s\\n' "$1" "$2" >> "$OPERATION_LOG" ;;
esac''')
        for shell in SHELLS:
            with self.subTest(shell=shell):
                self.log.unlink(missing_ok=True)
                result = self.run_shell(shell, 'dstop; drm alpha; drmi')
                self.assert_success(result)
                self.assertEqual(self.log.read_text().splitlines(), ['stop:alpha', 'stop:beta', 'rm:alpha', 'rmi:image-one', 'rmi:image-two'])

    def test_neovim_selection_preserves_arguments_in_both_shells(self):
        (self.home / '.config/LazyVim').mkdir(parents=True)
        self.fake('fzf', 'echo LazyVim')
        self.fake('nvim', 'printf "%s:%s\\n" "$NVIM_APPNAME" "$*"')
        for shell in SHELLS:
            result = self.run_shell(shell, 'nvims "a file"')
            self.assert_success(result)
            self.assertEqual(result.stdout, 'LazyVim:a file\n')

    def test_shared_temperature_formatter_preserves_native_backends(self):
        self.fake('sensors', "printf 'k10temp-pci-00c3\\nTctl: +50.0 C\\n'")
        self.fake('macmon', "printf '{\"temp\":{\"cpu_temp_avg\":50,\"gpu_temp_avg\":40}}\\n'")
        # The backend calls jq; this deterministic fixture avoids a jq dependency.
        self.fake('jq', "printf 'CPU\\taverage\\t50\\nGPU\\taverage\\t40\\n'")
        for system in ('Linux', 'Darwin'):
            self.platform(system)
            for shell in SHELLS:
                with self.subTest(system=system, shell=shell):
                    result = self.run_shell(shell, 'temps', env={'NO_COLOR': '1'})
                    self.assert_success(result)
                    self.assertIn('CPU', result.stdout)
                    self.assertIn('50.0 C', result.stdout)
                    self.assertIn('OK', result.stdout)
                    self.assertNotIn('\x1b[', result.stdout)

    def test_legacy_aliases_can_be_reloaded_into_functions(self):
        for shell in SHELLS:
            result = self.run_shell(shell, 'alias showdisk="echo old"; alias mycpu="echo old"; alias showmem="echo old"\n. "$DOTFILES_ROOT/shell/interactive.sh"\ntypeset -f showdisk >/dev/null; typeset -f mycpu >/dev/null; typeset -f showmem >/dev/null')
            self.assert_success(result)

    def test_local_overrides_still_win_in_installed_shells(self):
        config = self.home / '.config/dotfiles'
        config.mkdir(parents=True)
        for shell in SHELLS:
            (config / ('local.' + shell)).write_text('alias ll="echo local-wins"\nmkd() { echo local-function; }\n')
        for system, flag in (('Linux', 'linux'), ('Darwin', 'mac')):
            self.platform(system)
            subprocess.run(['/bin/bash', str(ROOT / 'install.sh'), '--platform', flag], env=self.env,
                           check=True, text=True, capture_output=True, timeout=20)
            for shell in SHELLS:
                result = self.run_shell(shell, 'alias ll; mkd', startup=True)
                self.assert_success(result)
                self.assertIn('local-wins', result.stdout)
                self.assertIn('local-function', result.stdout)


if __name__ == '__main__':
    unittest.main()
