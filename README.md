# dotfiles

Personal Linux/macOS configuration for shells, Git, SSH, editors, terminals,
and shared coding-agent instructions and audit skills. Installed files link to
this checkout; keep it in place.

## Setup

Clone this repository (or unpack the [ZIP download](https://github.com/MohamedElashri/dotfiles/archive/refs/heads/main.zip)),
then run as your normal user:

```bash
git clone --filter=blob:none --depth=1 https://github.com/MohamedElashri/dotfiles.git ~/projects/dotfiles
cd ~/projects/dotfiles
./bin/dotfiles bootstrap --dry-run
./bin/dotfiles bootstrap
```

Bootstrap installs system prerequisites, [Homebrew](https://docs.brew.sh/Installation),
CLI/development tools, pinned shell/editor assets, all fonts in `setup/fonts.json`,
selected GUI apps, configuration links, and Git hooks. It also selects Zsh as your
login shell. Missing Python is bootstrapped too; its absence limits the preview
to a stage overview. Administrator authentication may be requested.

Automatic provisioning targets Apple Silicon macOS 15+ and current Debian/Ubuntu
derivatives or Fedora. Linux GUI packages require x86_64 and an existing desktop:
Kitty, native [1Password](https://support.1password.com/install-linux/),
[VS Code](https://code.visualstudio.com/docs/setup/linux), and
[Zed](https://zed.dev/docs/installation). Mac apps are listed in `setup/mac-apps.txt`.
Installed formulas and GUI apps are skipped; native dependencies may be updated.
Downloads require internet access. GPU drivers, account sign-ins, and enabling
the 1Password SSH agent remain device-local.

For a server, add `--skip-apps --skip-shell`. Other exclusions: `--skip-dev`,
`--skip-fonts`, `--skip-assets`, or `--skip-packages --skip-apps` for your own
package manager. `--fonts meslo` selects a smaller font set. See
`./bin/dotfiles bootstrap --help`. Rerun after a failed stage; log out/in afterward.
Archive downloads work for setup; repository hooks and sync require a Git clone.

For links only, preview `./install.sh --dry-run`, then run `./install.sh`.
Only the personal profile is supported. Replaced targets are backed up under
`~/.dotfiles-backup/`. Extra files in skill folders or inaccessible agent
folders must be reconciled before installation.

## Daily use

```bash
dotfiles doctor
dotfiles sync --check
dotfiles sync --dry-run
dotfiles sync
```

Use `./bin/dotfiles` if the command is not on PATH yet. Sync requires a clean
tracking branch and refuses replaced links or divergent history. Missing links
are recreated. Use `./install.sh --status` to inspect drift; preserve desired
edits before reinstalling. Rerun the installer after moving the checkout.

## Customize

Both Bash and Zsh load `shell/interactive.sh`: common shortcuts live in
`shell/aliases.sh`, and helpers are grouped under `shell/functions/` by archives,
files, development, Docker, network, and system. Native OS adapters live in
`platform/linux/` and `platform/mac/`; shell hooks stay in `bash/` and `zsh/`.
Optional-tool aliases appear when their commands are available. `list_commands`
shows loaded shortcuts/helpers. `ll`, `la`, and `ports` now match across shells;
`update`/`upgrade` manage Homebrew on both OSes, while `mac-update` updates macOS.

App preferences live in `config/`. Package, plugin, and font choices live in
`setup/`; `dotfiles fonts --list` lists available font families.
After changing Waveterm source preferences or `setup/assets.json`, run
`dotfiles render` and keep the generated outputs too.

Device-only overrides belong in `~/.config/dotfiles/local.bash`, `local.zsh`,
`local.env.zsh`, and `local.gitconfig`; examples are in `templates/local/`.
Keep credentials, keys, history databases, and application runtime state outside Git.

Both platforms read `~/.ssh/config.local`. Temporary routes can live in
`~/.ssh/config.hep.local`, included from the top of `config.local`:

```sshconfig
Include ~/.ssh/config.hep.local

Host *
```

Keep private SSH files mode 600. Comment/remove the include to disable those
routes; `ssh -G <alias>` checks effective settings without connecting.

## Coding agents

Edit [`agent-workflow/AGENTS.md`](agent-workflow/AGENTS.md) to change personal
development defaults for every supported harness. It covers scoped changes,
local planning, verification, Conventional Commits, concise PR descriptions,
and communication. This is the single shared source: edit it here, then start
new agent sessions to pick up changes. Once installed, the symlinks expose edits
directly; you do not need to reinstall after changing the content. Each harness
receives the same file at its native global instruction path:

| Harness | Installed instruction file | Loading reference |
| --- | --- | --- |
| Codex | `~/.codex/AGENTS.md` | [AGENTS.md guide](https://developers.openai.com/codex/guides/agents-md/) |
| Claude Code | `~/.claude/CLAUDE.md` | [Memory guide](https://code.claude.com/docs/en/memory) |
| OpenCode | `~/.config/opencode/AGENTS.md` | [Instructions](https://opencode.ai/docs/instructions/), [V1 rules](https://opencode.ai/v1/docs/rules/) |
| pi | `~/.pi/agent/AGENTS.md` | [Context files](https://github.com/earendil-works/pi/tree/main/packages/coding-agent#context-files) |

Install just agent instructions and the two existing audit skills on Linux or
macOS, without changing shell or application configuration:

```bash
./install.sh --agents-only --dry-run
./install.sh --agents-only
./install.sh --agents-only --status
```

The regular installer/bootstrap also includes these links. Existing destination
files are moved to `~/.dotfiles-backup/<run>/<original-path>` before replacement;
review or merge any personal instructions from those backups. Repeat installs
leave correct links alone. Provider settings, credentials, sessions, plugins,
and unrelated skills stay local. Parent symlinks and inaccessible agent folders
must be reconciled before installation. No harness installation, account setup,
or web synchronization is performed. Keep this checkout in place and start new
agent sessions after setup or edits.

The installer targets the default paths above, regardless of environment
overrides. If you use `CODEX_HOME`, `CLAUDE_CONFIG_DIR`, `PI_CODING_AGENT_DIR`, or
a custom OpenCode configuration location, use the harness's documentation to
locate its effective global instruction file and link that file manually. For
example, for an existing custom Codex profile:

```bash
: "${CODEX_HOME:?Set CODEX_HOME to your custom absolute profile directory}"
mkdir -p "$CODEX_HOME"
ln -s "$PWD/agent-workflow/AGENTS.md" "$CODEX_HOME/AGENTS.md"
```

Run this from the checkout with `CODEX_HOME` set to the intended absolute path;
`ln -s` refuses an existing file, which you should review and back up first.
For another harness, use the same source with its documented user instruction
filename. A bare `~/AGENTS.md` is not a universal global configuration, and
Markdown `@` imports are not supported by every harness.

Repository and directory instructions refine these defaults according to each
harness's loading rules. Codex's `AGENTS.override.md` can replace the global
file; the installer preserves it. pi also supports override files in current
versions and can disable context loading. Check those controls if guidance is
missing. Use Claude Code's `/memory` to inspect loaded files; for other harnesses,
check their context diagnostics and ask a new session to summarize its active
instructions. `--status` checks links, not whether a model follows the rules.

The two shared skill folders link into `~/.agents/skills/` and `~/.claude/skills/`.
Use `$research-audit` / `$engineering-audit` in Codex, or
`/research-audit` / `/engineering-audit` in Claude Code. Audits are read-only
unless edits are authorized. Skill discovery in other harnesses depends on
their version and configuration; instruction-file support is independent.
Project agent guidance is visible to Git: inspect new files before adding them.

## Checks

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_private.py --worktree
python3 scripts/render_configs.py --check
git diff --check
```

Tests require Git, Python, Bash, Zsh, and SSH, and use disposable homes and local
Git remotes. Commit/push hooks scan private data; custom hook paths must chain them.
