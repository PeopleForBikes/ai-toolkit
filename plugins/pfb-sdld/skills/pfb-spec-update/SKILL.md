---
name: pfb-spec-update
description:
  Bring an existing feature specification in specs/NNNN-feature-name/ back in
  line with reality after design changes, or mark a feature or spike as
  cancelled (yanked). Use when the implementation diverged from the spec, scope
  changed, a feature was dropped, or a spike concluded No-Go.
argument-hint: "<spec folder> [what changed | yank <reason>]"
---

# pfb-spec-update

Specs are living documentation: if the design changes during implementation,
`design.md` and `tasks.md` must reflect what was actually built. Old specs are
never deleted.

## Hard rules

- Write only inside the given `specs/NNNN-*/` folder (and rename it when
  yanking). Never touch `docs/`.
- Never modify `specs/README.md`.
- Never delete a spec folder or its files.
- Do not change `requirements.md` without the user's explicit agreement:
  requirements changes are scope changes. Show the proposed wording first.
- Keep the documents' existing structure and section headings.

## Mode A: sync the spec with the implementation

1. Read the three documents and the implementation (the files named in
   `tasks.md`, plus the branch diff if the work is in progress).
2. List every divergence, grouped by document: what the spec says, what the code
   does, and the file/line evidence.
3. Ask the user, for each divergence, whether the spec or the code is right. Do
   not decide this on your own.
4. Update `design.md` and `tasks.md` for the divergences where the code is right
   (tick tasks that are done, add tasks that were needed, remove or strike tasks
   that were dropped with a one-line reason). Update `requirements.md` only
   where the user agreed.
5. Re-check traceability: every acceptance criterion still maps to a task.
6. Report what changed. Divergences where the code is wrong are fixes for the
   code, not the spec: list them for the user.

## Mode B: cancel ("yank") a feature

When the user says the feature is cancelled, superseded or abandoned, or a spike
concluded No-Go:

1. Ask for the reason and any link (PR, issue, replacing spec) if not given. For
   a spike, take the reason from its conclusion.
2. Rename the folder by appending the `-yanked` suffix, keeping its number:
   `specs/NNNN-feature-name/` becomes `specs/NNNN-feature-name-yanked/`. Use
   `git mv` when the folder is tracked so history follows the rename. If the
   name already ends with `-yanked`, do not rename it again.
3. Create `yanked.md` in the renamed folder:

   ```md
   # Yanked

   This feature was yanked because <reason> [<link text>](url).
   ```

   For a spike, state the question it investigated, the verdict and the main
   reasons, and link to the sections of `spike.md` that hold the evidence, so
   teammates know why the team stopped and do not repeat the same investigation.

4. Leave the existing documents (`spike.md`, `requirements.md`, `design.md`,
   `tasks.md`, `findings.md`) untouched.
5. Search the repository for links to the old folder path (other specs,
   `specs/learnings/`, code comments) and list them for the user; update them
   only inside `specs/`, never in `specs/README.md`.

## Finish

Format changed Markdown with the repo's formatter/linter if it has one, and
summarize the edits.
