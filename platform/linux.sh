# Linux-specific interactive aliases.
alias l.='ls -d .* --color=auto'
alias lt='ls --human-readable --size -1 -S --classify'
alias cpv='rsync -ah --info=progress2'
alias ports='netstat -tulanp'
alias mount_gpu='sshfs melashri@gpu:~/inference-engine $HOME/projects/lhcb/inference-engine -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=3,cache=no,uid=$(id -u),gid=$(id -g)'
alias showmem='echo "The current memory usage is: $(awk '"'"'/MemTotal|MemAvailable/{if ($1=="MemTotal:") total=$2; else if ($1=="MemAvailable:") available=$2} END{printf "%.2f%% used", (total-available)/total*100}'"'"' /proc/meminfo)"'
alias psf='ps auxf'
alias free='free -m'
alias fix-docker='exec newgrp docker'
alias open='xdg-open'
if [ -r /proc/version ] && command grep -qi microsoft /proc/version; then
  alias open='explorer.exe'
fi
