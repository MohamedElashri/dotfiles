# Interactive Zsh: explicit load order, shared on Linux and macOS.
[[ -o interactive ]] || return 0
export DOTFILES_ROOT="${${${(%):-%N}:A}:h:h}"
source "$DOTFILES_ROOT/shell/env.sh"
source "$DOTFILES_ROOT/zsh/environment.zsh"
# Small interactive shell options and feature flags.

# Disable bracketed paste mode if a terminal has trouble with it.
# if [[ $- == *i* ]]; then
#   bind 'set enable-bracketed-paste off'
# fi

export RUN_QURAN_VERSE_ON_STARTUP="${RUN_QURAN_VERSE_ON_STARTUP:-true}"

# History options. Oh My Zsh (lib/history.zsh) already enables: extended_history,
# hist_expire_dups_first, hist_ignore_dups, hist_ignore_space, hist_verify, and
# share_history (which implies inc_append_history). Only the extras live here.
setopt bang_hist            # ! triggers history expansion
setopt hist_find_no_dups    # don't repeat duplicates when searching (Ctrl-r)
setopt hist_ignore_all_dups # drop duplicates anywhere, not just adjacent
setopt hist_reduce_blanks   # collapse multiple blanks in stored entries

source "$DOTFILES_ROOT/zsh/tools.zsh"
source "$DOTFILES_ROOT/shell/aliases.sh"
source "$DOTFILES_ROOT/zsh/aliases.zsh"
source "$DOTFILES_ROOT/zsh/functions.zsh"
bindkey -s "^a" "nvims\n"
case "$(uname -s)" in
  Darwin) source "$DOTFILES_ROOT/platform/mac.sh"
          [[ -r "$HOME/.iterm2_shell_integration.zsh" ]] && source "$HOME/.iterm2_shell_integration.zsh" ;;
  Linux) source "$DOTFILES_ROOT/platform/linux.sh" ;;
esac
[[ -r "$HOME/.config/dotfiles/local.zsh" ]] && source "$HOME/.config/dotfiles/local.zsh"

# Run after local overrides so the startup-message toggle takes effect.
if [[ -t 1 && "$RUN_QURAN_VERSE_ON_STARTUP" == true && -x "$DOTFILES_ROOT/bin/terminal_quran.sh" ]]; then
  "$DOTFILES_ROOT/bin/terminal_quran.sh"
fi
return 0
