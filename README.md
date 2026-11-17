# dotfiles

Personal Linux/macOS configuration for shells, Git, SSH, editors, terminals,
and Codex/Claude Code audit skills. Installed files link to this checkout;
keep it in place.

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
