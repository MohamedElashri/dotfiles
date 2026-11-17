# Compatibility entry point; portable helpers live under shell/functions/.
: "${DOTFILES_ROOT:=${${${(%):-%N}:A}:h:h}}"
source "$DOTFILES_ROOT/shell/functions.sh"
