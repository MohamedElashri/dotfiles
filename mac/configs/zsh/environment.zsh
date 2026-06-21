# Compatibility wrapper for older installs that source ~/environment.zsh.

_dotfiles_zsh_dir="${DOTFILES_ZSH_DIR:-$HOME/.config/dotfiles/zsh}"
if [[ ! -d "$_dotfiles_zsh_dir/core" ]]; then
  _dotfiles_zsh_dir="${${(%):-%N}:A:h}"
fi

[[ -r "$_dotfiles_zsh_dir/core/00-path.zsh" ]] && source "$_dotfiles_zsh_dir/core/00-path.zsh"

unset _dotfiles_zsh_dir
