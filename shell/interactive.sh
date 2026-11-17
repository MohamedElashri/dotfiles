# One common CLI load order for interactive Bash and Zsh on both platforms.
. "$DOTFILES_ROOT/shell/aliases.sh" || return
. "$DOTFILES_ROOT/shell/functions.sh" || return
case "$(uname -s)" in
  Darwin) . "$DOTFILES_ROOT/platform/mac.sh" ;;
  Linux) . "$DOTFILES_ROOT/platform/linux.sh" ;;
esac
