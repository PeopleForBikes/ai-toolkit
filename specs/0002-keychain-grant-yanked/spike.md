# Spike: Dropping the keychain grant from pfb-claude

## Status

Concluded — No-Go: `pfb-claude` keeps the keychain grant for now, because the
only setup that removes it logs out parallel sessions until nono fixes #2087.
See §6.

## 1. Intent

The question: **can the `pfb-claude` nono profile stop giving agents the macOS
login keychain, without breaking Claude Code, the GitHub token route or
contributors' work for other clients?** It is a feasibility question: a fix that
protects only our GitHub token counts as a fallback, not as an answer.

It matters now because the keychain is the way around the limits put on the
agent's GitHub token, and may expose secrets that contributors keep for other
clients. `specs/0001-agent-github-identity/spike.md` §8.1 asked for this spike.

**Constraints that shaped scope** (agreed 2026-11-25):

- One profile for every contributor.
- Claude Code's real login never enters the sandbox: not in the keychain, and
  not in a file the agent can read. nono holds it, the agent sees a placeholder.
- One extra login or token step per contributor is acceptable, repeated at
  expiry.
- Experiments: static checks of candidate profiles in a scratch directory, live
  sessions started by the maintainer, and desk research on hosts the profile
  already allows. The agent does not read the value of any keychain item, dummy
  ones included; in a live session the maintainer runs those commands.

**Success bar** (agreed 2026-11-25), measured in a live session and outside it:

1. no keychain item can be read from the session;
2. Claude Code logs in and refreshes its login;
3. `gh` still works through the `github_agent` route;
4. one profile serves everyone;
5. sessions not started with `pfb-claude` are unaffected.

## 2. Current Baseline

Measured on 2026-11-25 in a `pfb-claude` session (nono 0.82.0, Claude Code
2.1.332, macOS 27.2.1, arm64):

- `nono why --self --path ~/Library/Keychains/login.keychain-db --op read`:
  `ALLOWED`, `granted_path`, read+write, source `group:claude_code_macos`.
- The grant has two sources in the pack `nolabs-ai/claude` 0.1.5
  (`~/.config/nono/packages/nolabs-ai/claude/profiles/claude.json`): the group
  `claude_code_macos`, which a child profile can exclude, and the pack's own
  `filesystem.allow` and `filesystem.bypass_protection` on
  `$HOME/Library/Keychains`, which it cannot remove (`nono profile guide`,
  "extends"). `nono/profiles/pfb-claude.json` extends the pack.
- The sandbox can read the agent's GitHub token in the keychain:
  `specs/0000-nono-profile-review/spike.md` §5.11, not repeated here.
- The dummy items `canary_default` and `canary_nono` of
  `specs/0001-agent-github-identity/spike.md` §8.1 exist:
  `security find-generic-password -s nono -a <item>` without `-w` exits 0 from
  the session. Their values were not read.
- The session cannot see the dummy keychain file's folder:
  `nono why --self --path ~/.local/share/pfb-spike --op read` answers `DENIED`,
  `path_not_granted`.
- 0.82.0 (2026-11-14) is the newest nono release. Issue
  [#2269](https://github.com/nolabs-ai/nono/issues/2269) is open with no label
  or milestone; its two comments are automated triage.

## 3. Candidates Considered

1 to 5 are those of `specs/0001-agent-github-identity/spike.md` §8.1.

| Candidate                                                    | Verdict                                           | Why                                                                                                                                                                            |
| ------------------------------------------------------------ | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1. Extend `default`, copy what is needed from the pack       | Works statically — see §5.1                       | Necessary for 2 and 7, not enough alone: Claude Code then keeps its real login in a file the agent reads (§5.3).                                                               |
| 2. With 1: a `claude setup-token` token, injected by a route | Fallback, not tested                              | Misses the refresh part of the bar (§1): the token lasts a year and is replaced by hand (Claude Code's documentation). Whether Claude Code accepts the placeholder is unknown. |
| 3. Items trusting only nono (`-T`)                           | Fallback, not tested                              | Protects our token only.                                                                                                                                                       |
| 4. A keychain file read by a `cmd://` capture                | Fallback, not tested                              | Protects our token only.                                                                                                                                                       |
| 5. Waiting for nono #2269                                    | Open                                              | No maintainer answer as of 2026-11-25; would shrink the copy of 1.                                                                                                             |
| 6. With 1: Claude Code's login in a file in `~/.claude`      | Rejected before testing                           | The agent could read the real login (§1).                                                                                                                                      |
| 7. With 1: nono's `oauth_capture` for Claude Code's login    | Fails with concurrent sessions — see §5.2 to §5.5 | nono holds the login, Claude Code sees phantoms. Open: concurrent sessions (nono #2087).                                                                                       |
| 8. With 1: `keychain_access` for one mediated command        | Rejected before testing                           | Claude Code reads its login by running `security`; mediating that command hands the same read to the agent, and the real login enters the sandbox (§1).                        |

## 4. Evaluation Method

- Candidate profiles are generated in the agent's scratch directory and not
  promoted. Candidate 1 is `pfb-claude` with `extends: ["default"]`, plus every
  group, path and setting of the pack except `claude_code_macos`, the VS Code
  groups and the two keychain entries; the two read paths of `claude_code_macos`
  (`~/.local/share/claude` and `~/Applications/Claude Code URL Handler.app`) are
  listed by hand; the hook script is named through `$NONO_PACKAGES`.
- Candidate 7 is candidate 1 plus:

  ```json
  {
    "credential_providers": {
      "claude_code": {
        "type": "oauth_capture",
        "token_endpoints": [
          {
            "host": "https://platform.claude.com",
            "path": "/v1/oauth/token",
            "response_fields": [
              {
                "path": "access_token",
                "kind": "opaque",
                "format": "sk-ant-oat01-{}"
              },
              { "path": "refresh_token", "kind": "opaque" },
              { "path": "id_token", "kind": "jwt" }
            ],
            "request_body": "auto",
            "request_nonce_fields": ["access_token", "refresh_token"]
          }
        ],
        "api_hosts": ["https://api.anthropic.com"],
        "credential_store": {
          "type": "file_json",
          "path": "$HOME/.claude/nono-login/.credentials.json",
          "phantom_fields": [
            "claudeAiOauth.accessToken",
            "claudeAiOauth.refreshToken"
          ]
        }
      }
    },
    "credential_routes": [
      { "name": "anthropic_oauth", "provider": "claude_code" }
    ]
  }
  ```

- Static: `nono profile validate`, `nono profile diff`,
  `nono why --profile <file>`. They resolve the profile without starting a
  session, so nothing about Claude Code's behavior is shown by them.
- Desk review: nono v0.82.0 source (tag commit `f1e0a7ac`) and issues on
  2026-11-25; Claude Code's documentation and, for what it does not document,
  strings of the 2.1.332 binary (minified code, so a reading of it, not a
  guarantee).
- Live: §4.1, started by the maintainer. nono cannot be nested.

### 4.1 Live session

Dummy items only. The maintainer runs the commands that read the keychain or the
login file; the agent reads neither. Output is reduced to an exit code or a
boolean, so no value reaches the conversation.

Outside the sandbox (`CAND7` is the candidate file):

```sh
cp "$CAND7" ~/.config/nono/profiles/pfb-spike-keychain.json
nono profile validate pfb-spike-keychain
mkdir -m 700 ~/.claude/nono-login
export CLAUDE_SECURESTORAGE_CONFIG_DIR="$HOME/.claude/nono-login"
nono run --allow-cwd --allow-launch-services --profile pfb-spike-keychain \
  -- claude auth login
jq '.claudeAiOauth.refreshToken | startswith("nono_")' \
  ~/.claude/nono-login/.credentials.json
nono run --allow-cwd --profile pfb-spike-keychain \
  -- claude --dangerously-skip-permissions --continue
```

| #   | Experiment                                                                                                                              | Expected                                 |
| --- | --------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| K1  | `security find-generic-password -s nono -a canary_default -w >/dev/null; echo $?`, typed by the maintainer with `!`; then `canary_nono` | Non-zero, no prompt                      |
| K2  | `security find-generic-password -s 'Claude Code-credentials' >/dev/null; echo $?`, same way (no `-w`)                                   | Non-zero                                 |
| K3  | The `jq` check above, after login                                                                                                       | `true`: a phantom is stored, not a token |
| K4  | A prompt in the session; `claude auth status`                                                                                           | Works, logged in                         |
| K5  | `gh api user --jq .login`; `gh pr list` on ai-toolkit                                                                                   | Works through the route                  |
| K6  | `expiresAt` set to a minute ago in the login file, then a prompt; then K3 again                                                         | Refreshes; still `true`                  |
| K7  | A second `pfb-spike-keychain` session during K6, then a prompt in each                                                                  | Unknown: nono #2087, #2299               |
| K8  | In a new terminal without the variable: `claude auth status`; `ls ~/.claude/.credentials.json`                                          | Logged in as before; no such file        |
| K9  | A `pfb-claude` session as today                                                                                                         | Logged in                                |

Added after §5.4, with candidate 7b (7 plus `CLAUDE_CONFIG_DIR` and
`CLAUDE_SECURESTORAGE_CONFIG_DIR` in `set_vars`, and
`https://mcp-proxy.anthropic.com` in `api_hosts`), started without the exported
variable:

- K10: both variables in the session; `~/.claude/.credentials.json` still
  absent.
- K11: the claude.ai connectors connect.

If K3 prints `false`, the session stops: the real login is in the file, and the
maintainer revokes it with `claude auth logout` in that profile and deletes the
file.

Cleanup: `claude auth logout` in the spike profile, then
`rm -r ~/.claude/nono-login ~/.config/nono/profiles/pfb-spike-keychain.json`,
and `unset CLAUDE_SECURESTORAGE_CONFIG_DIR`. The dummy items stay for the
fallbacks; their removal is in `specs/0001-agent-github-identity/spike.md` §8.1.

## 5. Findings

### 5.1 Candidate 1 — the keychain is denied, at the cost of a copy of the pack

- `nono profile validate` accepts the candidate (26 group references).
  `nono profile diff` against `pfb-claude` shows only the group
  `claude_code_macos`, the keychain `allow` and its `bypass_protection` gone,
  the two read paths of that group added, and the VS Code exclusions no longer
  needed.
- `nono why --profile <candidate> --op read` on `~/Library/Keychains`,
  `login.keychain-db` and `metadata.keychain-db`: `DENIED`, `filesystem_deny`.
  `~/.claude/settings.json` and `~/.claude.json`: `ALLOWED`.
- The route of [nono #2269](https://github.com/nolabs-ai/nono/issues/2269)
  (exclude the group, deny the path, in a child of the pack) does not work in
  0.82.0: `ALLOWED`, `granted_path`, `Source: profile`.
- Files are not the only door: without an authorized keychain grant nono denies
  the keychain services too, `com.apple.SecurityServer`, `securityd`,
  `security.keychaind`, `secd` and the prompt agent
  (`crates/nono/src/sandbox/macos.rs:559-583`); an authorized grant re-allows
  all five (`crates/nono-cli/src/policy.rs:1571-1578`). Read in source: K1 and
  K2 confirm it.
- The cost: `pfb-claude.json` goes from 105 to 235 lines as generated, and a
  change in a future version of the pack is no longer inherited.

### 5.2 Candidate 7 — valid, and its store is out of reach

- `nono profile validate` accepts it. The generated profile is 284 lines before
  trimming.
- nono keeps the real tokens in `oauth-capture/providers.json`, under
  `~/.local/state/nono` (`sandboxed-oauth-logins.mdx`).
  `nono why --profile <candidate>` denies that file for reading and writing
  (`path_not_granted`).
- nono's documentation gives an `oauth_capture` example for Claude Code, and a
  user of #2087 reports running this setup on macOS with the keychain denied
  ("Claude falls back to plain file storage"). Others' reports, not our run.
- **Open bug**: concurrent sessions overwrite each other's phantom store after a
  login or a refresh (#2087, open since 2026-10-09; #2299, open). The fix, PR
  #2088, is open and unmerged; one user reports a month of use on a build of it.
  Our contributors run several sessions at once, so this bug counts against the
  candidate; K7 shows how much.
- The real tokens are in plain text in nono's state directory (its documentation
  says so), kept for up to 90 days. They are out of the sandbox but not in the
  keychain.
- #1831 (an `allow_domain` entry with endpoint rules shadows the OAuth route)
  does not apply by its description: our only such entry is `github.com`, and
  `api.anthropic.com` is a plain name. K4 checks.

### 5.3 Claude Code's login — falls back to a file, which can be isolated

- Documented: when the keychain rejects the write, Claude Code stores its login
  in `~/.claude/.credentials.json`, and moves it back once the keychain is
  writable, the next time it writes a credential
  ([authentication](https://code.claude.com/docs/en/authentication),
  [troubleshooting](https://code.claude.com/docs/en/troubleshoot-install)).
- **Risk for bar 5**: with phantoms in that shared file, an ordinary session
  could move them into the keychain in place of the contributor's real login.
- Isolation, from the binary's code: `CLAUDE_SECURESTORAGE_CONFIG_DIR`, when set
  and not empty, is the folder of `.credentials.json` and part of the keychain
  service name. Not in Claude Code's
  [list of environment variables](https://code.claude.com/docs/en/env-vars), so
  it may change.
- ~~The profile cannot set it, so it has to be on the launch command.~~
  **Superseded by §5.4**: true only of profiles that reach the pack, where nono
  appends its own values after the profile's `set_vars`
  (`crates/nono-cli/src/sandbox_prepare.rs:238-247`, `:1777-1779`). Candidates 1
  and 7 do not, so `set_vars` should work (K10).
- The same file holds MCP server logins and plugin secrets (Claude Code's
  troubleshooting page), which would be stored in plain text, readable in the
  sandbox, if a contributor logs in to an MCP server there. `oauth_capture` as
  configured covers Claude Code's own login only.

### 5.4 First live session — login captured, gh works; two gaps found

Run on 2026-11-25 in a `pfb-spike-keychain` session (candidate 7, checked
identical to the candidate file with `cmp`; nono 0.82.0, Claude Code 2.1.332),
started by the maintainer with the commands of §4.1.

| #   | Result                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| K1  | `canary_default`: exit 44, `The specified item could not be found in the keychain`, preceded by `SecKeychainSearchCreateFromAttributes: One or more parameters passed to a function were not valid`. `canary_nono`: exit 44, same messages; same control, exit 0. Control for `canary_default`, run after it: without `-w`, the same lookup exits 0 in the maintainer's terminal, outside the sandbox, so the item still exists (and in the `pfb-claude` session before it, §2). |
| K2  | `Claude Code-credentials`, without `-w`: exit 44, same messages. Control in the maintainer's terminal: exit 0.                                                                                                                                                                                                                                                                                                                                                                   |
| K3  | `true`, reported by the maintainer. `claude auth login` completed.                                                                                                                                                                                                                                                                                                                                                                                                               |
| K4  | Prompts are answered. `claude auth status --json`: `loggedIn: true`, `authMethod: claude.ai`.                                                                                                                                                                                                                                                                                                                                                                                    |
| K5  | `gh api user` and `gh pr list -R PeopleForBikes/ai-toolkit`: exit 0. `GITHUB_TOKEN` equals `NONO_PROXY_TOKEN` (a placeholder).                                                                                                                                                                                                                                                                                                                                                   |
| K8  | In the maintainer's terminal, variable `unset`: `claude auth status --json` reports `loggedIn: true`. `~/.claude/.credentials.json`: no such file.                                                                                                                                                                                                                                                                                                                               |
| —   | `nono why --self`: `login.keychain-db` `DENIED` (`filesystem_deny`); `oauth-capture/providers.json` `DENIED` (`path_not_granted`).                                                                                                                                                                                                                                                                                                                                               |
| —   | `~/.claude/.credentials.json` does not exist: the isolated folder is used.                                                                                                                                                                                                                                                                                                                                                                                                       |

- **claude.ai connectors break**: Claude Code reports `CLAUDEAI_BEARER_REJECTED`
  for the claude.ai Docs connector, which worked in the `pfb-claude` session the
  same day. Connectors go through `mcp-proxy.anthropic.com` (Claude Code's
  binary), which candidate 7 does not list in `api_hosts`, so the phantom is
  probably forwarded as it is. Candidate 7b adds the host (K11). The phantoms of
  one host are admitted for the route names of that profile
  (`oauth_capture/mod.rs:264`, `proxy_runtime.rs:2642-2643`), and adding a host
  renames the route, so 7b probably needs a new login.
- **nono's Claude Code preparation is lost**: nono applies it only to profiles
  that reach the pack (`package_status.rs:157`, `sandbox_prepare.rs:1721-1726`).
  Here `CLAUDE_CONFIG_DIR` is unset, so Claude Code uses `~/.claude.json`
  instead of `~/.claude/.claude.json`, which the `pfb-claude` session uses: two
  diverging files, and the temporary files next to the first are not writable
  (`nono why`: `path_not_granted`), which nono's source says makes saves fail
  silently. Candidate 7b sets the variable. The check that the pack was not
  withdrawn by its publisher is lost too: candidate 1 costs more than lines.

- **Bar 1 (no keychain item can be read)**: met for the `security` tool, with
  the three lookups failing in the session and succeeding outside it. Other ways
  in (the Security framework) are denied by nono's source (§5.1), not tested.
- K8 was run while the spike session was open, before any refresh.

### 5.5 Second live session (7b) — refresh works, a parallel session is logged out

Run on 2026-11-25 in a session started with candidate 7b (`cmp`: identical to
the candidate file; same versions). The maintainer was asked to unset the
variable in the terminal first, which the session cannot verify.

| #      | Result                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| K10    | `CLAUDE_CONFIG_DIR` is `~/.claude` and `CLAUDE_SECURESTORAGE_CONFIG_DIR` is `~/.claude/nono-login` in the session; `~/.claude/.credentials.json` absent.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| K11    | The claude.ai Docs connector connects, and a read-only call to it answers.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| K3     | For the new login: `true`, reported by the maintainer.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| K4, K5 | `loggedIn: true`; `gh api user` and `gh pr list`: exit 0; `GITHUB_TOKEN` is still the placeholder.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| K6     | Pass. The maintainer set `expiresAt` a minute in the past at 17:43 (UTC−6); within seconds, before any prompt, the file was rewritten (`ls -l`: 17:43). Compared with the copy taken before the edit: new access token and new refresh token (both `false` for equality); access token still shaped `sk-ant-oat01-…` and refresh token still `nono_…` (phantoms); `expiresAt` 2026-11-26T07:43:50Z instead of 06:53:53Z, eight hours after the refresh. The session answers afterwards; `claude auth status`: `loggedIn: true`. So Claude Code refreshed through nono's token endpoint capture and received phantoms.                            |
| K7     | Fail. The maintainer forced a refresh with a second `pfb-spike-keychain` session open (the copy `.bak2` exists), then sent a prompt in each: one session answered, the other reported that it was logged out (exact text not kept; which session failed was not reported). The maintainer then ran `/login` in this session (`Login successful`); the login file was rewritten at 18:04 and `loginExpiresAt` moved to 2026-12-24, a new login. The claude.ai connector of this session disconnected and came back with it. This is the failure described in nono #2087 and #2299: each session's proxy loads the phantom store once, at startup. |
| —      | `nono why --self`: the keychain and `oauth-capture/providers.json` `DENIED`, as in §5.4.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |

- The profile alone can isolate the login, if the terminal had the variable
  unset (see above): no launch command is needed.
- The missing `api_hosts` entry is the likely cause of the failure of §5.4: 7b
  also had a new login and the two variables, so it was not isolated.
- `~/.claude/.claude.json` shrank by 11 kB between the sessions. Compared by key
  with Claude Code's own backups, only caches changed; no project was lost.

## 6. Conclusion & Recommendation

**No-Go**, decided by the maintainer on 2026-11-25.

Removing the keychain grant is feasible: a profile that extends `default`
instead of the pack, with nono capturing Claude Code's login (candidate 7b), met
four of the five parts of the bar in live sessions:

1. **No keychain item readable**: three lookups fail in the session and succeed
   outside it (K1, K2); the files and the keychain services are denied (§5.1).
2. **Claude Code logs in and refreshes**: yes, with placeholders only (K3, K4,
   K6), and the claude.ai connectors work once `mcp-proxy.anthropic.com` is
   listed (K11). **But not with two sessions open**: a refresh in one logged the
   other out (K7). Contributors run several sessions at once.
3. **`gh` works** through the `github_agent` route (K5).
4. **One profile**: the profile sets the variables that isolate the login (K10).
5. **Other sessions unaffected**: the contributor's own login stayed in place
   (K8, before the failed refresh); K9 was not run.

The failure of K7 is nono's (#2087, #2299): the fix, PR #2088, has merge
conflicts and no activity since 2026-10-09, and 0.82.0 is the newest release.
The maintainer chose not to ship a setup that logs sessions out, nor to make
`pfb-claude` depend on an unreleased fix.

Other costs found on the way, which any later attempt must weigh:

- Leaving the pack means copying it (105 to about 280 lines) and losing what
  nono does only for profiles that reach it: its Claude Code preparation (§5.4)
  and the check that the pack was not withdrawn.
- The isolation of the login relies on `CLAUDE_SECURESTORAGE_CONFIG_DIR`, which
  Claude Code does not document (§5.3).
- nono keeps the real tokens in plain text in its state directory, for up to 90
  days (§5.2).

**No stopgap**, also decided by the maintainer: candidates 3 and 4 protect only
the agent's GitHub token and were not tested. `SECURITY.md` ("Known gaps")
already tells contributors to keep tokens with wider scopes out of the login
keychain, and the token swap of `specs/0001-agent-github-identity` narrows what
the readable token can do.

**When to reopen**: when a nono release fixes #2087 (or #2269, which would
remove the copy of the pack), start from candidate 7b (§4) and repeat K7, K8 and
K9 first.

## 7. Still Open

- K9 (a `pfb-claude` session after the spike) and K8 after the refresh: not run
  before the verdict.
- Whether the claude.ai connector failure of §5.4 came from the missing host
  alone: 7b changed three things at once.
- Candidates 2, 3 and 4: not tested.
- Linux: not tested.
