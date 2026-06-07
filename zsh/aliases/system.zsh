# System and process aliases.

alias showdate='echo "Today is $(date)"'
alias printdir='echo "The current directory is: $(pwd)"'
alias listfiles='echo "The files in this directory are: $(ls)"'
alias showcpu='echo "The current CPU usage is: $(mpstat 1 1 | awk '\''/all/ {print 100 - $NF "%"}'\'')"'
alias showmem='echo "The current memory usage is: $(awk '"'"'/MemTotal|MemAvailable/{if ($1=="MemTotal:") total=$2; else if ($1=="MemAvailable:") available=$2} END{printf "%.2f%% used", (total-available)/total*100}'"'"' /proc/meminfo)"'
alias showdisk='echo "The disk usage is: $(df -h | awk '\''$NF=="/"{print $5}'\'')"'
alias mycpu='echo "Your current CPU usage is: $(ps -u $USER -o %cpu= | awk '\''{sum+=$1} END {printf "%.2f%%", sum}'\'')"'

alias process='ps aux'
alias process_user='ps -u $USER'
alias psa='ps -ef'
alias psf='ps auxf'
alias grep='grep --color=auto'
alias rm='rm -i'
alias free='free -m'
alias stats='zsh_stats'
alias fix-docker='exec newgrp docker'
