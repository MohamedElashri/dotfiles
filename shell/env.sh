# Environment shared by Bash and Zsh. No interactive hooks here.
for _dotfiles_bin in "$HOME/bin" "$HOME/.local/bin" "$HOME/.cargo/bin" "$HOME/.atuin/bin" "$HOME/.pixi/bin" "$DOTFILES_ROOT/bin"; do
  [ -d "$_dotfiles_bin" ] || continue
  case ":$PATH:" in *:"$_dotfiles_bin":*) ;; *) PATH="$_dotfiles_bin:$PATH" ;; esac
done
export PATH
unset _dotfiles_bin
