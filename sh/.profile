# ~/.profile: POSIX login-shell setup.
#
# This file is not read by bash(1) when ~/.bash_profile or ~/.bash_login exists.
# Keep this file portable: bash-only interactive hooks belong in .bashrc.

# the default umask is set in /etc/profile; for setting the umask
# for ssh logins, install and configure the libpam-umask package.
#umask 022

path_prepend() {
    [ -d "$1" ] || return
    case ":$PATH:" in
        *:"$1":*) ;;
        *) PATH="$1:$PATH" ;;
    esac
}

# User-local and toolchain command paths for login shells.
path_prepend "$HOME/bin"
path_prepend "$HOME/.local/bin"
path_prepend "$HOME/.cargo/bin"
path_prepend "$HOME/.atuin/bin"
path_prepend "$HOME/.pixi/bin"
export PATH

unset -f path_prepend 2>/dev/null || unset path_prepend

# If this login shell is bash, include the interactive bash setup when present.
if [ -n "$BASH_VERSION" ] && [ -f "$HOME/.bashrc" ]; then
    . "$HOME/.bashrc"
fi
