# Core aliases shared by Bash/Zsh and Linux/macOS. Local overrides load last.

# Recheck capabilities on reload as well as first startup. Clear only aliases
# owned by this file; shell-local overrides are reapplied after the core loads.
_dotfiles_tool_alias() {
  unalias "$1" 2>/dev/null || true
  # Selected command strings are intentionally captured when the core loads.
  # shellcheck disable=SC2139
  if command -v "$2" >/dev/null 2>&1; then alias "$1=$3"; fi
}

# Navigation and listings. Platform adapters supply only native color flags.
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias l.='ls -d .*'
alias lt='ls -lhSF'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'
alias -- -='cd -'
alias github='cd "$HOME/projects/github"'
alias doc='cd "$HOME/Documents"'
alias ds='cd "$HOME/.ssh"'
alias dz='cd "$DOTFILES_ROOT"'
alias de='cd "$HOME/Desktop"'
alias dq='cd "$HOME/Downloads"'
alias mkdir='mkdir -p'
alias findgrep='GrePFind'

# Files and modern replacements. Native commands remain available via command.
alias du='du -h'
alias df='df -h'
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'
alias ln='ln -i'
_dotfiles_tool_alias t tree 'tree -L 1'
unalias cat 2>/dev/null || true
if command -v bat >/dev/null 2>&1; then
  alias cat='bat'
elif command -v batcat >/dev/null 2>&1; then
  alias cat='batcat'
fi
if command -v dust >/dev/null 2>&1; then alias du='dust'; fi
if command -v duf >/dev/null 2>&1; then alias df='duf'; fi
_dotfiles_tool_alias diff colordiff colordiff
_dotfiles_tool_alias cpv rsync 'rsync -ah --info=progress2'

# Editors and configuration shortcuts.
_dotfiles_tool_alias nano micro micro
_dotfiles_tool_alias vim nvim nvim
_dotfiles_tool_alias vi nvim nvim
alias zshrc='cat ~/.zshrc'
alias zshconfig='nano ~/.zshrc'
alias edit_zsh='vim ~/.zshrc'
alias vim_rc='vim ~/.vimrc'
alias edit_nano='nano ~/.nanorc'
_dotfiles_tool_alias edit_zsh_code code 'code -r ~/.zshrc'
_dotfiles_tool_alias edit_zsh_insiders code-insiders 'code-insiders -r ~/.zshrc'
unalias vim_install nvim-lazy nvim-kick nvim-chad nvim-astro 2>/dev/null || true
if [ -d "$HOME/.vim/bundle/Vundle.vim" ]; then alias vim_install='vim +PluginInstall +qall'; fi
if command -v nvim >/dev/null 2>&1; then
  for _dotfiles_editor in 'LazyVim:lazy' 'kickstart:kick' 'NvChad:chad' 'AstroNvim:astro'; do
    _dotfiles_config=${_dotfiles_editor%:*}
    if [ -d "${XDG_CONFIG_HOME:-$HOME/.config}/$_dotfiles_config" ]; then
      # Expand the selected fixed configuration now, not the loop variable later.
      # shellcheck disable=SC2139
      alias "nvim-${_dotfiles_editor#*:}=NVIM_APPNAME=$_dotfiles_config nvim"
    fi
  done
  unset _dotfiles_editor _dotfiles_config
fi

# Shared package and development tools; OS updates have explicit platform names.
_dotfiles_tool_alias update brew 'brew update && brew upgrade'
_dotfiles_tool_alias upgrade brew 'brew upgrade'
_dotfiles_tool_alias pycat pygmentize 'pygmentize -g'
_dotfiles_tool_alias record asciinema 'asciinema rec'
_dotfiles_tool_alias mergepdf gs 'gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=_merged.pdf'
_dotfiles_tool_alias copilot gh 'gh copilot'
_dotfiles_tool_alias explain gh 'gh copilot explain'
_dotfiles_tool_alias suggest gh 'gh copilot suggest'
_dotfiles_tool_alias emergency gh 'gh emergency'
_dotfiles_tool_alias depressed gh 'gh emergency'
_dotfiles_tool_alias tired gh 'gh emergency'

# Processes and system information.
alias ports='lsof -nP -iTCP -sTCP:LISTEN'
alias process='ps aux'
alias process_user='ps -u "$USER"'
alias psa='ps -ef'
alias grep='grep --color=auto'
alias egrep='grep -E --color=auto'
alias fgrep='grep -F --color=auto'
alias showdate='echo "Today is $(date)"'
alias printdir='echo "The current directory is: $(pwd)"'
alias listfiles='echo "The files in this directory are: $(ls)"'

# Network helpers.
alias ping='ping -c 5'
alias weather_cincy='_dotfiles_weather Cincinnati'
alias weather_home='_dotfiles_weather Al+Mansurah,+Egypt'
alias weather_geneva='_dotfiles_weather Geneva'
_dotfiles_tool_alias wget wget 'wget -c'

# Shell and session shortcuts. reload is supplied by each shell entry point.
alias c='clear'
alias which='type -a'
alias :q='exit'
alias ext='exit'
alias xt='exit'
alias by='exit'
alias bye='exit'
alias die='exit'
alias quit='exit'
alias e='exit'
alias h='history'
alias ghist='history | grep'
alias restart_shell='exec "$SHELL" -l'
alias path='printf "%s\n" "$PATH" | tr ":" "\n"'
alias j='jobs -l'

# Tmux helpers.
alias tmux_new='tmux new -s'
alias tmux_attach='tmux a -t'
alias tmux_list='tmux ls'
alias tmux_kill='tmux kill-session -t'
alias tmux_kill_all='pkill -f tmux'
unset -f _dotfiles_tool_alias
