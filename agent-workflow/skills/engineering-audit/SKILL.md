---
name: engineering-audit
description: Audit code or implementation for regressions, architecture changes, or nontrivial bug fixes when an implementation audit is requested or the change warrants deeper review. Skip tiny changes and normal coding tasks where ordinary checks suffice.
---

# Engineering audit

An audit is read-only by default. Make fixes only when the user requested
remediation or the invoking task authorizes edits.

1. Identify authorized scope, expected behavior, project conventions, and
   critical invariants.
2. Inspect the relevant diff, code, and tests directly. Another agent's summary
   is a lead to investigate, not implementation evidence.
3. Construct credible failure modes: edge cases, input and data assumptions,
   error paths, concurrency and resource handling where relevant, security and
   safety boundaries, regressions, maintainability, and performance tradeoffs.
4. Execute proportionate, available objective checks. Prefer deterministic
   tests, static analysis, type checks, integration checks, and measured
   benchmarks over model self-rating. Investigate failures; never alter tests
   merely to make failing code pass.
5. For regression or performance claims, compare with a baseline, record the
   environment, and avoid comparing incompatible runs.
6. Report actionable findings by severity, with file/line references when
   possible. Separate reproducible failures, probable risks, and unverified
   concerns; explain the trigger and impact of each finding.
7. Summarize checks as PASS, FAIL, or NOT RUN and explain material limitations.
   Do not assert correctness solely because tests passed or an audit found
   nothing. If evidence is missing, specify the next check that could resolve it.

For scientific analysis, read [scientific-review.md](references/scientific-review.md)
when data provenance, units, statistics, or physics semantics determine correctness.

For an independent review, run objective checks first, then give a separate
reviewer the diff, relevant interfaces/tests, and acceptance criteria. Withhold
implementation narratives and desired findings. Each finding must state its
location, trigger, impact, evidence, and uncertainty. Reproduce a finding before
requesting a targeted repair; do not manufacture issues to fill a quota.
A manual review is trusted. Claim enforced read-only review only when all tools
are restricted; a read-only shell setting alone does not establish that boundary.
