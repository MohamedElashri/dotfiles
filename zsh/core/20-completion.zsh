# Completion paths that must be set before Oh My Zsh runs compinit.

if [[ -d "$HOME/.zfunc" ]]; then
  fpath=("$HOME/.zfunc" "${fpath[@]}")
fi
