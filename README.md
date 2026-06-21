# dotfiles

Personal dotfiles for Linux workstations, macOS, and HEP remote clusters — managed from a single repository.

## Platforms

| Platform | Detection | Description |
|----------|-----------|-------------|
| `linux`  | default on Linux | Local machines, devcontainers, VPS nodes |
| `mac`    | `uname == Darwin` | macOS — managed via Homebrew and stow |
| `hep`    | AFS/CVMFS mounts or hostname patterns | CERN lxplus, UC/GEOP clusters (sneezy, sleepy, goofy), GPU farm |

Platform is auto-detected. Override with `--platform linux|mac|hep`.

---

## Quick Start

### Linux / VPS / devcontainer

```bash
git clone https://github.com/MohamedElashri/dotfiles ~/projects/dotfiles
cd ~/projects/dotfiles
./bootstrap.sh --yes
```

Installs base packages (`curl git rsync zsh`), then restores dotfiles as symlinks.

### macOS

```bash
git clone https://github.com/MohamedElashri/dotfiles ~/projects/dotfiles
cd ~/projects/dotfiles
./bootstrap.sh --platform mac --yes
```

Dispatches to `mac/setup.sh`, which installs Homebrew packages and stows configs.

### HEP cluster (lxplus, sneezy, sleepy, …)

```bash
git clone https://github.com/MohamedElashri/dotfiles ~/dotfiles
cd ~/dotfiles
./bootstrap.sh --platform hep --yes
```

Skips package installation (no root on cluster). On lxplus, where the hostname
rotates (e.g. `lxplus901`), pass `--machine lxplus` to select the right aliases file:

```bash
./bootstrap.sh --platform hep --machine lxplus --yes
```

---

## Backup

Save your current `$HOME` dotfiles back into the repo before committing:

```bash
./backup                        # auto-detect platform
./backup --platform hep --machine lxplus
./backup --platform mac
```

On HEP machines, `~/.machine_aliases` is saved under `hep/machine_aliases/<machine>`.
On macOS, the backup script lives at `mac/backup` and is invoked automatically.

---

## Restore

Use `restore` directly when bootstrap has already run and you only want to sync files:

```bash
./restore --link                # symlink files back to this repo (default)
./restore --copy                # copy files into place
./restore --link --dry-run      # show what would happen, change nothing
./restore --platform hep --machine sneezy
```

Options:

| Flag | Description |
|------|-------------|
| `--link` | Symlink `$HOME` entries to this repo. Default. |
| `--copy` | Copy files; useful when the repo is on a network share. |
| `--platform NAME` | Override auto-detected platform. |
| `--machine NAME` | HEP only: pick the `hep/machine_aliases/<NAME>` file. |
| `-y, --yes` | Skip all confirmation prompts. |
| `-n, --dry-run` | Print what would happen without touching anything. |
| `--no-backup` | Do not move replaced targets to a backup directory. |

Replaced files are moved to `~/.dotfiles-backup/<timestamp>/` unless `--no-backup` is passed.

---

## Machine-Specific Overrides

Do not fork the repo for host-specific paths or secrets. Put local-only files here instead:

```
~/.config/dotfiles/zshrc.local.zsh   # loaded last by .zshrc
~/.dotfiles.local.zsh                 # fallback location
```

Examples of things that belong there:

- machine-specific `PATH` entries
- work-only aliases
- private tokens or environment variables
- host-specific cluster helpers

Templates live in `templates/local/` and are not installed automatically.

---

## Optional Tools (Linux only)

```bash
./bootstrap.sh --optional-tools
```

Installs if missing: **Oh My Zsh**, **Starship**, **Atuin**, **Rust**.
Each tool is skipped if already present. Individual tools can be installed by
running the corresponding `install_*` function from `bootstrap.sh`.
