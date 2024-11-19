
# Source additional configuration files
for config_file in ~/environment.zsh ~/aliases.zsh ~/config.zsh ~/functions.zsh ~/tricks.zsh; do
    if [[ -f "$config_file" ]]; then
        source "$config_file"
    fi
done

if [ -f ~/cli/m_nvim.zsh ]; then
    source ~/cli/m_nvim.zsh
fi

eval "$(atuin init zsh)"

. "$HOME/.cargo/env"
