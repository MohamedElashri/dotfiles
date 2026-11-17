# Linux-native command variants and integrations.
alias ls='ls --color=auto'
alias psf='ps auxf'
alias free='free -m'
alias fix-docker='exec newgrp docker'
alias open='xdg-open'
if [ -r /proc/version ] && command grep -qi microsoft /proc/version; then
  alias open='explorer.exe'
fi

unalias alert 2>/dev/null || true
if command -v notify-send >/dev/null 2>&1; then
# Add an "alert" alias for long running commands.  Use like so:
#   sleep 10; alert
alias alert='notify-send --urgency=low -i "$([ $? = 0 ] && echo terminal || echo error)" "$(history|tail -n1|sed -e '\''s/^\s*[0-9]\+\s*//;s/[;&|]\s*alert$//'\'')"'

fi
