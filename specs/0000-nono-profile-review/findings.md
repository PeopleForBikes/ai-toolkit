# Findings: Review of the pfb-claude nono profile

Everything non-obvious learned while implementing this feature: behavior that
looks like a bug unless you know it is deliberate, traps in the libraries and
tools, and what worked. Each entry says what the rule is, how it was caught, and
what it cost.

Status: complete for tasks 1 to 10 (`just ci` passes; live sessions with and
without the agent token verified on 2026-11-18). Keep it current as the code
changes.

## 1. Behavior that does not survive a naive implementation

### 1.1 A plain `git push` is stopped by GitHub before the proxy's rule applies

The `github.com` rules (`nono/profiles/pfb-claude.json`, `allow_domain` entry
`github.com`) refuse `POST …/git-receive-pack`, the push itself. But a push
starts with `GET /<owner>/<repo>.git/info/refs?service=git-receive-pack`, which
`GET /**` allows; GitHub answers it with `401` and a credential challenge, so a
push without credentials ends with
`fatal: could not read Username for 'https://github.com'` and never reaches the
rule. The proxy's refusal only shows on the `POST`: sent directly with `curl`,
`git-receive-pack` gets a `403` with no `server: GitHub-Babel` header and no
`x-github-request-id` (answered by the proxy), while `git-upload-pack` to the
same missing repository gets GitHub's own `401` (`server: GitHub-Babel/3.0`).

**Caught by**: task 8.4, which expected the push itself to be refused by the
proxy rather than by GitHub.

**Cost**: none for security (the rule holds for any agent that does obtain push
credentials); a test of Requirement 4.3 must send the `POST` directly, or it
only proves that the agent has no Git credentials.

### 1.2 Denying `.git/hooks` disables the hooks inside the sandbox

`$WORKDIR/.git/hooks` is in `filesystem.deny`
(`nono/profiles/pfb-claude.json:15`), and nono's deny covers reads as well as
writes: `ls .git/hooks` fails with `Operation not permitted`. Git treats the
unreadable directory as having no hooks, without a warning, so
`git commit --allow-empty` succeeds (Requirement 5.3) and any pre-commit hook
the contributor installed does not run on commits made in a Session.

**Caught by**: task 8.6;
`nono why --self --path .git/hooks/pre-commit --op write` reports
`filesystem_deny`, and a real write fails with `Operation not permitted`.

**Cost**: the commit fallback of `design.md` (Error Handling) was not needed.
`SECURITY.md` ("Files") and `CHANGELOG.md` said only that hooks were no longer
writable; both now say that commits in the sandbox skip them.

### 1.3 Without the agent token, the proxy refuses the route's calls with `503`

When the keychain item is missing, nono starts the Session anyway, leaves
`GITHUB_TOKEN` unset (no Session_Token is issued; `GITHUB_AGENT_BASE_URL` is
still set), and gh, with its empty `GH_CONFIG_DIR`, reports
`You are not logged into any GitHub hosts`. The proxy does not forward the
requests that match the route's `endpoint_rules` without a token: it answers
them itself with `503` and a JSON body whose `error` is `credential_unavailable`
("nono could not load the managed credential"), so even an anonymous `GET` of a
public repository through `api.github.com` fails. Requests outside the rules
(`DELETE`, `PATCH`) still reach GitHub and get `401 Requires authentication`
(`server: github.com`). `github.com` itself is unaffected (`200`).

**Caught by**: task 9, in a session started with a copy of the profile whose
`credential_key` is `nono_spike_missing` (no such keychain item, checked with
`security find-generic-password`, exit status only).

**Cost**: none against Requirement 3.5, which holds, and the design's open
question is closed (`design.md`, Error Handling). Without the token the agent
has no GitHub API access at all, not anonymous access; `SECURITY.md` now says
so. An agent calling the API with `curl` sees the `503`, not the
`401 Bad credentials` or "not logged in" that the README's recommended line
named; _corrected after task 10_: at the maintainer's request, Requirement 7.7
and the README line now name the `503` with `credential_unavailable` too.

## 2. Library and tooling traps

### 2.1 A bare `credential_key` accepts only letters, digits and underscores

`nono profile validate` refuses `"credential_key": "nono-spike-missing"`: the
key `must contain only alphanumeric characters and underscores`, unless it is a
URI (`op://`, `keyring://`, `env://` and others). The key is also the keychain
account name, so the account for a bare key cannot contain a hyphen. Task 9's
copy uses `nono_spike_missing`, and `tasks.md` was corrected.

### 2.2 nono adds a `<ROUTE>_BASE_URL` variable for a custom credential route

The Session's environment holds
`GITHUB_AGENT_BASE_URL=http://127.0.0.1:<port>/github_agent`, the route's local
reverse-proxy endpoint, next to `GITHUB_TOKEN` (the Session_Token) and
`NONO_PROXY_TOKEN`. gh does not use it: it reaches `api.github.com` through
`HTTPS_PROXY`, where the route injects the token. It is not a credential and
needs no `deny_vars` entry.

### 2.3 A mise shim with no configured version looks like a sandbox failure

`typos --version` in ai-toolkit fails with
`mise ERROR No version is set for shim: typos`: the tool is installed, but
ai-toolkit has no mise configuration and the maintainer has no global one. It is
not a denial. `mise x github:crate-ci/typos@1.52.1 -- typos --version` runs the
installed tool from the sandbox (`typos-cli 1.52.1`), and `just` (a mise shim
too) runs as usual.

### 2.4 The agent cannot see how its Session was started

`ps` is refused in the sandbox (`/bin/ps: Operation not permitted`), so the
launch command cannot be read from inside. Task 8.1 relied instead on the
installed profile being identical to the repository's (`jq -S` comparison of
`~/.config/nono/profiles/pfb-claude.json`) and on the Session's environment.

### 2.5 `unittest discover` does not run doctests on its own

`just test` runs `python3 -m unittest discover -s scripts`, which collects
`TestCase` classes only: a docstring example in a `scripts/` module never runs
unless the module adds it. `scripts/test_nono_profiles.py` defines `load_tests`
to add `doctest.DocTestSuite()` for its path helpers; before it, no module in
`scripts/` had a doctest that ran, although `CLAUDE.md` describes `just test` as
"unit tests and doctests".

## 3. Method — what actually worked

### 3.1 Run the invariant test on the old profile first

`scripts/test_nono_profiles.py` was written before the profile changed and run
on version 1.0.0 (`just test`, Python 3.15.2, 2026-11-18): 14 tests ran, 24
failures counting sub-tests, in seven tests. As expected, only
`test_no_wildcard_hosts` and `test_hosts_sorted` passed (the 1.0.0 hosts were
already sorted), and the five tests of `scripts/test_sync_claude_settings.py`
still passed. The failures name what 2.0.0 must change:

- `test_identity`: `meta.name` was `claude`.
- `test_no_dead_or_open_paths`: `/Library/Keychains`, `~/.docker` and
  `~/.config/gh` granted; no `.git/hooks` deny; no VS Code exclusion.
- `test_github_web_allows_reads_and_fetch`, `test_agent_route`,
  `test_developer_tokens_removed`: no endpoint rules, no credential route, no
  `deny_vars`.
- `test_hosts_documented`: `SECURITY.md` named none of the 15 allowed hosts in a
  code span; it only said "network access to the domains listed in the profile",
  so a new host never needed a documentation change.
- `test_token_check_matches_route`: no `agent_token_account` in the `justfile`.

_Corrected after task 7_: the launch warning of the `justfile` and
`test_token_check_matches_route` were removed at the maintainer's request
(macOS-specific, little value over the agent's own warning); the suite now has
13 tests (15 with the two doctests added after the spec review, §3.4), and the
other eight checks of the baseline above still apply.

Seeing each test fail on the old profile shows it can fail at all, which a test
written after the change cannot show.

### 3.2 Live session with the installed profile (task 8)

Started by the maintainer from ai-toolkit after
`just install-nono-profiles force`, with `just nono-claude-danger`
(`nono run --allow-cwd --profile pfb-claude -- claude --dangerously-skip-permissions`),
no extra flag; nono 0.82.0, gh authenticated as the maintainer's account through
the agent token. Every check passed, and no fallback of `design.md` was needed:

| Check (requirement)                 | Result                                                                                                                                                                               |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Token isolation (3.1, 3.2)          | `GITHUB_TOKEN` equals `NONO_PROXY_TOKEN` (64 characters, not a GitHub token); `GH_TOKEN`, `GH_ENTERPRISE_TOKEN`, `GITHUB_ENTERPRISE_TOKEN` unset; `deny_vars` kept the Session_Token |
| Agent token (3.2)                   | `gh api -i user`: `200`, `X-Oauth-Scopes: public_repo, read:org`; `gh auth status`: logged in through `GITHUB_TOKEN`                                                                 |
| gh on bna-api (3.6)                 | `gh pr list`, `gh issue list`, `gh pr checks 559`, `gh run view <failed run> --log-failed` (1662 lines) exit 0                                                                       |
| Outside the route (3.4)             | `DELETE` repository, `PUT …/pulls/1/merge`, `PATCH …/issues/1` on a missing repository: `401 Bad credentials`                                                                        |
| Allowed_Calls (3.3)                 | `POST …/issues` and `POST …/issues/1/comments` on a missing repository: `404 Not Found` (token sent)                                                                                 |
| Fetch and push (4.2, 4.3)           | `git ls-remote` on bna-api succeeds; push refused (§1.1)                                                                                                                             |
| Network (2.4, 2.5)                  | `cargo search serde`, a raw GitHub file (`200`), `uvx --from 'schemathesis==4.33.4' st --version` (`4.33.4`) succeed; `example.com` refused, `nono why`: `proxy_filtered`            |
| uv and mise (1.4, 6.1)              | `uv tool dir` is `~/.cache/uv/tools`; mise tools run (§2.3)                                                                                                                          |
| Code outside the sandbox (5.3, 5.4) | commit on a throwaway branch succeeds (branch deleted); writes to `.git/hooks` (`filesystem_deny`) and VS Code's `User/settings.json` (`path_not_granted`) refused                   |
| `just ci` (8.1)                     | lint, validate, 13 tests: pass                                                                                                                                                       |

The probes changed nothing on GitHub: they targeted
`PeopleForBikes/nono-spike-missing`, which does not exist.

### 3.3 Live session without the agent token (task 9)

Started by the maintainer from ai-toolkit with the copy of the installed profile
whose `credential_key` is `nono_spike_missing`
(`nono run --allow-cwd --profile <copy> -- claude --continue`). The Session
started; `GITHUB_TOKEN`, `GH_TOKEN`, `GH_ENTERPRISE_TOKEN` and
`GITHUB_ENTERPRISE_TOKEN` are unset; `gh auth status` exits 1 with
`You are not logged into any GitHub hosts` and `gh issue list` asks for a login,
so gh does not fall back to the developer's login (Requirement 3.5). The
keychain item `nono`/`github_agent` still exists, which rules out the installed
profile as the one in use: with it, `GITHUB_TOKEN` would be set (§3.2).

### 3.4 Break the profile to test the invariant test

The spec review (after task 10) ran the invariant test against modified copies
of the profile and found four that passed although they broke a property the
design says the test checks (P2, Requirement 3.5): nono's built-in `github`
route added to `credentials`, a second route reusing the agent's
`credential_key` towards another upstream, the route's `credential_key` set to
`env://GITHUB_TOKEN`, and `GH_CONFIG_DIR` pointed at `$HOME/.config/gh`. Path
grants were compared as exact strings, so `$HOME/.docker`, `~/.config/gh/` or
`~/.config/gh/hosts.yml` passed too. Writing the test first against 1.0.0 (§3.1)
showed each test could fail, not that it failed on every way of breaking its
property.

The test now requires `credentials == ["github_agent"]`, a single custom route
whose `credential_key` is `github_agent`, `GH_CONFIG_DIR` equal to
`$HOME/.cache/nono/gh`, and no grant on, inside or above a forbidden path after
normalizing `$HOME` and slashes (`normalize_path`, `overlaps`). A scratch script
that loads the test module, points `PROFILE_PATH` at a broken copy and runs
`PfbClaudeProfileTest` confirmed it: the eleven broken copies (the four above,
an unenabled second route, `GH_CONFIG_DIR` removed, and five path grants
including the parent `~/.config`) each fail the expected test, while the
unchanged profile and `~/.config/ghostty`, a near-miss that must pass, pass. Use
the same approach whenever a test guards a security property: list the ways to
break it, and run the test on each.
