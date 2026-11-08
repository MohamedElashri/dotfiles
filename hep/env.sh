# shellcheck shell=sh
# HEP_ROOT is set by this directory's .bashrc/.profile.
for _hep_bin in "$HOME/.local/bin" "$HOME/bin"; do
  [ -d "$_hep_bin" ] || continue
  case ":$PATH:" in *:"$_hep_bin":*) ;; *) PATH="$_hep_bin:$PATH" ;; esac
done
# Expose the optional dotfiles CLI only when the full checkout is present.
if [ -f "$HEP_ROOT/../setup/profiles/hep" ] && [ -x "$HEP_ROOT/../bin/dotfiles" ]; then
  DOTFILES_ROOT=$(cd -P "$HEP_ROOT/.." && pwd)
  export DOTFILES_ROOT
  case ":$PATH:" in *:"$DOTFILES_ROOT/bin":*) ;; *) PATH="$DOTFILES_ROOT/bin:$PATH" ;; esac
fi
export PATH
unset _hep_bin
