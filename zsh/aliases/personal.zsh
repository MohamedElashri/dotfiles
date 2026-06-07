# Personal and host-specific aliases that are safe to share in this repo.

alias mount_gpu='sshfs melashri@gpu:~/inference-engine $HOME/projects/lhcb/inference-engine -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=3,cache=no,uid=$(id -u),gid=$(id -g)'
alias emergency='gh emergency'
alias depressed='gh emergency'
alias tired='gh emergency'
