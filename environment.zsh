# Ensure ~/.local/bin is in PATH
export PATH=$HOME/.local/bin:$HOME/bin:$PATH

# Path to Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Set name of the theme to load
ZSH_THEME=""

# Source Oh My Zsh
source $ZSH/oh-my-zsh.sh

# Linuxbrew
if [ -f "/home/linuxbrew/.linuxbrew/bin/brew" ]; then
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
fi

# Starship prompt
if command -v starship &> /dev/null; then
    eval "$(starship init zsh)"
else
    echo "Starship is not installed or not in PATH. Please install it or add it to your PATH."
fi