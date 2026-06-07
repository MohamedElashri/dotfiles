#!/usr/bin/env bash

# Bootstrap this dotfiles repo on a Linux machine.
#
# Default behavior:
#   - install base dependencies when a known package manager is available
#   - restore dotfiles as symlinks into $HOME
#   - skip optional tools unless --optional-tools is passed

set -euo pipefail

COLOR_RED="\033[0;31m"
COLOR_GREEN="\033[0;32m"
COLOR_YELLOW="\033[0;33m"
COLOR_BLUE="\033[0;34m"
COLOR_RESET="\033[0m"

log_info()    { echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $1"; }
log_warn()    { echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $1"; }
log_error()   { echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"; }
log_success() { echo -e "${COLOR_GREEN}[OK]${COLOR_RESET} $1"; }

INSTALL_PACKAGES=1
INSTALL_OPTIONAL_TOOLS=0
RUN_RESTORE=1
RESTORE_MODE="link"
ASSUME_YES=0
DRY_RUN=0

BASE_PACKAGES=(curl git rsync zsh)

usage() {
    cat <<'EOF'
Usage: ./bootstrap.sh [OPTIONS]

Options:
  --optional-tools  Install Oh My Zsh, Starship, Atuin, and Rust when missing.
  --no-packages     Do not install package-manager dependencies.
  --no-restore      Do not run ./restore.
  --link            Restore dotfiles as symlinks. This is the default.
  --copy            Restore dotfiles as copies instead of symlinks.
  -y, --yes         Do not prompt.
  -n, --dry-run     Show what would run without changing files.
  -h, --help        Show this help.
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --optional-tools|--tools)
                INSTALL_OPTIONAL_TOOLS=1
                ;;
            --no-packages)
                INSTALL_PACKAGES=0
                ;;
            --no-restore)
                RUN_RESTORE=0
                ;;
            --link)
                RESTORE_MODE="link"
                ;;
            --copy)
                RESTORE_MODE="copy"
                ;;
            -y|--yes)
                ASSUME_YES=1
                ;;
            -n|--dry-run)
                DRY_RUN=1
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 2
                ;;
        esac
        shift
    done
}

confirm() {
    local message="$1"

    if [[ "$ASSUME_YES" -eq 1 ]]; then
        return 0
    fi

    if [[ ! -t 0 ]]; then
        log_warn "No terminal available for prompt: $message"
        return 1
    fi

    local reply
    read -rp "$(echo -e "${COLOR_YELLOW}[?]${COLOR_RESET} $message (y/N): ")" reply
    [[ "$reply" =~ ^[Yy]$ ]]
}

run() {
    if [[ "$DRY_RUN" -eq 1 ]]; then
        printf 'DRY-RUN:'
        printf ' %q' "$@"
        printf '\n'
    else
        "$@"
    fi
}

run_script() {
    local description="$1"
    local script="$2"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        printf 'DRY-RUN: %s\n' "$description"
    else
        bash -c "$script"
    fi
}

as_root() {
    if [[ "$EUID" -eq 0 ]]; then
        run "$@"
    elif command -v sudo >/dev/null 2>&1; then
        run sudo "$@"
    else
        log_warn "sudo is not available; cannot run as root: $*"
        return 127
    fi
}

detect_package_manager() {
    if command -v apt-get >/dev/null 2>&1; then
        echo apt
    elif command -v dnf >/dev/null 2>&1; then
        echo dnf
    elif command -v pacman >/dev/null 2>&1; then
        echo pacman
    elif command -v zypper >/dev/null 2>&1; then
        echo zypper
    elif command -v apk >/dev/null 2>&1; then
        echo apk
    elif command -v brew >/dev/null 2>&1; then
        echo brew
    else
        echo none
    fi
}

install_base_packages() {
    local manager
    manager="$(detect_package_manager)"

    if [[ "$manager" == "none" ]]; then
        log_warn "No supported package manager detected. Install manually: ${BASE_PACKAGES[*]}"
        return 0
    fi

    confirm "Install base packages with $manager: ${BASE_PACKAGES[*]}" || {
        log_info "Skipped package installation."
        return 0
    }

    if [[ "$manager" != "brew" && "$EUID" -ne 0 ]] && ! command -v sudo >/dev/null 2>&1; then
        log_warn "Package manager '$manager' requires root privileges, but sudo is missing. Skipping packages."
        return 0
    fi

    case "$manager" in
        apt)
            as_root apt-get update
            as_root apt-get install -y "${BASE_PACKAGES[@]}"
            ;;
        dnf)
            as_root dnf install -y "${BASE_PACKAGES[@]}"
            ;;
        pacman)
            as_root pacman -Sy --needed --noconfirm "${BASE_PACKAGES[@]}"
            ;;
        zypper)
            as_root zypper install -y "${BASE_PACKAGES[@]}"
            ;;
        apk)
            as_root apk add "${BASE_PACKAGES[@]}"
            ;;
        brew)
            run brew install "${BASE_PACKAGES[@]}"
            ;;
    esac
}

need_command() {
    local command_name="$1"
    command -v "$command_name" >/dev/null 2>&1
}

install_oh_my_zsh() {
    if [[ -r "$HOME/.oh-my-zsh/oh-my-zsh.sh" ]]; then
        log_success "Oh My Zsh already installed."
        return 0
    fi

    if ! need_command curl; then
        log_warn "curl is missing; skipping Oh My Zsh install."
        return 0
    fi

    confirm "Install Oh My Zsh" || return 0
    run_script \
        "sh -c \"\$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)\" \"\" --unattended" \
        'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended'
}

install_starship() {
    if need_command starship; then
        log_success "Starship already installed."
        return 0
    fi

    if ! need_command curl; then
        log_warn "curl is missing; skipping Starship install."
        return 0
    fi

    confirm "Install Starship" || return 0
    run_script \
        "curl -sS https://starship.rs/install.sh | sh -s -- -y" \
        'curl -sS https://starship.rs/install.sh | sh -s -- -y'
}

install_atuin() {
    if need_command atuin || [[ -r "$HOME/.atuin/bin/env" ]]; then
        log_success "Atuin already installed."
        return 0
    fi

    if ! need_command curl; then
        log_warn "curl is missing; skipping Atuin install."
        return 0
    fi

    confirm "Install Atuin" || return 0
    run_script \
        "curl https://raw.githubusercontent.com/atuinsh/atuin/main/install.sh | bash" \
        'curl https://raw.githubusercontent.com/atuinsh/atuin/main/install.sh | bash'
}

install_rust() {
    if need_command cargo; then
        log_success "Rust/Cargo already installed."
        return 0
    fi

    if ! need_command curl; then
        log_warn "curl is missing; skipping Rust install."
        return 0
    fi

    confirm "Install Rust via rustup" || return 0
    run_script \
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y" \
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"
}

install_optional_tools() {
    install_oh_my_zsh
    install_starship
    install_atuin
    install_rust
}

run_restore() {
    local repo_root="$1"
    local restore_args=("--$RESTORE_MODE")

    [[ "$ASSUME_YES" -eq 1 ]] && restore_args+=(--yes)
    [[ "$DRY_RUN" -eq 1 ]] && restore_args+=(--dry-run)

    if [[ "$DRY_RUN" -eq 1 ]]; then
        "$repo_root/restore" "${restore_args[@]}"
    else
        run "$repo_root/restore" "${restore_args[@]}"
    fi
}

main() {
    parse_args "$@"

    local repo_root
    repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    log_info "Repo root: $repo_root"
    [[ "$DRY_RUN" -eq 1 ]] && log_warn "Dry run only; no files will be changed."

    if [[ "$INSTALL_PACKAGES" -eq 1 ]]; then
        install_base_packages
    fi

    if [[ "$INSTALL_OPTIONAL_TOOLS" -eq 1 ]]; then
        install_optional_tools
    else
        log_info "Skipping optional tool installers. Use --optional-tools to enable them."
    fi

    if [[ "$RUN_RESTORE" -eq 1 ]]; then
        run_restore "$repo_root"
    fi

    log_success "Bootstrap complete."
}

main "$@"
