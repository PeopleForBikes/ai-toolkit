---
title: How a nono custom credential route behaves, with and without its secret
date: 2026-11-18
updated: 2026-11-18
category: integration-issues
status: active
tags: [nono, credentials, github, token, proxy, keychain]
modules: [nono/profiles/pfb-claude.json]
spec: specs/0000-nono-profile-review
related:
  - specs/0000-nono-profile-review/findings.md
  - specs/learnings/integration-issues/testing-a-github-push-block-in-nono.md
superseded_by:
---

# How a nono custom credential route behaves, with and without its secret

## Context

`pfb-claude` 2.0.0 gives agents a dedicated GitHub token through a nono custom
credential route, `github_agent` (`nono/profiles/pfb-claude.json:85-101`): the
supervisor reads the token from the login keychain (service `nono`, account
`github_agent`) and the proxy adds it to the matching requests to
`api.github.com`. Three behaviors of nono 0.82.0 surprised us while verifying it
on macOS.

## Symptom

- `nono profile validate` refuses a profile whose `credential_key` contains a
  hyphen: the key `must contain only alphanumeric characters and underscores`,
  unless it is a URI such as `op://` or `keyring://`.
- Without the keychain item, the session starts but every `gh` command says
  `You are not logged into any GitHub hosts`, and `curl` to `api.github.com`,
  even for a public repository, gets `HTTP 503` with
  `{"error":"credential_unavailable", …}`.
- The session's environment holds a variable nobody set,
  `GITHUB_AGENT_BASE_URL=http://127.0.0.1:<port>/github_agent`.

## What Did Not Work

- Expecting anonymous access without the token: the design assumed requests
  would reach GitHub without a token and get `401`. Only requests outside the
  route's `endpoint_rules` do.
- Naming a test key `nono-spike-missing`: refused by validation (above).

## Root Cause

- A bare `credential_key` is both the route's key and the keychain account name,
  and nono only accepts `[A-Za-z0-9_]` for it; anything else must be a URI
  (`op://`, `keyring://`, `env://`, …).
- When the secret cannot be loaded, nono still starts the session, leaves the
  route's `env_var` (`GITHUB_TOKEN`) unset, and its proxy answers every request
  matching the route's `endpoint_rules` itself with `503 credential_unavailable`
  instead of forwarding it. Requests outside the rules (for example `DELETE`)
  still reach GitHub and get `401 Requires authentication`. With the secret,
  `GITHUB_TOKEN` holds a placeholder equal to `NONO_PROXY_TOKEN`.
- nono exposes each custom route's local reverse-proxy endpoint as
  `<ROUTE>_BASE_URL`. gh does not use it (it goes through `HTTPS_PROXY`), and it
  is not a credential.

Observed in live sessions on 2026-11-18 (findings §1.3, §2.1, §2.2); nono's
source was not read.

## Solution

- Name keys with underscores (`github_agent`, `nono_spike_missing`).
- Treat `503 credential_unavailable` from `api.github.com` like "gh is not
  logged in": the agent token is missing. The README's recommended `CLAUDE.md`
  line tells agents to stop and ask the contributor in that case
  (`README.md:187-191`), and `SECURITY.md:99-103` documents it.
- Leave `<ROUTE>_BASE_URL` alone; it needs no `deny_vars` entry.

## Prevention

- `nono profile validate` (run by `just validate`) catches invalid keys.
- To test a missing secret, start a session with a copy of the profile whose
  `credential_key` names an account that does not exist; a dry run does not load
  credentials.
- Revisit when upgrading nono past 0.82.0: the `503` behavior and the variable
  name are not documented guarantees.
