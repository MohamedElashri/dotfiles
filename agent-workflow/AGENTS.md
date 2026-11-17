# Global Coding Agent Instructions

Defaults for all repositories and languages. Follow explicit task requests,
repository-specific instructions, and the active harness's instruction hierarchy
and approval controls.

## Working Principles

- Inspect relevant instructions, code, tests, and Git state before editing.
  Preserve existing user changes and avoid unrelated modifications.
- Make the smallest complete, reviewable change. Follow established patterns;
  avoid unnecessary abstractions, dependencies, and formatting churn.
- Prefer correctness, clarity, and maintainability. Avoid unintended behavior
  changes, hidden side effects, and silent error handling.
- Distinguish evidence from assumptions. Verify material, version-dependent
  claims against primary documentation when available. Never invent results,
  citations, executed commands, or capabilities.
- Obtain approval for destructive or hard-to-reverse actions unless already
  authorized. Never expose secrets in code, logs, or reports.

## Planning and Execution

- Handle simple tasks directly. For complex implementation work, use an existing
  `plan.md` or create a single `plan.md` when useful or requested. Follow a
  supplied template and keep scope, steps, acceptance criteria, and key decisions
  in that file.
- Do not create separate phase plans, progress reports, or implementation
  journals. Keep temporary personal notes untracked; respect established tracking
  conventions for project planning documents.
- Work incrementally and investigate failures rather than hiding them. Stay
  within scope; proceed without unnecessary approval requests, but ask when
  missing information materially affects correctness or risk.

## Verification

- Match verification effort to change risk. Run relevant focused checks, then
  broader checks when warranted. Add meaningful regression tests for behavior
  changes; do not weaken tests just to make them pass.
- Compare performance claims against measured baselines. Never claim checks or
  improvements that were not performed or observed.
- Report failed or unavailable checks and material residual risks. Mention
  successful verification in completion summaries only when useful, not as
  routine boilerplate.

## Git Commits

- Use Conventional Commits: `type(scope): imperative summary` (scope optional).
  Prefer `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `build`, `ci`, `chore`,
  or `revert`. Use lowercase after the prefix, aim for 50 characters or fewer,
  never exceed 72, and omit the trailing period.
- Describe what changed, not the development process. Add a body only when
  necessary to explain why, breaking behavior, or migration requirements.
  Avoid vague subjects, validation summaries, boilerplate, and agent attribution.
- Stage only relevant files and review the staged diff before committing.
  Commit, push, or open a PR only when requested or required by an established
  authorized workflow. Never force-push without authorization.

## Pull Requests

- Write a short, change-focused title, preferably in Conventional Commit form.
- For nontrivial changes, use this format; omit sections without useful content:

  ```markdown
  ## Summary
  1-3 sentences explaining what changed and why.

  ## Changes
  - Significant functional or architectural change
  - Another substantive change, if needed
  ```

- A single concise paragraph is enough for trivial changes. Focus on behavior
  and impact, not implementation diaries or promotional claims.
- Do not add Testing, Validation, Verification, or Test Plan sections, commands,
  checklists, or generic quality claims unless requested or required by the
  repository's PR policy.
- Mention breaking changes, migration steps, or compatibility implications when
  relevant. Make only claims supported by the actual diff.

## Communication and Tools

- Be direct and concise. Explain consequential decisions and tradeoffs, not
  routine actions. Use specialized skills or delegate only when materially useful.
- At completion, briefly state the outcome and any important unresolved issues.
  Avoid repetitive status reports and unnecessary documentation.
