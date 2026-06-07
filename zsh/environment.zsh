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

# Homebrew/Linuxbrew, when installed. Prefer known prefixes and the existing
# brew path over running `brew shellenv` on every startup.
if [[ -z "${HOMEBREW_PREFIX-}" ]]; then
  for _brew_prefix in /home/linuxbrew/.linuxbrew /opt/homebrew /usr/local; do
    if [[ -x "$_brew_prefix/bin/brew" ]]; then
      export HOMEBREW_PREFIX="$_brew_prefix"
      break
    fi
  done
fi

if [[ -n "${HOMEBREW_PREFIX-}" && -d "$HOMEBREW_PREFIX" ]]; then
  export HOMEBREW_CELLAR="${HOMEBREW_CELLAR:-$HOMEBREW_PREFIX/Cellar}"
  export HOMEBREW_REPOSITORY="${HOMEBREW_REPOSITORY:-$HOMEBREW_PREFIX/Homebrew}"
  _path_prepend "$HOMEBREW_PREFIX/bin" "$HOMEBREW_PREFIX/sbin"
  _pathvar_prepend MANPATH "$HOMEBREW_PREFIX/share/man"
  _pathvar_prepend INFOPATH "$HOMEBREW_PREFIX/share/info"
fi
unset _brew_prefix

# Go. Set GOPATH everywhere, and set GOROOT only when this dotfile can detect a
# manual or Homebrew Go installation.
export GOPATH="$HOME/go"
if [[ -d "${HOMEBREW_PREFIX:-}/opt/go/libexec" ]]; then
  export GOROOT="$HOMEBREW_PREFIX/opt/go/libexec"
elif [[ -d "/usr/local/go" ]]; then
  export GOROOT="/usr/local/go"
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

# TeX Live. Add every installed yearly tree, with the newest year winning
# because PATH entries are prepended as the sorted glob advances.
for _texlive_bin in /usr/local/texlive/*/bin/*(/N); do
  _texlive_root="${_texlive_bin:h:h}"
  _path_prepend "$_texlive_bin"
  _pathvar_prepend MANPATH "$_texlive_root/texmf-dist/doc/man"
  _pathvar_prepend INFOPATH "$_texlive_root/texmf-dist/doc/info"
done
unset _texlive_bin _texlive_root

# Optional startup Quran message is run from .zshrc after config.zsh is loaded.

# Machine-local environment. Keep host-specific paths and secrets out of the
# shared repo.
for _local_env_file in \
  "$HOME/.config/dotfiles/environment.local.zsh" \
  "$HOME/.environment.local.zsh"
do
  [[ -r "$_local_env_file" ]] && source "$_local_env_file"
done
unset _local_env_file
