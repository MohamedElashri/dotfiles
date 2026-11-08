#!/usr/bin/env bash
# Read-only, offline diagnostics. Bash 3.2 compatible; no Python dependency.
set -uo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
: "${HOME:?HOME must be set}"
profile=personal
installed=0
if [ -r "$HOME/.config/dotfiles/profile" ]; then
  IFS= read -r profile < "$HOME/.config/dotfiles/profile" || true
  installed=1
fi
while [ "$#" -gt 0 ]; do
  case "$1" in
    --profile) [ "$#" -ge 2 ] || { echo '--profile requires personal, minimal, or hep' >&2; exit 2; }; profile=$2; shift ;;
    --help|-h) echo 'Usage: dotfiles doctor [--profile personal|minimal|hep]'; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; exit 2 ;;
  esac
  shift
done
case "$profile" in personal|minimal|hep) ;; *) echo 'Invalid profile' >&2; exit 2 ;; esac
failures=0; warnings=0
ok() { printf '[OK] %s\n' "$*"; }
info() { printf '[INFO] %s\n' "$*"; }
fail() { printf '[FAIL] %s\n' "$*"; failures=$((failures + 1)); }
warn() { printf '[WARN] %s\n' "$*"; warnings=$((warnings + 1)); }
have() { command -v "$1" >/dev/null 2>&1; }
required() { if have "$1"; then ok "$1 available"; else fail "$1 missing: $2"; fi; }
config() { git config --global --includes --get "$1" 2>/dev/null || true; }
# Inspect the executable without evaluating arbitrary configuration or hooks.
first_program() {
  case "$1" in
    \"*) program=${1#\"}; program=${program%%\"*} ;;
    \'*) program=${1#\'}; program=${program%%\'*} ;;
    *) program=${1%% *} ;;
  esac
  case "$program" in \~/*) program="$HOME/${program#\~/}" ;; esac
}
configured_command() {
  first_program "$2"
  if [ -n "$program" ] && have "$program"; then
    ok "$1 available ($program)"
  else
    fail "$1 unavailable ($program): set an installed command in ~/.config/dotfiles/local.gitconfig"
  fi
}
printf 'Dotfiles doctor | profile: %s | OS: %s\n' "$profile" "$(uname -s)"
case "$(uname -s)" in Linux|Darwin) ;; *) fail 'Supported platforms are Linux and macOS.' ;; esac
required bash 'install Bash before running the installer'
if [ "$installed" = 0 ]; then
  fail "Profile not installed. Run ./install.sh --profile $profile (or hep/install.sh for HEP)."
else
  if bash "$ROOT/install.sh" --profile "$profile" --status; then
    ok 'Managed links are intact'
  else
    fail 'Managed links need attention. Reconcile detached files before reinstalling.'
  fi
fi
if [ "$profile" = hep ]; then
  info 'Standalone HEP requires Bash and standard Linux utilities; Git, Python, Zsh, and desktop apps are optional.'
  info 'Site modules/CVMFS and cluster authentication remain managed by the cluster.'
else
  required git 'install the essential packages in setup/README.md'
  required python3 'needed by update/rollback and private-data hooks; installation itself works without it'
  if have git; then
    for key in user.name user.email; do
      if [ -n "$(config "$key")" ]; then ok "Git $key configured"; else fail "Git $key missing: set it in ~/.config/dotfiles/local.gitconfig"; fi
    done
    editor=${GIT_EDITOR:-$(config core.editor)}
    editor=${editor:-${VISUAL:-${EDITOR:-vi}}}
    configured_command 'Git editor' "$editor"
    if [ "${GIT_PAGER+x}" = x ]; then
      pager=$GIT_PAGER
    else
      pager=$(config core.pager)
      pager=${pager:-${PAGER:-less}}
    fi
    # An explicitly empty pager disables paging and is valid.
    if [ -n "$pager" ]; then configured_command 'Git pager' "$pager"; else ok 'Git paging disabled'; fi
    log_pager=$(config pager.log)
    case "$log_pager" in
      *rg*) have rg || fail 'Git log pager needs rg (ripgrep), or override pager.log locally' ;;
    esac
    case "$log_pager" in
      *delta*) have delta || fail 'Git log pager needs delta (git-delta), or override pager.log locally' ;;
    esac
    if [ "$(git config --global --includes --bool commit.gpgsign 2>/dev/null)" = true ]; then
      format=$(config gpg.format)
      if [ "$format" = ssh ]; then
        signer=$(config gpg.ssh.program); signer=${signer:-ssh-keygen}
        [ -n "$(config user.signingkey)" ] || fail 'SSH commit signing is enabled without a signing key'
      else
        signer=$(config gpg.program); signer=${signer:-gpg}
      fi
      configured_command 'Commit signing program' "$signer"
      info 'Signing credentials/unlock are not tested. Configure them on this machine before committing.'
    else
      ok 'Commit signing is optional on this machine'
    fi
    helper=$(config 'credential.https://github.com.helper')
    case "$helper" in
      *'gh auth git-credential'*)
        required gh 'GitHub credential helper is configured; install gh or override the helper locally'
        info 'GitHub authentication: run gh auth login on a new machine; login status is not tested.' ;;
      *) info 'Git authentication: configure SSH keys or an HTTPS credential helper when pushing; credentials are not copied.' ;;
    esac
    if [ "$(git config --global --includes --bool filter.lfs.required 2>/dev/null)" = true ] && ! have git-lfs; then
      warn 'Git LFS is configured but git-lfs is missing; LFS repositories need it.'
    fi
  fi
  if [ "$profile" = personal ]; then
    have zsh || warn 'Zsh is not installed; Bash is available, but the personal Zsh configuration needs zsh.'
    [ -f "$HOME/.oh-my-zsh/oh-my-zsh.sh" ] || info 'Oh My Zsh is optional and absent; framework plugins/themes will not load.'
    info '1Password signing/SSH integration needs the app and agent configured separately.'
  else
    info 'Minimal installs Bash and Git settings only. Optional CLI tools can be added from setup/.'
  fi
fi
printf '\nDoctor: %s failure(s), %s warning(s). No settings changed; authentication was not contacted.\n' "$failures" "$warnings"
[ "$failures" = 0 ]
