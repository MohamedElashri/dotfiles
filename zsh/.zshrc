
# Source additional configuration files
for config_file in ~/environment.zsh ~/aliases.zsh ~/config.zsh ~/functions.zsh ~/tricks.zsh; do
    if [[ -f "$config_file" ]]; then
        source "$config_file"
    fi
done

if [ -f ~/cli/m_nvim.zsh ]; then
    source ~/cli/m_nvim.zsh
fi

# Oh My Zsh
if [[ -d "$HOME/.oh-my-zsh" ]]; then
  source "$HOME/.oh-my-zsh/oh-my-zsh.sh"
fi

# Starship
if command -v starship >/dev/null 2>&1; then
  eval "$(starship init zsh)"
fi

# Atuin
if command -v atuin >/dev/null 2>&1; then
  eval "$(atuin init zsh)"
fi

# Rust/Cargo
if [[ -f "$HOME/.cargo/env" ]]; then
  source "$HOME/.cargo/env"
fi