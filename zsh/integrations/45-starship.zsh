# Starship prompt. Load after Oh My Zsh so Starship owns the prompt.

if command -v starship >/dev/null 2>&1; then
  eval "$(starship init zsh)"
fi
