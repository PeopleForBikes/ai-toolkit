---
title: Git hooks do not run on commits made in the pfb-claude sandbox
date: 2026-11-18
updated: 2026-11-18
category: integration-issues
status: active
tags: [nono, git, hooks, pre-commit, sandbox]
modules: [nono/profiles/pfb-claude.json]
spec: specs/0000-nono-profile-review
related:
  - specs/0000-nono-profile-review/findings.md
superseded_by:
---

# Git hooks do not run on commits made in the pfb-claude sandbox

## Context

`pfb-claude` 2.0.0 denies the working directory's `.git/hooks`
(`nono/profiles/pfb-claude.json:15`), because a hook written by the agent would
run outside the sandbox the next time the contributor commits.

## Symptom

Inside a session, `git commit` succeeds without any warning, but no hook runs: a
project's pre-commit checks (formatting, linting, secrets scanning) are silently
skipped on the agent's commits. `ls .git/hooks` fails with
`Operation not permitted`, and
`nono why --self --path .git/hooks/pre-commit --op write` reports
`filesystem_deny`.

## What Did Not Work

- Expecting the deny to block writes only: nono's `filesystem.deny` blocks reads
  as well.

## Root Cause

Git looks up each hook in `.git/hooks`; when it cannot read the file, it treats
the hook as absent and carries on, without a message. The deny therefore
disables every hook in the sandbox, not only changes to them. Observed in the
live session of 2026-11-18 (findings §1.2).

## Solution

Accepted as the cost of closing a path that runs code outside the sandbox, and
documented in `SECURITY.md:111-115`. Projects that rely on hooks get the same
checks from their CI recipe (for example `just ci`) run in the session and in
CI, not from the hook.

## Prevention

- In a project used with the profile, do not rely on a Git hook as the only
  gate: make the agent run the project's quality command before committing
  (state it in `CLAUDE.md` / `AGENTS.md`), and keep the check in CI.
- Revisit if nono gains a write-only deny, or if the profile moves hooks to a
  read-only grant instead.
