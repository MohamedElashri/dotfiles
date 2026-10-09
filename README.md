# dotfiles

Shell and application settings for personal Linux/macOS machines and Bash-only
HEP clusters. The installer links selected files from this checkout into your
home directory. Keep the checkout in place so those links keep working.

## Install

Clone the repository, enter it, and preview the changes:

```bash
./install.sh --dry-run
```

Install the personal profile on Linux or macOS:

```bash
./install.sh
```

For a Linux HEP cluster, install the Bash-only profile:

```bash
./install.sh --profile hep
```

The installer backs up files it replaces under `~/.dotfiles-backup/`. Open a
new shell when it finishes. It links configuration only; package and application
setup is described in [setup/README.md](setup/README.md).

## Use and customize

Edit files in this checkout. Changes to linked files take effect directly; open
a new shell to reload shell settings. Common files:

| To change | Edit |
|---|---|
| Shared environment and PATH | `shell/env.sh` |
| Bash and Zsh aliases | `shell/aliases.sh` |
| Zsh settings, aliases, and functions | `zsh/` |
| Bash settings and tools | `bash/` |
| Linux/macOS aliases | `platform/` |
| HEP cluster settings | `hep/` |
| Git and SSH settings | `config/git/`, `config/ssh/` |
| Application settings | `config/` |
| Personal commands | `bin/` |

Keep machine-specific or private settings in local files under
`~/.config/dotfiles/`; they are loaded after the shared settings:

- `local.bash` for Bash aliases and settings
- `local.zsh` for Zsh aliases and settings
- `local.env.zsh` for Zsh environment variables needed before shell tools load
- `local.gitconfig` for Git overrides

Examples are in `templates/local/`. Do not commit credentials, tokens, private
keys, or authentication files. To enable the repository's commit and push
checks in this checkout, run:

```bash
git config --local core.hooksPath .githooks
```

## Update and check

On another machine, pull the latest changes and run `./install.sh` again when
the checkout moves or the set of installed files changes. Check whether an app
has replaced a managed symlink with:

```bash
./install.sh --status
```

If it reports a detached file, review that file and copy any desired changes
back into the matching file in this repository. Use `./install.sh --help` to
see installer options. For HEP cluster selection, see [hep/README.md](hep/README.md).
