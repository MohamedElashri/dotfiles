# Lazy nvm wrappers. Sourcing nvm.sh is expensive, so do it only on first use.

if [[ -z "${NVM_DIR-}" ]]; then
  if [[ -n "${XDG_CONFIG_HOME-}" ]]; then
    export NVM_DIR="$XDG_CONFIG_HOME/nvm"
  else
    export NVM_DIR="$HOME/.nvm"
  fi
fi

if [[ -s "$NVM_DIR/nvm.sh" ]]; then
  _load_nvm() {
    unset -f nvm node npm npx corepack yarn pnpm 2>/dev/null
    source "$NVM_DIR/nvm.sh"
    [[ -s "$NVM_DIR/bash_completion" ]] && source "$NVM_DIR/bash_completion"
  }

  nvm() { _load_nvm && nvm "$@"; }
  node() { _load_nvm && command node "$@"; }
  npm() { _load_nvm && command npm "$@"; }
  npx() { _load_nvm && command npx "$@"; }
  corepack() { _load_nvm && command corepack "$@"; }
  yarn() { _load_nvm && command yarn "$@"; }
  pnpm() { _load_nvm && command pnpm "$@"; }
fi
