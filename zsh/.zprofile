# Login environment only; interactive hooks belong in .zshrc.
export DOTFILES_ROOT="${${${(%):-%N}:A}:h:h}"
source "$DOTFILES_ROOT/shell/env.sh"
source "$DOTFILES_ROOT/zsh/environment.zsh"
_path_append "$HOME/.local/share/JetBrains/Toolbox/scripts" "$HOME/.opencode/bin"
return 0
