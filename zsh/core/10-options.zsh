# Small interactive shell options and feature flags.

# Disable bracketed paste mode if a terminal has trouble with it.
# if [[ $- == *i* ]]; then
#   bind 'set enable-bracketed-paste off'
# fi

export RUN_QURAN_VERSE_ON_STARTUP="${RUN_QURAN_VERSE_ON_STARTUP:-true}"
