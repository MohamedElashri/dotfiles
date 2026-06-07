# File and directory aliases.

alias ll='ls -l'
alias la='ls -la'
alias ..='cd ..'
alias l.='ls -d .* --color=auto'
alias mkdir='mkdir -p'
alias t='tree -L 1'
alias lt='ls --human-readable --size -1 -S --classify'
alias count='find . -type f | wc -l'
alias cpv='rsync -ah --info=progress2'
alias du='du -h'
alias df='df -h'
alias mount='mount |column -t'
