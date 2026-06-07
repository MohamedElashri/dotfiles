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
alias c='clear'
alias which='type -a'
