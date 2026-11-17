# Project instructions

Repository-specific guidance supplements global defaults. Read README.md,
CONTRIBUTING.md when present, and the instructions nearest the files being edited.

## Purpose and structure

Describe the project's users, runtime, entry points, key subsystems, and links to
architecture or domain documentation using observed repository facts.

## Development commands

Use the project's existing package scripts, Makefile, justfile, or documented
commands. Record verified setup, build, focused test, full test, lint/format, and
smoke commands here. Mark unknown or unavailable commands explicitly; do not
invent a task runner or treat this template as proof that a command exists.

## Invariants

Record actual public API, security, data, numerical, deployment, and performance
constraints relevant to this repository. Identify required fixtures and local
configuration without copying credentials or private data into instructions.

## Planning and verification

For complex work, maintain one plan.md with scope, steps, acceptance criteria,
verification, decisions, and deviations. Preserve an existing plan and its Git
tracking conventions. Do not add broad plan* ignores or extra progress journals.
Use focused objective checks before escalating to broader verification.
