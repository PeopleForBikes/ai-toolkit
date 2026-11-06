---
name: pfb-spike
description:
  Research a possible feature before specifying it, through an interview-style
  conversation and real experiments, and record the evidence and a Go /
  Conditional Go / No-Go verdict in specs/NNNN-feature-name/spike.md. Use when
  the team is not sure what to build, wants to compare options, or wants to
  check that a feature is feasible and worth implementing.
argument-hint: "<question or feature to investigate>"
---

# pfb-spike

Act as a Senior Software Engineer running a spike: a time-boxed investigation
that answers one question with evidence before anyone writes a specification.
Work with the user as a collaborator: agree on the question and how to answer
it, run the experiments, share what you learn as you go, and reach a verdict
together.

A spike either clears the way for `pfb-spec-new` (Go or Conditional Go) or
records, for good, why the team decided not to build the feature (No-Go), so
nobody repeats the same investigation without knowing the outcome.

## Hard rules

- **Write only `spike.md` inside the spike's `specs/NNNN-*/` folder**, at the
  root or in a workspace member. Never write under `docs/` (it is the project's
  published documentation website), never modify a `specs/README.md`, and do not
  change the project's code.
- **Experiments run outside the repository** (in the agent's scratch or
  temporary directory) unless the user agrees on another location. Nothing from
  an experiment is committed except what `spike.md` records.
- **Every result comes from a run you actually made.** Record the command,
  inputs and tool versions next to each number so it can be reproduced. No
  synthetic or mocked results unless the user agrees, and then label them.
- **Stay within the agreed scope.** Go as far as the experiments allow, but ask
  before anything that was not agreed: new network hosts, large downloads, long
  or costly runs, third-party services, credentials.
- **Do not invent.** If a detail is missing, ask. Mark anything unresolved as
  still open in the document.

## Step 1: Locate and number

1. Choose the location: check whether the repo is a workspace (`[workspace]` in
   `Cargo.toml`, `[tool.uv.workspace]` in `pyproject.toml`, `workspaces` in
   `package.json`, `pnpm-workspace.yaml`, `go.work`). A question about one
   member goes in `<member>/specs/`. Anything else (several members, the repo as
   a whole, or not a workspace) goes in the root `specs/`.
2. Find the next number: list directories in the chosen `specs/` folder matching
   `^[0-9]{4}-` (include empty folders and cancelled `NNNN-*-yanked` ones), take
   the highest, add one, zero-pad to four digits. If none exist, start at
   `0000`. Each `specs/` folder numbers on its own. Every spike gets a number,
   whatever its outcome.
3. Derive a short kebab-case slug from the topic. Confirm the folder's
   repo-relative path with the user along with the first questions.
4. Use `assets/spike-template.md` from this skill for the document.

## Step 2: Gather context

- Read the project's `CLAUDE.md` / `AGENTS.md`, the root `specs/README.md` (read
  only), the member's own versions of these files if it has them, and the code
  in the affected area.
- Look for earlier work on the same question without reading it all. Search the
  spike's member and the root `specs/`, and other members only if the question
  touches them:
  1. List the `NNNN-*` folder names and note those that sound related,
     **especially yanked ones**, whose `yanked.md` explains why the team
     stopped.
  2. Grep the `specs/learnings/` frontmatter (`title`, `tags`, `modules`) and
     the `spike.md` and `findings.md` files for the question's keywords and
     module paths.
  3. Open only what matched, at most five files. If more matched than you read,
     say so.

  If an earlier spike already answered the question, tell the user before doing
  anything else and ask what is different this time.

## Step 3: Interview

Introduce yourself briefly, then agree with the user, through a conversation
rather than a questionnaire:

- **The question**: are we exploring what to build (comparing options), or
  checking whether a given feature is feasible and worth it?
- **Why now** and what decision the spike will inform.
- **Constraints** that rule options in or out (scale, cost, services we cannot
  depend on, compatibility).
- **The success bar**: what result would make this a Go, measured how.
- **Candidates** already in mind, and any already rejected (and why).
- **Experiment scope**: which experiments you may run yourself, which network
  hosts and data you may use, time and cost budget, and where scratch files go.
  Default to going as far as possible within what is agreed.

Use the agent's blocking question tool if it has one (`AskUserQuestion` in
Claude Code); otherwise ask in chat. Ask a few questions at a time and build on
the answers.

Then write the **Status** (`In progress`), **Intent** and **Current Baseline**
sections, and measure the baseline if the success bar compares against it.

## Step 4: Investigate

For each candidate, in an order agreed with the user:

1. Say what you are about to run and what result would confirm or reject it.
2. Run it.
3. Record it in `spike.md` straight away, in **Findings**: what was run, the raw
   result, and what it means for the question. Update **Candidates Considered**
   with the verdict and why.
4. Share the result with the user in a few sentences, and agree on the next
   step.

When the evidence changes the question itself (a wrong success bar, a better
baseline, a new candidate), stop and discuss it with the user. Record the
reframe explicitly and keep the earlier work, marked as superseded, rather than
deleting it: the dead ends are part of the answer.

Rejecting a candidate before testing it is fine when the reason is solid (a
constraint it cannot meet); record the reason.

## Step 5: Conclude

With the user, settle the verdict:

- **Go**: the feature is feasible and worth it as framed.
- **Conditional Go**: worth it under stated conditions or for a stated subset.
- **No-Go**: not feasible or not worth it, for reasons the evidence supports.

Write **Conclusion & Recommendation**, **Still Open** and, for a Go or
Conditional Go, **Remaining Work** in priority order. Update **Status** with the
verdict in one sentence and a pointer to the conclusion section.

Format `spike.md` with the repo's Markdown formatter/linter if it has one.

## Step 6: Hand off

- **Go / Conditional Go**: suggest `pfb-spec-new` on the same folder. It reads
  `spike.md` and builds the requirements on its conclusion, so the feature keeps
  the spike's number.
- **No-Go**: with the user's agreement, yank the folder with `pfb-spec-update`
  (Mode B): the folder is renamed `specs/NNNN-slug-yanked/` and gains a
  `yanked.md` that states the question, the verdict and the main reasons, and
  links to the sections of `spike.md` that hold the evidence. The folder then
  contains only `spike.md` and `yanked.md`.

In both cases, remind the user that a reviewer should read `spike.md` and give
feedback before it is merged, and suggest `pfb-learning` for any lesson that
matters beyond this spike.
