# Atuin history integration.

[[ -r "$HOME/.atuin/bin/env" ]] && source "$HOME/.atuin/bin/env"

if command -v atuin >/dev/null 2>&1; then
  eval "$(atuin init zsh)"
fi
