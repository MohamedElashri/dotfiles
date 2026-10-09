# Optional machine setup

`../install.sh` only links configuration. It does not install packages, change the
login shell, apply macOS preferences, copy fonts, or download shell frameworks.

- `linux-packages.txt`: small optional workstation package list. Use your distro's package manager.
- `mac-packages.txt`: selected Homebrew formulae installed on this Mac.
- `mac-apps.txt`: selected Homebrew casks installed on this Mac.

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

## Recreating this Mac

The package lists include the installed Homebrew packages selected for this
setup. Karabiner-Elements is installed outside Homebrew on this Mac; install it
separately before using the linked `karabiner.json`. Its three keyboard remaps
refer to particular USB vendor and product IDs, so review them on a different
keyboard. DNSCrypt Proxy settings contain a personal server endpoint and remain
local; copy them securely to another Mac if needed.

Micro's `settings.json` and `bindings.json` are linked. Its installed plugins
are separate downloads: `detectindent`, `editorconfig`, `filemanager`, `fzf`,
`jump`, `palettero`, and `quickfix`. Install them through Micro's plugin manager
on another Mac to enable the configured bindings.

The alternate Neovim profiles are separate Git checkouts under `~/.config/`:

| Profile | Repository |
|---|---|
| LazyVim | `https://github.com/LazyVim/starter` |
| kickstart | `https://github.com/nvim-lua/kickstart.nvim.git` |
| NvChad | `https://github.com/NvChad/NvChad` |
| AstroNvim | `https://github.com/AstroNvim/AstroNvim` |

Clone only the profiles you use. The `nvims` picker discovers profiles present
on each machine. OpenCode's provider and credential files remain local; copy
provider settings securely and set up authentication separately on a new Mac.
Zed's selected Dracula Pro theme is also an external asset.
VS Code settings remain under its own Settings Sync. App
accounts, auth databases, caches, editor histories, and macOS preferences are
not portable dotfiles and are outside the installer.
