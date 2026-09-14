# POSIX login environment. Existing site login files are not replaced.
_dotfiles_file="$HOME/.profile"
while [ -L "$_dotfiles_file" ]; do
  _dotfiles_dir=$(cd -P "$(dirname "$_dotfiles_file")" && pwd)
  _dotfiles_file=$(readlink "$_dotfiles_file")
  case $_dotfiles_file in /*) ;; *) _dotfiles_file=$_dotfiles_dir/$_dotfiles_file ;; esac
done
DOTFILES_ROOT=$(cd -P "$(dirname "$_dotfiles_file")/.." && pwd)
export DOTFILES_ROOT
unset _dotfiles_file _dotfiles_dir
. "$DOTFILES_ROOT/shell/env.sh"
if [ -n "${BASH_VERSION:-}" ] && [ -r "$HOME/.bashrc" ]; then
  . "$HOME/.bashrc"
fi
