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
