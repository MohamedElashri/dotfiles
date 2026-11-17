# dotfiles

Personal Linux/macOS settings for shells, Git, SSH, editors and terminals.
Classic dotfiles work independently; coding-agent tools are optional.
Installed files link to this checkout, so keep it in place.

## Setup

```bash
git clone --filter=blob:none --depth=1 https://github.com/MohamedElashri/dotfiles.git ~/projects/dotfiles
cd ~/projects/dotfiles
./bin/dotfiles bootstrap --dry-run
./bin/dotfiles bootstrap
```

Supports Apple Silicon macOS 15+, Debian/Ubuntu derivatives and Fedora.
Linux desktop apps require x86_64 and a desktop session. Run as your normal user;
bootstrap downloads prerequisites, Homebrew packages, pinned assets, fonts and
apps, links configuration, enables hooks and selects Zsh. It installs Python if
needed; privileged steps may request authentication. Log out/in afterward.

For servers, add `--skip-apps --skip-shell`. For existing tools, use
`--skip-packages --skip-apps`. See `bootstrap --help` for asset, font and dev-tool
selections, and [setup/](setup/) for package/app manifests. Sign-ins, GPU drivers
and the 1Password SSH agent stay device-local.

To link configuration only, preview with `./install.sh --dry-run`, then run
`./install.sh`. Replacements are backed up in `~/.dotfiles-backup/`; unsafe
parent paths are refused. The installer uses Bash and system utilities; the CLI
uses Python 3.9+ and its standard library.
A [ZIP download](https://github.com/MohamedElashri/dotfiles/archive/refs/heads/main.zip)
works for setup; sync and hooks require a Git clone.

## Daily use

```bash
dotfiles doctor
dotfiles sync --check
dotfiles sync --dry-run
dotfiles sync
```

Use `./bin/dotfiles` until it is on PATH. Sync requires a clean tracking branch,
fast-forwards updates, restores missing links and updates enabled assets. It
stops on replaced links or divergent history. Inspect links with
`./install.sh --status`; rerun the installer after moving the checkout.
Use `doctor --online` to check GitHub authentication.

## Customize

| Location | Contents |
| --- | --- |
| `bash/`, `zsh/`, `shell/`, `platform/` | Shell startup, helpers and OS-specific commands |
| `config/` | Application, Git and SSH settings |
| `setup/` | Packages, apps, assets and fonts |

Device overrides: `~/.config/dotfiles/local.{bash,zsh,env.zsh,gitconfig}`;
[examples](templates/local/). Keep secrets and account state outside Git.
SSH overrides belong in `~/.ssh/config.local` (mode 600), before `Host *`;
inspect effective settings with `ssh -G <alias>`.

Use `list_commands` for shell helpers and `dotfiles fonts --list` for fonts.
Run `dotfiles render` after editing Waveterm source settings or
`setup/assets.json`, and retain the generated files.

## Coding agents

Install shared instructions and skills with `./install.sh --agents-only`.
For combined setup or maintenance, add `--with-agents` to the installer,
bootstrap, sync or doctor; repeat the option for each command.

Edit [agent-workflow/AGENTS.md](agent-workflow/AGENTS.md) to change global defaults
for Codex, Claude Code, OpenCode and pi, then start new sessions.
The [agent guide](docs/agent-evaluations.md) covers harness paths, skills,
project templates, diagnostics, evaluations and private reports.
Harness binaries and accounts are managed separately; setup and CI never run models.

## Checks

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_private.py --worktree
python3 scripts/render_configs.py --check
git diff --check
```

Tests use temporary homes and local remotes; they need Git, Python, Bash, Zsh and
SSH. Commit/push hooks scan for private data; chain them into custom hooks.
