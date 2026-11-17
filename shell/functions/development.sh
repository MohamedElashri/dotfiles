# Development, editor selection, and Git helpers.

unalias edit_host 2>/dev/null || true
edit_host() {
  local editor
  # sudo needs an executable path, not the description of a shell alias/function.
  if [ -n "${ZSH_VERSION-}" ]; then
    editor=$(builtin whence -p micro || builtin whence -p nano) || { echo 'Install micro or nano first.' >&2; return 1; }
  else
    editor=$(builtin type -P micro || builtin type -P nano) || { echo 'Install micro or nano first.' >&2; return 1; }
  fi
  sudo "$editor" /etc/hosts
}

crun() {
  if [ "$#" -ne 1 ] || [ -z "${1:-}" ]; then echo 'Usage: crun SOURCE_STEM' >&2; return 2; fi
  local source=$1
  case "$source" in -*) source="./$source" ;; esac
  command mkdir -p "build" && g++ "$source.cpp" -std=c++17 -o "build/$1.out" && "./build/$1.out"
}

GrePFind() {
  [ "$#" -eq 2 ] || { echo 'Usage: GrePFind DIRECTORY PATTERN' >&2; return 2; }
  command grep --color=auto -rnw -e "$2" -- "$1"
}

git_root() {
  local root
  root=$(git rev-parse --show-toplevel) || return
  cd "$root" || return
}

git_search() {
  [ "$#" -gt 0 ] || { echo 'Usage: git_search QUERY [GIT OPTIONS/PATHS...]' >&2; return 2; }
  local query=$1
  shift
  git log -S "$query" --source --all "$@"
}

create_and_push_repo() {
  if [ "$#" -lt 1 ] || [ "$#" -gt 2 ] || [ -z "$1" ]; then
    echo 'Usage: create_and_push_repo NAME [--private|--public]' >&2
    return 2
  fi
  local repo_name="$1" privacy_flag=--public
  [ "$#" -ne 2 ] || privacy_flag=$2
  case "$privacy_flag" in
    --private|--public) ;;
    *) echo 'Use --private or --public.' >&2; return 2 ;;
  esac
  if ! command -v gh >/dev/null 2>&1; then
    echo "Error: GitHub CLI (gh) is not installed. Please install it first."
    return 1
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

nvims() {
  local items config candidate config_root
  config_root="${XDG_CONFIG_HOME:-$HOME/.config}"
  items=("default")
  for candidate in kickstart LazyVim NvChad AstroNvim; do
    [[ -d "$config_root/$candidate" ]] && items+=("$candidate")
  done
  if (( ${#items[@]} == 1 )) || ! command -v fzf >/dev/null 2>&1; then
    nvim "$@"
    return
  fi
  config=$(printf "%s\n" "${items[@]}" | fzf --prompt=" Neovim Config  " --height=50% --layout=reverse --border --exit-0) || return
  if [[ -z $config ]]; then
    echo "Nothing selected"
    return 0
  elif [[ $config == "default" ]]; then
    config=""
  fi
  NVIM_APPNAME=$config nvim "$@"
}
