# ~/.zprofile: zsh login-shell setup.
#
# Login shells need PATH/toolchain variables even when they are not
# interactive. Interactive hooks stay in .zshrc.

[[ -r "$HOME/environment.zsh" ]] && source "$HOME/environment.zsh"

# Added by Toolbox App.
if [[ -d "$HOME/.local/share/JetBrains/Toolbox/scripts" ]]; then
  if typeset -f _path_append >/dev/null 2>&1; then
    _path_append "$HOME/.local/share/JetBrains/Toolbox/scripts"
  else
    export PATH="$PATH:$HOME/.local/share/JetBrains/Toolbox/scripts"
  fi
fi

# nvm is lazy-loaded from environment.zsh. This keeps login startup fast while
# preserving the nvm/node/npm commands once they are used.

unset -f _path_prepend _path_append _pathvar_prepend 2>/dev/null

# # Added by `rbenv init` on Mon Jan 26 04:30:48 PM CET 2026
# eval "$(rbenv init - --no-rehash zsh)"
