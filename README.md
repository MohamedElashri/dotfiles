# dotfiles

Personal Linux/macOS shell, Git, editor, and terminal settings. Installed files
link to this checkout, so keep it in place. AI tools and their settings are
managed separately; HEP integrations are retired.

## Install

| Profile | Use | Command |
|---|---|---|
| `personal` (default) | Workstations, shared CLI/editor settings, and apps | `./bin/dotfiles bootstrap` |
| `minimal` | VMs/headless machines; Bash and terminal Git | `./install.sh --profile minimal` |

For a workstation, install Git, Python 3.9+, Bash, and [Homebrew](https://brew.sh):

```bash
git clone --filter=blob:none --depth=1 https://github.com/MohamedElashri/dotfiles.git ~/projects/dotfiles
cd ~/projects/dotfiles
./bin/dotfiles bootstrap --dry-run
./bin/dotfiles bootstrap
```

Bootstrap installs curated tools, pinned shell/editor assets, links, and Git
hooks. Optional flags include `--dev`, Mac-only `--apps`, and `--fonts meslo`.
`--skip-packages` supports an existing toolset; `--skip-assets` skips downloads.
For links alone, use `./install.sh --dry-run`, then `./install.sh`.

For minimal devices, follow the [essential package instructions](setup/README.md).
Open a new shell afterward. Accounts, SSH keys, and signing credentials stay local.

## Everyday commands

```bash
dotfiles doctor           # Local links, tools, signing, and plugin checks
dotfiles update --check   # Fetch and validate upstream without changing live settings
dotfiles update           # Apply a validated update with a recovery journal
dotfiles rollback         # Undo the last update when later edits do not conflict
dotfiles sync             # Fast-forward, relink, and reconcile enabled assets
dotfiles status           # Inspect managed links
dotfiles assets --update  # Apply the declared shell/editor asset revisions
dotfiles fonts --list     # List optional checksum-verified font downloads
```

Review, commit, and push shared edits before updating another device. Updates
refuse dirty checkouts, conflicting files, and divergent history. Sync also
recreates missing links and supports `--dry-run`; it has no rollback journal.
Restart applications that cache configuration after updates.

## Customize and verify

Edit portable CLI/editor preferences in `config/cli/`, `config/editors/`, and
`config/tmux/`; shell settings live in `shell/`, `zsh/`, and `platform/`.
Waveterm and shell-plugin selections have generated outputs: edit their source
preferences/manifests, then run `dotfiles render` before committing.

Keep device-only overrides under `~/.config/dotfiles/local.*` using the
[examples](templates/local/). Credentials, history databases, and AI settings
stay outside Git. Fonts are optional downloads; the old binaries are preserved
locally in the ignored `.cache/legacy-fonts/`, with Git history left intact.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_private.py --worktree
python3 scripts/render_configs.py --check
git diff --check
```

See [usage and recovery](docs/usage.md) for overrides, Git ignores, backups, and
rollback, or [machine setup](setup/README.md) for provisioning and sync ownership.
