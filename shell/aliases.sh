# Portable aliases shared by interactive Bash and Zsh.
alias ll='ls -l'
alias la='ls -la'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'
alias -- -='cd -'
alias github='cd "$HOME/projects/github"'
alias lhcb='cd "$HOME/projects/lhcb"'
alias cern='cd "$HOME/projects/cern"'
alias doc='cd "$HOME/Documents"'
alias ds='cd "$HOME/.ssh"'
alias dz='cd "$DOTFILES_ROOT"'
alias de='cd "$HOME/Desktop"'
alias dq='cd "$HOME/Downloads"'
alias mkdir='mkdir -p'
alias t='tree -L 1'
alias count='find . -type f | wc -l'
alias du='du -h'
alias df='df -h'
alias ping='ping -c 5'
alias wget='wget -c'
alias myip='curl ifconfig.me && echo'
alias c='clear'
alias which='type -a'
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'
alias ln='ln -i'
alias tmux_new='tmux new -s'
alias tmux_attach='tmux a -t'
alias tmux_list='tmux ls'
alias tmux_kill='tmux kill-session -t'

if command -v bat >/dev/null 2>&1; then
  alias cat='bat'
elif command -v batcat >/dev/null 2>&1; then
  alias cat='batcat'
fi
if command -v dust >/dev/null 2>&1; then
  alias du='dust'
fi
if command -v duf >/dev/null 2>&1; then
  alias df='duf'
fi
if command -v colordiff >/dev/null 2>&1; then
  alias diff='colordiff'
fi
