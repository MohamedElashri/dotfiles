# mac/

macOS dotfiles and application configs, managed as part of the unified dotfiles
repository. Uses Homebrew and GNU stow for installation.

---

## Usage

From the repo root:

```bash
./bootstrap.sh --platform mac --yes
```

Or restore only (Homebrew and stow must already be installed):

```bash
./restore --platform mac
```

Both commands run `mac/setup.sh`, which installs packages and symlinks configs.

---

## Backup

Save your current macOS configs back into this directory:

```bash
# from the repo root
./backup --platform mac
```

This runs `mac/backup`, which copies configs from `$HOME` and app locations
back into `mac/configs/` and refreshes `mac/lists/brew.txt` and
`mac/lists/cask.txt`.

---

## What setup.sh Does

1. Sets macOS defaults (e.g. show hidden files in Finder, suppress login MOTD).
2. Creates `~/work/git/`.
3. Installs Homebrew formulae from `lists/brew.txt`.
4. Installs Homebrew casks from `lists/cask.txt`.
5. Stows `configs/zsh/` → `$HOME` (removes any existing `~/.zshrc` first).
6. Stows `configs/git/` → `$HOME`.
7. Symlinks `configs/vscode/settings.json` → `~/Library/Application Support/Code/User/settings.json`.
8. Copies fonts from `configs/fonts/`.

---

## Directory Layout

```
mac/
├── setup.sh              # macOS restore script (run via ./restore --platform mac)
├── backup                # macOS backup script (run via ./backup --platform mac)
├── lists/
│   ├── brew.txt          # Homebrew formulae (one per line, # comments ok)
│   └── cask.txt          # Homebrew casks (one per line, # comments ok)
└── configs/
    ├── cli/
    │   ├── atuin/        # atuin config
    │   ├── bat/          # bat config
    │   ├── gh/           # GitHub CLI config
    │   ├── helix/        # Helix editor config
    │   ├── hyper/        # Hyper terminal config
    │   └── nano/         # nano config
    ├── fonts/
    │   ├── Fonts/        # font files
    │   └── FontCollections/
    ├── git/
    │   ├── .gitconfig
    │   └── .gitignore_global
    ├── iterm2/           # iTerm2 preferences
    ├── rio-terminal/     # Rio terminal config
    ├── ssh/
    │   └── config
    ├── tmux/
    │   └── .tmux.conf
    ├── vscode/
    │   └── settings.json
    ├── waveterm/         # Wave terminal config
    ├── zed/              # Zed editor config
    └── zsh/
        ├── .zshrc
        ├── .zprofile
        ├── aliases.zsh
        ├── plugins.zsh
        ├── environment.zsh
        ├── config.zsh
        ├── functions.zsh
        └── shellhistory.zsh
```

---

## Adding Packages

Edit `lists/brew.txt` or `lists/cask.txt` directly. Blank lines and lines
starting with `#` are ignored. After editing, run:

```bash
brew install <package>          # to install immediately
./backup --platform mac         # to regenerate the full list from brew
```
