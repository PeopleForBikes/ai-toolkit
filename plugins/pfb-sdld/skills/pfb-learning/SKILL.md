---
name: pfb-learning
description:
  Capture solved problems or durable team decisions as searchable learnings in
  specs/learnings/<category>/, so future work (and future agents) can reuse
  them. Use after a non-obvious bug is fixed, a tricky investigation succeeds,
  the team settles a convention or tooling choice, or a feature is approved and
  its findings.md should be reviewed before merging.
argument-hint: "[spec folder, or brief context about what was learned]"
---

# pfb-learning

Each documented learning makes the next similar problem cheaper: the first time
takes research, the next time takes a lookup. Learnings are grounded in the code
and written to `specs/learnings/<category>/<slug>.md`, at the root or in a
workspace member (see Step 2). This skill has two modes:

- **Single learning** (the default): capture one lesson from the current session
  or the user's description, following Steps 1 to 6.
- **Feature review**: when the argument is a spec folder, or the user says a
  feature was approved, go through its `findings.md` as described in
  [Feature review](#feature-review). This is the last step of a feature, run
  after the reviewer approves and before merging.

## Hard rules

- **Write only under a `specs/learnings/` folder**, plus the optional
  instruction-file line in Step 6 with the user's consent. Never write under
  `docs/`: it is the project's published documentation website. Never modify a
  `specs/README.md` or a feature's `findings.md`.
- **One learning per run, unless reviewing a feature.** If a session produced
  several, write the first, then tell the user to run the skill again for the
  next. A feature review writes one learning per finding the user selects.
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

In a feature review, apply these to each finding rather than to the whole run.

## Feature review

The feature's conversation is usually gone by now, so `findings.md` is the
source. Recording nothing is a normal outcome: the store stays useful only if it
holds lessons that matter beyond one feature.

1. **Read** `findings.md`, `tasks.md` and the introduction of `requirements.md`
   in the spec folder. If `tasks.md` has unchecked items, say so and ask whether
   to continue. If there is no `findings.md`, say so and ask whether the user
   has a lesson to capture; if not, finish without writing anything.
2. **Skip what is already captured**: grep the frontmatter in
   `specs/learnings/`, in the feature's member and at the root, for entries
   whose `spec` names this folder or whose `related` links to this
   `findings.md`, and list the findings they cover.
3. **Sort the remaining findings.** Recommend a learning when work outside this
   feature could run into the same thing: a library or tooling trap, a reusable
   technique, a convention or decision. Recommend leaving a finding where it is
   when it only explains this feature's code; whoever works on that code will
   find it in `findings.md`.
4. **Ask.** Show each finding with your recommendation and a one-line reason,
   and let the user choose, including none. Use the agent's blocking question
   tool if it has one (`AskUserQuestion` in Claude Code); otherwise ask in chat.
   Write nothing until the user answers.
5. **Write** each selected finding by following Steps 2 to 5, combining findings
   about the same problem into one learning. Use the finding as your starting
   point for Step 1 and ask the user for anything it lacks. Re-read the code it
   cites instead of copying its claims, because the code may have moved. Set
   `spec` to the folder and link the `findings.md` in `related`.
6. **Finish** with Step 6, once, and the report below.

## Step 1: Gather

From the conversation (when this session did the work), the diff, the feature's
`findings.md` if there is one, and the code, collect:

- **Context**: what was being done, which modules, which spec folder if any.
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

Then choose where it goes. In a workspace, a learning whose `modules` all sit in
one member goes in `<member>/specs/learnings/`. Anything that applies more
widely (several members, repo-wide tooling or process), and anything in a repo
that is not a workspace, goes in the root `specs/learnings/`.

## Step 3: Check for overlap

Look for entries about the same problem or decision without reading the whole
store. Grep `specs/learnings/` (frontmatter first, then body text), in the
chosen location and at the root, and in other members only if the `modules`
touch them, then open only what matched. Grep the `findings.md` files in the
same `specs/` folders too: when the learning generalizes an entry from one of
them, keep that entry as is and link to it from the learning (in `related`).

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
- `spec`: the related spec folder as a full repo-relative path, or remove the
  line. Numbers are only unique within one `specs/` folder.

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
- `specs/learnings/` (at the root and in workspace members) — documented
  solutions to past problems and team decisions, by category, with frontmatter
  (`modules`, `tags`); relevant when working in those areas.
```

Show the proposed line and where it goes, and edit only after the user agrees.
Ask once per repository; if it is already there, skip this step silently.

## Finish

Report each file path, whether it was created or updated, and any superseded
entries. After a feature review, also list the findings left in `findings.md`.
