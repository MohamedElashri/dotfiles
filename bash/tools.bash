# Optional Bash tool initialization; PATH is set in shell/env.sh.

[ -r "$HOME/.cargo/env" ] && . "$HOME/.cargo/env"
[ -r "$HOME/.atuin/bin/env" ] && . "$HOME/.atuin/bin/env"

# Atuin's bash hook relies on preexec support and is only useful in a real
# terminal. The guard avoids stty noise for scripted `bash -i -c ...` runs.
if [ -t 0 ]; then
    [ -r "$HOME/.bash-preexec.sh" ] && . "$HOME/.bash-preexec.sh"
    if command -v atuin >/dev/null 2>&1; then
        eval "$(atuin init bash)"
    fi
fi

return 0
