#!/usr/bin/env bash
# Self-contained: copying this directory is enough to install HEP configuration.
set -euo pipefail
HEP_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
: "${HOME:?HOME must be set}"
OS=$(uname -s)
DRY_RUN=0; STATUS=0; MANIFEST=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run|-n) DRY_RUN=1 ;;
    --status) STATUS=1 ;;
    --manifest) MANIFEST=1 ;;
    --platform)
      if [ "$#" -lt 2 ] || [ "$2" != linux ]; then
        echo 'HEP requires Linux' >&2; exit 2
      fi
      OS=Linux; shift ;;
    --help|-h) echo 'Usage: ./hep/install.sh [--dry-run|--status]'; exit 0 ;;
    *) echo "Unknown HEP option: $1" >&2; exit 2 ;;
  esac
  shift
done
[ "$OS" = Linux ] || { echo 'HEP requires Linux' >&2; exit 2; }
previous=$(readlink "$HOME/.config/dotfiles/profile" 2>/dev/null || true)
previous_hep=${previous%/profile}
previous_repo=
case "$previous" in
  */setup/profiles/hep|*/setup/profiles/personal|*/setup/profiles/minimal) previous_repo=${previous%/setup/profiles/*} ;;
esac
sources=("$HEP_ROOT/profile" "$HEP_ROOT/.bashrc")
targets=("$HOME/.config/dotfiles/profile" "$HOME/.bashrc")
# Preserve site login files. Repair only links previously managed by this setup.
old_login=$(readlink "$HOME/.profile" 2>/dev/null || true)
managed_login=0
case "$old_login" in
  "$HEP_ROOT/.profile"|"$previous_hep/.profile") managed_login=1 ;;
esac
if [ -n "$previous_repo" ]; then
  case "$old_login" in
    "$previous_repo/shell/.profile"|"$previous_repo/sh/.profile"|"$previous_repo/config/mac/shell/.profile") managed_login=1 ;;
  esac
fi
if [ "$managed_login" = 1 ] ||
   { [ ! -e "$HOME/.profile" ] && [ ! -L "$HOME/.profile" ] && [ ! -e "$HOME/.bash_profile" ] && [ ! -e "$HOME/.bash_login" ]; }; then
  sources+=("$HEP_ROOT/.profile"); targets+=("$HOME/.profile")
fi
for name in profile .bashrc .profile env.sh common.bash select.bash lxplus.bash sneezy.bash sleepy.bash gpu_farm.bash; do
  [ -f "$HEP_ROOT/$name" ] || { echo "Missing HEP source: $name" >&2; exit 1; }
done
site="$HOME/.config/dotfiles/site.bash"
preserve_site=0
if [ -f "$HOME/.bashrc" ] && ! cmp -s "$HOME/.bashrc" "$HEP_ROOT/.bashrc"; then
  old=$(readlink "$HOME/.bashrc" || true)
  if [ "$old" != "$previous_hep/.bashrc" ] &&
     { [ -z "$previous_repo" ] || [ "$old" != "$previous_repo/bash/.bashrc" ]; }; then
    if [ -e "$site" ] || [ -L "$site" ]; then
      echo "Reconcile unmanaged .bashrc with $site first." >&2; exit 1
    fi
    preserve_site=1
  fi
fi
if [ "$MANIFEST" = 1 ]; then
  for target in "${targets[@]}"; do printf 'link\0%s\0' "$target"; done
  [ "$preserve_site" = 0 ] || printf 'change\0%s\0' "$site"
  exit 0
fi
if [ "$STATUS" = 1 ]; then
  drift=0
  for ((i=0; i<${#sources[@]}; i++)); do
    if [ ! -L "${targets[i]}" ] || [ "$(readlink "${targets[i]}")" != "${sources[i]}" ]; then
      printf 'Detached or missing: %s (expected %s)\n' "${targets[i]}" "${sources[i]}"
      drift=1
    fi
  done
  [ "$drift" != 0 ] || echo 'All HEP files are linked.'
  exit "$drift"
fi
run() {
  if [ "$DRY_RUN" = 1 ]; then printf 'Would run:'; printf ' %q' "$@"; printf '\n'; else "$@"; fi
}
backup="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)-$$"
if [ "$preserve_site" = 1 ]; then
  run mkdir -p "$(dirname "$site")"
  run cp -pL "$HOME/.bashrc" "$site"
fi
for ((i=0; i<${#sources[@]}; i++)); do
  source=${sources[i]}; target=${targets[i]}
  if [ -L "$target" ] && [ "$(readlink "$target")" = "$source" ]; then continue; fi
  run mkdir -p "$(dirname "$target")"
  if [ -e "$target" ] || [ -L "$target" ]; then
    saved="$backup/${target#"$HOME"/}"
    run mkdir -p "$(dirname "$saved")"
    run mv "$target" "$saved"
  fi
  run ln -s "$source" "$target"
done
if [ "$DRY_RUN" = 1 ]; then
  echo 'HEP preview complete; no files changed.'
else
  echo 'HEP installed. Open a new Bash shell.'
  [ ! -d "$backup" ] || printf 'Replaced files: %s\n' "$backup"
fi
