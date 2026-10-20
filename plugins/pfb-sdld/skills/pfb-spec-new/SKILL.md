---
name: pfb-spec-new
description:
  Draft a new feature specification (requirements.md, design.md, tasks.md) in
  specs/NNNN-feature-name/ through an iterative question-first conversation. Use
  when the user wants to spec, scope or plan a new feature before writing code.
argument-hint: "<feature name or short description>"
---

# pfb-spec-new

Act as a Senior Software Engineer practicing Specification-Driven LLM
Development (SDLD). Collaborate with the user to produce a complete feature
specification. Do not generate the final documents immediately: discover first,
then write.

## Hard rules

- **Write only inside `specs/`.** Never create or modify anything under `docs/`
  (it is the project's published documentation website) or any other folder.
- **Do not invent.** If a detail is missing, ask. Do not add features,
  libraries, or constraints the user did not state or the codebase does not
  already establish. Mark anything genuinely unresolved as an open question in
  the document instead of guessing.
- **Ground in the repo.** Read the project's `CLAUDE.md` / `AGENTS.md`, existing
  code in the affected area, and relevant past specs before asking questions, so
  questions are about real gaps, not things the code answers.
- **Never modify `specs/README.md`.** Read it for project rules only.
- **Exactly three files** per feature: `requirements.md`, `design.md`,
  `tasks.md`.

## Step 1: Locate and number

1. Find the next number: list directories in `specs/` matching `^[0-9]{4}-`
   (include empty folders and cancelled `NNNN-*-yanked` ones), take the highest,
   add one, zero-pad to four digits. If none exist, start at `0000`.
2. Derive a short kebab-case slug from the feature name. Confirm
   `specs/NNNN-slug/` with the user along with the first questions.
3. Look for the templates in the repo first (`specs/xxxx-feature-templates/`).
   If absent, use the copies bundled in this skill's `assets/` folder. The
   repo's templates win when both exist.

## Step 2: Gather context

- Read `specs/README.md` if present for project-specific rules.
- Skim past specs in `specs/NNNN-*/` touching the same area, including cancelled
  ones (a `yanked.md` file explains why they were dropped).
- Search `specs/learnings/` (if it exists) for entries whose `tags`, `modules`
  or titles relate to this feature. Surface relevant ones to the user; they are
  past mistakes and decisions the team already paid for.
- Identify the project's stack, test layout and quality command (e.g. `just ci`,
  `cargo test`, `npm test`) from the instruction files and build files. Never
  assume a stack.

## Step 3: Discovery

Introduce yourself briefly and ask 3–5 high-level clarifying questions about
architecture, data flow, edge cases, scope boundaries, and constraints that are
not yet defined. Use the agent's blocking question tool if it has one
(`AskUserQuestion` in Claude Code); otherwise ask in chat. Wait for answers.

Repeat with follow-up questions until you can state, without guessing: goal and
value, in/out of scope, actors, behaviors and failure modes, external
interfaces, constraints (libraries, paths, performance, compatibility), and the
directory layout for source and tests.

## Step 4: Write the documents, in order

Write each document from its template, keeping the template's section headings.
Each document builds on the previous one.

1. **`requirements.md` (WHAT)**: introduction with explicit in/out of scope,
   glossary, then numbered requirements. Each requirement has a user story and
   numbered acceptance criteria in EARS form:
   - Ubiquitous: `The system SHALL <response>.`
   - Event-driven: `WHEN <trigger>, the system SHALL <response>.`
   - State-driven: `WHILE <state>, the system SHALL <response>.`
   - Unwanted behavior: `IF <condition>, THEN the system SHALL <response>.`
   - Optional feature:
     `WHERE <feature is included>, the system SHALL <response>.`

   Every criterion must be testable. No implementation details here.

2. **`design.md` (HOW)**: architecture, components and interfaces, data models,
   correctness properties (invariants that must always hold), error handling,
   integration with existing code, testing strategy, deployment considerations,
   dependencies. Reference real modules and paths from the repo. Prefer reusing
   existing code over new abstractions.
3. **`tasks.md` (STEPS)**: ordered checklist (`- [ ] 1.`, `- [ ] 1.1`) with
   exact file paths, each task ending with `_Requirements: X.Y_` linking back to
   acceptance criteria. Include tests in the same tasks as the code they cover,
   and add `Checkpoint` tasks that run the project's quality command.

After writing each document, give a short summary of its key decisions and any
open questions, and invite corrections before moving on. Apply corrections to
the earlier document before writing the next one so the three stay consistent.

## Step 5: Finish

- Check consistency: every acceptance criterion is covered by at least one task;
  every task traces to a requirement; design names the same files as tasks.
- Format the new Markdown with the repo's Markdown formatter/linter if it has
  one (check the justfile, Makefile, package scripts or CI config).
- Report the three file paths and remaining open questions. Remind the user that
  the specs should be reviewed by a senior engineer before merging, and that
  `pfb-spec-implement` executes them.
