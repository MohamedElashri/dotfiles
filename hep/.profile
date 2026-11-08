# shellcheck shell=sh disable=SC1091
# POSIX login environment for a standalone HEP checkout.
_hep_file="$HOME/.profile"
while [ -L "$_hep_file" ]; do
  _hep_dir=$(cd -P "$(dirname "$_hep_file")" && pwd)
  _hep_file=$(readlink "$_hep_file")
  case $_hep_file in /*) ;; *) _hep_file=$_hep_dir/$_hep_file ;; esac
done
HEP_ROOT=$(cd -P "$(dirname "$_hep_file")" && pwd)
export HEP_ROOT
unset _hep_file _hep_dir
. "$HEP_ROOT/env.sh"
if [ -n "${BASH_VERSION:-}" ] && [ -r "$HOME/.bashrc" ]; then
  . "$HOME/.bashrc"
fi
