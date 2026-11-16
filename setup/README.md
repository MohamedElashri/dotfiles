# Machine setup and sync ownership

## Onboarding

Install Git, Python 3.9+, Bash, and Homebrew using its official platform
instructions. On Linux, install the distro build prerequisites described in
[Homebrew on Linux](https://docs.brew.sh/Homebrew-on-Linux). The bootstrap finds
Homebrew in its standard Apple Silicon, Intel Mac, and Linux locations.

Run from the repository root:

```bash
./bin/dotfiles bootstrap --dry-run
./bin/dotfiles bootstrap
```

Default provisioning includes the shared shell/editor tools, configuration
links, Git hooks, Oh My Zsh, selected custom plugins, the Mac Powerlevel10k
source, a LazyVim starter profile, and Micro plugins. Missing formulae are
installed without a blanket upgrade. Existing Git assets with another origin,
occupied paths, and dirty asset updates are refused. An existing asset at a
different revision is kept during bootstrap; `dotfiles assets --update` applies
the declared revision after checking for local edits.
The personal Dracula prompt is linked into Oh My Zsh's custom theme directory,
so framework updates keep it separate from upstream sources.

| Option | Adds or changes |
|---|---|
| `--dev` | Go, Node, uv, and ffmpeg from `dev-packages.txt` |
| `--apps` | Reviewed Mac GUI casks from `mac-apps.txt` |
| `--fonts meslo …` | Selected fonts from `fonts.json` |
| `--skip-packages` | Use tools installed by your distro or another package manager |
| `--skip-assets` | Install links without shell/editor asset downloads |

No login shell changes, macOS preferences, account logins, or OS upgrades happen
as part of bootstrap. Linux GUI applications remain distro-managed.

After provisioning:

1. Set up/unlock 1Password and the SSH agent, then run `gh auth login`. Git
   uses signed commits, the platform's 1Password signing executable, and Neovim
   as the editor. `templates/local/local.gitconfig.example` shows local overrides.
2. Restore private overrides and `~/.ssh/config.local` securely on either platform.
3. Authenticate Atuin against the configured personal server and restore its
   encryption key through your existing secure process. The shared config keeps
   the existing `~/atuin/.history.db`, `.key`, and `.session` paths on both platforms.
4. Select Zsh as the login shell if desired, open a new shell, restart apps,
   and run `dotfiles doctor`. `--online` also probes GitHub authentication;
   `--strict` makes optional-component warnings fail the check.

For custom Git hooks, chain `.githooks/pre-commit` and `.githooks/pre-push` into
the existing hook setup. Bootstrap keeps a custom `core.hooksPath` intact.

## Manifests

- `packages.txt`: shared direct Homebrew formulae. The old Linux and Mac
  filenames are compatibility symlinks to this one list. Libraries arrive as dependencies; the former Mac inventory is retained only
  as `archive/mac-packages-2026-11.txt` for reference.
- `dev-packages.txt`, `mac-apps.txt`: optional install groups.
- `assets.json`: public Git origins, immutable commits, shell plugin selections,
  and Micro plugin names.
- `fonts.json`: immutable Nerd Fonts release URLs and upstream SHA-256 checksums.

Edit these files deliberately. To update a Git source, review its upstream
changes and replace its commit in `assets.json`. `dotfiles assets --update`
then applies it locally; enabled assets are also reconciled during sync.
Shell plugin selection is also declared in `assets.json` and rendered into
`zsh/plugins.zsh`. Oh My Zsh auto-update is disabled so the manifest owns its
revision. Add extra locally installed plugins with `DOTFILES_EXTRA_OMZ_PLUGINS`
in `local.env.zsh`.

Package versions and Micro plugin releases are selected by their own
managers, so this is a declared workstation setup rather than an OS image or
an exact binary lockfile. Removing a package entry never uninstalls it.

Micro plugins use its [official plugin manager](https://github.com/micro-editor/micro/blob/master/runtime/help/plugins.md).
Pinned font checksums come from the [Nerd Fonts release](https://github.com/ryanoasis/nerd-fonts/releases/tag/v3.4.0).

## Existing devices and migration

AI application installation, provider settings, credentials, plugins, and
unrelated skills remain outside this installer. Earlier application settings
collected in this checkout are preserved only in ignored `.cache/excluded-ai/`.
The personal profile manages a Codex global file and two shared skill sources,
linked into both Codex and Claude Code:

| Repository source | Installed link |
|---|---|
| `agent-workflow/global.md` | `~/.codex/AGENTS.md` |
| `agent-workflow/skills/research-audit/` | `~/.agents/skills/research-audit/` |
| `agent-workflow/skills/engineering-audit/` | `~/.agents/skills/engineering-audit/` |
| `agent-workflow/skills/research-audit/` | `~/.claude/skills/research-audit/` |
| `agent-workflow/skills/engineering-audit/` | `~/.claude/skills/engineering-audit/` |

The global file is linked individually; only the two named skill directories
are linked in each harness, keeping their `SKILL.md` files regular for discovery. Existing
targets are backed up under `~/.dotfiles-backup/` before replacement; a real
skill directory with extra files or insufficient read/search access blocks
replacement before any configuration writes. `~/.codex/config.toml`,
`~/.claude/settings.json`, `~/.claude/CLAUDE.md`, auth, plugins,
sessions, permission state, and unrelated skills stay local. Review existing
instructions before reinstalling. Sync refuses detached target files until you
reconcile them; it recreates missing links. Only `personal` is supported.
Symlinked, non-directory, or unsearchable agent parents (`.codex`, `.agents`,
`.agents/skills`, `.claude`, `.claude/skills`)
block installation and sync before any configuration writes; reconcile those
layouts manually. The installer never replaces those parent directories.
Earlier managed `SKILL.md` file links migrate to named-directory links when
there are no sibling files; unmanaged manifests still require review before sync.

The global Git ignore allows project `AGENTS.md` and `.agents/skills/`, while
keeping `.codex/`, `AGENTS.override.md`, and credential files ignored. Inspect
newly visible untracked instructions in other repositories before adding them;
the installer never stages or commits them.

See [usage](../docs/usage.md) for previews and an optional Codex discovery check.
The links target the default homes; custom `CODEX_HOME` or `CLAUDE_CONFIG_DIR`
settings need manual review. They do not configure ChatGPT web personalization,
sync web chats, or upload Claude account skills. Other harnesses are outside
this installer's current scope.

Preview `./install.sh --dry-run` before adopting the expanded shared app links.
The installer backs up replaced files. Review existing Linux Atuin, GitHub CLI,
Micro and btop settings first; these were previously outside its
coverage. `dotfiles sync` refuses those detached files until reconciled.

Waveterm and Ghostty migrate from whole-directory links to individual file
links. The directory link is backed up, application-owned contents are copied
into a real directory, and selected config files are then linked. App state
can remain in the directory without being added to Git.

Atuin retains the existing home-relative database, encryption key, and session
paths under `~/atuin/` on both platforms. Existing history and account data are
never moved, merged, or replaced by the installer. Restore account/key material
securely on new devices before relying on history sync.

The older `config/mac/cli/…`, tmux, and Zed paths are compatibility symlinks.
Your old installed symlinks keep resolving while you prepare the migration.
Fonts from this working copy remain in `.cache/legacy-fonts/`; downloaded
fonts use `~/.cache/dotfiles/fonts/` and install under `~/Library/Fonts/` on Mac
or `~/.local/share/fonts/` on Linux. Font changes back up replaced files.
Git history has not been rewritten.

## What owns each setting

| Settings or state | Owner and coverage |
|---|---|
| Bash/Zsh, aliases, Git | This repository on Linux and Mac, with platform overrides |
| Atuin, Micro, Helix, GitHub CLI, bat, btop, asciinema, tmux | Shared configuration on both platforms |
| Waveterm | Common settings plus OS overrides; widgets/themes can differ |
| Ghostty and Zed | Shared settings on both platforms |
| SSH routes | Shared Linux routes plus `~/.ssh/config.local` overrides; local file only on Mac |
| Karabiner, Vicinae, Rio, Warp, Hyper, Nano, Powerlevel10k preferences | Existing Mac configuration |
| VS Code | Its own Settings Sync |
| Codex global guidance and shared Codex/Claude Code audit skills | `agent-workflow/`, linked by the personal installer |
| AI apps, private provider/runtime settings, plugins, other skills | Managed separately; outside dotfiles |
| Shell history | Atuin account sync; keys and sessions stay local |
| SSH private keys, credentials, auth/permission databases | Local secure storage and account setup |
| Device-only overrides | `~/.config/dotfiles/local.*` |

Git transports portable shell and application preferences. History databases
and account credentials stay outside the repository.

The Mac Karabiner remaps still refer to particular keyboard USB IDs. Zed's
Dracula Pro theme and optional alternative Neovim profiles remain external
assets. Set up those separately if you use them.
