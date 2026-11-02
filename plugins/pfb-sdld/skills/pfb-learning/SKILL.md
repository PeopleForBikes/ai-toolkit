---
name: pfb-learning
description:
  Capture one solved problem or durable team decision as a searchable learning
  in specs/learnings/<category>/, so future work (and future agents) can reuse
  it. Use after a non-obvious bug is fixed, a tricky investigation succeeds, or
  the team settles a convention or tooling choice.
argument-hint: "[optional: brief context about what was learned]"
---

# pfb-learning

Each documented learning makes the next similar problem cheaper: the first time
takes research, the next time takes a lookup. This skill writes **one** learning
per run, grounded in the code and the session, to
`specs/learnings/<category>/<slug>.md`.

## Hard rules

- **Write only under `specs/learnings/`**, plus the optional instruction-file
  line in Step 6 with the user's consent. Never write under `docs/`: it is the
  project's published documentation website. Never modify `specs/README.md`.
- **One learning per run.** If the session produced several, write the first,
  then tell the user to run the skill again for the next.
- **No claims from memory.** Before stating how code behaves, read the source
  line that defines it and cite it as `path:line`. Prefer PR or issue numbers
  over commit SHAs. If you cannot verify something, say so in the text.
- **No secrets** (tokens, credentials, private URLs, personal data) in the
  learning.

## Preconditions

Check these first; if one fails, explain why and stop unless the user insists:

- The problem is solved, not in progress.
- The solution was verified (tests pass, the command works, the behavior was
  observed).
- It is non-trivial: a typo or an obvious error is not worth a learning.

## Step 1: Gather

From the conversation, the diff and the code, collect:

- **Context**: what was being done, which modules, which spec (`specs/NNNN-*`)
  if any.
- **Symptom**: exact error messages and observable behavior.
- **What did not work**, and why.
- **Root cause**: the technical explanation.
- **Solution**: the fix, with short code excerpts and file references.
- **Prevention**: how to avoid it next time (a test, a lint rule, a convention,
  a check).

For a decision rather than a bug, collect: the decision, the options considered,
the reasons, and when it should be revisited.

Ask the user for anything that is missing instead of filling the gap.

## Step 2: Categorize

Pick exactly one category (it becomes the folder name):

| Track     | Category                 | Use for                                            |
| --------- | ------------------------ | -------------------------------------------------- |
| Problem   | `build-errors`           | build, packaging, dependency, CI failures          |
| Problem   | `test-failures`          | flaky or wrong tests, test-infrastructure issues   |
| Problem   | `runtime-errors`         | crashes and exceptions in running code             |
| Problem   | `logic-errors`           | wrong results without a crash                      |
| Problem   | `data-issues`            | database, schema, geometry/SRID, data-quality bugs |
| Problem   | `performance-issues`     | slowness, memory, resource exhaustion              |
| Problem   | `integration-issues`     | external services, APIs, cloud, third-party tools  |
| Problem   | `security-issues`        | vulnerabilities and their fixes                    |
| Knowledge | `architecture-decisions` | structural choices and their rationale             |
| Knowledge | `tooling-decisions`      | library, language or tool choices                  |
| Knowledge | `conventions`            | agreed ways of doing things in this project        |
| Knowledge | `workflow`               | developer experience and process lessons           |

## Step 3: Check for overlap

Search `specs/learnings/` (titles, `tags`, `modules`, and body text) for entries
about the same problem or decision. Also search the features' `findings.md`
files (`specs/*/findings.md`): when the learning generalizes an entry from one
of them, keep that entry as is and link to it from the learning (in `related`).

- **Same problem**: update the existing file instead of creating a new one. Add
  the new information, bump `updated`, and keep the history readable.
- **Related**: create a new file and link both ways in `related`.
- **Contradicted**: if the new learning makes an old one wrong, set the old
  one's `status: superseded` and `superseded_by`, and tell the user.

## Step 4: Write

Use `assets/learning-template.md` from this skill. File name: a short kebab-case
slug describing the problem or decision (no date; the date lives in the
frontmatter). Keep it short enough to read in two minutes: link to code instead
of pasting large blocks.

Fill the frontmatter carefully, because it is what makes the store searchable:

- `modules`: repo-relative paths or package names that the learning concerns.
- `tags`: 3–6 lowercase keywords someone would search for.
- `spec`: the related `specs/NNNN-*` folder, or remove the line.

## Step 5: Validate

Re-read the written file against the code: every `path:line` exists and says
what the learning claims; commands are copy-pasteable. Format it with the repo's
Markdown formatter/linter if it has one.

## Step 6: Discoverability

The store only pays off if agents know it exists. Read the project's instruction
files (`CLAUDE.md`, `AGENTS.md`; one may be a symlink or a shim including the
other, so edit the one with the real content). If nothing in them would lead an
agent to `specs/learnings/`, propose the smallest addition that fits the file's
existing style, ideally one line in an existing section, for example:

```md
- `specs/learnings/` — documented solutions to past problems and team decisions,
  by category, with frontmatter (`modules`, `tags`); relevant when working in
  those areas.
```

Show the proposed line and where it goes, and edit only after the user agrees.
Ask once per repository; if it is already there, skip this step silently.

## Finish

Report the file path, whether it was created or updated, and any superseded
entries.
