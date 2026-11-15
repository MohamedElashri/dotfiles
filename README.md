# dotfiles

Personal Linux/macOS shell, editor, and terminal configuration.
Keep the checkout in place: installed settings link to files in this repository.
AI-tool installation, settings, plugins, and skills are managed separately.

## New device

Install Git, Python 3.9+, Bash, and [Homebrew](https://brew.sh), then clone:

```bash
git clone --filter=blob:none --depth=1 https://github.com/MohamedElashri/dotfiles.git ~/projects/dotfiles
cd ~/projects/dotfiles
./bin/dotfiles bootstrap --dry-run
./bin/dotfiles bootstrap
```

Bootstrap installs curated direct dependencies, links configuration, enables
repository hooks, and provisions pinned shell/editor assets. It preserves
existing asset checkouts unless you explicitly update them. The package
manager chooses package versions; Git assets and font archives are pinned.

Optional groups can be added in the same command or a later run:

```bash
./bin/dotfiles bootstrap --dev --apps --fonts meslo --dry-run
```

`--apps` installs macOS GUI apps. On Linux, install GUI apps with your distro's
package manager. `--skip-packages` supports an existing distro-managed toolset;
`--skip-assets` skips shell/editor downloads. Log in to 1Password, GitHub, and Atuin separately. Open a new shell afterward. See
[setup/README.md](setup/README.md) for prerequisites, optional groups, and migration.

For configuration links alone, the original installer remains available:

```bash
./install.sh --dry-run
./install.sh
```

It backs up replaced files under `~/.dotfiles-backup/`. The personal profile is
the only supported profile; retired profile markers migrate on reinstall.

## Daily use

The `dotfiles` command is on PATH in new shells. From an existing shell, use
`./bin/dotfiles` directly.

```bash
dotfiles doctor           # Local dependency, link, signing, and plugin checks
dotfiles doctor --online  # Also verify GitHub authentication
dotfiles sync --dry-run   # Preview an update from a clean tracking branch
dotfiles sync            # Fast-forward, relink, and sync enabled asset groups
```

Before switching devices, review `git status` and `git diff`, commit intentional
changes, and push. On the other device, `dotfiles sync` refuses local edits,
replaced configuration links, and divergent Git history. It previews link
changes, installs them with backups, and checks the result. Missing links are
recreated. It never auto-commits, stashes, resets, or pushes.

`dotfiles sync --check` runs local preflight without fetching or changing files.
Bootstrap remembers enabled shell/editor asset groups in the local
`~/.config/dotfiles/features.json`. On an older installation, use
`dotfiles sync --assets` to enable those groups. Package upgrades stay in
your package manager; rerun bootstrap to install newly declared dependencies.
Restart apps that cache configuration after syncing.

If an app replaces a link, compare its detached file with the source shown by
`./install.sh --status`. Copy desired edits into the repository before reinstalling.
Doctor and `./install.sh --status` report detached files without changing them.
Running the installer normally applies links after backing up replaced files.

## What to edit

| Settings | Source |
|---|---|
| Shared environment and Bash/Zsh aliases | `shell/` |
| Zsh settings and functions | `zsh/` |
| Bash settings and tools | `bash/` |
| OS-specific shell settings | `platform/`, `config/mac/zsh/` |
| Custom shell prompt | `config/zsh/themes/` |
| Shared CLI/editor settings | `config/cli/`, `config/editors/`, `config/tmux/` |
| Waveterm common settings | `config/terminals/waveterm/settings.common.json` |
| Waveterm OS overrides | `config/terminals/waveterm/settings.linux.json`, `settings.mac.json` |
| Waveterm widgets and themes | The platform's `config/` directory |
| Git and SSH | `config/git/`, `config/ssh/`, `config/mac/ssh/` |
| Tool, plugin, and font choices | `setup/` manifests |

Waveterm's installed `settings.json` files and `zsh/plugins.zsh` are generated
and tracked. Shell plugin choices live in `setup/assets.json`. After
editing common settings or an OS override, run `dotfiles render` and commit
both the inputs and outputs. Doctor detects edits made directly to generated
outputs, so review and move any desired app-written changes into the inputs.
Older Mac source paths are compatibility symlinks to the shared configuration.

Private and device-specific settings stay under `~/.config/dotfiles/`:
`local.bash`, `local.zsh`, `local.env.zsh`, and `local.gitconfig`. Examples are in
`templates/local/`. Account databases, credentials, SSH keys, and application permission databases stay outside Git. VS Code keeps its own
Settings Sync; Atuin owns history sync. See the ownership table in
[setup/README.md](setup/README.md).

## Optional fonts

```bash
dotfiles fonts --list
dotfiles fonts meslo fira-code --dry-run
dotfiles fonts meslo fira-code
```

Downloads are pinned and SHA-256 verified, cached locally, and installed only
for your user. Original fonts from this checkout are preserved under the
ignored `.cache/legacy-fonts/`. Font binaries are removed from the current Git
tree; historical commits remain intact. The filtered shallow clone above
avoids fetching those old binary versions.

## Verify changes

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_private.py --worktree
python3 scripts/render_configs.py --check
git diff --check
```

Tests use disposable homes and local Git remotes. They require Git, Python 3.9+,
Bash, Zsh, and SSH, and do not download packages or call account services.
`dotfiles hooks` enables the commit/push guards in this checkout. Existing
custom hook paths are preserved and must chain these guards explicitly.
