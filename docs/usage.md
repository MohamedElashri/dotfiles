# Usage and recovery

See the [README](../README.md) for installation and commands, and the
[HEP guide](../hep/README.md) for standalone cluster setup.

## Local settings

Keep machine-specific settings in `~/.config/dotfiles/`:

| File | Purpose |
|---|---|
| `local.bash` | Bash overrides |
| `local.zsh` | Zsh overrides |
| `local.env.zsh` | Zsh environment, before tool initialization |
| `local.gitconfig` | Git overrides |

Copy the [examples](../templates/local/) you need. Keep credentials out of Git.
Enable this checkout's commit/push checks with
`git config --local core.hooksPath .githooks`.

## Updates and recovery

Updates require Bash, Git, Python 3, a clean checkout, an upstream branch, and
intact managed links. Commit and push shared edits before updating other machines.

```bash
dotfiles update --check  # fetch and validate; leave live settings unchanged
dotfiles update         # save recovery state and apply fast-forward changes
dotfiles rollback       # undo the last successful update
```

Incoming settings are checked in a temporary home before application. Updates
execute repository scripts; use trusted changes and close apps that rewrite
settings, since symlink changes become live immediately.

Failed installations attempt automatic recovery. Rollback stops if the checkout
or managed files changed afterward. After an interruption or failed recovery,
keep the printed recovery directory. Its `state.json` records the previous commit
and backups for manual recovery. Snapshots live under `dotfiles-updates/` inside
the checkout's Git directory and may contain private overrides; do not commit them.
Installer replacement backups are separate, under `~/.dotfiles-backup/`.

## Troubleshooting

| Problem | Action |
|---|---|
| Missing tools or Git setup | Run `dotfiles doctor`; follow [machine setup](../setup/README.md). It checks offline and returns 1 for failures. |
| Detached or missing links | Run `dotfiles status`, preserve wanted local edits in the checkout, then `dotfiles install`. |
| Command unavailable or checkout moved | Run `./install.sh` from the checkout, then open a new shell. |

Reinstalling remembers your profile. Switching profiles leaves previous links
in place; use a fresh home for a clean minimal setup.

## Global Git ignores

Personal/minimal profiles use [config/git/ignore](../config/git/ignore) through
`core.excludesFile`. It covers common AI settings, OS clutter, and editor leftovers
at any depth. Tracked files remain tracked; repository rules can override defaults.

Inspect a rule with `git check-ignore -v --no-index .claude/settings.json`.
Use `git add -f` for an intentional exception, or override `core.excludesFile`
in `local.gitconfig` for a different machine-wide list.
