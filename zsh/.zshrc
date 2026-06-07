# ~/.zshrc: interactive zsh setup.
#
# Load order:
#   1. environment.zsh  - PATH and toolchain variables only.
#   2. Oh My Zsh        - framework, plugins, completion, theme defaults.
#   3. Personal files   - aliases, options, functions, one-off helpers.
#   4. Prompt/history   - Starship and Atuin, after everything else is ready.

_source_if_readable() {
  [[ -r "$1" ]] && source "$1"
}

# Environment and PATH setup. This intentionally does not source Oh My Zsh.
_source_if_readable "$HOME/environment.zsh"

# Add txm completions before Oh My Zsh runs compinit.
if [[ -d "$HOME/.zfunc" ]]; then
  fpath=("$HOME/.zfunc" "${fpath[@]}")
fi

# Oh My Zsh framework. Keep the theme and plugin list here because OMZ reads
# them at source time.
export ZSH="${ZSH:-$HOME/.oh-my-zsh}"
ZSH_THEME="${ZSH_THEME:-dracula-pro}"
plugins=(git zsh-autosuggestions you-should-use adguard-helper)

if [[ -r "$ZSH/oh-my-zsh.sh" ]]; then
  source "$ZSH/oh-my-zsh.sh"
fi

# Personal zsh files. These load after OMZ so local aliases/functions win over
# plugin defaults.
for config_file in \
  "$HOME/aliases.zsh" \
  "$HOME/config.zsh" \
  "$HOME/functions.zsh" \
  "$HOME/tricks.zsh" \
  "$HOME/cli/m_nvim.zsh"
do
  _source_if_readable "$config_file"
done

# Prompt. Starship is intentionally after OMZ so it can own the prompt when it
# is installed.
if command -v starship >/dev/null 2>&1; then
  eval "$(starship init zsh)"
fi

# Rust/Cargo. environment.zsh already keeps Cargo on PATH; sourcing rustup's
# env file is retained for compatibility with rustup-managed updates.
_source_if_readable "$HOME/.cargo/env"

# Atuin history integration. PATH setup is cheap, but the shell hook is only
# useful when the binary exists.
_source_if_readable "$HOME/.atuin/bin/env"
if command -v atuin >/dev/null 2>&1; then
  eval "$(atuin init zsh)"
fi

# Optional startup message controlled from config.zsh.
if [[ -t 1 && "$RUN_QURAN_VERSE_ON_STARTUP" == "true" && -f "$HOME/cli/terminal_quran.sh" ]]; then
  "$HOME/cli/terminal_quran.sh"
fi

unset -f _source_if_readable _path_prepend _path_append _pathvar_prepend
