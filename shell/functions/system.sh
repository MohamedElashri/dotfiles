# Process inspection, information, and temperature helpers.
unalias showdisk mycpu 2>/dev/null || true

if command -v column >/dev/null 2>&1; then
  unalias mount 2>/dev/null || true
  mount() {
    if ! command -v column >/dev/null 2>&1; then command mount "$@"; return; fi
    local output
    output=$(command mount "$@") || return
    printf '%s\n' "$output" | column -t
  }
fi

showdisk() {
  local output
  output=$(command df -P /) || return
  printf '%s\n' "$output" | awk '$NF=="/" {print "The disk usage is: " $5}'
}

mycpu() {
  local output
  output=$(command ps -u "$USER" -o %cpu=) || return
  printf '%s\n' "$output" | awk '{sum+=$1} END {printf "Your current CPU usage is: %.2f%%\n", sum}'
}

if command -v mpstat >/dev/null 2>&1; then
  unalias showcpu 2>/dev/null || true
  showcpu() {
    local output
    output=$(command mpstat 1 1) || return
    printf '%s\n' "$output" | awk '/all/ {print "The current CPU usage is: " 100 - $NF "%"}'
  }
fi

cmd() {
  history | awk '{CMD[$2]++;count++;}END { for (a in CMD)print CMD[a] " " CMD[a]/count*100 "% " a;}' | grep -v "./" | column -c3 -s " " -t | sort -nr | nl | head -n10
}

list_commands() {
  echo "User-defined Aliases:"
  alias

  echo
  echo "User-defined Functions:"
  if [ -n "${ZSH_VERSION-}" ]; then
    typeset +f | LC_ALL=C sort
  else
    compgen -A function | LC_ALL=C sort
  fi
}

lk() {
  if [[ $# -gt 1 ]]; then
    echo "Usage: lk [pattern|all]  - find and kill processes listening on ports"
    return 2
  fi

  local raw
  raw=$(sudo lsof -iTCP -sTCP:LISTEN -n -P 2>/dev/null) || {
    echo "lsof failed."
    return 1
  }

  local header output body result
  header=$(echo "$raw" | head -1)
  body=$(echo "$raw" | tail -n +2)

  if [[ "${1:-}" = "all" ]]; then
    output=$body
  elif [[ $# -eq 1 ]]; then
    if output=$(printf '%s\n' "$body" | command grep -i -- "$1"); then :; else
      result=$?
      [ "$result" -eq 1 ] || return "$result"
    fi
  else
    output=$body
  fi

  if [[ -z "$output" ]]; then
    echo "No listening processes found."
    return 0
  fi

  echo "$header"
  if [ -t 1 ] && [ -z "${NO_COLOR+x}" ] && [ "$#" -eq 1 ] && [ "$1" != all ]; then
    printf '%s\n' "$output" | command grep -i --color=always -- "$1"
  else
    printf '%s\n' "$output"
  fi
  echo ""

  [[ $# -eq 0 ]] && return 0

  local pids pid_count
  pids=$(echo "$output" | awk '{print $2}' | grep -E '^[0-9]+$' | sort -u)
  pid_count=$(printf '%s\n' "$pids" | awk 'NF {n++} END {print n+0}')

  if [[ "$pid_count" -eq 0 ]]; then
    echo "No PIDs found."
    return 0
  fi

  printf 'PIDs to kill: %s\n' "$pids"
  echo -n "Kill these ${pid_count} process(es)? [y/N] "
  local confirm
  IFS= read -r confirm || return 1

  if [[ "$confirm" =~ ^[Yy]$ ]]; then
    local pid
    printf '%s\n' "$pids" | while IFS= read -r pid; do
      # An unprivileged kill -0 cannot distinguish a missing PID from one
      # owned by another user. Let the requested privileged operation report it.
      echo "Sending SIGTERM to PID $pid..."
      sudo kill -15 "$pid" || return
    done || return
    echo "Done."
  else
    echo "Aborted."
  fi
}

# System helpers.

ii() {
  local result=0
  echo -e "\n${COL_GREEN-}You are currently logged in to:${COL_RESET-} "
  command hostname || result=$?
  echo -e "\n${COL_GREEN-}Additional information:${COL_RESET-} ${NC-} "
  command uname -a || result=$?
  echo -e "\n${COL_GREEN-}Users logged on:${COL_RESET-} ${NC-} "
  command w -h || result=$?
  echo -e "\n${COL_GREEN-}Current date:${COL_RESET-} ${NC-} "
  command date || result=$?
  echo -e "\n${COL_GREEN-}Machine stats:${COL_RESET-} ${NC-} "
  command uptime || result=$?
  echo -e "\n${COL_GREEN-}Current network location:${COL_RESET-} ${NC-} "
  if command -v scselect >/dev/null 2>&1; then command scselect || result=$?; fi
  echo -e "\n${COL_GREEN-}Public facing IP Address:${COL_RESET-} ${NC-} "
  myip || result=$?
  echo
  return "$result"
}


unalias temps 2>/dev/null

temps() {
    local readings color=0

    # Enable colors only in interactive terminals.
    if [ -t 1 ] && [ -z "${NO_COLOR+x}" ] &&
       [ "${TERM:-dumb}" != "dumb" ]; then
        color=1
    fi

    case "$(uname -s)" in
        Linux)
            if ! command -v sensors >/dev/null 2>&1; then
                echo "Install lm-sensors first."
                return 1
            fi

            readings=$(LC_ALL=C sensors | LC_ALL=C awk '
                /^[^ \t][^:]*$/ {
                    chip = $0
                    next
                }

                /:[ \t]*[+-]?[0-9]+([.][0-9]+)?/ {
                    if ($0 !~ /C/) next

                    label = $0
                    sub(/:.*/, "", label)
                    gsub(/^[ \t]+|[ \t]+$/, "", label)

                    value = $0
                    sub(/^[^:]*:[ \t]*/, "", value)
                    sub(/[^0-9.+-].*$/, "", value)

                    if (value !~ /^[+-]?[0-9]+([.][0-9]+)?$/)
                        next

                    c = tolower(chip)
                    rank = 0

                    if (c ~ /^(k10temp|zenpower)/) {
                        key = "CPU"
                        if (label == "Tctl") rank = 100
                        else if (label == "Tdie") rank = 90
                        else if (label == "temp1") rank = 10
                    }
                    else if (c ~ /^coretemp/) {
                        key = "CPU"
                        if (label ~ /^Package id/) rank = 100
                        else if (label ~ /^Core [0-9]+$/) rank = 50
                        else if (label == "temp1") rank = 10
                    }
                    else if (c ~ /^(amdgpu|nouveau|i915)/) {
                        key = "GPU"
                        if (label == "edge") rank = 100
                        else if (label == "temp1") rank = 50
                    }
                    else if (c ~ /^nvme/) {
                        key = "NVME:" c
                        if (label == "Composite") rank = 100
                        else if (label == "temp1") rank = 50

                        if (!(key in seen)) {
                            nvme_keys[++nvme_count] = key
                            seen[key] = 1
                        }
                    }
                    else if (c ~ /^(mt[0-9]|iwlwifi|ath[0-9])/) {
                        key = "Wi-Fi"
                        if (label == "temp1") rank = 100
                    }
                    else if (c ~ /^(r8169|igc|e1000e)/) {
                        key = "Ethernet"
                        if (label == "temp1") rank = 100
                    }
                    else next

                    if (rank > 0 &&
                        (!(key in values) || rank > ranks[key])) {
                        values[key] = value
                        labels[key] = label
                        ranks[key] = rank
                    }
                }

                END {
                    if ("CPU" in values)
                        printf "CPU\t%s\t%s\n",
                               labels["CPU"], values["CPU"]

                    if ("GPU" in values)
                        printf "GPU\t%s\t%s\n",
                               labels["GPU"], values["GPU"]

                    for (i = 1; i <= nvme_count; i++) {
                        key = nvme_keys[i]
                        if (!(key in values)) continue

                        name = "NVMe SSD"
                        if (nvme_count > 1)
                            name = name " " i

                        printf "%s\t%s\t%s\n",
                               name, labels[key], values[key]
                    }

                    if ("Wi-Fi" in values)
                        printf "Wi-Fi\t%s\t%s\n",
                               labels["Wi-Fi"], values["Wi-Fi"]

                    if ("Ethernet" in values)
                        printf "Ethernet\t%s\t%s\n",
                               labels["Ethernet"], values["Ethernet"]
                }
            ') || return 1
            ;;

        Darwin)
            if [ "$(uname -m)" = "arm64" ]; then
                if ! command -v macmon >/dev/null 2>&1 ||
                   ! command -v jq >/dev/null 2>&1; then
                    echo "Install: brew install macmon jq"
                    return 1
                fi

                readings=$(macmon pipe -s 1 | jq -r '
                    .temp |
                    (["CPU", "average", .cpu_temp_avg],
                     ["GPU", "average", .gpu_temp_avg]) |
                    select(.[2] | type == "number") |
                    @tsv
                ') || return 1
            else
                if ! command -v osx-cpu-temp >/dev/null 2>&1; then
                    echo "Install: brew install osx-cpu-temp"
                    return 1
                fi

                readings=$(
                    for device in CPU GPU; do
                        case "$device" in
                            CPU) flag="-c" ;;
                            GPU) flag="-g" ;;
                        esac

                        value=$(osx-cpu-temp "$flag" -T 2>/dev/null) ||
                            continue

                        printf '%s\t%s\t%s\n' \
                            "$device" "sensor" "$value"
                    done
                )
            fi
            ;;

        *)
            echo "Unsupported operating system."
            return 1
            ;;
    esac

    if [ -z "$readings" ]; then
        echo "No supported temperature sensors found."
        return 1
    fi

    # Shared formatter and configurable thresholds.
    printf '%s\n' "$readings" | LC_ALL=C awk -F '\t' \
        -v color="$color" \
        -v cpu_w="${TEMPS_CPU_WARN:-75}" \
        -v cpu_h="${TEMPS_CPU_HOT:-85}" \
        -v gpu_w="${TEMPS_GPU_WARN:-70}" \
        -v gpu_h="${TEMPS_GPU_HOT:-85}" \
        -v nvme_w="${TEMPS_NVME_WARN:-60}" \
        -v nvme_h="${TEMPS_NVME_HOT:-70}" \
        -v wifi_w="${TEMPS_WIFI_WARN:-65}" \
        -v wifi_h="${TEMPS_WIFI_HOT:-80}" \
        -v eth_w="${TEMPS_ETH_WARN:-65}" \
        -v eth_h="${TEMPS_ETH_HOT:-80}" '
        BEGIN {
            esc = sprintf("%c", 27)
            green = esc "[32m"
            yellow = esc "[33m"
            red = esc "[31m"
            reset = esc "[0m"
        }

        NF >= 3 {
            device = $1
            label = $2
            temp = $3 + 0

            if (temp <= 0) next

            if (device == "CPU") {
                warn = cpu_w; hot = cpu_h
            }
            else if (device == "GPU") {
                warn = gpu_w; hot = gpu_h
            }
            else if (device ~ /^NVMe SSD/) {
                warn = nvme_w; hot = nvme_h
            }
            else if (device == "Wi-Fi") {
                warn = wifi_w; hot = wifi_h
            }
            else if (device == "Ethernet") {
                warn = eth_w; hot = eth_h
            }
            else next

            if (temp >= hot) {
                status = "HOT"
                shade = red
            }
            else if (temp >= warn) {
                status = "WARM"
                shade = yellow
            }
            else {
                status = "OK"
                shade = green
            }

            if (color)
                printf "  %-14s %-12s : %s%5.1f C  %-4s%s\n",
                       device, label, shade, temp, status, reset
            else
                printf "  %-14s %-12s : %5.1f C  %s\n",
                       device, label, temp, status
        }
    '
}
