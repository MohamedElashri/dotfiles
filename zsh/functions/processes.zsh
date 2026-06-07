# Process helpers.

lk() {
  if [[ $# -gt 1 && "$1" != "all" ]]; then
    echo "Usage: lk [pattern|all]  - find and kill processes listening on ports"
    return 1
  fi

  local raw
  raw=$(sudo lsof -iTCP -sTCP:LISTEN -n -P 2>/dev/null) || {
    echo "lsof failed."
    return 1
  }

  local header output
  header=$(echo "$raw" | head -1)

  if [[ "$1" = "all" ]]; then
    output=$(echo "$raw" | tail -n +2)
  elif [[ $# -eq 1 ]]; then
    output=$(echo "$raw" | grep -i "$1")
  else
    output=$(echo "$raw" | tail -n +2)
  fi

  if [[ -z "$output" ]]; then
    echo "No listening processes found."
    return 0
  fi

  echo "$header"
  echo "$output" | grep -i --color=always "${1:-.}"
  echo ""

  [[ $# -eq 0 ]] && return 0

  local -a pids
  pids=($(echo "$output" | awk '{print $2}' | grep -E '^[0-9]+$' | sort -u))

  if [[ ${#pids[@]} -eq 0 ]]; then
    echo "No PIDs found."
    return 0
  fi

  echo "PIDs to kill: ${pids[*]}"
  echo -n "Kill these ${#pids[@]} process(es)? [y/N] "
  local confirm
  read -r confirm

  if [[ "$confirm" =~ ^[Yy]$ ]]; then
    local pid
    for pid in "${pids[@]}"; do
      if kill -0 "$pid" 2>/dev/null; then
        echo "Sending SIGTERM to PID $pid..."
        sudo kill -15 "$pid"
      else
        echo "PID $pid no longer exists, skipping."
      fi
    done
    echo "Done."
  else
    echo "Aborted."
  fi
}
