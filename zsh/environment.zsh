# Shared zsh environment.
#
# Keep this file limited to PATH entries and exported toolchain variables.
# Interactive frameworks and hooks belong in .zshrc so scripts and subshells do
# not pay for prompt/history/plugin setup.

typeset -gaU path

_path_prepend() {
  local dir
  for dir in "$@"; do
    [[ -d "$dir" ]] || continue
    path=("$dir" "${path[@]:#$dir}")
  done
}

_path_append() {
  local dir
  for dir in "$@"; do
    [[ -d "$dir" ]] || continue
    path=("${path[@]:#$dir}" "$dir")
  done
}

_pathvar_prepend() {
  local var_name="$1"
  local dir="$2"
  local current="${(P)var_name}"

  [[ -d "$dir" ]] || return
  case ":$current:" in
    *":$dir:"*) ;;
    *) export "$var_name=$dir:$current" ;;
  esac
}

# User-local command paths.
_path_prepend "$HOME/.local/bin" "$HOME/bin"

# Linuxbrew without running `brew shellenv` on every shell startup.
if [[ -d "/home/linuxbrew/.linuxbrew" ]]; then
  export HOMEBREW_PREFIX="/home/linuxbrew/.linuxbrew"
  export HOMEBREW_CELLAR="$HOMEBREW_PREFIX/Cellar"
  export HOMEBREW_REPOSITORY="$HOMEBREW_PREFIX/Homebrew"
  _path_prepend "$HOMEBREW_PREFIX/bin" "$HOMEBREW_PREFIX/sbin"
  _pathvar_prepend MANPATH "$HOMEBREW_PREFIX/share/man"
  _pathvar_prepend INFOPATH "$HOMEBREW_PREFIX/share/info"
fi

# Go installed through Linuxbrew. Prefer the stable opt symlink to avoid a
# `brew --prefix go` process during every startup.
export GOPATH="$HOME/go"
if [[ -d "${HOMEBREW_PREFIX:-}/opt/go/libexec" ]]; then
  export GOROOT="$HOMEBREW_PREFIX/opt/go/libexec"
elif [[ -d "/home/linuxbrew/.linuxbrew/opt/go/libexec" ]]; then
  export GOROOT="/home/linuxbrew/.linuxbrew/opt/go/libexec"
fi
[[ -n "${GOROOT:-}" ]] && _path_append "$GOROOT/bin"
_path_append "$GOPATH/bin"
# export GO111MODULE=on

# Nix daemon profile, when installed.
if [[ -r /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]]; then
  source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
fi

# nvm is intentionally lazy-loaded. Sourcing nvm.sh is one of the slowest shell
# startup steps, but these wrappers keep nvm/node/npm commands working.
if [[ -z "${NVM_DIR-}" ]]; then
  if [[ -n "${XDG_CONFIG_HOME-}" ]]; then
    export NVM_DIR="$XDG_CONFIG_HOME/nvm"
  else
    export NVM_DIR="$HOME/.nvm"
  fi
fi

if [[ -s "$NVM_DIR/nvm.sh" ]]; then
  _load_nvm() {
    unset -f nvm node npm npx corepack yarn pnpm 2>/dev/null
    source "$NVM_DIR/nvm.sh"
    [[ -s "$NVM_DIR/bash_completion" ]] && source "$NVM_DIR/bash_completion"
  }

  nvm() { _load_nvm && nvm "$@"; }
  node() { _load_nvm && command node "$@"; }
  npm() { _load_nvm && command npm "$@"; }
  npx() { _load_nvm && command npx "$@"; }
  corepack() { _load_nvm && command corepack "$@"; }
  yarn() { _load_nvm && command yarn "$@"; }
  pnpm() { _load_nvm && command pnpm "$@"; }
fi

# Ruby gems installed under the home directory.
export GEM_HOME="$HOME/gems"
_path_prepend "$GEM_HOME/bin"

# Rust/Cargo, Atuin, Pixi.
_path_prepend "$HOME/.cargo/bin" "$HOME/.atuin/bin" "$HOME/.pixi/bin"

# TeX Live 2026.
_path_prepend "/usr/local/texlive/2026/bin/x86_64-linux"
_pathvar_prepend MANPATH "/usr/local/texlive/2026/texmf-dist/doc/man"
_pathvar_prepend INFOPATH "/usr/local/texlive/2026/texmf-dist/doc/info"

# Optional startup Quran message is run from .zshrc after config.zsh is loaded.

##### Physics Tools #####

# Physics environment
# export PHYSICS_ROOT="$HOME/physics"

# # Setup ROOT bindings
# export PYTHONPATH=$(brew --prefix)/lib/python3.12/site-packages:$PYTHONPATH

# # Setup PYTHIA environment
# export PYTHIA8=$HOME/physics/pythia
# export PATH=$PYTHIA8/bin:$PATH
# export LD_LIBRARY_PATH=$PYTHIA8/lib:$LD_LIBRARY_PATH
# export PYTHONPATH=$PYTHIA8/lib:$PYTHONPATH

# # Setup FASTJET environment (optional)
# export PATH=$HOME/physics/fastjet/bin:$PATH:$PATH
# export LD_LIBRARY_PATH=$HOME/physics/fastjet/lib:$LD_LIBRARY_PATH
# export PKG_CONFIG_PATH=$HOME/physics/fastjet/lib/pkgconfig:$PKG_CONFIG_PATH
