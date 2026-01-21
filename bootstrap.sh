#!/bin/bash
# Install dependencies first
sudo apt update && sudo apt install -y curl git zsh

# Install Oh My Zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

# Install Starship
curl -sS https://starship.rs/install.sh | sh -s -- -y

# Install Atuin
curl https://raw.githubusercontent.com/atuinsh/atuin/main/install.sh | bash

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Restore dotfiles
./restore