---
name: pfb-spec-implement
description:
  Implement a feature from its specification in specs/NNNN-feature-name/ by
  executing tasks.md in order, checking off tasks as they are completed. Use
  when the user asks to build or implement a spec.
argument-hint: "<spec folder, e.g. specs/0006-direct-osm-download>"
disable-model-invocation: true
---

# pfb-spec-implement

You are a senior software engineer implementing a feature using
Specification-Driven Development (SDLD).

## Inputs

The spec folder given as argument. If none is given, list `specs/NNNN-*/`
folders (excluding cancelled `*-yanked` ones) whose `tasks.md` has unchecked
items and ask which one. Read all three documents fully before changing any
code:

- `requirements.md` is the source of truth for **behavior**.
- `design.md` is the source of truth for **architecture and constraints**.
- `tasks.md` is the source of truth for **file structure and sequencing**.

If the folder name ends with `-yanked` or it contains `yanked.md`, the feature
was cancelled: stop and tell the user.

Also read the project's `CLAUDE.md` / `AGENTS.md` for conventions and the
quality command (e.g. `just ci`, `cargo test`, `npm test`), and search
`specs/learnings/` (if present) for entries related to the modules you will
touch. If the folder has a `spike.md` or a `findings.md` from earlier work, read
them too.

## Rules

- Do not invent functionality not described in the requirements.
- Do not skip or reorder tasks unless strictly necessary for correctness; say so
  when you do.
- Write production-quality code: no placeholders, no TODOs, full typing where
  the language supports it, matching the surrounding code's style.
- Enforce every correctness property in `design.md`; handle the error and edge
  cases it lists (errors, permissions, partial state).
- Tests are part of each task, not an afterthought. Cover main flows and failure
  cases.
- Never write planning or spec material under `docs/`; it is the published
  documentation website. Only touch `docs/` when a task explicitly calls for
  user-facing documentation changes.
- Never modify `specs/README.md`.
- Do not commit or push unless the user asks.

## Execution loop

For each task in `tasks.md`, in order:

1. Implement it, editing files directly.
2. Run the relevant tests.
3. Tick its checkbox (`- [ ]` to `- [x]`) in `tasks.md`.
4. At each `Checkpoint` task, run the project's full quality command and fix
   failures before continuing.

## Recording findings

Keep `findings.md` in the spec folder as the record of everything non-obvious
learned while implementing: behavior that looks like a bug unless you know it is
deliberate, library and tooling traps, and techniques that worked. It explains
why the code behaves as it does after the conversation that produced it is gone.

- Create it from `assets/findings-template.md` (in this skill) the first time
  you learn something non-obvious; do not create an empty one.
- Add an entry as soon as you learn it, without waiting to be asked: what the
  rule is (with `path:line`), how it was caught, and what it cost, using
  measured numbers where you have them.
- When a later discovery proves an entry wrong or incomplete, correct the entry
  and say what changed, rather than adding a contradicting one.
- Skip the obvious: a typo or a routine fix is not a finding.

## When the spec is wrong or incomplete

If implementing a task reveals that the spec is ambiguous, contradictory or
infeasible:

- **Behavior changes** (anything in `requirements.md`): stop and ask the user.
- **Design or task changes** needed for correctness: explain the deviation, then
  update `design.md` and `tasks.md` to reflect reality. Specs must not be left
  outdated.

## Finish

- Run the full quality command one last time and report the result honestly,
  including failures.
- Summarize: tasks completed, deviations from the spec (and where the spec was
  updated), the entries added to `findings.md`, and anything left unchecked.
- Remind the user that a reviewer should read `findings.md` and give feedback
  before merging.
- Suggest `pfb-spec-review` for a spec-compliance review, and `pfb-learning` for
  findings that matter beyond this feature.
