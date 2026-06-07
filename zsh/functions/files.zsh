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
  local path="$1"
  local size size_gb size_mb

  if [[ ! -e "$path" ]]; then
    echo "Error: File or folder not found!"
    return 1
  fi

  size=$(du -sb "$path" | awk '{print $1}')
  if [[ $size -ge 1073741824 ]]; then
    size_gb=$(bc <<< "scale=2; $size / 1073741824")
    echo "Size of '$path': $size_gb GB"
  else
    size_mb=$(bc <<< "scale=2; $size / 1048576")
    echo "Size of '$path': $size_mb MB"
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
  tmp="$(mktemp --tmpdir "remote-${host}-${base%.pdf}.XXXXXX.pdf")" || return 1

  scp -o ClearAllForwardings=yes -o ForwardX11=no \
    "${host}:${remote_file}" "$tmp" || {
      echo "Failed to copy remote PDF"
      rm -f "$tmp"
      return 1
    }

  xdg-open "$tmp" >/dev/null 2>&1 &
}
