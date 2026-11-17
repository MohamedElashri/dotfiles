# Docker helpers; Docker remains an optional, separately installed tool.

dalias() {
  alias | grep 'docker' | sed "s/^\([^=]*\)=\(.*\)/\1 => \2/" | sed "s/['|\']//g" | sort
  alias | grep '__d' | sed "s/^\([^=]*\)=\(.*\)/\1 => \2/" | sed "s/['|\']//g" | sort
}

dbash() {
  [ "$#" -eq 1 ] || { echo 'Usage: dbash CONTAINER_FILTER' >&2; return 2; }
  local identifier
  identifier=$(docker ps -q --filter "name=$1") || return
  case "$identifier" in
    ''|*$'\n'*) echo 'Expected exactly one running container; refine the filter.' >&2; return 1 ;;
  esac
  docker exec -it "$identifier" bash
}

dip() {
  [ "$#" -gt 0 ] || { echo 'Usage: dip CONTAINER...' >&2; return 2; }
  local container
  for container in "$@"; do
    docker inspect -f "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" "$container" || return
  done
}

dst() {
  [ "$#" -le 1 ] || { echo 'Usage: dst [PATTERN]' >&2; return 2; }
  local output
  output=$(docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.PIDs}}') || return
  if [[ -z ${1:-} ]]; then
    printf '%s\n' "$output"
  else
    printf '%s\n' "$output" | command grep --color=auto -- "$1"
  fi
}

# Read one ID at a time so Bash and Zsh pass identical arguments without
# relying on their different unquoted command-substitution splitting rules.
_dotfiles_docker_action() {
  local action=$1 ids pattern selected identifier matches='' result
  shift
  if [ "$action" = rmi ]; then
    ids=$(docker images --filter 'dangling=true' -aq --no-trunc) || return
  else
    ids=$(docker ps -aq --no-trunc) || return
  fi
  [ -n "$ids" ] || return 0
  if [ "$#" -eq 0 ]; then set -- '.'; fi
  for pattern in "$@"; do
    if selected=$(printf '%s\n' "$ids" | command grep -- "$pattern"); then
      matches="$matches$selected"$'\n'
    else
      result=$?
      [ "$result" -eq 1 ] || return "$result"
    fi
  done
  # Validate every filter before making changes, and act once per selected ID.
  matches=$(printf '%s' "$matches" | awk 'NF && !seen[$0]++') || return
  while IFS= read -r identifier; do
    [ -n "$identifier" ] || continue
    docker "$action" "$identifier" || return
  done <<< "$matches"
}

dstop() { _dotfiles_docker_action stop "$@"; }
drm() { _dotfiles_docker_action rm "$@"; }
drmi() { _dotfiles_docker_action rmi "$@"; }
