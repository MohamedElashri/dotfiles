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
