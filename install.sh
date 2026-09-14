#!/usr/bin/env bash
# Link configuration only. Compatible with the Bash shipped by macOS.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
PROFILE=personal
if [ -r "$HOME/.config/dotfiles/profile" ]; then
  read -r PROFILE < "$HOME/.config/dotfiles/profile"
fi
OS=$(uname -s)
DRY_RUN=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --profile) [ "$#" -ge 2 ] || { echo '--profile requires personal or hep' >&2; exit 2; }; PROFILE=$2; shift ;;
    --platform) [ "$#" -ge 2 ] || exit 2; case "$2" in linux) OS=Linux ;; mac) OS=Darwin ;; *) echo 'Use --platform linux|mac and --profile hep for clusters' >&2; exit 2 ;; esac; shift ;;
    --dry-run|-n) DRY_RUN=1 ;;
    --help|-h) echo 'Usage: ./install.sh [--profile personal|hep] [--platform linux|mac] [--dry-run]'; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done
case "$PROFILE" in personal|hep) ;; *) echo 'Invalid profile' >&2; exit 2 ;; esac
case "$OS" in Linux|Darwin) ;; *) echo "Unsupported OS: $OS" >&2; exit 2 ;; esac
[ "$PROFILE" != hep ] || [ "$OS" = Linux ] || { echo 'HEP profile requires Linux' >&2; exit 2; }
: "${HOME:?HOME must be set}"
BACKUP="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)-$$"
sources=(); targets=()
add() { sources+=("$ROOT/$1"); targets+=("$HOME/$2"); }
add "setup/profiles/$PROFILE" .config/dotfiles/profile
add bash/.bashrc .bashrc
# Do not replace site login files. Supply .profile only for a fresh home.
if [ ! -e "$HOME/.profile" ] && [ ! -L "$HOME/.profile" ] && [ ! -e "$HOME/.bash_profile" ] && [ ! -e "$HOME/.bash_login" ]; then
  add shell/.profile .profile
elif [ -L "$HOME/.profile" ] && [ "$(readlink "$HOME/.profile")" = "$ROOT/sh/.profile" ]; then
  add shell/.profile .profile
fi
if [ "$PROFILE" = personal ]; then
  add zsh/.zshenv .zshenv
  add zsh/.zprofile .zprofile
  add zsh/.zshrc .zshrc
  add config/git/.gitconfig .gitconfig
  add config/git/.stCommitMsg .stCommitMsg
  add config/git/ignore .config/dotfiles/git-ignore
  if [ "$OS" = Darwin ]; then
    add config/git/mac.gitconfig .config/dotfiles/git-platform
    add config/mac/ssh/config .ssh/config
    add config/mac/zsh/.p10k.zsh .p10k.zsh
    add config/mac/cli/atuin/config.toml .config/atuin/config.toml
    add config/mac/cli/bat/config .config/bat/config
    add config/mac/cli/helix/config.toml .config/helix/config.toml
    add config/mac/tmux/.tmux.conf .tmux.conf
    add config/mac/rio-terminal .config/rio
    add config/mac/vscode/settings.json 'Library/Application Support/Code/User/settings.json'
    add config/mac/zed/settings.json .config/zed/settings.json
    add config/mac/waveterm .waveterm/config
  else
    add config/git/linux.gitconfig .config/dotfiles/git-platform
    add config/ssh/config .ssh/config
    add config/terminals/ghostty .config/ghostty
    add config/terminals/waveterm/config .waveterm/config
  fi
fi
# Validate all sources before making any changes.
for src in "${sources[@]}"; do [ -e "$src" ] || { echo "Missing source: $src" >&2; exit 1; }; done
printf 'OS: %s | profile: %s | repository: %s\n' "$OS" "$PROFILE" "$ROOT"
run() {
  if [ "$DRY_RUN" = 1 ]; then printf 'Would run:'; printf ' %q' "$@"; printf '\n'; else "$@"; fi
}
# Keep an unmanaged pre-existing Bash rc as a site hook, including /etc/bashrc
# initialization and module definitions. Existing repo links need no hook.
site="$HOME/.config/dotfiles/site.bash"
if [ -f "$HOME/.bashrc" ] && ! cmp -s "$HOME/.bashrc" "$ROOT/bash/.bashrc"; then
  old_target=$(readlink "$HOME/.bashrc" || true)
  case "$old_target" in
    "$ROOT/"*) ;;
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
