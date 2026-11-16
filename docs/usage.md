# Dotfiles usage

The personal profile links a Codex global file and the same two skill directories
into both Codex and Claude Code on Linux and macOS:

| Repository source | Destination |
|---|---|
| `agent-workflow/global.md` | `~/.codex/AGENTS.md` |
| `agent-workflow/skills/research-audit/` | `~/.agents/skills/research-audit/` |
| `agent-workflow/skills/engineering-audit/` | `~/.agents/skills/engineering-audit/` |
| `agent-workflow/skills/research-audit/` | `~/.claude/skills/research-audit/` |
| `agent-workflow/skills/engineering-audit/` | `~/.claude/skills/engineering-audit/` |

The Codex global guidance covers everyday evidence and verification habits;
the installer preserves Claude's own `CLAUDE.md` and settings. Use the shared
`research-audit` for consequential research claims and source checks, or
`engineering-audit` for implementation audits:

| Harness | Explicit invocation |
|---|---|
| Codex | `$research-audit`, `$engineering-audit` |
| Claude Code | `/research-audit`, `/engineering-audit` |

These skills apply to
explicit or clearly applicable audits, rather than every ordinary task.
Audits are read-only unless the invoking task authorizes edits.

## Preview and install

From the checkout root:

```bash
./install.sh --profile personal --dry-run
./install.sh --profile personal --list
./install.sh --profile personal --manifest
./install.sh --profile personal
./install.sh --profile personal --status
```

`--manifest` and `--list` print the same tab-separated source/target pairs.
Preview and inspection commands do not create directories or change files.
Only `personal` is supported; there is no `minimal` profile in this checkout.

The global file and each harness's two named skill directories are managed separately,
preserving unrelated skills and private application configuration. Skill
manifests are regular `SKILL.md` files inside the linked directories: the tested
Codex CLI skips manifest-file symlinks during discovery. Existing targets are moved to
`~/.dotfiles-backup/<run>/<original-relative-path>` before replacement.
Repeat installation leaves correct links and backups alone.

A real skill directory containing only `SKILL.md` (or no files) can be backed up
and replaced. If it contains other entries, including hidden files or dangling
links, installation stops with `Unmanaged skill contents` before any configuration
writes. Reconcile that content manually; it is never silently moved or hidden.
Unreadable or unsearchable real skill directories also stop preflight with
`Cannot inspect skill directory`, preventing a partial installation.
When a link needs changes, installation and update preflight also require write
access to its existing parent and to any real skill directory being moved into
backup. Correct managed links remain usable under read-only parents.
Earlier managed manifest-file links migrate through the same backup mechanism
when no sibling content is present. Sync still refuses unmanaged manifests.

Agent parent directories must be real, searchable directories. If `.codex`,
`.agents`, `.agents/skills`, `.claude`, or `.claude/skills` is a symlink, an
ordinary file, or an unsearchable directory, installation and
diagnostics stop with `Blocked agent parent` before changing any configuration.
List/manifest remain available. Reconcile the existing directory layout manually;
the installer does not replace directory links or write through them into a
shared skill store or another checkout.

If `--status` reports a detached file, compare it with the reported source and
preserve any desired edits before reinstalling. `--check-existing` and
`dotfiles sync --check` refuse existing conflicts without replacing them.
Missing targets are reported by status/doctor and recreated on install/sync.
After moving the checkout, rerun its installer to repair links using the saved
profile marker. Backups remain available for manual recovery; there is no
automatic rollback command.

## Ownership and discovery

These paths target the harnesses' default homes. A custom `CODEX_HOME` or an existing
`~/.codex/AGENTS.override.md` can change which global instructions are loaded.
A custom `CLAUDE_CONFIG_DIR` changes where Claude finds personal skills and
requires manual review of these default links.
Private provider settings, authentication, sessions, permissions, caches,
local endpoints, and unrelated skills remain outside this repository.
The installer does not install either harness or change account/model settings.

For an optional discovery check with an already installed Codex, use a
disposable HOME and repository. Install links into that home, then start a new
Codex session and inspect its loaded instructions and skill list. Request each
audit explicitly on harmless fixtures; try a small ordinary task to check that
both skills are not forced into every interaction. Treat this as a separate
runtime check: link tests alone do not establish model behavior. Such sessions
can require credentials and network and incur usage; do not put them in CI.
Never copy credentials into this checkout to run the check.

For Claude Code, start a new local session and inspect the `/` command menu for
both audit names. Its SDK initialization metadata can also list commands without
sending a user/model prompt; a successful listing verifies discovery, not audit
quality or automatic selection. Use a disposable home for these checks.

The [official instruction guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
and [skill guide](https://learn.chatgpt.com/docs/build-skills) describe discovery
and frontmatter. Claude's [skill guide](https://code.claude.com/docs/en/skills)
documents its personal skill directories, directory links, and slash commands.
Other harnesses are outside the current installer scope. Local instructions do
not update ChatGPT web personalization, sync web chats, or upload skills to
Claude account, Cowork, or cloud sessions.

## Git ignore migration

The managed global ignore allows project `AGENTS.md` and `.agents/skills/` so
teams can deliberately version their guidance. `.codex/`, `AGENTS.override.md`,
and credential patterns stay ignored. Other repositories may expose previously
hidden instruction files as untracked: inspect their contents and ownership
before adding them. The installer never stages or commits files in any repository.

## Private and temporary SSH routes

Both platforms read `~/.ssh/config.local`; Linux loads it before shared routes
and defaults so local values take precedence. Keep temporary host groups in a
separate private file, such as `~/.ssh/config.hep.local`, and include it near the
top of `config.local`:

```sshconfig
Include ~/.ssh/config.hep.local

Host *
```

The final `Host *` resets matching scope before any additional local settings.
Keep these files mode 600 under the existing private SSH directory. Comment out
the include, or remove the fragment, to disable the temporary routes. These
private filenames are ignored and rejected by the commit scanner if copied into
the repository's SSH configuration directories. Use `ssh -G <alias>` to inspect
effective settings without connecting; actual login/authentication is a separate
check.
