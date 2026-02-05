################################## ME dotfiles ##################################



## System Information
alias showdate='echo "Today is $(date)"'
alias printdir='echo "The current directory is: $(pwd)"'
alias listfiles='echo "The files in this directory are: $(ls)"'
alias showcpu='echo "The current CPU usage is: $(mpstat 1 1 | awk '\''/all/ {print 100 - $NF "%"}'\'')"'
alias showmem='echo "The current memory usage is: $(awk '"'"'/MemTotal|MemAvailable/{if ($1=="MemTotal:") total=$2; else if ($1=="MemAvailable:") available=$2} END{printf "%.2f%% used", (total-available)/total*100}'"'"' /proc/meminfo)"'
alias showdisk='echo "The disk usage is: $(df -h | awk '\''$NF=="/"{print $5}'\'')"'
alias mycpu='echo "Your current CPU usage is: $(ps -u $USER -o %cpu= | awk '\''{sum+=$1} END {printf "%.2f%%", sum}'\'')"'

## File and Directory Management
alias ll='ls -l'
alias la='ls -la'
alias ..='cd ..'
alias l.='ls -d .* --color=auto'
alias mkdir='mkdir -p'
alias t='tree -L 1'


## Exit commands
alias :q='exit'
alias ext='exit'
alias xt='exit'
alias by='exit'
alias bye='exit'
alias die='exit'
alias quit='exit'


## Local HEP
alias mount_gpu='sshfs melashri@gpu:~/inference-engine $HOME/projects/lhcb/inference-engine -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=3,cache=no,uid=$(id -u),gid=$(id -g)'


## File Viewing and Editing
alias zshrc='cat ~/.zshrc'
alias nano='micro'
alias zshconfig='nano ~/.zshrc'
alias edit_zsh='vim ~/.zshrc' # Use vim as the default editor
alias edit_zsh_code='code -r ~/.zshrc' # Edit with VSCode
alias edit_zsh_insiders='code-insiders -r ~/.zshrc' # Edit with VSCode Insiders
alias vim_rc='vim ~/.vimrc' # Quick access to vim config
alias edit_host='sudo nano /etc/hosts'
alias edit_nano='nano ~/.nanorc'
alias vim_install='vim +PluginInstall +qall' # Install vim packages through vundle
alias vim='nvim'
alias vi='vim' # Set vi to open vim


## Process Management
alias process='ps aux'
alias process_user='ps -u $USER'
alias psa='ps -ef'
alias psf='ps auxf'

## System Commands
alias grep='grep --color=auto'
alias rm='rm -i'
alias h='history'
alias du='du -h'
alias df='df -h'
alias reload='source ~/.zshrc'
alias which='type -a'
alias c='clear'
alias free='free -m'

## Tmux
alias tmux_new='tmux new -s' # new session by name by default
alias tmux_attach='tmux a -t' # attach by name by default
alias tmux_list='tmux ls' # list the active session
alias tmux_kill='tmux kill-session -t'
alias tmux_kill_all='pkill -f tmux' # kill all tmux processes

## Utilities
alias lt='ls --human-readable --size -1 -S --classify'
alias ghist='history|grep' # find command in history
alias count='find . -type f | wc -l' # count how many files in a directory
alias cpv='rsync -ah --info=progress2' # copy progress bar
alias restart_shell="exec ${SHELL} -l"
alias path='echo -e ${PATH//:/\\n}'
alias h='history'
alias j='jobs -l'
alias e='exit'
alias stats='zsh_stats'
alias mount='mount |column -t'


## Network
alias ping='ping -c 5'
alias wget='wget -c'
alias ports='netstat -tulanp'
alias myip='curl ifconfig.me && echo'


## Github Copilot
alias copilot='gh copilot'
alias explain='gh copilot explain'
alias suggest='gh copilot suggest'


### Misc ###
alias weather_cincy="curl https://wttr.in/Cincinnati | head -7" 
alias weather_home="curl https://wttr.in/Al+Mansurah,+Egypt | head -7" 
alias weather_cern="curl https://wttr.in/Geneva | head -7"
alias emergency="gh emergency"
alias depressed="gh emergency"
alias tired="gh emergency"
alias fix-docker='exec newgrp docker'

################################## ME dotfiles ##################################
