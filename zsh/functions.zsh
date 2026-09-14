# Archive helpers.

zipf() { zip -r "$1".zip "$1"; }

extract() {
  if [[ -f "$1" ]]; then
    case "$1" in
      *.tar.bz2) tar xjf "$1" ;;
      *.tar.gz)  tar xzf "$1" ;;
      *.bz2)     bunzip2 "$1" ;;
      *.rar)     unrar e "$1" ;;
      *.gz)      gunzip "$1" ;;
      *.tar)     tar xf "$1" ;;
      *.tbz2)    tar xjf "$1" ;;
      *.tgz)     tar xzf "$1" ;;
      *.zip)     unzip "$1" ;;
      *.Z)       uncompress "$1" ;;
      *.7z)      7z x "$1" ;;
      *)         echo "'$1' cannot be extracted via extract()" ;;
    esac
  else
    echo "'$1' is not a valid file"
  fi
}

# General development helpers.

crun() {
  mkdir -p "build" && g++ "$1.cpp" -std=c++17 -o "build/$1.out" && "./build/$1.out"
}

GrePFind() {
  grep -rnw "$1" -e "$2"
}

# Docker helpers.

dalias() {
  alias | grep 'docker' | sed "s/^\([^=]*\)=\(.*\)/\1 => \2/" | sed "s/['|\']//g" | sort
  alias | grep '__d' | sed "s/^\([^=]*\)=\(.*\)/\1 => \2/" | sed "s/['|\']//g" | sort
}

dbash() {
  docker exec -it "$(docker ps -aqf "name=$1")" bash
}

dip() {
  local container
  for container in "$@"; do
    docker inspect -f "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" "$container"
  done
}

dst() {
  if [[ -z $1 ]]; then
    docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.PIDs}}'
  else
    docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.PIDs}}' | grep "$1"
  fi
}

dstop() {
  local container
  if [[ $# -eq 0 ]]; then
    docker stop $(docker ps -aq --no-trunc)
  else
    for container in "$@"; do
      docker stop $(docker ps -aq --no-trunc | grep "$container")
    done
  fi
}

drm() {
  local container
  if [[ $# -eq 0 ]]; then
    docker rm $(docker ps -aq --no-trunc)
  else
    for container in "$@"; do
      docker rm $(docker ps -aq --no-trunc | grep "$container")
    done
  fi
}

drmi() {
  local container
  if [[ $# -eq 0 ]]; then
    docker rmi $(docker images --filter 'dangling=true' -aq --no-trunc)
  else
    for container in "$@"; do
      docker rmi $(docker images --filter 'dangling=true' -aq --no-trunc | grep "$container")
    done
  fi
}

# File and directory helpers.

trash() { command mv "$@" "$HOME/.Trash"; }

fff() {
  local file_name="$1"
  find . -name "$file_name"
}

ffs() {
  local prefix="$1"
  find . -name "$prefix*"
}

ffe() {
  local suffix="$1"
  find . -name "*$suffix"
}

mkd() {
  mkdir -p "$@" && cd "$_"
}

get_size() {
  local target="$1"
  local size size_gb size_mb

  if [[ ! -e "$target" ]]; then
    echo "Error: File or folder not found!"
    return 1
  fi

  if [[ "$(uname -s)" == Darwin ]]; then
    # BSD du reports disk usage in KiB; GNU du supports apparent byte size.
    size=$(du -sk "$target" | awk '{print $1 * 1024}')
  else
    size=$(du -sb "$target" | awk '{print $1}')
  fi
  if [[ $size -ge 1073741824 ]]; then
    size_gb=$(bc <<< "scale=2; $size / 1073741824")
    echo "Size of '$target': $size_gb GB"
  else
    size_mb=$(bc <<< "scale=2; $size / 1048576")
    echo "Size of '$target': $size_mb MB"
  fi
}

open_remote_pdf() {
  if [[ "$#" -ne 2 ]]; then
    echo "Usage: open_remote_pdf HOST /remote/path/file.pdf"
    return 2
  fi

  local host="$1"
  local remote_file="$2"
  local base tmp

  base="$(basename "$remote_file")"
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/remote-pdf.XXXXXX")" || return 1

  tmp="$tmp/$base"

  scp -o ClearAllForwardings=yes -o ForwardX11=no \
    "${host}:${remote_file}" "$tmp" || {
      echo "Failed to copy remote PDF"
      rm -f "$tmp"
      return 1
    }

  if [[ "$(uname -s)" == Darwin ]]; then
    command open "$tmp"
  else
    command xdg-open "$tmp" >/dev/null 2>&1 &
  fi
}

# Git and GitHub helpers.

git_root() {
  cd "$(git rev-parse --show-toplevel)"
}

git_search() {
  git log -S "$1" --source --all "$2"
}

create_and_push_repo() {
  if ! command -v gh >/dev/null 2>&1; then
    echo "Error: GitHub CLI (gh) is not installed. Please install it first."
    return 1
  fi

  if [[ -z "$1" ]]; then
    echo "Usage: create_and_push_repo <repo-name> [--private]"
    return 1
  fi

  local repo_name="$1"
  local privacy_flag="--public"

  if [[ "$2" = "--private" ]]; then
    privacy_flag="--private"
  fi

  git init || { echo "Error: Failed to initialize git repository."; return 1; }
  git add . || { echo "Error: Failed to add files to git repository."; return 1; }
  git commit -m "Initial commit" || { echo "Error: Failed to commit files."; return 1; }

  if ! gh repo create "$repo_name" "$privacy_flag" --disable-wiki --disable-issues --source=. --remote=origin --push; then
    echo "Error: Failed to create GitHub repository and push files."
    return 1
  fi

  echo "Repository $repo_name created and pushed successfully!"
}

# Miscellaneous helpers.

cheat() {
  curl "https://cheat.sh/$1"
}

cmd() {
  history | awk '{CMD[$2]++;count++;}END { for (a in CMD)print CMD[a] " " CMD[a]/count*100 "% " a;}' | grep -v "./" | column -c3 -s " " -t | sort -nr | nl | head -n10
}

list_commands() {
  echo "User-defined Aliases:"
  alias

  echo
  echo "User-defined Functions:"
  typeset -f | awk '/^[a-zA-Z0-9]/ {print $1}' | while read -r function_name; do
    echo "$function_name"
  done
}

# Network and upload helpers.

transfer() {
  local file
  local -a file_array
  file_array=("${@}")

  if [[ "${file_array[@]}" == "" || "${1}" == "--help" || "${1}" == "-h" ]]; then
    echo "${0} - Upload arbitrary files to \"tr.melashri.eu.org\"."
    echo ""
    echo "Usage: ${0} [options] [<file>]..."
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help"
    echo "      show this message"
    echo ""
    echo "EXAMPLES:"
    echo "  Upload a single file from the current working directory:"
    echo "      ${0} \"image.img\""
    echo ""
    echo "  Upload multiple files from the current working directory:"
    echo "      ${0} \"image.img\" \"image2.img\""
    echo ""
    echo "  Upload a file from a different directory:"
    echo "      ${0} \"/tmp/some_file\""
    echo ""
    echo "  Upload all files from the current working directory. Be aware of the webserver's rate limiting!:"
    echo "      ${0} *"
    echo ""
    echo "  Upload a single file from the current working directory and filter out the delete token and download link:"
    echo "      ${0} \"image.img\" | awk --field-separator=\": \" '/Delete token:/ { print \$2 } /Download link:/ { print \$2 }'"
    echo ""
    echo "  Show help text from \"transfer.sh\":"
    echo "      curl --request GET \"https://tr.melashri.eu.org\""
    return 0
  fi

  for file in "${file_array[@]}"; do
    if [[ ! -f "${file}" ]]; then
      echo -e "\e[01;31m'${file}' could not be found or is not a file.\e[0m" >&2
      return 1
    fi
  done
  unset file

  local upload_files curl_output awk_output

  du -L "${file_array[@]}" >&2
  if [[ "${ZSH_NAME}" == "zsh" ]]; then
    read $'upload_files?\e[01;31mDo you really want to upload the above files ('"${#file_array[@]}"$') to "tr.melashri.eu.org"? (Y/n): \e[0m'
  elif [[ "${BASH}" == *"bash"* ]]; then
    read -p $'\e[01;31mDo you really want to upload the above files ('"${#file_array[@]}"$') to "tr.melashri.eu.org"? (Y/n): \e[0m' upload_files
  fi

  case "${upload_files:-y}" in
    "y"|"Y")
      for file in "${file_array[@]}"; do
        curl_output=$(curl --request PUT --progress-bar --dump-header - --upload-file "${file}" "https://tr.melashri.eu.org/")
        awk_output=$(awk \
          'gsub("\r", "", $0) && tolower($1) ~ /x-url-delete/ \
          {
            delete_link=$2;
            print "Delete command: curl --request DELETE " "\""delete_link"\"";

            gsub(".*/", "", delete_link);
            delete_token=delete_link;
            print "Delete token: " delete_token;
          }

          END{
            print "Download link: " $0;
          }' <<< "${curl_output}")

        echo -e "${awk_output}\n"

        if (( ${#file_array[@]} > 4 )); then
          sleep 5
        fi
      done
      ;;
    "n"|"N")
      return 1
      ;;
    *)
      echo -e "\e[01;31mWrong input: '${upload_files}'.\e[0m" >&2
      return 1
      ;;
  esac
}

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
  command -v scselect >/dev/null 2>&1 && scselect
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

# Deliberately silly terminal tricks.

busywork() {
  local descriptions=(
    "Monitoring processes and managing memory usage..."
    "Scanning system logs for critical issues..."
    "Running inference benchmark on CPU and GPU, comparing results..."
    "Checking data integrity and creating backups..."
    "Analyzing system resource usage and providing optimization tips..."
  )

  local variations=(
    'while true; do \
        echo "$(date): Checking running processes..."; sleep 1; \
        ps aux --sort=-%mem | head -n 5; sleep 1; \
        echo "$(date): Monitoring high-memory processes..."; sleep 1; \
        ps aux --sort=-%mem | awk "{if (\$4 > 30) print}" | head -n 2; sleep 2; \
        echo "$(date): Attempting resource adjustments..."; sleep 1; \
        echo "PID 1234 (example_process) marked for resource reduction"; sleep 1; \
        echo "$(date): Reviewing CPU usage..."; sleep 1; \
        ps aux --sort=-%cpu | head -n 5; sleep 2; \
    done'
    'while true; do \
        echo "$(date): Starting log scan..."; sleep 1; \
        tail -f /var/log/syslog /var/log/auth.log 2>/dev/null | grep -E "ERROR|WARNING|Failed|Accepted|Denied" | while read line; do \
            echo "$line"; sleep 0.5; \
            echo "$(date): Checking recent entries..."; sleep 1; \
        done; \
        echo "$(date): No immediate critical issues detected. Continuing scan..."; sleep 2; \
    done'
    'while true; do \
        echo "$(date): Loading dataset for inference..."; sleep 2; \
        echo "$(date): Running CPU inference benchmark..."; sleep 3; \
        echo "CPU Inference: Throughput at 175 samples/sec"; sleep 2; \
        echo "Accuracy: 82.5%"; sleep 1; \
        echo "$(date): Switching to GPU inference benchmark..."; sleep 2; \
        echo "$(date): GPU inference in progress, checking throughput..."; sleep 1; \
        echo "GPU Inference: Throughput at 476 samples/sec"; sleep 2; \
        echo "Accuracy: 83.0%"; sleep 2; \
        echo "$(date): Benchmark comparison: GPU is 2.7x faster, Accuracy +0.5%"; sleep 2; \
        echo "$(date): Re-running GPU inference to verify consistency..."; sleep 2; \
    done'
    'while true; do \
        echo "$(date): Starting data integrity check on ~/inference_engine..."; sleep 2; \
        ls -lh ~/inference_engine 2>/dev/null | head -n 5; sleep 1; \
        echo "$(date): Verifying integrity of critical files..."; sleep 1; \
        ls -lh ~/inference_engine/important_file.dat 2>/dev/null || echo "File missing! Check configuration."; sleep 1; \
        echo "$(date): No corruption found. Preparing backup..."; sleep 1; \
        echo "Backing up to /backup/inference_engine"; sleep 3; \
        ls -lh /backup/inference_engine 2>/dev/null | head -n 5; sleep 1; \
        echo "$(date): Backup verification complete."; sleep 2; \
    done'
    'while true; do \
        echo "$(date): Collecting CPU and memory usage data..."; sleep 1; \
        top -bn1 | head -n 10; sleep 2; \
        echo "$(date): Checking memory usage trends..."; sleep 1; \
        free -h | grep -E "Mem|Swap"; sleep 1; \
        echo "$(date): CPU load distribution across cores..."; sleep 1; \
        mpstat -P ALL 1 1 | tail -n +4; sleep 2; \
        echo "$(date): System usage check complete."; sleep 2; \
    done'
  )

  local index selected_description selected_variation
  index=$((RANDOM % ${#variations[@]}))
  selected_description="${descriptions[$index]}"
  selected_variation="${variations[$index]}"

  echo -e "\033[0;32m$selected_description\033[0m"
  eval "$selected_variation"
}

alias abusy="busywork"

nvims() {
  local items config
  items=("default" "kickstart" "LazyVim" "NvChad" "AstroNvim")
  config=$(printf "%s\n" "${items[@]}" | fzf --prompt=" Neovim Config  " --height=50% --layout=reverse --border --exit-0)
  if [[ -z $config ]]; then
    echo "Nothing selected"
    return 0
  elif [[ $config == "default" ]]; then
    config=""
  fi
  NVIM_APPNAME=$config nvim "$@"
}
