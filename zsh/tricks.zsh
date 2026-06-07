# Compatibility wrapper for older installs that source ~/tricks.zsh.

_dotfiles_zsh_dir="${DOTFILES_ZSH_DIR:-$HOME/.config/dotfiles/zsh}"
if [[ ! -d "$_dotfiles_zsh_dir/functions" ]]; then
  _dotfiles_zsh_dir="${${(%):-%N}:A:h}"
fi

[[ -r "$_dotfiles_zsh_dir/functions/tricks.zsh" ]] && source "$_dotfiles_zsh_dir/functions/tricks.zsh"

unset _dotfiles_zsh_dir
