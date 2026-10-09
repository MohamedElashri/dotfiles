# Editors and config shortcuts.

alias zshrc='cat ~/.zshrc'
alias nano='micro'
alias zshconfig='nano ~/.zshrc'
alias edit_zsh='vim ~/.zshrc'
alias edit_zsh_code='code -r ~/.zshrc'
(( $+commands[code-insiders] )) && alias edit_zsh_insiders='code-insiders -r ~/.zshrc'
alias vim_rc='vim ~/.vimrc'
alias edit_host='sudo nano /etc/hosts'
alias edit_nano='nano ~/.nanorc'
[[ -d "$HOME/.vim/bundle/Vundle.vim" ]] && alias vim_install='vim +PluginInstall +qall'
alias vim='nvim'
alias vi='vim'

# File and directory aliases.

alias mount='mount |column -t'

# GitHub CLI helpers.

alias copilot='gh copilot'
alias explain='gh copilot explain'
alias suggest='gh copilot suggest'

# Network aliases.

alias weather_cincy="curl https://wttr.in/Cincinnati | head -7"
alias weather_home="curl https://wttr.in/Al+Mansurah,+Egypt | head -7"
alias weather_cern="curl https://wttr.in/Geneva | head -7"

# Personal and host-specific aliases that are safe to share in this repo.

alias emergency='gh emergency'
alias depressed='gh emergency'
alias tired='gh emergency'

# Shell convenience aliases.

alias :q='exit'
alias ext='exit'
alias xt='exit'
alias by='exit'
alias bye='exit'
alias die='exit'
alias quit='exit'
alias e='exit'
alias h='history'
alias ghist='history|grep'
alias reload='source ~/.zshrc'
alias restart_shell="exec ${SHELL} -l"
alias path='echo -e ${PATH//:/\\n}'
alias j='jobs -l'

# System and process aliases.

alias showdate='echo "Today is $(date)"'
alias printdir='echo "The current directory is: $(pwd)"'
alias listfiles='echo "The files in this directory are: $(ls)"'
(( $+commands[mpstat] )) && alias showcpu='echo "The current CPU usage is: $(mpstat 1 1 | awk '\''/all/ {print 100 - $NF "%"}'\'')"'
alias showdisk='echo "The disk usage is: $(df -h | awk '\''$NF=="/"{print $5}'\'')"'
alias mycpu='echo "Your current CPU usage is: $(ps -u $USER -o %cpu= | awk '\''{sum+=$1} END {printf "%.2f%%", sum}'\'')"'

alias process='ps aux'
alias process_user='ps -u $USER'
alias psa='ps -ef'
alias grep='grep --color=auto'
alias stats='zsh_stats'

# Tmux aliases.

alias tmux_kill_all='pkill -f tmux'

# Neovim configurations.
[[ -d "${XDG_CONFIG_HOME:-$HOME/.config}/LazyVim" ]] && alias nvim-lazy="NVIM_APPNAME=LazyVim nvim"
[[ -d "${XDG_CONFIG_HOME:-$HOME/.config}/kickstart" ]] && alias nvim-kick="NVIM_APPNAME=kickstart nvim"
[[ -d "${XDG_CONFIG_HOME:-$HOME/.config}/NvChad" ]] && alias nvim-chad="NVIM_APPNAME=NvChad nvim"
[[ -d "${XDG_CONFIG_HOME:-$HOME/.config}/AstroNvim" ]] && alias nvim-astro="NVIM_APPNAME=AstroNvim nvim"
