#!/usr/bin/env python3
"""Check dotfiles for credentials without displaying their values.

The commit hook checks staged additions. Worktree and history modes support
manual audits; history mode scans reachable Git blobs, including old versions.
"""

import argparse
import pathlib
import re
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
MAX_TEXT_BYTES = 2_000_000

RULES = (
    ("private key", re.compile(rb"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{40,})\b")),
    ("GitLab token", re.compile(rb"\bglpat-[A-Za-z0-9_-]{20,}\b")),
    ("AWS access key", re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("Google API key", re.compile(rb"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Slack token", re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("OpenAI-style key", re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{30,}\b")),
    ("Bearer token", re.compile(rb"\bBearer [A-Za-z0-9._~+/-]{24,}\b")),
)
ASSIGNMENT = re.compile(
    rb"(?im)(?:^|[{,])\s*['\"]?([A-Za-z][\w.-]*(?:_TOKEN|_SECRET|_PASSWORD|_API_KEY|_PRIVATE_KEY|_ACCESS_KEY|_SECRET_KEY|password|secret|oauth_token))['\"]?\s*[:=]\s*(?:['\"]([^'\"\r\n]{12,})['\"]|([A-Za-z0-9._~+/=-]{16,}))"
)
PLACEHOLDER = re.compile(rb"(?i)(example|placeholder|replace|your[_ -]|change[_ -]me|dummy|<|\$\{|\{\{)")
PROTECTED_NAMES = {
    "auth.json", "auth.db", "oauth_creds.json", "hosts.yml",
    "credentials", "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa",
}
PROTECTED_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".kdbx", ".sqlite", ".sqlite3")


def git(*args, input_bytes=None):
    result = subprocess.run(
        ["git", *args], cwd=ROOT, input=input_bytes,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", "replace").strip())
    return result.stdout


def check_path(path):
    name = pathlib.PurePosixPath(path).name.lower()
    if name in PROTECTED_NAMES or name.endswith(PROTECTED_SUFFIXES):
        return "credential file name"
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        return "environment file name"
    if path == "config/mac/cli/opencode/config.json":
        return "local OpenCode credentials file"
    if path in ("config/mac/cli/opencode/opencode.jsonc", "config/mac/cli/dnscrypt-proxy/dnscrypt-proxy.toml"):
        return "private service endpoint file"
    if path in ("config/mac/ssh/config.local", ".ssh/config.local"):
        return "private SSH routes file"
    return None


def check_content(data):
    if len(data) > MAX_TEXT_BYTES or b"\0" in data:
        return None
    for label, pattern in RULES:
        if pattern.search(data):
            return label
    for match in ASSIGNMENT.finditer(data):
        value = match.group(2) or match.group(3)
        if not PLACEHOLDER.search(value):
            return "credential assignment"
    return None


def staged_files():
    names = git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
    for raw in filter(None, names.split(b"\0")):
        path = raw.decode("utf-8", "surrogateescape")
        yield path, git("show", ":" + path)


def worktree_files():
    names = git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    for raw in filter(None, names.split(b"\0")):
        path = raw.decode("utf-8", "surrogateescape")
        full = ROOT / path
        if full.is_file() and not full.is_symlink():
            if full.stat().st_size <= MAX_TEXT_BYTES:
                yield path, full.read_bytes()
            else:
                yield path, b""


def history_files():
    objects = git("rev-list", "--objects", "--all").splitlines()
    paths = {}
    for line in objects:
        oid, sep, raw_path = line.partition(b" ")
        if sep:
            paths.setdefault(oid, raw_path.decode("utf-8", "surrogateescape"))
    if not paths:
        return
    checks = git("cat-file", "--batch-check", input_bytes=b"\n".join(paths) + b"\n").splitlines()
    selected = []
    for line in checks:
        oid, kind, size = line.split()
        if kind == b"blob" and int(size) <= MAX_TEXT_BYTES:
            selected.append(oid)
    if not selected:
        return
    batch = git("cat-file", "--batch", input_bytes=b"\n".join(selected) + b"\n")
    pos = 0
    for expected in selected:
        end = batch.index(b"\n", pos)
        oid, kind, size = batch[pos:end].split()
        pos = end + 1
        count = int(size)
        data = batch[pos:pos + count]
        pos += count + 1
        if oid != expected or kind != b"blob":
            raise RuntimeError("Unexpected Git object response")
        yield paths[oid] + "@" + oid[:8].decode("ascii"), data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--staged", action="store_true")
    modes.add_argument("--worktree", action="store_true")
    modes.add_argument("--history", action="store_true")
    args = parser.parse_args()
    files = staged_files() if args.staged else history_files() if args.history else worktree_files()
    findings = []
    for path, data in files:
        base_path = path.split("@", 1)[0] if args.history else path
        reason = check_path(base_path) or check_content(data)
        if reason:
            findings.append((path, reason))
    for path, reason in findings:
        print(f"{path}: {reason}")
    print(f"Private-data check: {len(findings)} finding(s).")
    return 1 if findings else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError) as error:
        print(f"Private-data check failed: {error}", file=sys.stderr)
        sys.exit(2)
