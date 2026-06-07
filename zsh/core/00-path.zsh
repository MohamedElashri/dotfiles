# PATH and exported toolchain variables shared by interactive zsh sessions.

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

_path_prepend "$HOME/.local/bin" "$HOME/bin"

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

export GOPATH="$HOME/go"
if [[ -d "${HOMEBREW_PREFIX:-}/opt/go/libexec" ]]; then
  export GOROOT="$HOMEBREW_PREFIX/opt/go/libexec"
elif [[ -d "/usr/local/go" ]]; then
  export GOROOT="/usr/local/go"
fi
[[ -n "${GOROOT:-}" ]] && _path_append "$GOROOT/bin"
_path_append "$GOPATH/bin"
# export GO111MODULE=on

if [[ -r /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]]; then
  source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
fi

export GEM_HOME="$HOME/gems"
_path_prepend "$GEM_HOME/bin"

_path_prepend "$HOME/.cargo/bin" "$HOME/.atuin/bin" "$HOME/.pixi/bin"

for _texlive_bin in /usr/local/texlive/*/bin/*(/N); do
  _texlive_root="${_texlive_bin:h:h}"
  _path_prepend "$_texlive_bin"
  _pathvar_prepend MANPATH "$_texlive_root/texmf-dist/doc/man"
  _pathvar_prepend INFOPATH "$_texlive_root/texmf-dist/doc/info"
done
unset _texlive_bin _texlive_root

for _local_env_file in \
  "$HOME/.config/dotfiles/environment.local.zsh" \
  "$HOME/.environment.local.zsh"
do
  [[ -r "$_local_env_file" ]] && source "$_local_env_file"
done
unset _local_env_file
