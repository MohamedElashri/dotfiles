# HEP clusters

This directory is an independent Linux setup. Copy **the entire `hep/` directory,
including its hidden files**, to a permanent location on a cluster. It needs only
Bash and standard Linux utilities. No personal dotfiles, packages, root privileges,
Git, Python, Zsh, desktop apps, or 1Password configuration are required.

From inside the copied directory:

```bash
./install.sh --dry-run
./install.sh
./install.sh --status
```

From a full dotfiles checkout, use `./hep/install.sh`.
`./install.sh --profile hep` at the repository root remains a compatibility shortcut.

The installer links this directory's `.bashrc`, a profile marker, and `.profile`
when appropriate. Existing site login files are preserved. An unmanaged Bash rc
is retained in `~/.config/dotfiles/site.bash` and loaded before the HEP settings;
replaced files are backed up under `~/.dotfiles-backup/`. Git, SSH, Zsh, and app
configuration are left alone. If site login files do not already load `.bashrc`,
source it after the site's login initialization.

Bash loads `common.bash`, then `select.bash` chooses the cluster at shell startup,
so a shared home works across different login nodes. `lxplus*`, `sneezy`, `sleepy`,
and `gpu_farm` are recognized; unknown hosts load only the common settings.
Set `DOTFILES_MACHINE` to one of those names when an explicit override is needed.
Put personal Bash overrides in `~/.config/dotfiles/local.bash` (loaded last).
Cluster software such as CVMFS and modules remains managed by the cluster.

Keep the copied directory in place because the home files are symlinks. After
moving or refreshing it, run its installer again. A full Git checkout can use
the optional `dotfiles update` command and its recovery checks; a standalone copy
can be refreshed by copying the updated `hep/` files, without installing Git or
Python. The HEP installer also migrates links from the previous shared layout.
