# System helpers.

ii() {
  echo -e "\n${COL_GREEN}You are currently logged in to:$COL_RESET "
  echo -e "$HOSTNAME"
  echo -e "\n${COL_GREEN}Additional information:$COL_RESET $NC "
  uname -a
  echo -e "\n${COL_GREEN}Users logged on:$COL_RESET $NC "
  w -h
  echo -e "\n${COL_GREEN}Current date:$COL_RESET $NC "
  date
  echo -e "\n${COL_GREEN}Machine stats:$COL_RESET $NC "
  uptime
  echo -e "\n${COL_GREEN}Current network location:$COL_RESET $NC "
  scselect
  echo -e "\n${COL_GREEN}Public facing IP Address:$COL_RESET $NC "
  myip
  echo
}

if [[ "$(uname -s)" != "Darwin" ]]; then
  if grep -q Microsoft /proc/version 2>/dev/null; then
    alias open='explorer.exe'
  else
    alias open='xdg-open'
  fi
fi
