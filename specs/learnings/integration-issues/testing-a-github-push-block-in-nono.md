---
title: Test a github.com push block by sending git-receive-pack, not git push
date: 2026-11-18
updated: 2026-11-18
category: integration-issues
status: active
tags: [nono, github, git, push, endpoint-rules, proxy]
modules: [nono/profiles/pfb-claude.json]
spec: specs/0000-nono-profile-review
related:
  - specs/0000-nono-profile-review/findings.md
  - specs/learnings/integration-issues/nono-credential-route-behavior.md
superseded_by:
---

# Test a github.com push block by sending git-receive-pack, not git push

## Context

`pfb-claude` 2.0.0 allows only reads and Git fetches on `github.com`
(`nono/profiles/pfb-claude.json:58-65`): `GET /**`, `HEAD /**` and
`POST /*/*/git-upload-pack`. A push, `POST …/git-receive-pack`, matches no rule
and must be refused by nono's proxy (Requirement 4.3 of the spec).

## Symptom

`git push https://github.com/<owner>/<repo>.git …` in the session fails with
`fatal: could not read Username for 'https://github.com': terminal prompts disabled`:
GitHub's credential challenge, not the proxy's refusal. The test seems to pass,
but it proves only that the agent has no Git credentials.

## What Did Not Work

- `git push` as the test: it never reaches the request the rule refuses.

## Root Cause

A push starts with `GET /<owner>/<repo>.git/info/refs?service=git-receive-pack`.
That is a `GET`, so the `GET /**` rule lets it through, and GitHub answers `401`
with a credential challenge. Without credentials Git stops there; the
`POST …/git-receive-pack` that the rules refuse is never sent. With credentials
it would be sent and refused.

## Solution

Send the refused request directly and check who answers:

```sh
curl -sS -i -X POST \
  -H 'Content-Type: application/x-git-receive-pack-request' --data-binary '' \
  https://github.com/PeopleForBikes/nono-spike-missing.git/git-receive-pack
```

The proxy answers `403` with no `server: GitHub-Babel` header and no
`x-github-request-id`. The same request to `git-upload-pack` reaches GitHub and
gets its own `401` (`server: GitHub-Babel/3.0`), which shows the difference
comes from the rule. Target a repository that does not exist, so nothing can
change on GitHub. Observed on 2026-11-18 (findings §1.1).

## Prevention

- `test_github_web_allows_reads_and_fetch` (`scripts/test_nono_profiles.py`)
  keeps the rules exactly to reads and `git-upload-pack`.
- When checking any proxy endpoint rule, send the exact request the rule should
  refuse and check the response headers to tell the proxy from the upstream.
