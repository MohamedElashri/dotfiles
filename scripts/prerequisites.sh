#!/usr/bin/env bash
# First-stage setup: runs before Python exists; compatible with macOS Bash 3.2.
set -euo pipefail
dry=0
system=$(uname -s)
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run) dry=1 ;;
    --platform) shift; case "${1:-}" in mac) system=Darwin ;; linux) system=Linux ;; *) exit 2 ;; esac ;;
    *) echo "Unknown prerequisite option: $1" >&2; exit 2 ;;
  esac
  shift
done
run() {
  if [ "$dry" = 1 ]; then printf 'Would run:'; printf ' %q' "$@"; printf '\n'; else "$@"; fi
}
fail() { echo "dotfiles: $*" >&2; exit 1; }
if [ "$dry" = 0 ]; then
  [ "$(id -u)" != 0 ] || fail 'Run bootstrap as your normal user, not root or sudo.'
  [ "$system" = "$(uname -s)" ] || fail '--platform may target another OS only with --dry-run.'
fi
case "$system" in
  Linux)
    # /etc/os-release is supplied by the OS, not by the checkout.
    # shellcheck disable=SC1091
    if [ -r /etc/os-release ]; then . /etc/os-release; else ID=debian; ID_LIKE=; fi
    case " $ID ${ID_LIKE:-} " in
      *' debian '*|*' ubuntu '*) manager=apt ;;
      *' fedora '*) manager=dnf ;;
      *) fail 'Automatic prerequisites support Debian/Ubuntu derivatives and Fedora. Use --skip-packages with preinstalled tools on other distributions.' ;;
    esac
    missing=0
    for tool in gcc make curl git file ps python3 fc-cache ssh; do command -v "$tool" >/dev/null 2>&1 || missing=1; done
    # Preview conservatively includes prerequisites without launching Python.
    # Apple's Python launcher can create HOME/Library even for a version probe.
    if [ "$dry" = 1 ] || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))' >/dev/null 2>&1; then missing=1; fi
    if [ "$missing" = 1 ]; then
      if [ "$manager" = apt ]; then
        run sudo apt-get update
        run sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y build-essential procps curl file git python3 ca-certificates fontconfig openssh-client
      else
        run sudo dnf install -y gcc gcc-c++ make procps-ng curl file git python3 ca-certificates fontconfig openssh-clients
      fi
    fi
    ;;
  Darwin)
    if ! xcode-select -p >/dev/null 2>&1; then
      # The same softwareupdate discovery used by Homebrew's official installer.
      marker=/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress
      if [ "$dry" = 1 ]; then
        echo 'Would discover and install Apple Command Line Tools with softwareupdate.'
      else
        [ ! -L "$marker" ] || fail 'The Apple CLT marker is a symlink; reconcile it before setup.'
        created=0
        if [ ! -e "$marker" ]; then sudo touch "$marker"; created=1; fi
        cleanup() { if [ "$created" = 1 ]; then sudo rm -f "$marker"; fi; }
        trap cleanup EXIT
        label=$(softwareupdate --list 2>/dev/null | sed -n 's/.*Label: \(Command Line Tools.*\)/\1/p' | sort -V | tail -n 1)
        [ -n "$label" ] || fail 'Apple offers no Command Line Tools update. Install Xcode/CLT and rerun bootstrap.'
        sudo softwareupdate --install "$label"
        cleanup
        trap - EXIT
        xcode-select -p >/dev/null 2>&1 || sudo xcode-select --switch /Library/Developer/CommandLineTools
      fi
    fi
    ;;
  *) fail "Unsupported OS: $system" ;;
esac
brew=
if [ "$system" = "$(uname -s)" ]; then
  brew=$(command -v brew || true)
  if [ -z "$brew" ]; then
    for prefix in /opt/homebrew /home/linuxbrew/.linuxbrew /usr/local; do
      if [ -x "$prefix/bin/brew" ]; then brew=$prefix/bin/brew; break; fi
    done
  fi
fi
if [ -z "$brew" ]; then
  if [ "$dry" = 0 ] && [ "$system" = Darwin ] && [ "$(uname -m)" != arm64 ]; then
    fail 'The pinned Homebrew installer requires Apple Silicon. Keep an existing Intel Homebrew installation or provision packages separately.'
  fi
  url=https://raw.githubusercontent.com/Homebrew/install/e5b3c5834e3932c8aaa42deef4794076c9b0cbf0/install.sh
  if [ "$dry" = 1 ]; then
    echo "Would download, SHA-256 verify, and run the pinned Homebrew installer: $url"
  else
    sudo -v
    temporary=$(mktemp -d)
    trap 'rm -rf "$temporary"' EXIT
    curl --fail --location --retry 2 --output "$temporary/install.sh" "$url"
    expected=5f333bbe53bc490e51e7ccb1df8779b3dd6ee73a1a7379efda216edb08ccb148
    if command -v sha256sum >/dev/null 2>&1; then
      actual=$(sha256sum "$temporary/install.sh"); actual=${actual%% *}
    else
      actual=$(shasum -a 256 "$temporary/install.sh"); actual=${actual%% *}
    fi
    [ "$actual" = "$expected" ] || fail 'Homebrew installer checksum mismatch; nothing executed.'
    NONINTERACTIVE=1 /bin/bash "$temporary/install.sh"
    rm -rf "$temporary"
    trap - EXIT
  fi
fi
