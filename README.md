# dotfiles

Personal Linux/macOS configuration for Bash, Zsh, Git, SSH, editors, terminals,
and coding agents. Installed files link to this checkout; keep it in place.

## Setup

Run as your normal user:

```bash
git clone --filter=blob:none --depth=1 https://github.com/MohamedElashri/dotfiles.git ~/projects/dotfiles
cd ~/projects/dotfiles
./bin/dotfiles bootstrap --dry-run
./bin/dotfiles bootstrap
```

Bootstrap provisions system prerequisites, Homebrew packages, pinned shell/editor
assets, fonts, desktop apps, configuration links, and repository hooks. It also
selects Zsh as your login shell. Downloads need internet access; privileged
steps may request administrator authentication. Missing Python is bootstrapped
first, which limits the preview to a stage overview until Python is available.

Automatic setup supports Apple Silicon macOS 15+, Debian/Ubuntu derivatives, and
Fedora. Linux desktop apps require x86_64 and a desktop session. Apps are listed
in `setup/mac-apps.txt` and `setup/linux-apps.json`. Installed packages/apps are
kept; native dependencies may be updated. Account sign-ins, GPU drivers, and
enabling the 1Password SSH agent remain device-local. Log out/in after setup.

For a server, use `--skip-apps --skip-shell`. Other selections are `--skip-dev`,
`--skip-fonts`, `--fonts meslo`, `--skip-assets`, or `--skip-packages --skip-apps`
for preinstalled tools. Run `./bin/dotfiles bootstrap --help` for all options.

Classic dotfiles are the default. Setup, sync and diagnostics work without the
agent workflow files, harness binaries, accounts, or evaluation dependencies.
The link-only installer needs Bash and standard system utilities; the main CLI
uses Python 3.9+ and its standard library.

| Install scope | Preview | Install |
| --- | --- | --- |
| Configuration links | `./install.sh --dry-run` | `./install.sh` |
| Configuration and agent links | `./install.sh --with-agents --dry-run` | `./install.sh --with-agents` |
| Agent instructions and shared skills | `./install.sh --agents-only --dry-run` | `./install.sh --agents-only` |

Replaced files are backed up under `~/.dotfiles-backup/`. Put wanted device
settings in the local overrides below. Parent directories must be real,
searchable directories; resolve symlinks or conflicts before installation.
Skill directories with extra user files also require manual reconciliation.
A [ZIP download](https://github.com/MohamedElashri/dotfiles/archive/refs/heads/main.zip)
works for setup; hooks and sync require a Git clone.

## Daily use

```bash
dotfiles doctor
dotfiles sync --check
dotfiles sync --dry-run
dotfiles sync
```

Use `./bin/dotfiles` until it is on PATH. Sync requires a clean tracking branch,
fast-forwards from its upstream, restores missing links, and updates enabled
shell/editor assets. It stops on replaced links or divergent history. Inspect
links with `./install.sh --status` (`--agents-only` limits the scope). Preserve
wanted edits before reinstalling; rerun the installer after moving the checkout.
Use `dotfiles doctor --online` to include GitHub authentication checks.
Add `--with-agents` to bootstrap, sync, doctor, or the installer when you want
agent links included. This choice is explicit for each command; ordinary commands
leave existing agent files alone.

## Customize

| Location | Purpose |
| --- | --- |
| `shell/aliases.sh`, `shell/functions/` | Shared CLI shortcuts and helpers |
| `bash/`, `zsh/` | Shell startup and tool integration |
| `platform/linux/`, `platform/mac/` | Native command variants |
| `config/` | Application preferences, Git, and SSH |
| `setup/` | Packages, apps, pinned assets, and fonts |
| [`agent-workflow/AGENTS.md`](agent-workflow/AGENTS.md) | Shared coding-agent defaults |

Both shells load `shell/interactive.sh`; `list_commands` lists available helpers.
Optional-tool shortcuts load when their commands are installed. Run
`dotfiles render` after changing Waveterm source settings or `setup/assets.json`
and keep the generated outputs. Use `dotfiles fonts --list` to inspect families.

Device-only overrides live in `~/.config/dotfiles/local.bash`, `local.zsh`,
`local.env.zsh`, and `local.gitconfig`; examples are in `templates/local/`.
Keep credentials, keys, account state, and history outside Git. Both platforms
include `~/.ssh/config.local`; keep it mode 600. Additional SSH fragments can be
included there before `Host *`. Check effective settings with `ssh -G <alias>`.

## Coding agents

Opt in with `./install.sh --agents-only`, or add `--with-agents` to bootstrap or
the installer for combined setup. Classic dotfiles do not load the agent Python
modules or require anything under `agent-workflow/`.

Edit [`agent-workflow/AGENTS.md`](agent-workflow/AGENTS.md) here to change global
development defaults, then start new agent sessions. All four harnesses link to
that one file, so content edits need no reinstall.

| Harness | Global instruction file |
| --- | --- |
| [Codex](https://developers.openai.com/codex/guides/agents-md/) | `~/.codex/AGENTS.md` |
| [Claude Code](https://code.claude.com/docs/en/memory) | `~/.claude/CLAUDE.md` |
| [OpenCode](https://opencode.ai/docs/instructions/) | `~/.config/opencode/AGENTS.md` |
| [pi](https://github.com/earendil-works/pi/tree/main/packages/coding-agent#context-files) | `~/.pi/agent/AGENTS.md` |

The installer uses these default locations. Custom harness homes require manual
links to the same source at the harness's documented instruction path. Repository
instructions and harness overrides can change which guidance applies; inspect
loaded context if defaults are missing. `--status` verifies links only.

Shared skills link into `~/.agents/skills/` and `~/.claude/skills/`. Invoke
`$research-audit` / `$engineering-audit` in Codex, or `/research-audit` /
`/engineering-audit` in Claude Code. Audits are read-only unless edits are
authorized. Harness binaries, credentials, settings, sessions, and unrelated
skills stay local. The specialized `cuda-performance` skill is also installed;
it does not add domain assumptions to the global policy. Review project agent
guidance before adding it to Git.

Project onboarding and local diagnostics:

```bash
dotfiles agents doctor
dotfiles agents init --target /absolute/project/path --dry-run
```

Initialization preserves existing project guidance and never changes ignore
rules. Add `--with-plan` to create a single plan template when one is absent.
Source templates live in `agent-workflow/templates/`.

Synthetic evaluations separate offline scoring from live agent execution:

```bash
dotfiles agents eval list
dotfiles agents eval score --case E03 --candidate /absolute/candidate --trusted-candidate
dotfiles agents eval report --format json
dotfiles agents eval prune --days 30
```

Functional scoring executes trusted submitted code; it is not a hostile-code
sandbox. A live run needs separate authorization and explicit limits, for example:

```bash
dotfiles agents eval run --case E03 --harness codex --live --profile trusted \
  --timeout 180 --output-limit 1048576 --auth-file "$HOME/.codex/auth.json"
```

Only the Codex 0.169.x adapter is implemented. It requires a passing native
boundary probe and refuses protected/adversarial modes. Reports contain hashes,
versions, limits, outcomes and available usage metadata, with unknown cost kept
as null. State stays outside Git under the private XDG state directory. Pruning
is a preview unless `--apply` is supplied. See [contracts, capabilities, safety
limits, and recovery](docs/agent-evaluations.md) for details. Normal setup and CI
remain offline with respect to model execution.

## Checks

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_private.py --worktree
python3 scripts/render_configs.py --check
git diff --check
```

Tests require Git, Python, Bash, Zsh, and SSH. They use temporary homes, local Git
remotes, and mocked platform/tool operations. Commit/push hooks scan private data;
chain them manually when using a custom Git hooks path.
