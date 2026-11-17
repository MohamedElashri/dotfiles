# macOS desktop integration.

trash() { command mv -i "$@" "$HOME/.Trash/"; }

gen_pass() {
  [ "$#" -eq 0 ] || { echo 'Usage: gen_pass' >&2; return 2; }
  command -v pbcopy >/dev/null 2>&1 || { echo 'pbcopy is required.' >&2; return 1; }
  # Keep generated data out of shell variables/xtrace and copy only after
  # generation succeeds. Python is already a workstation dependency.
  command python3 -I - <<'PY'
import secrets
import string
import subprocess
import sys

try:
    password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))
    result = subprocess.run(['pbcopy'], input=password, text=True, stdout=subprocess.DEVNULL)
except OSError as error:
    print(f'Password generation or copy failed: {error.strerror}', file=sys.stderr)
    sys.exit(1)
sys.exit(result.returncode if result.returncode >= 0 else 128 - result.returncode)
PY
}
