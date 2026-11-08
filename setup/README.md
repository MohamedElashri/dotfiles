# New machine setup

`../install.sh` only links configuration. It does not install packages, change the
login shell, apply macOS preferences, copy fonts, or download shell frameworks.

Start with `minimal` for a VM or headless machine. It needs only Bash to link
configuration, plus Git/Python 3 for updates and `vi`/`less` for its Git defaults.
Authentication is configured separately. HEP has its own installer and needs none
of these package lists; see [../hep/README.md](../hep/README.md).

| List | Purpose |
|---|---|
| `linux-packages.txt` | Essential Debian/Ubuntu packages for minimal + updates |
| `mac-packages.txt` | Essential Homebrew additions; use macOS's Bash, vi, less, and SSH |
| `linux-optional-packages.txt` | Optional Debian/Ubuntu CLI tools |
| `mac-optional-packages.txt` | Optional Homebrew CLI tools |
| `mac-apps.txt` | Optional desktop applications |
| `reference/mac-packages.txt` | Previous machine inventory, including libraries; reference only |

The essential lists are deliberately small. Add project runtimes and scientific
tools for the projects that need them. Review optional lists before installing;
package names vary between Linux distributions. The Linux list uses Ubuntu names
such as [openssh-client](https://packages.ubuntu.com/noble/openssh-client) and
[vim-tiny](https://packages.ubuntu.com/noble/vim-tiny).

On Debian/Ubuntu, from the repository root:

```bash
sudo apt-get update
awk 'NF && $1 !~ /^#/ {print $0}' setup/linux-packages.txt | xargs sudo apt-get install -y
./install.sh --profile minimal --dry-run
./install.sh --profile minimal
./bin/dotfiles doctor
```

If Git is not present yet, install `git` and `ca-certificates` first, then clone
this repository over HTTPS. On macOS, after installing Homebrew, install the
essential list explicitly ([Homebrew documents `python3`](https://formulae.brew.sh/formula/python@3.14)):

```bash
while IFS= read -r package || [ -n "$package" ]; do
  case "$package" in ''|\#*) continue ;; esac
  brew install "$package"
done < setup/mac-packages.txt
./install.sh --profile minimal
./bin/dotfiles doctor
```

For a personal workstation, install the optional tools you use and select
`--profile personal`. Its Git config expects Delta/Ripgrep, GitHub CLI credentials,
and 1Password signing; the Mac editor defaults to Neovim, while Linux uses the
Flatpak Commit app. Run `dotfiles doctor` to find missing configured commands.
You can select a different editor or signing policy in
`~/.config/dotfiles/local.gitconfig`. Minimal has no dependency on those apps.

Use `brew install --cask` with reviewed entries in `setup/mac-apps.txt` for apps.
Fonts remain in `config/mac/fonts/` for optional manual installation.
Oh My Zsh, Starship, Atuin, Conda and nvm hooks activate only when present.
`doctor` is read-only and offline: it checks command availability and installed
links, then describes the authentication/signing work still needed. It does not
install packages, test login credentials, run configured editors/signers, or make
network requests. Missing essential tools/configuration return exit code 1;
optional warnings do not. Re-run it after machine setup and local overrides.

The Linux CI job starts in an Ubuntu container, installs only the essential list,
and checks a fresh minimal home before adding Zsh/ShellCheck for the full tests.
Run `python3 -m unittest discover -s tests -v` locally for disposable-home coverage,
including copied-folder HEP installation and update/rollback.

## Recreating this Mac

The reference inventory preserves the old Mac package list; it is not an
instruction to install every dependency on a new machine. Karabiner-Elements is
installed outside Homebrew on this Mac; install it
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
