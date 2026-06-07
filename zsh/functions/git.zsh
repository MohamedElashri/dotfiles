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
