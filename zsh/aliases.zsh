# Zsh-only interactive helpers. Shared aliases live in shell/aliases.sh.
alias reload='source ~/.zshrc'
(( $+functions[zsh_stats] )) && alias stats='zsh_stats'
return 0
