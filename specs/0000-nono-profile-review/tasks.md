# Implementation Plan: Review of the pfb-claude nono profile

## Overview

The invariant test comes first and runs against the current 1.0.0 profile, so
that each property is seen failing before the profile is rewritten. Then the
profile and the documentation, which the test also reads. The live session comes
last: it needs the profile installed, so it runs in a new session started by the
maintainer, and its results go to `findings.md`. Commit each task on its own
(one change per commit), with the test and the change it covers together.

## Tasks

- [x] 1. Write the invariant test against the current profile
  - [x] 1.1 Create `scripts/test_nono_profiles.py`
    - `unittest`, standard library only, docstrings on the class and each test,
      in the style of `scripts/test_sync_claude_settings.py`.
    - Locate the repository with `Path(__file__).resolve().parent.parent`; load
      `nono/profiles/pfb-claude.json` (`json`), and read `SECURITY.md` as text.
    - Tests, as in `design.md` (component 2): `test_identity`,
      `test_no_wildcard_hosts`, `test_hosts_sorted`,
      `test_github_web_allows_reads_and_fetch`, `test_agent_route`,
      `test_developer_tokens_removed`, `test_no_dead_or_open_paths`,
      `test_hosts_documented`. Rules compare as sets of `(method, path)` pairs.
    - _Requirements: 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_
  - [x] 1.2 Run `just test` on the 1.0.0 profile and record in `findings.md`
        which tests fail and why (expected: all but `test_no_wildcard_hosts` and
        `test_hosts_sorted`: the 1.0.0 hosts are already sorted); the existing
        settings tests still pass.
    - _Requirements: 8.1_

- [x] 2. Rewrite `nono/profiles/pfb-claude.json` as version 2.0.0
  - Write the file of `design.md` (component 1), keeping `suppress_save_prompt`
    from 1.0.0 unchanged and the `description`
    `PeopleForBikes agents: org tools, dedicated GitHub token`.
  - Check the host list against Requirement 2.1 (31 hosts, `github.com` as an
    object), in code-point order.
  - `just validate-nono-profiles` passes; in `just test`, only
    `test_hosts_documented` still fails, until task 4.
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.6, 3.1, 3.3,
    3.4, 3.5, 4.1, 5.1, 5.2, 6.1_

- [x] 3. ~~Warn about a missing agent token in `justfile`~~ Dropped
  - Implemented, then removed at the maintainer's request: the check worked on
    macOS only and added little over the agent's own warning (task 5, README
    adoption note). The `justfile` is unchanged by this feature, and
    `test_token_check_matches_route` went with it.

- [x] 4. Document the profile in `SECURITY.md`
  - Replace the `pfb-claude` bullet of "What the shared configuration grants"
    with the subsection "The `pfb-claude` nono profile" of `design.md`
    (component 3): the base it extends, a table of every allowed host in code
    spans with its reason, the `github.com` rules, paths added and removed,
    ports, `deny_vars` and `set_vars`, the agent token route and its
    Allowed_Calls, and the accepted gaps (GraphQL mutations, the token readable
    in the login keychain, `.git/config` and `~/.claude` writable, Linux not
    verified, `claude/settings/base.json` skipped under
    `--dangerously-skip-permissions`).
  - Update "Supported versions" if it names the profile's version.
  - `test_hosts_documented` passes.
  - _Requirements: 7.1, 7.2_

- [x] 5. Update `README.md`
  - "nono profiles": replace the sentence on `~/.config/gh`,
    `/Library/Keychains` and `~/.docker` with a summary pointing to
    `SECURITY.md`; add "The agent's GitHub token": classic token, scopes
    `public_repo` and `read:org`, an expiry (90 days suggested),
    `security add-generic-password -s nono -a github_agent -w`, rotation with
    `-U`, `just install-nono-profiles force`, restart sessions; what happens
    without it (the session starts, gh is not logged in).
  - "Adopting the skills in a project": the two recommended lines for each
    project's `CLAUDE.md` / `AGENTS.md`: read CI logs with `gh run view`
    (`--log`, `--log-failed`, `--job <id> --log`), and stop and ask the
    contributor to set up the agent token when gh is not logged in, GitHub
    answers `401 Bad credentials`, or the proxy answers `503` with
    `credential_unavailable`.
  - Check the "Quick start" and "Layout" sections still match.
  - _Requirements: 7.3, 7.4, 7.5, 7.7_

- [x] 6. Add the change to `CHANGELOG.md` under `## [Unreleased]`
  - **Changed**, **Added** and **Removed** entries of `design.md` (component 5),
    including that contributors must create the agent token and run
    `just install-nono-profiles force`.
  - _Requirements: 7.6_

- [x] 7. Checkpoint: formatting and CI
  - Run `just fmt-md`, then `just ci` (lint, validate, test): everything passes,
    the invariant test included.
  - _Requirements: 1.6, 8.1_

- [x] 8. Live session with the installed profile (macOS)
  - [x] 8.1 Ask the maintainer to run `just install-nono-profiles force` and to
        start a new session from ai-toolkit with `just nono-claude-danger`, no
        extra flag; record the commands in `findings.md`.
    - _Requirements: 3.2_
  - [x] 8.2 Token isolation: `GITHUB_TOKEN` equals `NONO_PROXY_TOKEN`; no
        `GH_TOKEN`, `GH_ENTERPRISE_TOKEN` or `GITHUB_ENTERPRISE_TOKEN` (names
        only); `gh api -i user` reports
        `X-Oauth-Scopes: public_repo,     read:org`. If `GITHUB_TOKEN` is
        missing, apply the fallback of `design.md` (Error Handling): remove it
        from `deny_vars` and from the test, and record it.
    - _Requirements: 3.1, 3.2_
  - [x] 8.3 GitHub use: `gh pr list`, `gh issue list`, `gh pr checks` and
        `gh run view --log-failed` on `PeopleForBikes/bna-api`; probes that
        cannot change anything, as in `spike.md` §5.11 (`DELETE` and
        `PUT …/merge` on a missing repository or pull request → `401`; `POST` an
        issue on a missing repository → `404`).
    - _Requirements: 3.3, 3.4, 3.6_
  - [x] 8.4 No push over HTTPS:
        `git ls-remote https://github.com/PeopleForBikes/bna-api.git` succeeds;
        a `POST …/git-receive-pack` sent directly to a repository that does not
        exist is refused by the proxy (no GitHub headers); a plain `git push`
        stops earlier at GitHub's credential challenge (`findings.md` §1.1).
    - _Requirements: 4.2, 4.3_
  - [x] 8.5 Network and tools: `cargo search`, a file from
        `raw.githubusercontent.com`,
        `uvx --from 'schemathesis==4.33.4' st     --version` (uv's tool
        directory is `UV_TOOL_DIR`), a host outside the list refused, a tool
        installed by mise
        (`mise x github:crate-ci/typos@1.52.1 -- typos --version`; ai-toolkit
        sets no version for the shim, `findings.md` §2.3).
    - _Requirements: 1.4, 1.5, 2.4, 2.5, 6.1_
  - [x] 8.6 Code outside the sandbox: `git commit --allow-empty` on a throwaway
        branch, then delete the branch; `nono why --self --op write` refuses
        `.git/hooks/pre-commit` and VS Code's `User/settings.json`. If the
        commit fails, apply the fallback of `design.md` (remove the `.git/hooks`
        deny and its test expectation) and record it.
    - _Requirements: 5.3, 5.4_
  - [x] 8.7 Run `just ci` in the session.
    - _Requirements: 8.1_

- [x] 9. Session without the agent token (macOS)
  - Write a copy of the installed profile to the agent's scratch directory with
    `credential_key` set to `nono_spike_missing` (a bare key accepts only
    letters, digits and underscores, `findings.md` §2.1); ask the maintainer to
    start a session with it
    (`nono run --allow-cwd --profile <copy> -- claude …`).
  - In that session: it started; `GITHUB_TOKEN` holds no GitHub token;
    `gh auth status` reports no login and does not fall back to the developer's
    login. If nono refused to start, stop and ask the team (design Open
    Questions). Record the result in `findings.md`.
  - _Requirements: 3.5_

- [x] 10. Checkpoint: final consistency
  - `just ci` passes; `design.md` and `tasks.md` still describe what was built
    (otherwise `pfb-spec-update`); every fallback taken is in `findings.md`.
  - _Requirements: 8.1_

## Notes

- Tasks 8 and 9 need sessions the maintainer starts; the agent cannot start or
  nest nono sessions (`spike.md` §4). Use `claude --continue` from the same
  directory to resume.
- The probes of task 8 must not change anything on GitHub: target a repository
  or pull request that does not exist. Anything that does change GitHub needs
  the maintainer's agreement first.
- Never print a token: check lengths, prefixes or equality only.
- Changes to the profile, the test's expectations or `SECURITY.md` are
  security-sensitive (`CLAUDE.md`, "Security"): describe what each grants and
  why in the pull request.
- Do not commit or push unless asked (`CLAUDE.md`).
