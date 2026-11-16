# Environment shared by Bash and Zsh. No interactive hooks here.
_dotfiles_prefix=${HOMEBREW_PREFIX-}
if [ -z "$_dotfiles_prefix" ] && ! command -v brew >/dev/null 2>&1; then
  for _dotfiles_candidate in /home/linuxbrew/.linuxbrew /opt/homebrew /usr/local; do
    if [ -x "$_dotfiles_candidate/bin/brew" ]; then _dotfiles_prefix=$_dotfiles_candidate; break; fi
  done
fi
if [ -n "$_dotfiles_prefix" ]; then
  for _dotfiles_bin in "$_dotfiles_prefix/sbin" "$_dotfiles_prefix/bin"; do
    [ -d "$_dotfiles_bin" ] || continue
    case ":$PATH:" in *:"$_dotfiles_bin":*) ;; *) PATH="$_dotfiles_bin:$PATH" ;; esac
  done
fi
unset _dotfiles_prefix _dotfiles_candidate
for _dotfiles_bin in "$HOME/bin" "$HOME/.local/bin" "$HOME/.cargo/bin" "$HOME/.atuin/bin" "$HOME/.pixi/bin" "$DOTFILES_ROOT/bin"; do
  [ -d "$_dotfiles_bin" ] || continue
  case ":$PATH:" in *:"$_dotfiles_bin":*) ;; *) PATH="$_dotfiles_bin:$PATH" ;; esac
done
export PATH
unset _dotfiles_bin
