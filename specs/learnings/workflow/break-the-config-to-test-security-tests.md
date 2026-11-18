---
title: Check a security invariant test against the old config and broken copies
date: 2026-11-18
updated: 2026-11-18
category: workflow
status: active
tags: [testing, security, invariants, mutation, nono]
modules: [scripts/test_nono_profiles.py, nono/profiles/pfb-claude.json]
spec: specs/0000-nono-profile-review
related:
  - specs/0000-nono-profile-review/findings.md
superseded_by:
---

# Check a security invariant test against the old config and broken copies

## Context

`scripts/test_nono_profiles.py` guards the security properties of the
`pfb-claude` nono profile in `just ci`: no wildcard host, no push over HTTPS,
the agent token only on allowed calls, the developer's tokens kept out, no
ineffective or token-bearing path grant. A test like this passes on the day it
is written whether or not it checks anything.

## Symptom

The test was written first and run on the old 1.0.0 profile, where it failed
where expected. The spec review then ran it on modified copies of the 2.0.0
profile, and four broke a property the design said was checked, yet passed:

- nono's built-in `github` route added to `credentials`, which injects the
  developer's `GITHUB_TOKEN`;
- a second route reusing the agent's `credential_key` towards another upstream;
- the route's `credential_key` set to `env://GITHUB_TOKEN`;
- `GH_CONFIG_DIR` pointed at `$HOME/.config/gh`.

Path grants were compared as exact strings, so `$HOME/.docker`, `~/.config/gh/`
and `~/.config/gh/hosts.yml` passed too.

## What Did Not Work

- Seeing the test fail on the old config only: it proves each test can fail, not
  that it fails on every way of breaking its property.
- Checking that a value is present (`GH_CONFIG_DIR` set, `github_agent` in the
  list) instead of what it is.

## Root Cause

Each assertion checked the shape of the correct profile ("the agent route is
right") rather than ruling out the dangerous ones ("nothing else can carry a
token"). Requirements phrased as "IF … THEN the test SHALL fail" name the bad
states, and the test has to be run against them.

## Solution

1. Write the test before the change and run it on the old config; record which
   tests fail and why.
2. List the ways to break each property, and run the test on a broken copy for
   each, plus near-misses that must pass. A scratch script is enough: import the
   test module, point its `PROFILE_PATH` (`scripts/test_nono_profiles.py:16`) at
   a modified copy, and run the `TestCase`.
3. Tighten until every broken copy fails: exact equality on allow-lists
   (`credentials == ["github_agent"]`, a single custom route, its
   `credential_key`, `test_agent_route` at `scripts/test_nono_profiles.py:177`),
   exact values (`GH_CONFIG_DIR`, line 193), and normalized path comparison that
   also rejects paths inside or above a forbidden one (`normalize_path` and
   `overlaps`, lines 96 and 113).

After the fix, eleven broken copies each failed the expected test, while the
unchanged profile and `~/.config/ghostty` (a near-miss of `~/.config/gh`) passed
(findings §3.1, §3.4).

## Prevention

- When a test guards a security property, list its broken variants in the review
  and run them; keep the list in `findings.md` or the PR.
- Prefer exact sets and values to "contains" checks, so that widening a grant
  needs a deliberate, reviewed change to the test.
