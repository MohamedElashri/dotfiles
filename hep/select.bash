# Select per shell, so one shared home works across different login nodes.
_dotfiles_host=${DOTFILES_MACHINE:-$(hostname -s)}
case "$_dotfiles_host" in
  lxplus*) _dotfiles_host=lxplus ;;
  sneezy|sleepy|gpu_farm) ;;
  *) _dotfiles_host= ;;
esac
if [ -n "$_dotfiles_host" ]; then
  . "$DOTFILES_ROOT/hep/$_dotfiles_host.bash"
fi
unset _dotfiles_host
