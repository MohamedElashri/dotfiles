# Compatibility wrapper for older installs that source ~/aliases.zsh.

_dotfiles_zsh_dir="${DOTFILES_ZSH_DIR:-$HOME/.config/dotfiles/zsh}"
if [[ ! -d "$_dotfiles_zsh_dir/aliases" ]]; then
  _dotfiles_zsh_dir="${${(%):-%N}:A:h}"
fi

for _dotfiles_alias_file in "$_dotfiles_zsh_dir"/aliases/*.zsh(N); do
  source "$_dotfiles_alias_file"
done

unset _dotfiles_alias_file _dotfiles_zsh_dir
