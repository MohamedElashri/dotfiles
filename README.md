# dotfiles

Personal dotfiles designed to run on more than one Linux machine.

## Quick Start

Clone the repository, then run:

```bash
./bootstrap.sh --yes
```

The default bootstrap behavior is conservative:

- detect the package manager and install only base dependencies: `curl`, `git`, `rsync`, `zsh`
- restore dotfiles as symlinks into `$HOME`
- skip optional tool installers
- back up replaced files under `~/.dotfiles-backup/<timestamp>/`

To install optional tools too:

```bash
./bootstrap.sh --yes --optional-tools
```

Optional tools currently mean Oh My Zsh, Starship, Atuin, and Rust.

## Restore Only

Use `restore` when dependencies are already installed:

```bash
./restore --link
./restore --copy
./restore --link --dry-run
```

`--link` keeps `$HOME` files pointing at this repo. `--copy` copies files into
place. Existing targets are moved to `~/.dotfiles-backup/<timestamp>/` before
replacement unless `--no-backup` is passed.

## Machine-Specific Overrides

Do not fork the repo for host-specific paths or secrets. Put local-only files in:

```text
~/.config/dotfiles/environment.local.zsh
~/.config/dotfiles/zshrc.local.zsh
~/.environment.local.zsh
~/.dotfiles.local.zsh
```

Examples of things that belong there:

- machine-specific PATH entries
- work-only aliases
- private tokens or environment variables
- host-specific SSH or cluster helpers

## Shell Layout

- `zsh/.zshenv`: minimal zsh setup loaded by every zsh process
- `zsh/.zprofile`: zsh login-shell setup
- `zsh/.zshrc`: interactive zsh setup
- `zsh/environment.zsh`: shared PATH and exported toolchain variables
- `zsh/plugins.zsh`: desired Oh My Zsh plugins; missing plugins are skipped
- `bash/.bashrc`: interactive bash setup
- `sh/.profile`: POSIX login-shell setup
- `cli/`: user scripts restored to `~/cli`

The zsh config skips missing tools and paths. For example, missing `nvm`,
Homebrew, TeX Live, Starship, Atuin, or optional Oh My Zsh plugins should not
break startup.
