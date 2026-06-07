# Optional startup message controlled from core/10-options.zsh.

if [[ -t 1 && "$RUN_QURAN_VERSE_ON_STARTUP" == "true" && -f "$HOME/cli/terminal_quran.sh" ]]; then
  "$HOME/cli/terminal_quran.sh"
fi
