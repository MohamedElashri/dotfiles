# Coding agents

The maintained policy, project templates, skills, fixtures, and runner live in
this dotfiles checkout. Normal bootstrap and CI never invoke a model. The runner
uses Python 3.9+ and the standard library; no Docker or account is needed for
scorer tests, onboarding, diagnostics, or metadata reports.

Agent setup is optional: classic install/bootstrap/sync/doctor exclude agent
links by default, and classic CLI commands do not import the evaluation modules.
Use `--with-agents` for combined setup/maintenance or `install.sh --agents-only`
for agent links. Classic operation also works when `agent-workflow/` and
`scripts/agent_*.py` are absent.

## Installation and instructions

Preview `./install.sh --agents-only --dry-run`, then run
`./install.sh --agents-only` to link the shared policy and skills. Add
`--with-agents` to the installer, bootstrap, sync or doctor for combined
operations. Each command requires its own opt-in; classic commands leave
existing agent files alone.

Edit [AGENTS.md](../agent-workflow/AGENTS.md), then start new sessions. Content
edits need no reinstall because all harnesses link to the same source.

| Harness | Global instruction file |
| --- | --- |
| [Codex](https://developers.openai.com/codex/guides/agents-md/) | `~/.codex/AGENTS.md` |
| [Claude Code](https://code.claude.com/docs/en/memory) | `~/.claude/CLAUDE.md` |
| [OpenCode](https://opencode.ai/docs/instructions/) | `~/.config/opencode/AGENTS.md` |
| [pi](https://github.com/earendil-works/pi/tree/main/packages/coding-agent#context-files) | `~/.pi/agent/AGENTS.md` |

These are default homes; custom homes need manual links to the same policy.
Repository instructions and harness overrides can change loaded guidance.
Installer `--status` checks links only. Harness binaries, credentials, settings,
sessions and unrelated skills remain local.
Skill directories containing extra user files require manual reconciliation
before replacement.

Shared skills link into `~/.agents/skills/` and `~/.claude/skills/`:
`research-audit`, `engineering-audit` and `cuda-performance`. Invoke
`$research-audit` / `$engineering-audit` in Codex, or `/research-audit` /
`/engineering-audit` in Claude Code. Audits are read-only unless edits are
authorized; the CUDA skill adds no domain assumptions to the global policy.

## Projects and commands

```bash
dotfiles agents doctor
dotfiles agents init --target /absolute/project/path --dry-run
dotfiles agents eval list
dotfiles agents eval score --case E03 --candidate /absolute/candidate --trusted-candidate
dotfiles agents eval report --format json
dotfiles agents eval prune --days 30
```

Initialization preserves existing guidance and ignore rules. Add `--with-plan`
to create one plan template when absent. Source [project templates](../agent-workflow/templates/)
remain editable; review generated guidance before adding it to Git.

Scoring is offline; functional candidates require explicit trust because their
code executes. Live evaluation requires separate authorization and explicit
limits. Only the Codex 0.169.x adapter is implemented:

```bash
dotfiles agents eval run --case E03 --harness codex --live --profile trusted \
  --timeout 180 --output-limit 1048576 --auth-file "$HOME/.codex/auth.json"
```

## Cases and scoring

`agent-workflow/evals/cases.json` contains version-1 synthetic cases and seeded
passing/failing submissions. `case.schema.json` and `result.schema.json` describe
the public JSON contracts. Matching stdlib validators enforce this version,
allowed grader IDs, normalized relative paths, and fixture content hashes; this
is not a general JSON Schema interpreter. Content hashes use Python JSON with
`sort_keys=True`, compact comma/colon separators, `ensure_ascii=True`, UTF-8, and
SHA-256; hashes are computed from data, not file formatting.

E01 checks commit structure and limited keyword relevance. E02 checks PR
structure and brevity. Substantive semantic accuracy still needs review; a
structural pass is not proof of truth. E03–E05 check arithmetic correctness,
preservation of user work, and repair without weakening tests. R01 validates a
concrete reproducible review finding. D01 checks duplicate-safe SQLite ingestion,
transaction rollback after an injected interruption, and restart/repeat behavior.

`eval score` never invokes a model. Functional graders execute a private copy of
submitted code only with `--trusted-candidate`. Review a candidate before giving
that consent. A clean temporary home, argument arrays, and timeouts do not make
arbitrary Python safe. Symlinks, hard links, special files, oversized trees,
fixture mutations, and changes outside each case's explicit scope are rejected.
Held-out acceptance programs run outside the submitted checkout. Live-run
functional grading also executes inside the native command sandbox with a
separate credential-free profile; model-generated Python is not implicitly
trusted to run on the host. Passing and
failing examples test graders; only confirmed live model/tool activity followed
by a passing independent grade counts as a successful agent run.

## Harness support

| Harness | Inspected interface | Live adapter | Protected/all-tool profile |
| --- | --- | --- | --- |
| Codex 0.169.x | `exec`, named permissions, ephemeral sessions | Trusted synthetic cases, native-command probe required | Unsupported |
| Claude Code 2.1.311 | Print mode, bare mode, tool permissions, Bash sandbox | Not implemented | Not verified |
| OpenCode | Installed CLI and current permission documentation | Not implemented | Not verified |
| pi 1.5.2 | Print/version interface, configurable extensions | Not implemented | Not verified |

`agents doctor` probes versions in temporary empty homes and reports effective
instruction links and override files without authenticating, downloading, or
changing installed settings. Missing or unparseable versions remain unknown.
It does not infer sandbox enforcement from a version string.

The Codex adapter builds an independent Git repository with no remotes. It loads
no user hooks, skills, plugins, rules, proxies, SSH agent, or shell configuration.
Only the explicitly selected authentication file is copied after the native
probe succeeds, and it is removed with the owned run directory. The profile is
default-deny outside the fixture, a private scratch directory, minimal system
paths, and the installed toolchain. It denies command network access and protects
Git metadata. The probe exercises in-scope writes, outside/symlink/credential
access, Git metadata writes, and a reachable synthetic loopback endpoint.

These checks validate native command restrictions on the actual platform. They
do not establish identical enforcement for every model tool or account-managed
feature. Protected/adversarial tasks and automated read-only review fail closed;
no permissive fallback exists. Run only the supplied trusted synthetic cases.
The native sandbox may be unavailable inside another sandbox; repair the host
setup or run from a supported host rather than disabling isolation.

An invocation requires `--live`, a harness/profile, a 1–180 second timeout, and
an explicit output limit of 1 KiB–1 MiB. Private disk defaults to 128 MiB;
`--disk-limit` selects 1–256 MiB (per-file hard limit, aggregate polling). The runner makes no retries. Built-in
provider retries and actual monetary cost may be unavailable; the deadline still
applies and no hard cost cap is claimed. Process groups are terminated on
completion, timeout, output/disk limits, SIGINT, or SIGTERM. Detached hostile
processes, hard aggregate memory/CPU limits, and a strict aggregate disk quota
are not guaranteed. Individual files are capped; aggregate disk use is polled.
These limits are another reason protected execution is unsupported.

`--policy baseline` omits the local global instruction file; `current` supplies
its exact content in an isolated Codex home. This controls local policy loading,
not administrator/account instructions. No causal A/B or cross-harness ranking
is inferred, and live repetitions require their own authorization.

Sources: [Codex permissions](https://learn.chatgpt.com/docs/permissions),
[Codex configuration](https://developers.openai.com/codex/config-reference/),
[Claude Code sandbox scope](https://code.claude.com/docs/en/sandboxing),
[OpenCode permissions](https://opencode.ai/docs/permissions/), and
[pi extension security](https://github.com/earendil-works/pi/tree/main/packages/coding-agent#extensions).

## Reports and recovery

Private state defaults to `${XDG_STATE_HOME:-~/.local/state}/dotfiles/agent-evals`
on Linux and macOS. `--state` selects another absolute private directory.
Directories must be user-owned mode 0700; records are mode 0600. Unmanaged
nonempty state roots and symlinked paths are refused. The runner marks owned
workspaces and deletes only those whose ownership still validates.

Records include schema/run/case versions, case/fixture/grader/runner/policy
hashes, independent base commit, harness/version/model when known, instruction
mode, platform, execution mode, limits, timestamps, durations, real exit/check
results, runner retries, and exposed usage/cost. Outcomes distinguish pass, fail,
blocked, error, and unknown. Unknown cost is JSON null, never zero. Prompts,
conversations, raw output, commands, environment dumps, candidate contents, and
credentials are not persisted. JSON and text summaries contain metadata only.

A pending record is saved before invocation; final writes use atomic replacement.
If storage itself fails, a pending record may remain. Reports never treat that
as success. Grouped metrics separate grader/live evidence and incompatible
versions, policies, cases, models, resource limits, platforms and runner hashes.
Unknown metrics stay unknown; small sample sizes do not establish reliability.

`eval prune --days 30` previews retention. Add `--apply` to delete only eligible
runner-owned records and stale marked workspaces. An exclusive lock prevents
concurrent live runs and destructive retention during a run. Unexpected files
are preserved. If ownership or deletion cannot be proved, cleanup refuses the
path and requires manual review. No arbitrary history ingestion or Hession
bridge is provided: Hession 0.4.0 documents exports, not an evaluation import API.

## Independent review

Run objective checks first. Give a separate reviewer the diff, relevant
interfaces/tests, and acceptance criteria, using `engineering-audit`. Do not give
it the implementer's desired conclusions. Require location, trigger, impact,
evidence, and uncertainty; reproduce a finding before a targeted repair handoff.
R01 supplies a seeded reproducible defect for this flow. Automatic reviewer
invocation and bounded repair are deferred until all-tool read-only enforcement
is verified. No automatic merge or remote repository retirement is performed.
