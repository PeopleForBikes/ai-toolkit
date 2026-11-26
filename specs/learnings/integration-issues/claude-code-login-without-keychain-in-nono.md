---
title: Claude Code's login without the keychain in nono
date: 2026-11-25
updated: 2026-11-25
category: integration-issues
status: active
tags: [nono, claude-code, keychain, oauth-capture, login, sandbox]
modules: [nono/profiles/pfb-claude.json]
spec: specs/0002-keychain-grant-yanked
related:
  - specs/0002-keychain-grant-yanked/spike.md
  - specs/learnings/integration-issues/nono-credential-route-behavior.md
superseded_by:
---

# Claude Code's login without the keychain in nono

## Context

`pfb-claude` extends the `nolabs-ai/claude` pack, which grants the login
keychain for Claude Code's own login, so agents can read any item stored with
`security`. `specs/0002-keychain-grant-yanked` tried to remove that grant: a
profile extending `default` instead of the pack, with nono's `oauth_capture`
holding Claude Code's real login and the sandbox seeing only placeholders
("phantoms"). It works for one session and fails with two (spike §5.5, K7); the
spike concluded No-Go. These behaviors, hidden behind the profile, will matter
to any later attempt and to anyone building a Claude Code profile that does not
extend the pack.

Observed on 2026-11-25 with nono 0.82.0 and Claude Code 2.1.332 on macOS. nono
paths below are in [nolabs-ai/nono](https://github.com/nolabs-ai/nono) at tag
`v0.82.0`.

## Symptom

- In a session of a profile that extends `default`, `CLAUDE_CONFIG_DIR` is
  unset, though the same Claude Code under `pfb-claude` has it set to
  `~/.claude`. Claude Code then uses `~/.claude.json` instead of
  `~/.claude/.claude.json`: two configuration files that diverge, and
  `nono why --self --path ~/.claude.json.tmp.1.abc --op write` answers
  `path_not_granted` for the temporary files it writes next to the first.
- The claude.ai connectors (MCP) fail with `CLAUDEAI_BEARER_REJECTED` while
  prompts work.
- With two sessions open, a login refresh in one leaves the other logged out.

## What Did Not Work

- A child of the pack that excludes `claude_code_macos` and denies
  `$HOME/Library/Keychains`: the pack's own `allow` and `bypass_protection` win
  (`nono why`: `ALLOWED`, `Source: profile`), as reported in
  [nono #2269](https://github.com/nolabs-ai/nono/issues/2269).
- `api_hosts: ["https://api.anthropic.com"]` alone in the `oauth_capture`
  provider: connectors go to `mcp-proxy.anthropic.com` (a constant in Claude
  Code's binary), which then receives a placeholder.

## Root Cause

- **nono prepares Claude Code only for pack profiles.** It sets
  `CLAUDE_CONFIG_DIR=~/.claude` and an empty `CLAUDE_SECURESTORAGE_CONFIG_DIR`
  when the profile reaches the pack
  (`crates/nono-cli/src/package_status.rs:157`, called at
  `crates/nono-cli/src/sandbox_prepare.rs:1725`), and only when the host has no
  `CLAUDE_CONFIG_DIR` (`sandbox_prepare.rs:1761`). A profile extending `default`
  gets neither.
- **For pack profiles, nono's values come last.** They are appended after the
  profile's `set_vars` (`sandbox_prepare.rs:1777-1779`; values from
  `sandbox_prepare.rs:238-247`), and a later key replaces an earlier one, so a
  pack profile cannot set `CLAUDE_SECURESTORAGE_CONFIG_DIR` itself; only the
  launching shell can. Read in source, not run.
- **Claude Code stores its login in a file when the keychain refuses it**, and
  moves it back to the keychain once that is writable again, the next time it
  writes a credential
  ([troubleshooting](https://code.claude.com/docs/en/troubleshoot-install)).
  With the shared `~/.claude/.credentials.json`, an ordinary session could move
  a sandbox's placeholders into the keychain over the real login. Documented,
  not observed.
- **`CLAUDE_SECURESTORAGE_CONFIG_DIR`, when set and not empty, is both the
  folder of `.credentials.json` and part of the keychain service name** (read in
  Claude Code's minified binary, 2.1.332; not in its
  [list of environment variables](https://code.claude.com/docs/en/env-vars), so
  it may change).
- **Each session's proxy loads nono's phantom store once**, so a refresh in one
  session gives Claude Code placeholders the other session's proxy does not know
  ([nono #2087](https://github.com/nolabs-ai/nono/issues/2087),
  [#2299](https://github.com/nolabs-ai/nono/issues/2299); fix in
  [PR #2088](https://github.com/nolabs-ai/nono/pull/2088), unmerged on
  2026-11-25).

## Solution

No change shipped. What worked, in the candidate profile of
`specs/0002-keychain-grant-yanked/spike.md` §4 and §4.1 (7b):

```json
"environment": {
  "set_vars": {
    "CLAUDE_CONFIG_DIR": "$HOME/.claude",
    "CLAUDE_SECURESTORAGE_CONFIG_DIR": "$HOME/.claude/nono-login"
  }
},
"credential_providers": {
  "claude_code": {
    "type": "oauth_capture",
    "api_hosts": ["https://api.anthropic.com", "https://mcp-proxy.anthropic.com"]
  }
}
```

(The provider's `token_endpoints` and `credential_store` are in the spike.) With
it: the keychain is denied, the login file holds only placeholders, a refresh
works, the connectors connect, and the contributor's own login and
`~/.claude/.credentials.json` are untouched (spike §5.4, §5.5).

## Prevention

- In a Claude Code profile that does not extend the pack, set
  `CLAUDE_CONFIG_DIR` and a dedicated `CLAUDE_SECURESTORAGE_CONFIG_DIR` in
  `set_vars`, and list every Anthropic host that receives the login in
  `api_hosts`.
- Check a login file by shape only:
  `jq '.claudeAiOauth.refreshToken | startswith("nono_")' <file>` must print
  `true`.
- Test two sessions and a forced refresh (`expiresAt` set a minute in the past)
  before relying on `oauth_capture`.
- Revisit when a nono release fixes #2087 or #2269, or when upgrading Claude
  Code past 2.1.332.
