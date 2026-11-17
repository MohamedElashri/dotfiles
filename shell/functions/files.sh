# File and directory helpers shared by Bash and Zsh.

count() {
  [ "$#" -eq 0 ] || { echo 'Usage: count (recursive files in the current directory)' >&2; return 2; }
  # NUL delimiters handle every filename; pipefail is confined to a subshell.
  local total
  total=$(set -o pipefail; command find . -type f -print0 | LC_ALL=C tr -cd '\000' | wc -c) || return
  printf '%s\n' "$total"
}

# Count directory entries without parsing ls or depending on GNU find/fd flags.
_dotfiles_count_entries() {
  command python3 -I - "$@" <<'PY'
import os
import sys

directory, mode, hidden, exclude_dsstore = sys.argv[1:]
counts = {'files': 0, 'dirs': 0, 'links': 0}
try:
    with os.scandir(directory) as entries:
        for entry in entries:
            if hidden == '0' and entry.name.startswith('.'):
                continue
            if exclude_dsstore == '1' and entry.name == '.DS_Store':
                continue
            if entry.is_symlink():
                counts['links'] += 1
            elif entry.is_file(follow_symlinks=False):
                counts['files'] += 1
            elif entry.is_dir(follow_symlinks=False):
                counts['dirs'] += 1
except OSError as error:
    print(f'Cannot count {directory!r}: {error.strerror}', file=sys.stderr)
    sys.exit(1)
if exclude_dsstore == '1':
    print(counts[mode])
else:
    print(f'{counts[mode]} {mode}')
    if counts['links']:
        print(f'symbolic: {counts["links"]}')
PY
}

fcount() {
  local OPTIND=1 opt mode='' hidden=0
  while getopts 'fdah' opt; do
    case "$opt" in
      f) mode=files ;;
      d) mode=dirs ;;
      a) hidden=1 ;;
      h) echo 'Usage: fcount [-f|-d] [-a] [DIRECTORY]'; return 0 ;;
      *) return 2 ;;
    esac
  done
  shift $((OPTIND - 1))
  if [ -z "$mode" ] || [ "$#" -gt 1 ]; then
    echo 'Usage: fcount [-f|-d] [-a] [DIRECTORY]' >&2
    return 2
  fi
  _dotfiles_count_entries "${1:-.}" "$mode" "$hidden" 0
}

count_files() {
  [ "$#" -le 1 ] || { echo 'Usage: count_files [DIRECTORY]' >&2; return 2; }
  _dotfiles_count_entries "${1:-.}" files 1 1
}

fff() {
  [ "$#" -eq 1 ] || { echo 'Usage: fff NAME_PATTERN' >&2; return 2; }
  local file_name="$1"
  find . -name "$file_name"
}

ffs() {
  [ "$#" -eq 1 ] || { echo 'Usage: ffs PREFIX' >&2; return 2; }
  local prefix="$1"
  find . -name "$prefix*"
}

ffe() {
  [ "$#" -eq 1 ] || { echo 'Usage: ffe SUFFIX' >&2; return 2; }
  local suffix="$1"
  find . -name "*$suffix"
}

mkd() {
  if [ "$#" -ne 1 ] || [ -z "${1:-}" ]; then echo 'Usage: mkd DIRECTORY' >&2; return 2; fi
  local destination=$1
  case "$destination" in /*) ;; *) destination="./$destination" ;; esac
  command mkdir -p -- "$destination" && builtin cd -- "$destination" || return
}

get_size() {
  [ "$#" -eq 1 ] || { echo 'Usage: get_size PATH' >&2; return 2; }
  local target="$1"
  local size size_gb size_mb size_kb operand
  case "$target" in -*) operand="./$target" ;; *) operand=$target ;; esac

  if [[ ! -e "$target" ]]; then
    echo "Error: File or folder not found!"
    return 1
  fi

  if [[ "$(uname -s)" == Darwin ]]; then
    # BSD stat reports apparent size for files; du handles directories.
    if [[ -f "$target" ]]; then
      size=$(command stat -f %z "$operand") || return
    else
      size=$(command du -sk "$operand") || return
      size=${size%%[[:space:]]*}
      case "$size" in ''|*[!0-9]*) echo 'Invalid size returned by du.' >&2; return 1 ;; esac
      size=$(awk -v size="$size" 'BEGIN {printf "%.0f", size * 1024}') || return
    fi
  else
    size=$(command du -sb "$operand") || return
    size=${size%%[[:space:]]*}
  fi
  case "$size" in ''|*[!0-9]*) echo 'Invalid size returned by size backend.' >&2; return 1 ;; esac
  if [[ $size -lt 1024 ]]; then
    echo "Size of '$target': $size B"
  elif [[ $size -lt 1048576 ]]; then
    size_kb=$(awk -v size="$size" 'BEGIN {printf "%.2f", size / 1024}')
    echo "Size of '$target': $size_kb KB"
  elif [[ $size -ge 1073741824 ]]; then
    size_gb=$(awk -v size="$size" 'BEGIN {printf "%.2f", size / 1073741824}')
    echo "Size of '$target': $size_gb GB"
  else
    size_mb=$(awk -v size="$size" 'BEGIN {printf "%.2f", size / 1048576}')
    echo "Size of '$target': $size_mb MB"
  fi
}
