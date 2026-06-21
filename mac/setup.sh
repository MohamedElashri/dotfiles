#!/usr/bin/env bash
# MacOS setup / restore script.
# Run from the mac/ directory (restore --platform mac does this automatically).

# Remove Message of the day prompt
touch "$HOME/.hushlogin"

# Show hidden files in Finder
defaults write com.apple.finder AppleShowAllFiles YES

# Basic file system setup
mkdir -p "$HOME/work/git"

# Install all homebrew packages
echo "Installing brew packages from lists/brew.txt..."
while IFS='' read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    brew install "$line"
done < "./lists/brew.txt"

# Install all cask packages
echo "Installing cask packages from lists/cask.txt..."
while IFS='' read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    brew install --cask "$line"
done < "./lists/cask.txt"

# Zsh config via stow
rm -f "$HOME/.zshrc"
stow configs/zsh -t "$HOME"

# Git config via stow
stow configs/git -t "$HOME/"
git config --global core.excludesfile "$HOME/.gitignore"

# VSCode settings (stow cannot handle paths with spaces so use a direct symlink)
VSCODE_USER="$HOME/Library/Application Support/Code/User"
mkdir -p "$VSCODE_USER"
ln -sf "$(pwd)/configs/vscode/settings.json" "$VSCODE_USER/settings.json"

# Fonts — use find so filenames with spaces are handled correctly.
[[ -d configs/fonts/Fonts/ ]] && \
    find configs/fonts/Fonts/ -maxdepth 1 -type f -exec cp -f {} ~/Library/Fonts/ \;
[[ -d configs/fonts/FontCollections/ ]] && \
    find configs/fonts/FontCollections/ -maxdepth 1 -type f -exec cp -f {} ~/Library/FontCollections/ \;
