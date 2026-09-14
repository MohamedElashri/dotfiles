# Optional machine setup

`../install.sh` only links configuration. It does not install packages, change the
login shell, apply macOS preferences, copy fonts, or download shell frameworks.

- `linux-packages.txt`: small optional workstation package list. Use your distro's package manager.
- `mac-packages.txt`: preserved Homebrew formula list.
- `mac-apps.txt`: preserved Homebrew cask list.

Edit these lists deliberately. They are not regenerated from the machine.
On macOS, after installing Homebrew, install a reviewed list explicitly:

```bash
while IFS= read -r package || [ -n "$package" ]; do
  case "$package" in ''|\#*) continue ;; esac
  brew install "$package"
done < setup/mac-packages.txt
```

Use `brew install --cask` with `setup/mac-apps.txt` for applications.
Fonts remain in `config/mac/fonts/` for optional manual installation.
Oh My Zsh, Starship, Atuin, Conda and nvm hooks activate only when present.
HEP machines need none of these setup steps.
