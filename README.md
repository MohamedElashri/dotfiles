# dotfiles

One repository for Linux, macOS, and Bash-only HEP clusters. Edit the files here;
installed files are symlinks, so there is no backup/restore cycle for everyday edits.

## Install

Clone this repository anywhere that will remain accessible to your shell, then run:

```bash
./install.sh --dry-run          # preview; never writes or installs packages
./install.sh                    # Linux or macOS personal setup
./install.sh --status           # check whether any managed file was replaced
./install.sh --profile hep      # Linux clusters: Bash only, no root required
```

A repeat install keeps the saved profile unless you explicitly pass `--profile`.
The OS comes from `uname`. HEP is an explicit profile, never inferred from CVMFS,
AFS, or a university hostname. `--platform linux|mac` overrides the OS for previews
or preparing a home directory. Package installation is separate: see [setup](setup/README.md).

The installer backs up replaced files and links under
`~/.dotfiles-backup/<timestamp>-<pid>/`, preserves existing site login files, and leaves
correct links alone. On Linux, an existing Bash rc from outside this checkout is
copied to `~/.config/dotfiles/site.bash` and loaded before personal settings,
preserving site initialization such as `/etc/bashrc` and module definitions.
Review this saved hook once during migration; it can also contain personal
settings you want to move. On macOS, the previous Bash rc is backed up without
being loaded as a site hook.
If both an unmanaged rc and a site hook already exist, installation stops rather
than overwriting the hook. Existing Bash login files must source `~/.bashrc` for an
interactive Bash login; they are not rewritten automatically. On a personal Mac
without a Bash login file, the installer links a tracked `.profile` that retains
the macOS hooks and loads `.bashrc`.

## Where to edit

| Change | File |
|---|---|
| Shared environment and PATH | `shell/env.sh` |
| Portable aliases for Bash and Zsh | `shell/aliases.sh` |
| Zsh settings and load order | `zsh/.zshrc` |
| Zsh aliases / functions | `zsh/aliases.zsh`, `zsh/functions.zsh` |
| Zsh-specific toolchain paths | `zsh/environment.zsh` |
| Zsh prompt, completion and tool initialization | `zsh/tools.zsh` |
| Bash settings / integrations | `bash/.bashrc`, `bash/tools.bash` |
| OS-specific aliases | `platform/linux.sh`, `platform/mac.sh` |
| Mac Zsh aliases, functions, environment | `config/mac/zsh/` |
| Shared cluster settings and Bash helpers | `hep/common.bash` |
| Settings for one cluster | `hep/lxplus.bash`, `hep/sneezy.bash`, etc. |
| Git and SSH | `config/git/`, `config/ssh/` |
| Application settings | `config/terminals/`, `config/mac/` |
| Executable personal scripts | `bin/` |

For a change: edit, open a new shell, inspect `git diff`, then commit. Run
`./install.sh --status` to catch an app that replaced a symlink with its own file;
review and copy that file into the matching repo path before reinstalling. On another
machine, pull and open a new shell. Run installation again only when destinations
are added or the checkout moves. Keep the checkout available: copy mode is retired.

## Private data

This repository is public. Keep credentials, private keys, authentication state,
tokens and machine-local permissions in their applications or local overrides.
The installer links only selected settings files, never whole credential
directories. VS Code settings are handled by Settings Sync outside this repo.

Enable the included commit guard once per checkout:

```bash
git config --local core.hooksPath .githooks
python3 scripts/check_private.py --worktree
python3 scripts/check_private.py --history
```

The hooks check staged additions before each commit and reachable Git history
before each push. They report file paths and finding types without displaying
values. `.gitignore` blocks common credential
paths, but the check also catches files added with `git add -f`. Review every
diff before pushing; a pattern check cannot recognize every kind of private
information. Git author email and cluster identifiers remain in current files
and public Git history; this change does not rewrite that history. The hook setting
is local to each clone and should be enabled
again on another Mac.

Application configs may be rewritten by their applications. Check `git diff`
before committing; do not automatically import settings or package inventories.
The personal profile installs Git, SSH and selected app configs; the HEP profile
installs Bash and its profile selection only, leaving site Git/SSH settings alone.
SSH and Wave Terminal use separate Mac and Linux configs. Mac Wave files are
linked individually so other application state can remain in its directory.
The explicit source/destination list is in `install.sh`.

### This Mac

Run `./install.sh --dry-run` to review the exact links, then `./install.sh`.
The first install saves the Mac's previous files in the printed backup directory.
The Mac's gh aliases, Atuin settings, Wave widgets, prompt, and shell aliases
have been captured in `config/mac/`. SSH routes remain in the private
`~/.ssh/config.local`, loaded by the tracked SSH config. Copy that local file
securely to another Mac if needed; do not commit it. Open a new terminal after
installation. Edits to linked home files then appear directly in `git diff` here.
The installer also links the Mac's asciinema, btop, Claude, micro, Vicinae,
Karabiner-Elements, and Warp settings. It links individual files in each app's
directory so generated state and unrelated files stay with the application.
The former standalone Mac Zsh files were moved into the install backup after
their active settings were migrated.
Tmux uses built-in status styling, so its config does not depend on TPM plugins.

Authentication files such as `~/.config/gh/hosts.yml` and SSH private keys stay
outside this repository.
DNSCrypt Proxy and OpenCode service endpoints are also kept in local app files.
On another Mac, install the applications first, then run `./install.sh` and
`./install.sh --status`. See [Mac setup notes](setup/README.md) for the
applications and plugin settings that need separate installation.

## Local settings

Use `~/.config/dotfiles/local.zsh` or `local.bash` for private paths, aliases and
secrets. These load last in interactive shells. Use
`~/.config/dotfiles/local.env.zsh` for Zsh environment variables and tool options
(such as `ZSH_THEME`) that must be set before initialization; it is loaded in both
login and interactive Zsh. Examples are in `templates/local/`. Git overrides go in
`~/.config/dotfiles/local.gitconfig`. Do not commit secrets here.

Zsh startup explicitly loads shared environment, Zsh environment/settings/tools,
shared and Zsh aliases, functions, OS aliases, then local overrides. `.zprofile`
loads login environment without interactive hooks; `.zshenv` stays minimal.
Bash loads its site hook, shared settings, OS aliases and tools, HEP settings when
selected, then local overrides. Optional integrations are guarded by availability.

The installer consolidates old Zsh override files into `local.env.zsh` and
`local.zsh`, backing up the originals and preserving the current overrides last.
Startup reads only these canonical names.

## HEP and shared homes

The installer records `personal` or `hep` in `~/.config/dotfiles/profile`.
`hep/select.bash` selects the cluster on each new shell: `lxplus*` maps to lxplus;
sneezy, sleepy and gpu_farm select their named files. Unknown hosts load only
`hep/common.bash`. This works when login nodes share a home directory.

Override for an unusual hostname by exporting `DOTFILES_MACHINE=lxplus` before
starting Bash (or set it in the saved site hook). `DOTFILES_PROFILE` overrides the
saved profile. A local override loaded last is too late to change selection for
that same startup. Adding a cluster means adding its file and an explicit case
in `hep/select.bash`.

## Migration and recovery

`install.sh` is the only installation entrypoint. The old bootstrap, restore,
backup and macOS setup wrappers have been removed, along with compatibility
symlinks and duplicate scripts. Update other machines by pulling and running
`./install.sh` (or `./install.sh --profile hep` for a first cluster migration)
before opening a new shell. Old home links pointing into removed paths are
replaced or backed up by the installer; unrelated files are left alone.

The unused nested repositories were archived outside this checkout in
`../dotfiles-legacy-archive-20260914/` on the development machine. They retain
their complete Git history and are not part of the active configuration.

To undo an installation, replace a new home symlink with its corresponding saved
file from the printed backup directory. Freshly added links have no previous file.
To undo repository edits, use Git after reviewing your working tree.

## Verification

```bash
python3 -B -m unittest discover -s tests -v
```

Tests use temporary homes to verify dry runs, backup preservation, repeat installs,
local overrides, Linux/macOS destination selection and cluster selection.

## Optional assets

Installed fonts remain available under `config/mac/fonts/` for manual use; they
are not loaded by shell startup. The unfinished remote
Jupyter helper was archived with the legacy repositories; it was not used by
shell startup and failed syntax validation.
