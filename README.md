# dotfiles

One repository for Linux, macOS, and Bash-only HEP clusters. Edit the files here;
installed files are symlinks, so there is no backup/restore cycle for everyday edits.

## Install

Clone this repository anywhere that will remain accessible to your shell, then run:

```bash
./install.sh --dry-run          # preview; never writes or installs packages
./install.sh                    # Linux or macOS personal setup
./install.sh --profile hep      # Linux clusters: Bash only, no root required
```

A repeat install keeps the saved profile unless you explicitly pass `--profile`.
The OS comes from `uname`. HEP is an explicit profile, never inferred from CVMFS,
AFS, or a university hostname. `--platform linux|mac` overrides the OS for previews
or preparing a home directory. Package installation is separate: see [setup](setup/README.md).

The installer backs up replaced files and links under
`~/.dotfiles-backup/<timestamp>-<pid>/`, preserves existing login files, and leaves
correct links alone. An existing Bash rc from outside this checkout is copied to
`~/.config/dotfiles/site.bash` and loaded before personal settings, preserving site
initialization such as `/etc/bashrc` and module definitions. Review this saved hook
once during migration; it can also contain personal settings you want to move.
If both an unmanaged rc and a site hook already exist, installation stops rather
than overwriting the hook. Existing login files must source `~/.bashrc` for an
interactive Bash login; they are not rewritten automatically.

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
| Shared cluster settings and Bash helpers | `hep/common.bash` |
| Settings for one cluster | `hep/lxplus.bash`, `hep/sneezy.bash`, etc. |
| Git and SSH | `config/git/`, `config/ssh/` (macOS SSH: `config/mac/ssh/`) |
| Application settings | `config/terminals/`, `config/mac/` |
| Executable personal scripts | `bin/` |

For a change: edit, open a new shell, inspect `git diff`, then commit. On another
machine, pull and open a new shell. Run installation again only when destinations
are added or the checkout moves. Keep the checkout available: copy mode is retired.

Application configs may be rewritten by their applications. Check `git diff`
before committing; do not automatically import settings or package inventories.
The personal profile installs Git, SSH and selected app configs; the HEP profile
installs Bash and its profile selection only, leaving site Git/SSH settings alone.
The explicit source/destination list is in `install.sh`.

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
local overrides, Linux/macOS destination selection and cluster selection. macOS
shell integration still needs a smoke test on an actual Mac.

## Optional assets

Application files that are not in the installer's explicit list (including fonts,
iTerm2 preferences, Hyper, Nano, gh settings and the ShellHistory integration) remain available under
`config/mac/` for manual use. They are not loaded by shell startup. The unfinished remote
Jupyter helper was archived with the legacy repositories; it was not used by
shell startup and failed syntax validation.
