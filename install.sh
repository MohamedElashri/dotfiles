#!/usr/bin/env bash
# Link configuration only. Compatible with the Bash shipped by macOS.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
: "${HOME:?HOME must be set}"
physical_path() {
  local candidate=$1 suffix='' parent directory normalized
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
# The installation marker records the source location after a checkout move.
profile_link=$(link_reference "$HOME/.config/dotfiles/profile" || true)
case "$profile_link" in
  /*/setup/profiles/personal)
    PREVIOUS_ROOT=${profile_link%/setup/profiles/*}
    ;;
esac
OS=$(uname -s)
DRY_RUN=0
STATUS=0
LIST=0
CHECK_EXISTING=0
AGENTS_ONLY=0
WITH_AGENTS=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --platform) [ "$#" -ge 2 ] || exit 2; case "$2" in linux) OS=Linux ;; mac) OS=Darwin ;; *) echo 'Use --platform linux|mac' >&2; exit 2 ;; esac; shift ;;
    --dry-run|-n) DRY_RUN=1 ;;
    --status) STATUS=1 ;;
    --list|--manifest) LIST=1 ;;
    --check-existing) CHECK_EXISTING=1 ;;
    --agents-only) AGENTS_ONLY=1 ;;
    --with-agents) WITH_AGENTS=1 ;;
    --help|-h) echo 'Usage: ./install.sh [--platform linux|mac] [--with-agents|--agents-only] [--dry-run|--status|--list|--manifest|--check-existing]'; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done
case "$OS" in Linux|Darwin) ;; *) echo "Unsupported OS: $OS" >&2; exit 2 ;; esac
BACKUP="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)-$$"
sources=(); targets=()
add() { sources+=("$ROOT/$1"); targets+=("$HOME/$2"); }
add setup/profiles/personal .config/dotfiles/profile
add bash/.bashrc .bashrc
# Preserve existing login files; relocate only links owned by this installer.
profile_source=shell/.profile
if [ ! -e "$HOME/.profile" ] && [ ! -L "$HOME/.profile" ] && [ ! -e "$HOME/.bash_profile" ] && [ ! -e "$HOME/.bash_login" ]; then
  add "$profile_source" .profile
elif [ -L "$HOME/.profile" ]; then
  case "$(link_reference "$HOME/.profile" || true)" in
    "$ROOT/shell/.profile"|"$PREVIOUS_ROOT/shell/.profile") add "$profile_source" .profile ;;
  esac
fi
add zsh/.zshenv .zshenv
add zsh/.zprofile .zprofile
add zsh/.zshrc .zshrc
add config/git/.gitconfig .gitconfig
add config/git/.stCommitMsg .stCommitMsg
add config/git/ignore .config/dotfiles/git-ignore
# Classic dotfiles never require agent sources or access harness directories.
if [ "$WITH_AGENTS" = 1 ] || [ "$AGENTS_ONLY" = 1 ]; then
  add agent-workflow/AGENTS.md .codex/AGENTS.md
  add agent-workflow/AGENTS.md .claude/CLAUDE.md
  add agent-workflow/AGENTS.md .config/opencode/AGENTS.md
  add agent-workflow/AGENTS.md .pi/agent/AGENTS.md
  for skill in research-audit engineering-audit cuda-performance; do
    add "agent-workflow/skills/$skill" ".agents/skills/$skill"
    add "agent-workflow/skills/$skill" ".claude/skills/$skill"
  done
fi
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
# Reuse the normal backup, preflight, and diagnostic paths for agent-only setup.
if [ "$AGENTS_ONLY" = 1 ]; then
  agent_sources=(); agent_targets=()
  for ((i=0; i<${#sources[@]}; i++)); do
    case "${sources[i]}" in
      "$ROOT/agent-workflow/"*)
        agent_sources+=("${sources[i]}"); agent_targets+=("${targets[i]}") ;;
    esac
  done
  sources=("${agent_sources[@]}"); targets=("${agent_targets[@]}")
fi
# Validate all sources before making any changes.
for src in "${sources[@]}"; do
  [ -e "$src" ] || { echo "Missing source: $src" >&2; exit 1; }
  case "$src" in
    "$ROOT/agent-workflow/skills/"*)
      if [ ! -f "$src/SKILL.md" ] || [ -L "$src/SKILL.md" ]; then
        echo "Skill source must contain a regular manifest: $src/SKILL.md" >&2
        exit 1
      fi ;;
  esac
done
if [ "$LIST" = 1 ]; then
  for ((i=0; i<${#sources[@]}; i++)); do printf '%s\t%s\n' "${sources[i]}" "${targets[i]}"; done
  exit 0
fi
# Parent links can redirect replacements into source or application directories.
# Require real, searchable parents before any installation writes occur.
for ((i=0; i<${#sources[@]}; i++)); do
  parent=${targets[i]%/*}
  while [ "$parent" != "$HOME" ]; do
    if [ -L "$parent" ] || { [ -e "$parent" ] && [ ! -d "$parent" ]; }; then
      printf 'Blocked configuration parent: %s (reconcile symlinks or non-directories manually)\n' "$parent" >&2
      exit 1
    fi
    if [ -d "$parent" ] && [ ! -x "$parent" ]; then
      printf 'Blocked configuration parent: %s (directory is not searchable)\n' "$parent" >&2
      exit 1
    fi
    parent=${parent%/*}
  done
  case "${sources[i]}" in
    "$ROOT/agent-workflow/skills/"*)
      dest=${targets[i]}
      if [ -d "$dest" ] && [ ! -L "$dest" ]; then
        if [ ! -r "$dest" ] || [ ! -x "$dest" ]; then
          printf 'Cannot inspect skill directory: %s (read and search access required)\n' "$dest" >&2
          exit 1
        fi
        # A directory replacement must not hide user-owned sibling content.
        for entry in "$dest"/* "$dest"/.[!.]* "$dest"/..?*; do
          [ -e "$entry" ] || [ -L "$entry" ] || continue
          if [ "$entry" = "$dest/SKILL.md" ] && [ ! -d "$entry" ]; then continue; fi
          printf 'Unmanaged skill contents: %s (reconcile before replacing the skill directory)\n' "$entry" >&2
          exit 1
        done
      fi ;;
  esac
  # Existing correct links need no directory writes. Otherwise reject known
  # write blockers before changing unrelated configuration or fetching updates.
  dest=${targets[i]}
  if [ "$STATUS" = 0 ] && { [ ! -L "$dest" ] || [ "$(readlink "$dest")" != "${sources[i]}" ]; }; then
    write_parent=$(dirname "$dest")
    while [ ! -d "$write_parent" ]; do write_parent=$(dirname "$write_parent"); done
    if [ ! -w "$write_parent" ]; then
      printf 'Configuration path is not writable: %s\n' "$write_parent" >&2
      exit 1
    fi
    # Moving a real directory to the backup parent requires write access to
    # that directory as well as its current parent on supported platforms.
    if [ -d "$dest" ] && [ ! -L "$dest" ] && [ ! -w "$dest" ]; then
      printf 'Configuration path is not writable: %s\n' "$dest" >&2
      exit 1
    fi
  fi
done
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
    managed=0
    actual=$(canonical_path "$dest" || true)
    expected=$(canonical_path "$src" || true)
    if [ -L "$dest" ] && [ -n "$expected" ] && [ "$actual" = "$expected" ]; then
      managed=1
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
printf 'OS: %s | repository: %s\n' "$OS" "$ROOT"
run() {
  if [ "$DRY_RUN" = 1 ]; then printf 'Would run:'; printf ' %q' "$@"; printf '\n'; else "$@"; fi
}
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
if [ "$AGENTS_ONLY" = 0 ]; then
  run chmod 700 "$HOME/.ssh"
fi
if [ "$DRY_RUN" = 1 ]; then
  echo 'Preview complete; no files changed.'
else
  if [ "$AGENTS_ONLY" = 1 ]; then
    echo 'Done. Start new coding-agent sessions to load the instructions.'
  else
    echo 'Done. Open a new shell.'
  fi
  [ ! -d "$BACKUP" ] || printf 'Replaced files: %s\n' "$BACKUP"
fi
