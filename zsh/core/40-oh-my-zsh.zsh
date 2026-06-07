# Oh My Zsh framework setup.

export ZSH="${ZSH:-$HOME/.oh-my-zsh}"
ZSH_CUSTOM="${ZSH_CUSTOM:-$ZSH/custom}"

_omz_theme_exists() {
  local theme="$1"
  [[ -f "$ZSH/themes/$theme.zsh-theme" || -f "$ZSH_CUSTOM/themes/$theme.zsh-theme" ]]
}

if [[ -z "${ZSH_THEME-}" ]]; then
  if _omz_theme_exists dracula-pro; then
    ZSH_THEME="dracula-pro"
  else
    ZSH_THEME="robbyrussell"
  fi
fi

plugins=()
_omz_add_plugin() {
  local plugin
  for plugin in "$@"; do
    if [[ -d "$ZSH/plugins/$plugin" || -d "$ZSH_CUSTOM/plugins/$plugin" ]]; then
      plugins+=("$plugin")
    fi
  done
}
_omz_add_plugin "${DOTFILES_OMZ_PLUGINS[@]}"

if [[ -r "$ZSH/oh-my-zsh.sh" ]]; then
  source "$ZSH/oh-my-zsh.sh"
fi
