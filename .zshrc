
# Source additional configuration files
for config_file in ~/environment.zsh ~/plugins.zsh ~/aliases.zsh ~/functions.zsh; do
    if [[ -f "$config_file" ]]; then
        source "$config_file"
    fi
done

if [ -f ~/.m_nvim.zsh ]; then
    source ~/.m_nvim.zsh
fi

