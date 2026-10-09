# Mac-specific environment, shared by login and interactive Zsh.
# Atuin reads the linked XDG config; older shells may export this legacy path.
unset ATUIN_CONFIG_DIR
_path_append "/Applications/ShellHistory.app/Contents/Helpers" "/Applications/Visual Studio Code.app/Contents/Resources/app/bin"
_path_prepend "/opt/homebrew/opt/llvm/bin" "/opt/homebrew/opt/openjdk@17/bin" "$HOME/.venv-vllm-metal/bin"
export GOBIN="$GOPATH/bin"
export MICRO_TRUECOLOR=1
export HOMEBREW_NO_ANALYTICS=1
export HOMEBREW_NO_ENV_HINTS=1
[[ -t 0 ]] && export GPG_TTY="$(tty)"
_op_agent="$HOME/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
[[ -S "$_op_agent" ]] && export SSH_AUTH_SOCK="$_op_agent"
unset _op_agent
