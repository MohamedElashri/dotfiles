# Compatibility wrapper for older installs that source ~/m_nvim.zsh.

_dotfiles_zsh_dir="${DOTFILES_ZSH_DIR:-$HOME/.config/dotfiles/zsh}"
if [[ ! -d "$_dotfiles_zsh_dir/integrations" ]]; then
  _dotfiles_zsh_dir="${${(%):-%N}:A:h}"
fi

[[ -r "$_dotfiles_zsh_dir/integrations/50-neovim.zsh" ]] && source "$_dotfiles_zsh_dir/integrations/50-neovim.zsh"

unset _dotfiles_zsh_dir
