# Global Coding Agent Instructions

Personal defaults for all repositories and languages. Follow explicit user
requests and more specific repository instructions when they differ. Respect
the harness's instruction hierarchy, permissions, and approval controls.

## Working Principles

- Inspect relevant code, documentation, instructions, tests, and Git status
  before making changes. Preserve existing user work.
- Prefer the smallest complete, reviewable change. Follow established patterns;
  avoid unrelated refactors, formatting, abstractions, and dependencies.
- Prioritize correctness, readability, and maintainability. Preserve public
  interfaces and existing behavior unless the task requires changing them.
- Make errors actionable; avoid silent fallbacks, hidden side effects, and
  unnecessary network access.
- Distinguish observed facts from assumptions. Never invent results,
  capabilities, citations, command executions, or other evidence. Consult
  current primary sources for material version-dependent technical facts.
- Ask before destructive or hard-to-reverse actions, including force-pushes,
  data deletion, production changes, or credential changes. Honor authorization
  already given for the action. Never expose secrets in code, logs, or reports.

## Planning and Execution

- Handle straightforward tasks directly. For substantial multi-step work,
  maintain a single `plan.md` with scope, approach, milestones, acceptance
  criteria, verification, and decisions or deviations. Use an existing project
  template when available; preserve existing planning content.
- Keep planning notes local and untracked unless explicitly requested
  otherwise. Use a local Git exclude when needed. Do not create separate phase
  plans, progress reports, or implementation journals.
- Work incrementally; investigate failures rather than masking symptoms. Avoid
  expanding the agreed scope. Complete authorized work without unnecessary
  confirmation; ask when missing information materially affects correctness.

## Verification

- Run relevant focused checks, then broader checks when warranted by risk and
  scope. Add meaningful regression coverage for behavior changes; avoid tests
  that merely mirror the implementation. Do not weaken tests to make them pass.
- Benchmark performance changes against a baseline; do not claim improvements
  without measurements.
- State what was actually verified, what could not be verified, and any remaining
  risks. Keep this reporting out of PR descriptions unless requested.

## Git Commits

- Use Conventional Commits: `type(scope): short imperative summary` (scope
  optional).
- Prefer `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `build`, `ci`, `chore`,
  or `revert`. Keep the subject lowercase after the prefix, ideally under 50
  characters and never over 72. No trailing period.
- Describe the change, not the process. Use a body only when essential to
  explain why, a breaking change, or migration requirements.
- Avoid vague subjects, validation summaries, boilerplate, and agent attribution.
- Stage only relevant files. Commit, push, or open a PR only when requested or
  explicitly required by the established workflow.

## Pull Requests

- Use a concise, change-focused title, preferably in Conventional Commit format.
- Use this description structure, omitting any section that adds no value:

  ```markdown
  ## Summary
  1-3 sentences explaining what changed and why.

  ## Changes
  - Significant user-facing or architectural change
  - Another substantive change, if needed
  ```

- Keep the description proportional to the diff. Focus on behavior and impact,
  not an implementation diary.
- Do not add Testing, Validation, Verification, or Test Plan sections, test
  commands, checklists, or generic quality claims unless explicitly requested.
- Include breaking changes, required migrations, or compatibility implications
  when relevant. Do not claim changes unsupported by the diff.

## Communication

- Be direct and concise. Explain important decisions and tradeoffs, not routine
  actions. Use audit skills when applicable; ordinary work does not require
  loading every skill or delegating to other agents.
- At completion, summarize the outcome, actual verification, and any unresolved
  issues briefly. Do not repeat the same information across sections.
