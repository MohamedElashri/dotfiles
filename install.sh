#!/usr/bin/env bash
# Link configuration only. Compatible with the Bash shipped by macOS.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
: "${HOME:?HOME must be set}"
PROFILE=personal
physical_path() {
  local candidate=$1 suffix= parent directory normalized
  # Resolve existing ancestors even when a moved checkout's leaf no longer
  # exists. macOS aliases /var through /private/var, including temporary homes.
  while [ ! -d "$candidate" ]; do
    parent=$(dirname "$candidate")
    [ "$parent" != "$candidate" ] || return 1
    suffix="/$(basename "$candidate")$suffix"
    candidate=$parent
  done
  directory=$(cd -P "$candidate" 2>/dev/null && pwd) || return 1
  normalized="${directory%/}$suffix"
  printf '%s\n' "${normalized:-/}"
}
link_reference() {
  local reference
  reference=$(readlink "$1" 2>/dev/null) || return 1
  case "$reference" in /*) ;; *) reference="$(dirname "$1")/$reference" ;; esac
  physical_path "$reference"
}
PREVIOUS_ROOT=$ROOT
# The installed marker records the old checkout even after it has moved.
# Retired profiles migrate to the personal setup; never load their contents.
profile_link=$(link_reference "$HOME/.config/dotfiles/profile" || true)
case "$profile_link" in
  /*/setup/profiles/*)
    PREVIOUS_ROOT=${profile_link%/setup/profiles/*}
    ;;
esac
OS=$(uname -s)
DRY_RUN=0
STATUS=0
LIST=0
CHECK_EXISTING=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --profile) [ "$#" -ge 2 ] || { echo '--profile requires personal' >&2; exit 2; }; PROFILE=$2; shift ;;
    --platform) [ "$#" -ge 2 ] || exit 2; case "$2" in linux) OS=Linux ;; mac) OS=Darwin ;; *) echo 'Use --platform linux|mac' >&2; exit 2 ;; esac; shift ;;
    --dry-run|-n) DRY_RUN=1 ;;
    --status) STATUS=1 ;;
    --list) LIST=1 ;;
    --check-existing) CHECK_EXISTING=1 ;;
    --help|-h) echo 'Usage: ./install.sh [--profile personal] [--platform linux|mac] [--dry-run|--status|--list|--check-existing]'; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done
case "$PROFILE" in personal) ;; *) echo 'Invalid profile; only personal is supported' >&2; exit 2 ;; esac
case "$OS" in Linux|Darwin) ;; *) echo "Unsupported OS: $OS" >&2; exit 2 ;; esac
BACKUP="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)-$$"
sources=(); targets=()
add() { sources+=("$ROOT/$1"); targets+=("$HOME/$2"); }
add setup/profiles/personal .config/dotfiles/profile
add bash/.bashrc .bashrc
# Preserve existing login files; relocate only links owned by this installer.
profile_source=shell/.profile
[ "$OS" != Darwin ] || profile_source=config/mac/shell/.profile
if [ ! -e "$HOME/.profile" ] && [ ! -L "$HOME/.profile" ] && [ ! -e "$HOME/.bash_profile" ] && [ ! -e "$HOME/.bash_login" ]; then
  add "$profile_source" .profile
elif [ -L "$HOME/.profile" ]; then
  case "$(link_reference "$HOME/.profile" || true)" in
    "$ROOT/sh/.profile"|"$ROOT/shell/.profile"|"$ROOT/config/mac/shell/.profile"|"$PREVIOUS_ROOT/sh/.profile"|"$PREVIOUS_ROOT/shell/.profile"|"$PREVIOUS_ROOT/config/mac/shell/.profile") add "$profile_source" .profile ;;
  esac
fi
add zsh/.zshenv .zshenv
add zsh/.zprofile .zprofile
add zsh/.zshrc .zshrc
add config/git/.gitconfig .gitconfig
add config/git/.stCommitMsg .stCommitMsg
add config/git/ignore .config/dotfiles/git-ignore
add config/tmux/.tmux.conf .tmux.conf
add config/editors/zed/settings.json .config/zed/settings.json
add config/terminals/ghostty/config .config/ghostty/config
add config/cli/atuin/config.toml .config/atuin/config.toml
add config/cli/asciinema/defaults.toml .config/asciinema/defaults.toml
add config/cli/bat/config .config/bat/config
add config/cli/btop/btop.conf .config/btop/btop.conf
add config/cli/helix/config.toml .config/helix/config.toml
add config/cli/gh/config.yml .config/gh/config.yml
add config/cli/micro/settings.json .config/micro/settings.json
add config/cli/micro/bindings.json .config/micro/bindings.json
if [ -d "$HOME/.oh-my-zsh/.git" ]; then
  add config/zsh/themes/dracula-pro.zsh-theme .oh-my-zsh/custom/themes/dracula-pro.zsh-theme
fi
if [ "$OS" = Darwin ]; then
  add config/mac/ssh/config .ssh/config
  for name in settings.json termthemes.json widgets.json; do
    add "config/mac/waveterm/config/$name" ".waveterm/config/$name"
  done
  add config/git/mac.gitconfig .config/dotfiles/git-platform
  add config/mac/zsh/.p10k.zsh .p10k.zsh
  add config/mac/cli/nano/nanorc .nanorc
  add config/mac/cli/vicinae/settings.json .config/vicinae/settings.json
  add config/mac/cli/hyper/hyper.js/.hyper.js .hyper.js
  add config/mac/karabiner/karabiner.json .config/karabiner/karabiner.json
  add config/mac/rio-terminal .config/rio
  add config/mac/warp/settings.toml .warp/settings.toml
else
  add config/ssh/config .ssh/config
  for name in settings.json termthemes.json widgets.json connections.json; do
    add "config/terminals/waveterm/config/$name" ".waveterm/config/$name"
  done
  add config/git/linux.gitconfig .config/dotfiles/git-platform
fi
# Validate all sources before making any changes.
for src in "${sources[@]}"; do [ -e "$src" ] || { echo "Missing source: $src" >&2; exit 1; }; done
if [ "$LIST" = 1 ]; then
  for ((i=0; i<${#sources[@]}; i++)); do printf '%s\t%s\n' "${sources[i]}" "${targets[i]}"; done
  exit 0
fi
if [ "$CHECK_EXISTING" = 1 ]; then
  canonical_path() {
    local candidate=$1 directory next hops=0
    while [ "$hops" -lt 40 ]; do
      candidate=$(physical_path "$candidate") || return 1
      case "$candidate" in "$PREVIOUS_ROOT/"*) candidate="$ROOT/${candidate#"$PREVIOUS_ROOT"/}" ;; esac
      directory=$(cd -P "$(dirname "$candidate")" 2>/dev/null && pwd) || return 1
      candidate="$directory/$(basename "$candidate")"
      if [ ! -L "$candidate" ]; then printf '%s\n' "$candidate"; return 0; fi
      next=$(readlink "$candidate") || return 1
      case "$next" in /*) candidate=$next ;; *) candidate="$directory/$next" ;; esac
      hops=$((hops + 1))
    done
    return 1
  }
  conflict=0
  for ((i=0; i<${#sources[@]}; i++)); do
    src=${sources[i]}; dest=${targets[i]}
    [ -e "$dest" ] || [ -L "$dest" ] || continue
    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then continue; fi
    # Profile markers are installer metadata, including retired profile names.
    if [ "$dest" = "$HOME/.config/dotfiles/profile" ]; then
      if [ -L "$dest" ]; then
        case "$(link_reference "$dest" || true)" in "$ROOT/setup/profiles/"*|"$PREVIOUS_ROOT/setup/profiles/"*) continue ;; esac
      elif [ -f "$dest" ]; then
        saved_profile=
        IFS= read -r saved_profile < "$dest" || true
        case "$saved_profile" in personal|hep) continue ;; esac
      fi
    fi
    managed=0
    actual=$(canonical_path "$dest" || true)
    expected=$(canonical_path "$src" || true)
    if [ -n "$expected" ] && [ "$actual" = "$expected" ]; then
      if [ -L "$dest" ]; then
        managed=1
      else
        # Only known legacy directory links may supply an ordinary file.
        for relative in .waveterm/config .config/ghostty; do
          case "$dest" in "$HOME/$relative/"*) [ ! -L "$HOME/$relative" ] || managed=1 ;; esac
        done
      fi
    fi
    if [ "$managed" = 0 ]; then printf 'Detached: %s\n' "$dest"; conflict=1; fi
  done
  exit "$conflict"
fi
if [ "$STATUS" = 1 ]; then
  drift=0
  for ((i=0; i<${#sources[@]}; i++)); do
    src=${sources[i]}; dest=${targets[i]}
    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
      continue
    fi
    if [ -e "$dest" ] || [ -L "$dest" ]; then
      printf 'Detached: %s (expected %s)\n' "$dest" "$src"
    else
      printf 'Missing: %s (expected %s)\n' "$dest" "$src"
    fi
    drift=1
  done
  [ "$drift" = 0 ] && echo 'All managed files are linked.'
  exit "$drift"
fi
printf 'OS: %s | profile: %s | repository: %s\n' "$OS" "$PROFILE" "$ROOT"
run() {
  if [ "$DRY_RUN" = 1 ]; then printf 'Would run:'; printf ' %q' "$@"; printf '\n'; else "$@"; fi
}
# Keep an unmanaged pre-existing Bash rc as a site hook, including /etc/bashrc
# initialization and module definitions. Existing repo links need no hook.
site="$HOME/.config/dotfiles/site.bash"
if [ "$OS" != Darwin ] && [ -f "$HOME/.bashrc" ] && ! cmp -s "$HOME/.bashrc" "$ROOT/bash/.bashrc"; then
  old_target=$(link_reference "$HOME/.bashrc" || true)
  case "$old_target" in
    "$ROOT/"*|"$PREVIOUS_ROOT/"*) ;;
    *)
      if [ -e "$site" ] || [ -L "$site" ]; then
        echo "Existing site hook and unmanaged .bashrc; reconcile $site before installation." >&2
        exit 1
      fi
      run mkdir -p "$(dirname "$site")"
      run cp -pL "$HOME/.bashrc" "$site"
      ;;
  esac
fi
# Replace legacy whole-directory links with real directories and file links.
# Copy their contents first so application-owned files survive the migration.
for relative in .waveterm/config .config/ghostty; do
  dest="$HOME/$relative"
  if [ -L "$dest" ]; then
    case "$(link_reference "$dest" || true)" in
      "$ROOT/"*|"$PREVIOUS_ROOT/"*)
        copy_contents=0
        [ ! -d "$dest" ] || copy_contents=1
        saved="$BACKUP/legacy-links/$relative"
        run mkdir -p "$(dirname "$saved")"
        run mv "$dest" "$saved"
        run mkdir -p "$dest"
        if [ "$copy_contents" = 1 ]; then run cp -pRL "$saved/." "$dest/"; fi
        ;;
    esac
  fi
done
# Consolidate old local override names, keeping the current override last.
# Copies are backed up before removal; dry-run performs no reads of their contents.
migrate_overrides() {
  local target="$HOME/.config/dotfiles/$1" old found=0 temp saved
  shift
  for old in "$@"; do [ ! -f "$HOME/$old" ] || found=1; done
  [ "$found" = 1 ] || return 0
  if [ "$DRY_RUN" = 1 ]; then
    printf 'Would consolidate legacy overrides into %s (originals backed up)\n' "$target"
    return 0
  fi
  mkdir -p "$(dirname "$target")"
  temp=$(mktemp "$HOME/.config/dotfiles/.migration.XXXXXX")
  for old in "$@"; do
    if [ -f "$HOME/$old" ]; then
      cat "$HOME/$old" >> "$temp"
      printf '\n' >> "$temp"
    fi
  done
  if [ -f "$target" ]; then cat "$target" >> "$temp"; fi
  for old in "$@" "${target#"$HOME"/}"; do
    if [ -e "$HOME/$old" ] || [ -L "$HOME/$old" ]; then
      saved="$BACKUP/$old"
      mkdir -p "$(dirname "$saved")"
      mv "$HOME/$old" "$saved"
    fi
  done
  mv "$temp" "$target"
}
if [ "$PROFILE" = personal ]; then
  migrate_overrides local.env.zsh .config/dotfiles/environment.local.zsh .environment.local.zsh
  migrate_overrides local.zsh .config/dotfiles/zshrc.local.zsh .dotfiles.local.zsh
fi
for ((i=0; i<${#sources[@]}; i++)); do
  src=${sources[i]}; dest=${targets[i]}
  if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
    printf 'Already linked: %s\n' "$dest"
    continue
  fi
  run mkdir -p "$(dirname "$dest")"
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    saved="$BACKUP/${dest#"$HOME"/}"
    run mkdir -p "$(dirname "$saved")"
    run mv "$dest" "$saved"
  fi
  run ln -s "$src" "$dest"
done
# Retire only links installed by the old layout, never similarly named user files.
if [ "$PROFILE" = personal ]; then
  for name in aliases functions environment config plugins tricks m_nvim; do
    dest="$HOME/$name.zsh"
    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$ROOT/zsh/$name.zsh" ]; then
      run mkdir -p "$BACKUP"
      run mv "$dest" "$BACKUP/$name.zsh"
    fi
  done
  for name in core aliases functions integrations; do
    dest="$HOME/.config/dotfiles/zsh/$name"
    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$ROOT/zsh/$name" ]; then
      run mkdir -p "$BACKUP/.config/dotfiles/zsh"
      run mv "$dest" "$BACKUP/.config/dotfiles/zsh/$name"
    fi
  done
  if [ -L "$HOME/cli" ] && [ "$(readlink "$HOME/cli")" = "$ROOT/cli" ]; then
    run mkdir -p "$BACKUP"
    run mv "$HOME/cli" "$BACKUP/cli"
  fi
  run chmod 700 "$HOME/.ssh"
fi
if [ "$DRY_RUN" = 1 ]; then
  echo 'Preview complete; no files changed.'
else
  echo 'Done. Open a new shell.'
  [ ! -d "$BACKUP" ] || printf 'Replaced files: %s\n' "$BACKUP"
fi
