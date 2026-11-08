# dotfiles

Bash, Zsh, Git, and app settings for macOS/Linux, plus a standalone HEP setup.
Files are symlinked into your home directory; keep the checkout in place.

## Install

| Profile | Use | Command |
|---|---|---|
| `minimal` | VMs and headless machines; Bash + terminal Git | `./install.sh --profile minimal` |
| `personal` (default) | Personal workstations; shells, Git/SSH, and apps | `./install.sh --profile personal` |
| `hep` | Linux clusters; independent Bash setup | `./hep/install.sh` |

Install the [essential packages](setup/README.md), then clone and install your
chosen profile. For a VM:

```bash
git clone https://github.com/MohamedElashri/dotfiles.git ~/dotfiles
cd ~/dotfiles
./install.sh --profile minimal --dry-run
./install.sh --profile minimal
./bin/dotfiles doctor
```

Open a new shell afterward; minimal uses Bash. HEP can also be installed from a
copy of `hep/` alone, including hidden files: [HEP instructions](hep/README.md).

## Everyday commands

```bash
dotfiles update --check  # preview and validate upstream
dotfiles update         # apply a validated update
dotfiles doctor         # check tools and configuration offline
dotfiles status         # check managed links
dotfiles rollback       # undo the last successful update
dotfiles install        # reapply links without updating
```

Commit and push edits from this checkout, then run `dotfiles update` on other
machines. Updates require Bash, Git, Python 3, and a clean checkout.

## Customize

| To change | Edit |
|---|---|
| Environment and PATH | `shell/env.sh` |
| Shared aliases | `shell/aliases.sh` |
| Shell settings | `bash/`, `zsh/` |
| OS-specific settings | `platform/` |
| Git and SSH | `config/git/`, `config/ssh/` |
| Apps | `config/` |
| Personal commands | `bin/` |

Keep private and machine-specific overrides in `~/.config/dotfiles/local.*`;
[examples](templates/local/) show the supported filenames.

Personal/minimal Git settings globally ignore AI files such as `.claude` and
`.codex`, plus OS clutter and editor leftovers. Already tracked files stay tracked.

See [usage and recovery](docs/usage.md) for override details, backups, Git ignores,
and troubleshooting, or [machine setup](setup/README.md) for packages and apps.
