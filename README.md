# dotfiles

Personal Linux/macOS configuration for shells, Git, SSH, editors, terminals,
and Codex/Claude Code audit skills. Installed files link to this checkout;
keep it in place.

## Setup

Install Git, Bash, Python 3.9+, and [Homebrew](https://brew.sh), then:

```bash
git clone --filter=blob:none --depth=1 https://github.com/MohamedElashri/dotfiles.git ~/projects/dotfiles
cd ~/projects/dotfiles
./bin/dotfiles bootstrap --dry-run
./bin/dotfiles bootstrap
```

Bootstrap installs packages and pinned shell/editor assets, links configuration,
and enables Git hooks. Optional flags: `--dev`, `--apps` (macOS), `--fonts meslo`,
`--skip-packages`, and `--skip-assets`. See `./bin/dotfiles bootstrap --help`.
Set up 1Password, GitHub, and Atuin accounts separately, then open a new shell.

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

Edit `shell/`, `bash/`, `zsh/`, `platform/`, or `config/`. Package, plugin, and
font choices live in `setup/`; `dotfiles fonts --list` lists optional fonts.
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

## Audit skills

`agent-workflow/global.md` links to `~/.codex/AGENTS.md`. The two shared skill
folders link into `~/.agents/skills/` and `~/.claude/skills/`.
Use `$research-audit` / `$engineering-audit` in Codex, or
`/research-audit` / `/engineering-audit` in Claude Code. Audits are read-only
unless edits are authorized. Provider settings and unrelated skills stay local;
no account/web sync is configured. Custom harness homes need manual review.
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
