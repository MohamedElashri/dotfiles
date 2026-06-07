# Compatibility wrapper for older installs that source ~/functions.zsh.

_dotfiles_zsh_dir="${DOTFILES_ZSH_DIR:-$HOME/.config/dotfiles/zsh}"
if [[ ! -d "$_dotfiles_zsh_dir/functions" ]]; then
  _dotfiles_zsh_dir="${${(%):-%N}:A:h}"
fi

[[ -r "$_dotfiles_zsh_dir/integrations/10-conda.zsh" ]] && source "$_dotfiles_zsh_dir/integrations/10-conda.zsh"

for _dotfiles_function_file in "$_dotfiles_zsh_dir"/functions/*.zsh(N); do
  source "$_dotfiles_function_file"
done

unset _dotfiles_function_file _dotfiles_zsh_dir
