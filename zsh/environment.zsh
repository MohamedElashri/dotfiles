## Ensure ~/.local/bin is in PATH
export PATH=$HOME/.local/bin:$HOME/bin:$PATH

## Path to Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

## Set name of the theme to load
ZSH_THEME="dracula-pro"

plugins=(git zsh-autosuggestions insult-zsh you-should-use adguard-helper)

## Source Oh My Zsh
source $ZSH/oh-my-zsh.sh

## Linuxbrew
if [ -f "/home/linuxbrew/.linuxbrew/bin/brew" ]; then
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
fi


## Starship prompt
if command -v starship &> /dev/null; then
    eval "$(starship init zsh)"
else
    echo "Starship is not installed or not in PATH. Please install it or add it to your PATH."
fi

## Atuin shell plugin
eval "$(atuin init zsh)"


## Go 
export GOPATH=$HOME/go
export GOROOT=/home/linuxbrew/.linuxbrew/Cellar/go/1.23.3/libexec
export PATH=$PATH:$GOROOT/bin:$GOPATH/bin
#export GO111MODULE=on

## nix 
if [ -e /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]; then
  . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
fi

## nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion


## Add terminal_quran
if [[ $- == *i* && "$RUN_QURAN_VERSE_ON_STARTUP" == "true" ]]; then
~/cli/terminal_quran.sh
fi

## Install Ruby Gems to ~/gems
export GEM_HOME="$HOME/gems"
export PATH="$HOME/gems/bin:$PATH"


## Add Rust Cargo to PATH
export PATH="$PATH:$HOME/.cargo/bin"