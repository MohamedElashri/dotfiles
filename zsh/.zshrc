# ~/.zshrc: interactive zsh setup.
#
# Load order:
#   1. core/         - PATH helpers, options, completion, Oh My Zsh.
#   2. aliases/      - simple command aliases grouped by domain.
#   3. functions/    - shell functions grouped by domain.
#   4. integrations/ - optional external tool hooks.
#   5. local files   - machine-specific, untracked overrides.

_dotfiles_source_if_readable() {
  [[ -r "$1" ]] && source "$1"
}

_dotfiles_source_dir() {
  local dir="$1"
  local file

  [[ -d "$dir" ]] || return 0
  for file in "$dir"/*.zsh(N); do
    _dotfiles_source_if_readable "$file"
  done
}

_dotfiles_zshrc_file="${${(%):-%N}:A}"
export DOTFILES_ZSH_DIR="${DOTFILES_ZSH_DIR:-$HOME/.config/dotfiles/zsh}"

# Allow the repo copy of .zshrc to run before restore has installed modules.
if [[ ! -d "$DOTFILES_ZSH_DIR/core" ]]; then
  export DOTFILES_ZSH_DIR="${_dotfiles_zshrc_file:h}"
fi

_dotfiles_source_dir "$DOTFILES_ZSH_DIR/core"
_dotfiles_source_dir "$DOTFILES_ZSH_DIR/aliases"
_dotfiles_source_dir "$DOTFILES_ZSH_DIR/functions"
_dotfiles_source_dir "$DOTFILES_ZSH_DIR/integrations"

# Machine-local zsh customizations. These files are intentionally not tracked
# by this repo and are useful for host-specific aliases, PATHs, and secrets.
for _dotfiles_local_file in \
  "$HOME/.config/dotfiles/zshrc.local.zsh" \
  "$HOME/.dotfiles.local.zsh"
do
  _dotfiles_source_if_readable "$_dotfiles_local_file"
done

unset _dotfiles_local_file _dotfiles_zshrc_file
unset -f _dotfiles_source_if_readable _dotfiles_source_dir
unset -f _path_prepend _path_append _pathvar_prepend _omz_theme_exists _omz_add_plugin
# sanad completion start
fpath=("$HOME/.zsh/completions" $fpath)
autoload -Uz compinit
compinit
# sanad completion end
