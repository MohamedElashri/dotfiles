# macOS integrations around the shared shell setup.
if [[ "$(uname -s)" == Darwin ]]; then
  [[ -r "$HOME/Library/Application Support/amazon-q/shell/zshrc.pre.zsh" ]] && source "$HOME/Library/Application Support/amazon-q/shell/zshrc.pre.zsh"
fi
typeset -gaU fpath
fpath=("$HOME/.zsh/completion" "$HOME/.zsh/completions" $fpath)
# Completion paths that must be set before Oh My Zsh runs compinit.

if [[ -d "$HOME/.zfunc" ]]; then
  fpath=("$HOME/.zfunc" "${fpath[@]}")
fi

# Desired Oh My Zsh plugins.
#
# The setup below filters this list against plugins actually installed on the
# current machine, so missing optional plugins do not break shell startup.

DOTFILES_OMZ_PLUGINS=(git zsh-autosuggestions you-should-use adguard-helper insult-zsh)

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

# Initialize completions once, including personal and sanad completions.
if ! (( $+functions[compdef] )); then
  autoload -Uz compinit
  compinit
fi
# Optional Conda integration.

for _conda_prefix in \
  "$HOME/miniforge3" \
  "$HOME/miniconda3" \
  "$HOME/anaconda3" \
  "/opt/conda" \
  "/opt/homebrew/Caskroom/miniforge/base"
do
  if [[ -x "$_conda_prefix/bin/conda" ]]; then
    __conda_setup="$("$_conda_prefix/bin/conda" 'shell.zsh' 'hook' 2> /dev/null)"
    if [[ $? -eq 0 ]]; then
      eval "$__conda_setup"
    elif [[ -f "$_conda_prefix/etc/profile.d/conda.sh" ]]; then
      source "$_conda_prefix/etc/profile.d/conda.sh"
    fi
    unset __conda_setup
    break
  elif [[ -f "$_conda_prefix/etc/profile.d/conda.sh" ]]; then
    source "$_conda_prefix/etc/profile.d/conda.sh"
    break
  elif [[ -d "$_conda_prefix/bin" ]]; then
    _path_prepend "$_conda_prefix/bin"
    break
  fi
done
unset _conda_prefix

if command -v conda >/dev/null 2>&1 && [[ -z "${CONDA_EXE-}" ]]; then
  __conda_setup="$(conda 'shell.zsh' 'hook' 2> /dev/null)"
  if [[ $? -eq 0 ]]; then
    eval "$__conda_setup"
  fi
  unset __conda_setup
fi

# Lazy nvm wrappers. Sourcing nvm.sh is expensive, so do it only on first use.

if [[ -z "${NVM_DIR-}" ]]; then
  if [[ -n "${XDG_CONFIG_HOME-}" ]]; then
    export NVM_DIR="$XDG_CONFIG_HOME/nvm"
  else
    export NVM_DIR="$HOME/.nvm"
  fi
fi

if [[ -s "$NVM_DIR/nvm.sh" ]]; then
  _load_nvm() {
    unset -f nvm node npm npx corepack yarn pnpm 2>/dev/null
    source "$NVM_DIR/nvm.sh"
    [[ -s "$NVM_DIR/bash_completion" ]] && source "$NVM_DIR/bash_completion"
    return 0
  }

  nvm() { _load_nvm && nvm "$@"; }
  node() { _load_nvm && command node "$@"; }
  npm() { _load_nvm && command npm "$@"; }
  npx() { _load_nvm && command npx "$@"; }
  corepack() { _load_nvm && command corepack "$@"; }
  yarn() { _load_nvm && command yarn "$@"; }
  pnpm() { _load_nvm && command pnpm "$@"; }
fi

# Rust/Cargo integration. PATH is already handled by environment.zsh.

[[ -r "$HOME/.cargo/env" ]] && source "$HOME/.cargo/env"

# Atuin history integration.

[[ -r "$HOME/.atuin/bin/env" ]] && source "$HOME/.atuin/bin/env"

if command -v atuin >/dev/null 2>&1; then
  eval "$(atuin init zsh)"
fi

# Starship prompt. Load after Oh My Zsh so Starship owns the prompt.

if [[ ${TERM:-dumb} != dumb ]] && command -v starship >/dev/null 2>&1; then
  eval "$(starship init zsh)"
fi

if [[ "$(uname -s)" == Darwin ]]; then
  [[ -r "$HOME/Library/Application Support/amazon-q/shell/zshrc.post.zsh" ]] && source "$HOME/Library/Application Support/amazon-q/shell/zshrc.post.zsh"
  # Keep the existing macOS prompt when the framework provides p10k.
  if (( $+functions[p10k] )) && [[ -r "$HOME/.p10k.zsh" ]]; then
    source "$HOME/.p10k.zsh"
  fi
fi
return 0
