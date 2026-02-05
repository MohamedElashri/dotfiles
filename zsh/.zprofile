export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" # This loads nvm

# Added by Toolbox App
export PATH="$PATH:/home/melashri/.local/share/JetBrains/Toolbox/scripts"


# Added by `rbenv init` on Mon Jan 26 04:30:48 PM CET 2026
eval "$(rbenv init - --no-rehash zsh)"
