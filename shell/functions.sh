# Shared Bash/Zsh functions, grouped by purpose. Loading performs no remote actions.
for _dotfiles_group in archives files development docker network system; do
  # shellcheck source=/dev/null
  . "$DOTFILES_ROOT/shell/functions/$_dotfiles_group.sh" || return
done
unset _dotfiles_group
