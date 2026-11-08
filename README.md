# dotfiles

Shell and application settings for personal Linux/macOS machines and Bash-only
HEP clusters. The installer links selected files from this checkout into your
home directory. Keep the checkout in place so those links keep working.

## Install

Clone the repository, enter it, and preview the changes:

```bash
./install.sh --dry-run
```

Install the personal profile on Linux or macOS:

```bash
./install.sh
```

For a Linux HEP cluster, install the Bash-only profile:

```bash
./install.sh --profile hep
```

The installer backs up files it replaces under `~/.dotfiles-backup/`. Open a
new shell when it finishes. It links configuration only; package and application
setup is described in [setup/README.md](setup/README.md).

## Use and customize

Edit files in this checkout. Changes to linked files take effect directly; open
a new shell to reload shell settings. Common files:

| To change | Edit |
|---|---|
| Shared environment and PATH | `shell/env.sh` |
| Bash and Zsh aliases | `shell/aliases.sh` |
| Zsh settings, aliases, and functions | `zsh/` |
| Bash settings and tools | `bash/` |
| Linux/macOS aliases | `platform/` |
| HEP cluster settings | `hep/` |
| Git and SSH settings | `config/git/`, `config/ssh/` |
| Application settings | `config/` |
| Personal commands | `bin/` |

Keep machine-specific or private settings in local files under
`~/.config/dotfiles/`; they are loaded after the shared settings:

- `local.bash` for Bash aliases and settings
- `local.zsh` for Zsh aliases and settings
- `local.env.zsh` for Zsh environment variables needed before shell tools load
- `local.gitconfig` for Git overrides

Examples are in `templates/local/`. Do not commit credentials, tokens, private
keys, or authentication files. To enable the repository's commit and push
checks in this checkout, run:

```bash
git config --local core.hooksPath .githooks
```

## Update and check

After installation, open a new shell. The same commands work from any directory
in Bash and Zsh on macOS and Linux:

```bash
dotfiles update --check  # fetch and validate without changing live configuration
dotfiles update       # validate, save recovery state, then apply upstream
dotfiles rollback     # undo the last successful update
dotfiles status       # check for missing links or files replaced by an app
dotfiles install      # reapply links without pulling
```

`update` and `rollback` require Python 3, Bash, and Git on macOS or Linux.
Installation itself still requires only Bash. `update` remembers the installed
personal/HEP profile and detects the current OS. Before fetching, it requires
a clean checkout, an upstream branch, and intact managed links. If an app has
replaced a link, reconcile that file and run `dotfiles install` first.

The updater fetches without changing the live checkout, checks fast-forward
ancestry, and exports the exact incoming commit into a temporary directory. It
checks shell/Python syntax and Git config parsing, then installs into a disposable
home and checks its links and shell startup. Zsh checks run when Zsh is available.
`--check` stops here; it updates remote-tracking refs but leaves live files alone.

Before applying, it records the previous commit and saves affected home files,
symlinks, and permissions under the checkout's Git directory in
`dotfiles-updates/<timestamp>/`. Snapshots are private to your user and may include
local override contents; keep them out of version control. The actual update uses
fast-forward only, refuses to overwrite ignored local files, and stops on a
collision with a newly managed home path. It never automatically stashes or pushes.

If installation or its link check fails, the updater attempts to restore the
previous commit and affected home paths. `dotfiles rollback` can also undo the
last completed update, but refuses subsequent conflicting checkout/home edits,
including ignored files that would be replaced. An already-current update keeps
the existing rollback point. Updates and rollbacks cannot run concurrently.

These checks catch common configuration failures; incoming scripts still need to
be trusted. They do not test every application's behavior or isolate arbitrary
installer side effects. Close apps that rewrite managed settings while updating.
Live symlinks see the new settings during application, so the update is not
atomic to running apps. If recovery fails or a process is killed/power is lost
during application, further updates stop and print the recovery directory.
Keep that directory: `state.json` records the previous commit, original paths,
and numbered backup files for manual recovery. Do not blindly reset over newer
edits. `~/.dotfiles-backup/` remains the installer's separate replacement backup.

To share edits made on one machine, review, commit, and push them from the checkout:

```bash
git status
git diff
git add <files-you-reviewed>
git commit -m "Update dotfiles"
git push
```

Then run `dotfiles update` on each other machine. Shared changes apply everywhere;
keep machine-specific settings in the local override files described above.
Existing links reflect applied changes immediately, and reinstalling also links
newly managed files. Open a new shell to reload shell settings.

Before the command is on PATH, or after moving the checkout, run
`./bin/dotfiles update`, `./install.sh`, or `./install.sh --status` from its root.
If it reports a detached file, review that file and copy any desired changes
back into the matching file in this repository. Use `./install.sh --help` to
see installer options. For HEP cluster selection, see [hep/README.md](hep/README.md).

## Global Git ignores

The personal profile links `config/git/ignore` to
`~/.config/dotfiles/git-ignore`. The shared Git config sets `core.excludesFile`
to that path on macOS and Linux, so these rules apply to every repository
without editing each repository's `.gitignore`. On a machine with an existing
installation, edits to this linked file take effect immediately.

The list covers common AI assistant directories (including all of `.claude`
and `.codex`), instruction files such as `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`,
AI-specific GitHub/VS Code settings, OS metadata, and editor swap/backup files.
Patterns apply at any depth. Add explicit names to this file when adopting a
new AI tool; there is no universal filename pattern for every AI setting.
Environment files, general IDE settings, and language/build output remain
repository-specific choices.

Git ignores only affect untracked files. Existing tracked files remain tracked,
including the AI app settings intentionally stored in this dotfiles repository.
Repository rules or a repository's own `core.excludesFile` can override global
defaults. To inspect which rule applies, use:

```bash
git check-ignore -v --no-index .claude/settings.json .codex/config.toml
```

Use `git add -f <path>` for an intentional exception, or put a different
`core.excludesFile` in `~/.config/dotfiles/local.gitconfig` for a machine override.
