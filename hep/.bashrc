# shellcheck shell=bash disable=SC1091
# Bash-only cluster startup; every required source lives beside this file.
case $- in *i*) ;; *) return 0 ;; esac
_hep_file=${BASH_SOURCE[0]}
while [ -L "$_hep_file" ]; do
  _hep_dir=$(cd -P "$(dirname "$_hep_file")" && pwd)
  _hep_file=$(readlink "$_hep_file")
  case $_hep_file in /*) ;; *) _hep_file=$_hep_dir/$_hep_file ;; esac
done
HEP_ROOT=$(cd -P "$(dirname "$_hep_file")" && pwd)
export HEP_ROOT
unset _hep_file _hep_dir
[ -r "$HOME/.config/dotfiles/site.bash" ] && . "$HOME/.config/dotfiles/site.bash"
. "$HEP_ROOT/env.sh"
. "$HEP_ROOT/common.bash"
. "$HEP_ROOT/select.bash"
[ -r "$HOME/.config/dotfiles/local.bash" ] && . "$HOME/.config/dotfiles/local.bash"
return 0
