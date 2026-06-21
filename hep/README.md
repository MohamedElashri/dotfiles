# hep/

Dotfiles for HEP remote clusters: CERN lxplus, UC/GEOP machines (sneezy, sleepy,
goofy), and the GPU farm. These machines are bash-only (no zsh) and shared
systems where you have no root access.

---

## Usage

From the repo root on a HEP machine:

```bash
./bootstrap.sh --platform hep --yes
```

Or restore only (if bootstrap has already run):

```bash
./restore --platform hep
```

### lxplus hostname rotation

lxplus login nodes have rotating numbered hostnames (`lxplus901`, `lxplus902`, …).
Pass `--machine lxplus` explicitly so the right aliases file is selected:

```bash
./bootstrap.sh --platform hep --machine lxplus --yes
./restore      --platform hep --machine lxplus
```

When `--machine` is omitted, the script uses `hostname -s` — which on lxplus gives
a numbered name that has no matching aliases file.

---

## Backup

Save your current cluster dotfiles back into this directory:

```bash
# from the repo root
./backup --platform hep --machine lxplus
./backup --platform hep --machine sneezy
```

`~/.machine_aliases` is saved as `hep/machine_aliases/<machine>`.

---

## Adding a New Machine

1. Log in to the machine and set up `~/.machine_aliases` with any host-specific
   aliases, PATH extensions, or module loads you need.
2. Run `./backup --platform hep --machine <name>` from the repo root.
   This saves `~/.machine_aliases` → `hep/machine_aliases/<name>`.
3. Commit the new file.

On subsequent logins, `./restore --platform hep --machine <name>` will install it.

---

## What Gets Restored

| Source | Destination |
|--------|-------------|
| `hep/bash/.bashrc` | `~/.bashrc` |
| `hep/bash/.bash_aliases` | `~/.bash_aliases` |
| `hep/bash/.bash_config` | `~/.bash_config` |
| `hep/bash/.bash_functions` | `~/.bash_functions` |
| `hep/machine_aliases/<machine>` | `~/.machine_aliases` |

`rsync` is not required on HEP machines — restore only copies individual files.
