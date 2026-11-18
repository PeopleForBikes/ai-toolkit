# Spike: Review of the pfb-claude nono profile

## Status

Concluded — Conditional Go: a single, up-to-date `pfb-claude` with a handful of
reviewed hosts, a classic agent token injected by nono's proxy, and the cleanup
of §5.1 removes the one-off grants of past work without opening a new channel,
provided the conditions of §6 are met. See §6.

## 1. Intent

Agents at PeopleForBikes run in the [nono] sandbox with `pfb-claude`, a profile
the organization shares (`nono/profiles/pfb-claude.json` in this repository,
started by `just nono-claude-danger` here and in bna-api). It must stay tight,
yet recent features and spikes needed one-off grants to finish their work (PyPI,
`raw.githubusercontent.com`, the Docker socket, GitHub release assets, GitHub
Actions logs), and every one-off grant means stopping the session and restarting
it with extra flags. Some restrictions slow the agent down for little gain:
`raw.githubusercontent.com` is blocked although the same content is reachable
through hosts the profile already allows.

The spike answers: **which changes to `pfb-claude` give the best trade-off
between a hermetic sandbox and an agent that completes most of its work without
one-off grants?** It informs an update of the shared profile, which the team may
then publish in the [ai-toolkit](https://github.com/PeopleForBikes/ai-toolkit)
project.

**Constraints that shaped scope**:

- One profile for every PeopleForBikes repository (bna-api,
  brokenspoke-analyzer, ai-toolkit, …), not a base with per-repository layers.
- macOS and Linux. The experiments run on macOS only; anything specific to Linux
  is marked as not tested.
- On GitHub, the agent may read everything (code, issues, pull requests, Actions
  logs), create pull requests and comment on issues and pull requests. It must
  not push, merge, or change repository or organization settings. Pushing stays
  with the developer, over SSH. _Superseded by §1.1._
- Tools are installed outside the sandbox (`bna-api/specs/0003-tool-manager`),
  so the profile does not need what installing them needs (sigstore, TUF,
  `nodejs.org`, write access to mise's data directory).
- The maintainer applies the changes to `pfb-claude` by hand: the spike provides
  `nono run` command lines and candidate profile files, and never promotes a
  profile.

**Success bar** (agreed 2026-11-18):

1. Every one-off grant recorded in past spikes and in the agent transcripts is
   either covered by the recommended profile or rejected with a stated reason.
2. The profile adds no high-risk capability (credentials, the Docker socket,
   wildcard storage hosts) and reduces the GitHub write scope to reading,
   creating pull requests and commenting.
3. A live session with the candidate passes `just ci` and a fixed task list:
   `cargo search`, fetching a raw GitHub file, `gh pr view` and
   `gh pr create --dry-run`, `gh run view --log`, and
   `uvx schemathesis --version`.

### 1.1 Reframe (2026-11-18, after the static review)

After reading §5.2, the team changed two things:

- **GitHub**: agents sometimes need to create issues and pull requests, so the
  team accepts more GitHub access than above, through **a token dedicated to the
  agent**, scoped to what the agent needs and never an admin token, and stored
  in the keychain. The developer's own `GITHUB_TOKEN` must not be readable by
  the agent. Reading the CI logs of GitHub workflows should work if possible.
- **How candidates are tested**: every grant is passed as a `nono run` flag on
  top of `--profile pfb-claude`, not through a candidate profile file. Flags can
  only add access, so the restrictions of candidate 1 (group exclusion,
  `deny_vars`, `filesystem.deny`, endpoint rules on hosts the profile already
  allows) stay static findings; they go into the profile by hand.

Success bar item 2 now reads: the profile adds no high-risk capability, the
agent never sees the developer's GitHub token, and the agent's own token can
read, create and comment on issues and pull requests and read Actions, but
cannot push, merge, or change settings. Item 3 adds `gh issue create` and
reading the logs of a failed job. The work of §5.6 (candidate 1, built on C2) is
kept as superseded.

### 1.2 Reframe (2026-11-18, after the token review)

- **Classic token, for now**: the team chose a classic personal access token
  dedicated to the agent over a fine-grained one (§5.9 compares them). A classic
  scope cannot separate creating issues and pull requests from pushing, so the
  limits move back to nono's proxy (§5.10), with the GraphQL gap of C2 accepted
  as a known risk. The fine-grained token (C4) is set aside, not rejected.
- **Location**: the spike moves to the ai-toolkit repository, which holds the
  shared profile. It started in bna-api as
  `bna-api/specs/0006-nono-profile-review/spike.md`, never committed there, and
  moved here on 2026-11-18 as `specs/0000-nono-profile-review/spike.md`. Paths
  written `bna-api/…` are in the
  [bna-api](https://github.com/PeopleForBikes/bna-api) repository; other paths
  are in this one.

Success bar item 2 now reads: the agent never sees the developer's GitHub token;
the agent's own token reads, creates and comments on issues and pull requests,
and reads Actions; the proxy refuses the REST calls that push, merge, delete or
change settings.

## 2. Current Baseline

Measured on 2026-11-18 inside a session started with
`nono run --allow-cwd --profile pfb-claude -- claude --dangerously-skip-permissions`
(nono 0.82.0, macOS arm64). The capabilities come from the file nono names in
`$NONO_CAP_FILE`; each claim below was checked with `nono why --self`.

### 2.1 The profile

`~/.config/nono/profiles/pfb-claude.json` extends `nolabs-ai/claude`, which
extends `default`. On top of the base it grants:

- **Filesystem**: read `/Library/Keychains`, `~/.config/gh`, `~/.config/mise`,
  `~/.docker`, `~/.local/bin/mise`, `~/.local/share/mise`; read and write
  `~/.local/state/mise`, `~/.npm`; write `~/.cargo/git`, `~/.cargo/registry`,
  `~/Library/Caches/brokenspoke-analyzer`.
- **Network**: proxy filtering with 20 hosts (`allow_domain`): Claude's own
  hosts, `github.com`, `api.github.com`, `codeload.github.com`,
  `objects.githubusercontent.com`, `release-assets.githubusercontent.com`,
  `results-receiver.actions.githubusercontent.com`, `index.crates.io`,
  `static.crates.io`, `registry.npmjs.org`, `download.geofabrik.de` and three
  Overpass mirrors, `localhost` and `127.0.0.1`; local ports 3000 and 5432.
- `meta.name` is `claude`, not `pfb-claude`.

From `nolabs-ai/claude` it inherits read and write access to `~/.claude`, to the
login keychain (`~/Library/Keychains`, through `bypass_protection`), to VS
Code's configuration (`~/.vscode`, `~/Library/Application Support/Code`, group
`vscode_macos`), and the working directory.

### 2.2 Published and installed copies differ

The published copy, `nono/profiles/pfb-claude.json` in this repository
(installed by `just install-nono-profiles`), is older than the installed one the
measurements above come from. Compared with `diff` on 2026-11-18, the installed
copy adds the mise grants (`~/.config/mise`, `~/.local/share/mise`,
`~/.local/bin/mise`, `~/.local/state/mise`), write access to `~/.cargo/git`,
`~/.cargo/registry` and `~/.npm`, and the hosts `localhost`,
`registry.npmjs.org`, `release-assets.githubusercontent.com`,
`results-receiver.actions.githubusercontent.com` and `static.crates.io`. These
are one-off grants made permanent locally and never published; `SECURITY.md`
still describes the published copy. Other contributors run the published copy,
so their agents miss the tools installed by mise (see
`bna-api/.github/CONTRIBUTING.md`).

`claude/settings/base.json` allows only read-only `git` and `gh` commands and
asks before anything else, but `just nono-claude-danger` starts Claude Code with
`--dangerously-skip-permissions`, which skips those rules: in that mode the nono
profile is the only limit on what the agent does.

### 2.3 One-off grants in the record

Past spikes and features restarted the session with extra flags:

| Grant                                                                  | Needed for                            | Source                                                                               |
| ---------------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------ |
| `--allow-domain release-assets.githubusercontent.com` (now in profile) | GitHub release downloads              | `bna-api/specs/0003-tool-manager/spike.md` §2                                        |
| `--allow-domain nodejs.org`                                            | mise installing Node.js               | `bna-api/specs/0003-tool-manager/spike.md` §4                                        |
| `--allow-domain tmaproduction.blob.core.windows.net`                   | `gh` fetching release attestations    | `bna-api/specs/0003-tool-manager/spike.md` §5.2                                      |
| `--allow-domain raw.githubusercontent.com`                             | codebook's dictionaries; schema files | `bna-api/specs/0002-rust-tooling/spike.md`                                           |
| `--allow-domain pypi.org`, `files.pythonhosted.org`, writable uv tools | Schemathesis through `uvx`; Posting   | `bna-api/specs/0005-schemathesis/design.md`, `bna-api/lambdas/specs/0000-…/spike.md` |
| `--bypass-protection ~/.docker`, `--allow-unix-socket …/docker.sock`   | Docker Compose stacks                 | `bna-api/specs/learnings/integration-issues/docker-in-the-nono-sandbox.md`           |

The agent transcripts of the three PeopleForBikes projects on this machine
(`~/.claude/projects/*/*.jsonl`) also hold the proxy's denials. Counted with:

```bash
grep -rhoE 'host [a-zA-Z0-9.-]+:[0-9]+ is not in the allowlist' \
  --include='*.jsonl' ~/.claude/projects \
  | sort | uniq -c | sort -rn
```

| Mentions | Host                                                                | Status today |
| -------: | ------------------------------------------------------------------- | ------------ |
|       35 | `registry.npmjs.org`                                                | allowed      |
|       30 | `crates.io`                                                         | denied       |
|       12 | `release-assets.githubusercontent.com`                              | allowed      |
|       11 | `tuf-repo.github.com`                                               | denied       |
|        8 | `results-receiver.actions.githubusercontent.com`                    | allowed      |
|        6 | `oauth2.sigstore.dev`                                               | denied       |
|        6 | `mcp-proxy.anthropic.com`                                           | allowed      |
|        4 | `tmaproduction.blob.core.windows.net`                               | denied       |
|        7 | `productionresultssa{1,11,32}.blob.core.windows.net` (Actions logs) | denied       |

A mention is not a distinct event: a denial quoted again later in the same
transcript counts twice, so the numbers rank the hosts but do not count
incidents. WebFetch goes through the same proxy; the transcripts hold 59
WebFetch calls, to `code.claude.com` (24), `mise.jdx.dev` (8), `oxc.rs`,
`neon.com`, `github.com` and `erraggy.github.io`; all but `github.com` are
denied today.

## 3. Candidates Considered

| Candidate                                                      | Verdict                            | Why                                                                                                                                                   |
| -------------------------------------------------------------- | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| A. Clean up dead and redundant grants                          | Recommended (static) — see §5.1    | Three grants never apply, one repeats the base profile, `blocked_commands` is not enforced, and a built-in group replaces the mise grants.            |
| B1. Built-in `developer` network profile                       | Rejected (static) — see §5.3       | Covers our gaps but also opens GitLab, a dozen LLM APIs, six more package registries and the sigstore signing hosts.                                  |
| B2. Hand-picked hosts                                          | Tested, works — see §5.3, §5.11    | `crates.io`, `raw.githubusercontent.com`, PyPI and seven documentation hosts; each adds no channel the profile does not already open.                 |
| B3. Network approvals (ask, do not deny)                       | Not tested yet — see §5.3          | Would replace restarts for the long tail of hosts; how a terminal prompt coexists with Claude's interface is unknown.                                 |
| `*.blob.core.windows.net` (Actions logs, attestations)         | Rejected before testing — see §5.3 | Matches every Azure storage account, including one an attacker owns. `productionresultssa*` is not a valid pattern.                                   |
| Listing GitHub's 199 log storage accounts                      | Rejected (tested) — see §5.8       | `productionresultssa0` to `199` exist, 199 hosts that GitHub can extend; not needed, since `gh run view` reads the same logs through an allowed host. |
| F. Actions logs through `gh run view`                          | Recommended (tested) — see §5.8    | `--log`, `--log-failed` and `--job <id> --log` work today; only the raw REST job-log endpoint redirects to a blocked storage host.                    |
| Sigstore and TUF hosts, `nodejs.org`                           | Rejected before testing — see §5.3 | Needed only to install tools, which happens outside the sandbox.                                                                                      |
| Docker socket in the profile                                   | Rejected before testing — see §5.3 | Gives the agent what Docker Desktop shares (all of `/Users`); stays a one-off grant, as the Docker learning says.                                     |
| C1. Strip `GITHUB_TOKEN` from the environment only             | Insufficient — see §5.2            | gh falls back to the token in the login keychain, which the sandbox can read.                                                                         |
| C2. Method and path rules on `github.com` and `api.github.com` | Superseded — see §1.1, §5.2        | Blocks `git push` over HTTPS and REST mutations; cannot filter GraphQL. The team chose a scoped token (C4) instead.                                   |
| C3. nono's `github` credential route (phantom token)           | Tested, works — see §5.11          | The sandbox holds nono's session token; the proxy adds the real one on `api.github.com`. gh on macOS accepts the TLS interception.                    |
| C4. A fine-grained token for agents                            | Set aside for now — see §1.2, §5.9 | GitHub itself enforces the agent's permissions, GraphQL included; the team chose a classic token for now.                                             |
| C5. A classic agent token, limited by the proxy                | Chosen, tested — see §5.10, §5.11  | Reads, issues and pull requests work; REST merges, deletions and writes go out without the token (401). GraphQL and the keychain copy stay open.      |
| D. Close paths that run code outside the sandbox               | Profile only (static) — see §5.4   | Exclude the VS Code group, deny `.git/hooks`; no `nono run` flag expresses them. `.git/config` and `~/.claude` cannot be made read-only.              |
| E. Writable uv tool directory through `UV_TOOL_DIR`            | Tested, works — see §5.5, §5.11    | Points uv at the writable cache; no new filesystem grant. On the command line, an environment prefix.                                                 |

## 4. Evaluation Method

- Machine: macOS arm64, nono 0.82.0 (Homebrew), gh 2.105.0, uv 0.13.9, in a
  session started from `just nono-claude-danger` (§2).
- Static checks run inside that session: `nono why --self` for the session's own
  capabilities, `nono why --profile <file>` and `nono profile validate` /
  `nono profile diff` for candidate files, and `nono profile guide` and
  `nono profile groups` for what nono supports. `nono why --profile` grants no
  working directory; `--allow <checkout>` stands in for `--allow-cwd`.
  `nono profile diff` does not show endpoint rules or the `environment` section.
- nono cannot be nested: `nono run --profile default -- /usr/bin/true` inside
  the session fails to create its audit directory under
  `~/.local/state/nono/audit/` (`Operation not permitted`). So no new host or
  profile can be tried from inside a session: each live test is a new session
  that the maintainer starts with a candidate file, then resumes this
  conversation (`claude --continue`).
- Candidate 1 (§5.6) was written to the agent's scratch directory and recorded
  in this document; none is promoted or written to `~/.config/nono`. Since the
  reframe (§1.1), live tests pass every grant as a `nono run` flag on top of
  `--profile pfb-claude`.
- The keychain check (§5.2) counted the length of a secret and never printed it,
  as agreed.
- Every result in §5 is a real run on 2026-11-18 unless labelled as desk review.

## 5. Findings

### 5.1 Profile hygiene — four grants do nothing, one control is not enforced

```bash
nono why --self --path /Library/Keychains/System.keychain --op read
#   DENIED  Reason: filesystem_deny  (filesystem.deny rule: /Library/Keychains)
nono why --self --path ~/.docker/config.json --op read
#   DENIED  Reason: filesystem_deny  (filesystem.deny rule: ~/.docker)
nono why --self --path ~/.local/bin/mise --op read
#   DENIED  Reason: path_not_granted  (the file does not exist on this machine)
```

- `/Library/Keychains` and `~/.docker`: the base profile's deny groups
  (`deny_keychains_macos`, `deny_credentials`) win over a grant unless
  `bypass_protection` names the path too. Both grants are dead, which is the
  right outcome; they only mislead readers into thinking the agent reads them.
- `~/.local/bin/mise`: needed only by contributors who installed mise with its
  own installer (`bna-api/.github/CONTRIBUTING.md`); harmless when absent.
- `~/Library/Caches/brokenspoke-analyzer`: the inherited group
  `user_caches_macos` already grants `~/Library/Caches` for reading and writing.
- The built-in group `mise_manager` (`nono profile groups mise_manager`) grants
  read access to `/etc/mise`, `~/.local/bin/mise`, `~/.config/mise`,
  `~/.local/share/mise` and `~/.tool-versions`: every mise read grant of the
  profile, plus the Linux system configuration. Only the state directory
  (`~/.local/state/mise`, read and write) stays hand-written.
- The capability file lists `blocked_commands` (`rm`, `cp`, `mv`, `chmod`,
  `xargs`, `npm`, `pip`, `kill`, …), yet each of them ran in the session (`cp`,
  `mv`, `chmod`, `xargs ls`, `npm --version`, `pip3 --version`, `kill -0`, and
  `rm` on a scratch file all exit 0). The guide explains why: `commands.deny` is
  "startup-only" and "not enforced on child processes" (deprecated since
  v0.33.0). It protects nothing, so it should not count as a safeguard.
- `meta.name` reads `claude`; it should read `pfb-claude`, since the profile is
  shared.

### 5.2 GitHub — the agent holds an organization admin token

```bash
gh auth status            # token values redacted
#   ✓ Logged in to github.com account … (GITHUB_TOKEN)   Active account: true
#     Token scopes: 'admin:org', 'gist', 'notifications', 'read:project',
#                   'read:repo_hook', 'repo', 'user', 'workflow', 'write:packages'
#   ✓ Logged in to github.com account … (keyring)         Active account: false
#     Token scopes: 'admin:public_key', 'gist', 'read:org', 'repo'
nono why --self --unix-socket "$SSH_AUTH_SOCK"
#   DENIED  Reason: unix_socket_not_granted
security find-generic-password -s gh:github.com -w | wc -c
#   75   (exit 0: the keyring token is readable; its value was not printed)
```

- The sandbox inherits the developer's `GITHUB_TOKEN`, and `github.com` and
  `api.github.com` are open to every method. The agent cannot push over SSH (the
  SSH agent's socket is denied, and `~/.ssh` is in the deny groups), but with
  this token it can push over HTTPS, merge, change workflows, administer the
  organization, or copy anything to a secret gist. This is by far the largest
  gap in the profile, and it makes every other network question secondary:
  GitHub already accepts any data the agent wants to send.
- **C1** (`environment.deny_vars: ["GITHUB_TOKEN", …]`) removes the variable,
  but gh then uses its keyring account, whose `repo` scope still pushes and
  merges. The keyring entry is readable because the base profile
  `nolabs-ai/claude` grants the login keychain (Claude Code keeps its own
  credentials there), and gh stores its token through the `security` tool, so
  any process in the sandbox can read it. An extending profile cannot remove an
  inherited filesystem grant (`nono profile guide`, "extends").
- **C2**: `allow_domain` accepts endpoint rules: the proxy intercepts TLS and
  allows only the listed methods and paths. Rules can allow reading, `git`
  fetches (`POST /<owner>/<repo>/git-upload-pack`) and the REST calls that
  create a pull request or a comment, and deny `git-receive-pack` (push) and
  every other REST mutation. They cannot filter GraphQL: gh sends nearly every
  command (`gh pr view`, `gh pr list`, `gh pr create`, `gh issue …`) as
  `POST /graphql`, and GraphQL can also merge (`mergePullRequest`), delete a
  branch (`deleteRef`) or write a commit (`createCommitOnBranch`), per GitHub's
  GraphQL schema (desk review). Allowing `/graphql` keeps gh working and leaves
  those open; denying it breaks most of gh. To be measured in §5.7.
- **C3**: nono ships a `github` credential route (`--credential github`): the
  sandbox gets a phantom `GITHUB_TOKEN`, and the proxy swaps in the real one,
  only on `api.github.com` and only for requests allowed by `--allow-endpoint`.
  The token cannot leave the sandbox, but the GraphQL limit of C2 remains, and
  so does the keyring token. Not tested yet.
- **C4** (desk review): a fine-grained personal access token restricted to the
  PeopleForBikes repositories, with Contents read, Pull requests and Issues read
  and write, Actions read and Metadata read. GitHub enforces it on every API,
  GraphQL included: the token cannot push (Contents read), merge needs Contents
  write, and settings need Administration. Injected through a credential route
  (C3), it never enters the sandbox. Costs: a token per developer (or a shared
  bot), the organization's approval of fine-grained tokens if its policy asks
  for it, and an expiry to renew. The developer's own tokens must then stay out
  of the sandbox, which brings back the keychain problem of C1.

### 5.3 Network — what to add, what to leave out

`nono why --self --host <host>` denies every host below today. The built-in
network profiles (in the nono binary's embedded `network-policy.json`) group
hosts:

- **B1, `developer` profile**: groups `llm_apis` (16 hosts),
  `package_registries` (18), `github` (8), `gitlab` (3), `sigstore` (4) and
  `documentation` (8). It covers `crates.io`, PyPI, `raw.githubusercontent.com`,
  `nodejs.org` and `docs.rs`, but also opens hosts no PeopleForBikes project
  uses (GitLab, RubyGems, Maven, Nix, `cdn.jsdelivr.net`, `unpkg.com`, `esm.sh`,
  a dozen LLM APIs) and `oauth2.sigstore.dev`, a signing host. It lacks
  `release-assets.githubusercontent.com`. Rejected: too wide for a profile meant
  to stay tight, and its content changes with nono releases.
- **B2, hand-picked**:
  - `raw.githubusercontent.com`: serves files of public repositories, the same
    content as `codeload.github.com` (archives) and
    `api.github.com/repos/…/contents/…`, both already allowed. It accepts no
    upload, so it adds no exfiltration channel. Unblocks schema URLs
    (`#:schema https://raw.githubusercontent.com/…` in
    `bna-api/specs/0005-schemathesis`, `bna-api/lambdas/slumber.yml`),
    dictionaries, install scripts read before running them, and Markdown
    documentation of tools.
  - `crates.io`: the API behind `cargo search` and `cargo info`; the index and
    downloads (`index.crates.io`, `static.crates.io`) are already allowed.
    Publishing needs a token in `~/.cargo/credentials.toml`, absent here and
    read-only in the sandbox.
  - `pypi.org`, `files.pythonhosted.org`: Schemathesis (`just test-schemathesis`
    in `bna-api/lambdas/tests`) and any Python tool run through `uvx`. Same
    class of risk as `registry.npmjs.org` and the crates.io hosts, already
    allowed.
  - Documentation read through WebFetch: `code.claude.com`, `docs.rs`,
    `doc.rust-lang.org`, `docs.github.com`, `hurl.dev`, `mise.jdx.dev`,
    `nono.sh`. Static sites that accept no upload. The list will keep growing;
    B3 would handle the long tail better than adding hosts one by one.
- **B3, approvals**: `network.approval_backends` with `{ "type": "terminal" }`
  asks the developer before connecting to a host outside the allowlist, instead
  of denying it; `deny_domain` entries are never offered. A `unix://` webhook
  can show the question in a helper instead. Not tested: the prompt shares the
  terminal with Claude Code's interface.
- **Rejected before testing**:
  - GitHub Actions logs and attestation bundles live on
    `productionresultssa<N>.blob.core.windows.net` and
    `tmaproduction.blob.core.windows.net`. A wildcard must cover whole labels
    (`productionresultssa*` never matches, per the guide), so the only pattern
    is `*.blob.core.windows.net`, which matches every Azure storage account,
    including one an attacker creates to receive data. Enumerating the numbered
    hosts is impractical (199 of them, §5.8), and not needed: `gh run view`
    reads the same logs through an allowed host.
  - `tuf-repo.github.com`, the sigstore hosts and `nodejs.org` are only needed
    to install tools (mise verifying attestations, mise installing Node.js),
    which happens outside the sandbox (`bna-api/.github/CONTRIBUTING.md`,
    "Agents in the nono sandbox").
  - The Docker socket gives the agent whatever Docker Desktop shares, normally
    all of `/Users` through a bind mount. It stays a one-off grant
    (`bna-api/specs/learnings/integration-issues/docker-in-the-nono-sandbox.md`).

### 5.4 Paths that run code outside the sandbox

```bash
nono why --self --op write --path .git/hooks/pre-commit          # ALLOWED
nono why --self --op write --path .git/config                    # ALLOWED
nono why --self --op write --path ~/.claude/settings.json        # ALLOWED
nono why --self --op write \
  --path "~/Library/Application Support/Code/User/settings.json" # ALLOWED
nono why --self --op write --path ~/.cargo/bin/cargo             # DENIED
```

A file the agent writes in the sandbox and the developer's tools run outside it
turns a sandboxed mistake or injection into code running with no sandbox.
Ordinary source files are in that set too, but changes to them show up in a
review; these do not:

- `.git/hooks/*` and `.git/config` (`core.hooksPath`, `core.fsmonitor`,
  `core.sshCommand`) run on the developer's next `git` command, and never appear
  in a diff.
- `~/.claude/settings.json` holds hooks that run in every later Claude session,
  sandboxed or not.
- VS Code's settings and extensions run in the editor.

What nono can express: `groups.exclude: ["vscode_macos"]` drops the VS Code
grants; `filesystem.deny: ["$WORKDIR/.git/hooks"]` blocks the hooks directory
(checked with `nono why --profile <candidate> --allow <checkout>`: `src/x` is
allowed, `.git/hooks/pre-commit` is `filesystem_deny`). A deny always wins over
a grant and there is no read-only override inside a writable directory, so
`.git/config` (git must read it) and `~/.claude` (Claude Code must write it)
stay writable. Whether git commits normally with an unreadable hooks directory
is checked in §5.7.

### 5.5 uv — a variable, not a grant

```bash
uvx --from 'schemathesis==4.33.4' st --version
#   error: Could not create temporary file
#     cause: Operation not permitted (os error 1) at path "~/.local/share/uv/tools/.tmpN1AyR8"
UV_TOOL_DIR="$HOME/.cache/uv/tools" uvx --from 'schemathesis==4.33.4' st --version
#   cause: Failed to fetch: https://pypi.org/simple/schemathesis/
#   … tunnel error: unsuccessful
```

`uvx` writes to uv's tool directory before it resolves anything. With
`UV_TOOL_DIR` in the cache, which the base profile already grants for writing,
the only remaining failure is the network. `environment.set_vars` can set it for
every session. On Linux, `~/.cache` is not granted by the base profile as a
whole (to be checked).

### 5.6 Candidate 1 — superseded by the reframe (§1.1)

Kept for its restrictions (A, D, E), which still belong in the profile, and for
the C2 rules, which the team set aside for a scoped token. Written to the
agent's scratch directory as `pfb-claude-candidate-1.json`;
`nono profile validate` reports it valid (27 group references). It combines A,
B2, C2 (with `/graphql` allowed), D and E, and extends `nolabs-ai/claude`
directly so that its endpoint rules for GitHub do not merge with today's
unrestricted `github.com` entry.

```json
{
  "extends": ["nolabs-ai/claude"],
  "meta": {
    "name": "pfb-claude",
    "version": "2.0.0-rc.1",
    "description": "PeopleForBikes: Claude Code with the org's tools; …"
  },
  "groups": { "include": ["mise_manager"], "exclude": ["vscode_macos"] },
  "filesystem": {
    "allow": ["~/.local/state/mise", "~/.npm"],
    "read": ["~/.config/gh"],
    "write": ["~/.cargo/git", "~/.cargo/registry"],
    "deny": ["$WORKDIR/.git/hooks"],
    "suppress_save_prompt": ["… unchanged …"]
  },
  "environment": {
    "deny_vars": [
      "GITHUB_TOKEN",
      "GH_TOKEN",
      "GH_ENTERPRISE_TOKEN",
      "GITHUB_ENTERPRISE_TOKEN"
    ],
    "set_vars": { "UV_TOOL_DIR": "$HOME/.cache/uv/tools" }
  },
  "network": {
    "block": false,
    "allow_http2": true,
    "allow_domain": [
      "127.0.0.1",
      "localhost",
      "api.anthropic.com",
      "downloads.claude.ai",
      "mcp-proxy.anthropic.com",
      "platform.claude.com",
      "statsig.anthropic.com",
      {
        "domain": "github.com",
        "endpoints": [
          { "method": "GET", "path": "/**" },
          { "method": "HEAD", "path": "/**" },
          { "method": "POST", "path": "/*/*/git-upload-pack" }
        ]
      },
      {
        "domain": "api.github.com",
        "endpoints": [
          { "method": "GET", "path": "/**" },
          { "method": "HEAD", "path": "/**" },
          { "method": "POST", "path": "/graphql" },
          { "method": "POST", "path": "/repos/*/*/pulls" },
          { "method": "POST", "path": "/repos/*/*/issues/*/comments" },
          { "method": "POST", "path": "/repos/*/*/pulls/*/comments" },
          { "method": "POST", "path": "/repos/*/*/pulls/*/comments/*/replies" },
          { "method": "POST", "path": "/repos/*/*/pulls/*/reviews" }
        ]
      },
      "codeload.github.com",
      "objects.githubusercontent.com",
      "raw.githubusercontent.com",
      "release-assets.githubusercontent.com",
      "results-receiver.actions.githubusercontent.com",
      "crates.io",
      "index.crates.io",
      "static.crates.io",
      "registry.npmjs.org",
      "pypi.org",
      "files.pythonhosted.org",
      "code.claude.com",
      "doc.rust-lang.org",
      "docs.github.com",
      "docs.rs",
      "hurl.dev",
      "mise.jdx.dev",
      "nono.sh",
      "download.geofabrik.de",
      "overpass-api.de",
      "overpass.kumi.systems",
      "overpass.openstreetmap.fr"
    ],
    "open_port": [3000, 5432]
  }
}
```

`nono why --profile <candidate> --host` allows `raw.githubusercontent.com`,
`crates.io`, PyPI and `code.claude.com`, and still denies
`productionresultssa1.blob.core.windows.net` and `example.com`.

On this machine, stripping `GITHUB_TOKEN` makes gh use the keyring account
(`repo` scope), so the session tests the proxy rules with that token.

### 5.7 Live session with candidate 1 — not run

Superseded by the reframe before it ran; the live test is now §5.9.

### 5.8 Actions logs — readable today through `gh run view`

```bash
gh run view 44137094284 -R PeopleForBikes/bna-api --log | head -5   # works
# works (failed run)
gh run view 44136169241 -R PeopleForBikes/bna-api --log-failed
# works (failed job)
gh run view -R PeopleForBikes/bna-api --job 134226180254 --log
gh api repos/PeopleForBikes/bna-api/actions/jobs/134229485471/logs
#   Get "https://productionresultssa17.blob.core.windows.net/actions-results/…/logs/job/job-logs.txt?…sig=…":
#   Forbidden: host productionresultssa17.blob.core.windows.net:443
#   is not in the allowlist
GH_DEBUG=api gh api repos/PeopleForBikes/bna-api/actions/runs/44136169241/logs
#   302 → https://results-receiver.actions.githubusercontent.com/rest/runs/…
#   … /logs → 200
```

- The run's log archive, which `gh run view` uses for `--log`, `--log-failed`
  and `--job <id> --log`, redirects to
  `results-receiver.actions.githubusercontent.com`, already allowed. Only the
  REST endpoint for one job's log (`/actions/jobs/<id>/logs`) redirects to a
  storage account, through a signed URL valid for a few minutes.
- The past denials of `productionresultssa*` (§2.3) came from that REST endpoint
  (`gh api …/actions/jobs/<id>/logs`, in ai-toolkit and bna-api) or from
  `nono why` probes, never from `gh run view` (found by matching each denial in
  the transcripts to the Bash command before it).
- Listing the storage accounts is not practical: a DNS lookup (no connection) of
  `productionresultssa<N>.blob.core.windows.net` resolves for N from 0 to 199
  except 22, and fails for 22, 500 and an invented account name, so the lookups
  are meaningful. That is 199 hosts, and GitHub can add more.
- So reading CI logs needs no new host: agents should use `gh run view`. A line
  in the agent instructions (the project's `CLAUDE.md`, or a skill in
  ai-toolkit) covers it. Logs of a run still in progress are not tested.

### 5.9 A dedicated agent token — desk review, then the test session

Not run yet. The plan follows.

**The token** (desk review of GitHub's fine-grained token settings): created by
a developer under _Settings → Developer settings → Personal access tokens →
Fine-grained tokens_, resource owner PeopleForBikes, all repositories (or the
selected ones), with:

| Permission (repository) | Access         | Why                                                         |
| ----------------------- | -------------- | ----------------------------------------------------------- |
| Metadata                | Read           | Required by GitHub                                          |
| Contents                | Read           | Read code; cannot push or merge                             |
| Issues                  | Read and write | Create issues, comment, label                               |
| Pull requests           | Read and write | Create pull requests from pushed branches, comment, review  |
| Actions                 | Read           | Runs, jobs and their logs                                   |
| Commit statuses         | Read           | `gh pr checks` (the Checks API is not available, see below) |

No organization permission, no Administration, Workflows, Secrets, Variables or
Packages. Expiry of 90 days. If the organization requires approval of
fine-grained tokens, an owner approves it once. Pull requests and issues the
agent creates appear under the developer's name; a machine account or a GitHub
App would separate them (not evaluated).

**Keeping the developer's token away from the agent**: with
`--credential github`, nono reads `GITHUB_TOKEN` from its own environment,
outside the sandbox, and gives the sandbox a phantom value; the proxy puts the
real token back only on requests to `api.github.com` (built-in route in nono's
`network-policy.json`: `credential_key: env://GITHUB_TOKEN`, header
`Authorization: token {}`). Starting nono with `GITHUB_TOKEN` set to the agent
token, read from the keychain outside the sandbox, replaces the developer's
token for that session only. In a profile, `environment.deny_vars` removes the
variable instead; it has no flag.

**Keychain caveat**: the sandbox reads the login keychain (§5.2). An agent token
stored there is readable by the agent through `security`, which is acceptable
only because the token holds nothing beyond the agent's own permissions. The
developer's own gh token (the `keyring` account of `gh auth status`) stays
readable too, with its `repo` scope, until it leaves the login keychain.

**Classic or fine-grained** (desk review of GitHub's documentation, 2026-11-18:
[Managing your personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens),
[GitHub credential types](https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/github-credential-types)):
no classic scope allows creating issues and pull requests without also pushing.
Private repositories need `repo`, which pushes, merges and changes settings on
every repository the developer can reach, in every organization; `public_repo`
does the same on public repositories. A classic token would bring back the C2
rules and their GraphQL gap (§5.2). A fine-grained token has a single owner
(PeopleForBikes), can be narrowed to selected repositories, has per-permission
read or write, expires within the organization's maximum lifetime (366 days by
default), and can require an owner's approval, which a classic token cannot.
Documented gaps of fine-grained tokens that touch agents: the Checks API (so
`gh pr checks` may not show every check), Packages, and contributing to
repositories outside the owner (an agent cannot open an issue upstream, for
example on nono). GitHub describes these gaps as temporary.

**nono's proxy injection with the keychain**: `--credential github` already is
proxy injection; on the command line it can only read `env://GITHUB_TOKEN`. A
profile can define its own route that reads the keychain itself, outside the
sandbox, so no shell command handles the token:

```json
{
  "network": {
    "credentials": ["github_agent"],
    "custom_credentials": {
      "github_agent": {
        "upstream": "https://api.github.com",
        "credential_key": "github_agent",
        "env_var": "GITHUB_TOKEN",
        "credential_format": "token {}"
      }
    }
  }
}
```

A bare `credential_key` names an account under the keychain service `nono`
(`security add-generic-password -s nono -a github_agent -w`);
`keyring://<service>/<account>` reads any other item, and `op://` reads
1Password. The route covers one upstream: `github.com` (git over HTTPS) and
`uploads.github.com` get no token, which suits an agent that does not push.
`endpoint_rules` can narrow the route further. Not run.

**Test session**: replaced by §5.10 after the team chose a classic token.

### 5.10 A classic agent token, limited by the proxy

**Which repositories**: `gh repo list PeopleForBikes --no-archived` lists 16
public repositories (bna-api, ai-toolkit, brokenspoke-analyzer, bna-website,
bna-lambdas, …) and 2 private ones (`bna-site`, `infra`).

**The token** (desk review of GitHub's classic scopes): created by a developer
under _Settings → Developer settings → Personal access tokens → Tokens
(classic)_, with:

| Scope         | Why                                                                                         |
| ------------- | ------------------------------------------------------------------------------------------- |
| `public_repo` | Read public repositories, create and comment on issues and pull requests, read Actions logs |
| `read:org`    | Organization teams and membership, for example `gh pr create --reviewer <team>`             |

Left out: `repo` (only `bna-site` and `infra` need it, and agents should not
reach `infra`), `workflow`, `gist`, `admin:*`, `delete_repo`, `write:packages`,
`user`. Expiry of 90 days. `public_repo` still pushes and merges on every public
repository the developer can write, in any organization, and lets the agent open
issues upstream (for example on nono), which a fine-grained token cannot.

**Stored** in the keychain, under the service nono reads for a profile's
`credential_key` (§5.9), so the same item serves the command line now and the
profile later: `security add-generic-password -s nono -a github_agent -w`.

**Limits on the proxy**: `--credential github` gives the sandbox a phantom
token, and each `--allow-endpoint github:METHOD:PATH` flag lets one kind of
request through to `api.github.com`; everything else on that route is refused.
The set below allows reading, GraphQL (which gh needs) and the REST calls that
create or comment on issues and pull requests, and so refuses through REST:
merging (`PUT …/pulls/<n>/merge`), writing files (`PUT …/contents/…`), creating
references (`POST …/git/refs`), deleting anything, and changing settings.

```text
github:GET:/**
github:POST:/graphql
github:POST:/repos/*/*/issues
github:POST:/repos/*/*/issues/*/comments
github:POST:/repos/*/*/pulls
github:POST:/repos/*/*/pulls/*/comments
github:POST:/repos/*/*/pulls/*/reviews
```

`nono run --dry-run --allow-cwd --profile pfb-claude --credential github` with
three of these flags exits 0: nono accepts the syntax; the dry run does not show
the rules, so whether they hold is part of the test session.

**Known gaps**, accepted with the classic token:

- GraphQL is open, and it can merge, delete a branch or commit
  (`mergePullRequest`, `deleteRef`, `createCommitOnBranch`, desk review).
- The token sits in the login keychain, which the sandbox reads (§5.2): an agent
  that reads it directly bypasses the proxy, and `github.com` accepts a push
  over HTTPS with it. Endpoint rules on `github.com` refusing `git-receive-pack`
  (C2, §5.6) close the push, but only in the profile: on the command line
  `pfb-claude`'s plain `github.com` entry wins.

**Test session**: run on 2026-11-18, see §5.11.

### 5.11 Live session with the classic agent token

The maintainer created the token (`public_repo`, `read:org`), stored it with
`security add-generic-password -s nono -a github_agent -w`, and started the
session from bna-api with every grant on the command line:

```sh
GITHUB_TOKEN="$(security find-generic-password -s nono -a github_agent -w)" \
UV_TOOL_DIR="$HOME/.cache/uv/tools" \
nono run --allow-cwd --profile pfb-claude \
  --allow ~/projects/PeopleForBikes/ai-toolkit \
  --credential github \
  --allow-endpoint 'github:GET:/**' \
  --allow-endpoint 'github:POST:/graphql' \
  --allow-endpoint 'github:POST:/repos/*/*/issues' \
  --allow-endpoint 'github:POST:/repos/*/*/issues/*/comments' \
  --allow-endpoint 'github:POST:/repos/*/*/pulls' \
  --allow-endpoint 'github:POST:/repos/*/*/pulls/*/comments' \
  --allow-endpoint 'github:POST:/repos/*/*/pulls/*/reviews' \
  --allow-domain raw.githubusercontent.com --allow-domain crates.io \
  --allow-domain pypi.org --allow-domain files.pythonhosted.org \
  --allow-domain code.claude.com --allow-domain docs.rs \
  --allow-domain doc.rust-lang.org --allow-domain docs.github.com \
  --allow-domain hurl.dev --allow-domain mise.jdx.dev --allow-domain nono.sh \
  -- claude --dangerously-skip-permissions --continue
```

**The token stays out of the sandbox**:

```bash
[ "$GITHUB_TOKEN" = "$NONO_PROXY_TOKEN" ]   # true: 64 hex characters, no ghp_
echo "$GITHUB_BASE_URL"                     # http://127.0.0.1:51986/github
gh api -i user | grep -i x-oauth-scopes     # X-Oauth-Scopes: public_repo, read:org
```

The sandbox's `GITHUB_TOKEN` is nono's session token, not a GitHub token. gh
still talks to `api.github.com` through the proxy (it ignores
`GITHUB_BASE_URL`), and the proxy replaces the session token with the agent
token: GitHub reports the agent token's scopes, not the developer's. gh 2.105.0
on macOS accepts the proxy's TLS interception, which answers the main open
question of §5.9.

**Reading works**: `gh pr list`, `gh issue list`, `gh pr view 559`,
`gh pr checks 559` (three checks listed, despite the Checks API gap of
fine-grained tokens) and `gh run view 44136169241 --log-failed` all exit 0.
`gh repo view PeopleForBikes/infra` fails with
`Could not resolve to a Repository`: the private repository is out of reach, as
intended.

**The endpoint rules decide which requests carry the token**, probed with
requests that cannot change anything (a repository or pull request that does not
exist, an invalid GraphQL node):

| Request                                                 | Result                                                       |
| ------------------------------------------------------- | ------------------------------------------------------------ |
| `DELETE /repos/…`, `PUT …/pulls/999999/merge`           | GitHub: `401 Bad credentials`                                |
| `POST …/git/refs`, `PUT …/contents/…`, `PATCH /repos/…` | GitHub: `401 Bad credentials`                                |
| `POST /repos/…/issues` (allowed)                        | GitHub: `404 Not Found` (authenticated; the repo is missing) |
| GraphQL `addComment` on an invalid ID (allowed)         | GitHub: `NOT_FOUND`, `Could not resolve to a node…`          |

A request outside the rules is not stopped by the proxy: it goes to GitHub
without the agent token (the session token passes through unchanged), and GitHub
refuses it as unauthenticated, with its own JSON body. The effect is the one
wanted: the token never merges, deletes, writes a file, creates a reference or
changes a setting through REST. GraphQL mutations carry the token, as expected
(§5.10).

**The token is still readable in the keychain**:
`security find-generic-password -s nono -a github_agent -w | wc -c` prints 41
(exit 0; a classic token is 40 characters; the value was not printed). An agent
that reads it bypasses the proxy, and could push over HTTPS to any public
repository the developer can write; not attempted. gh's own keyring account now
holds a token with the same scopes (`public_repo`, `read:org`), so the
`repo`-scoped token of §5.2 is no longer in the keychain on this machine.

**Network and tools**:

| Check                                                      | Result                                 |
| ---------------------------------------------------------- | -------------------------------------- |
| `cargo search sea-orm --limit 1`, `cargo info sea-orm`     | `sea-orm = "2.0.4"`; exit 0            |
| `curl -sSfL https://raw.githubusercontent.com/…/README.md` | `# bna-api`; exit 0                    |
| `uvx --from 'schemathesis==4.33.4' st --version`           | `st, version 4.33.4` in 3.9 s          |
| WebFetch `https://nono.sh/` (allowed)                      | page summarized                        |
| WebFetch `https://neon.com/docs/…` (not allowed)           | `proxy refused the connection`         |
| `just ci` in bna-api                                       | exit 0 in 46 s (57 passed, 26 ignored) |

With the maintainer's agreement, `gh issue create` then `gh issue close` on
ai-toolkit created and closed
[ai-toolkit#3](https://github.com/PeopleForBikes/ai-toolkit/issues/3) through
the agent token; GitHub records it under the developer's account (`rgreinho`),
as for any personal token.

Not run: `gh pr create --dry-run` (it may push the branch), and the restrictions
that only a profile expresses (§5.4, `deny_vars`).

## 6. Conclusion & Recommendation

**Conditional Go**, agreed with the maintainer on 2026-11-18.

Against the success bar (§1, as reframed in §1.1 and §1.2):

1. **One-off grants**: each one is covered or rejected with a reason.
   `crates.io`, `raw.githubusercontent.com`, PyPI (with `UV_TOOL_DIR`) and seven
   documentation hosts are added (§5.3, §5.5, tested in §5.11); the GitHub
   release, Actions results and npm hosts that only the installed copy had are
   published (§2.2). Actions logs need no host: `gh run view` reads them (§5.8).
   Sigstore, TUF, `nodejs.org` and the attestation storage serve tool installs,
   which happen outside the sandbox; Azure storage wildcards would accept
   anyone's account; the Docker socket stays a one-off grant (§5.3).
2. **No high-risk capability, and a narrower GitHub**: the developer's token
   never enters the sandbox; the agent's classic token (`public_repo`,
   `read:org`) is injected by the proxy only for reads, GraphQL and the REST
   calls that create issues, pull requests and comments, so REST merges,
   deletions, file writes, references and settings reach GitHub without it
   (§5.11). Two gaps are accepted by the team: GraphQL mutations carry the
   token, and the token is readable in the login keychain (§5.10, §5.11).
3. **Live session**: every check of the task list passed, including `just ci`,
   except `gh pr create --dry-run`, not run because it may push (§5.11).

Network additions were the smaller part of the problem. The largest gap was the
developer's organization-admin token inside the sandbox (§5.2), and the quickest
win is the cleanup: dead grants, an unenforced command list, and a published
profile older than the one in use (§5.1, §2.2).

**Recommendation**: rewrite `nono/profiles/pfb-claude.json` from candidate 1
(§5.6) with these changes, under these conditions:

- **One profile, published**: the installed copies and the published one must
  match again; contributors reinstall with `just install-nono-profiles force`.
- **The agent token in the profile**: a `custom_credentials` route (§5.9) that
  reads the classic agent token from the keychain
  (`credential_key: "github_agent"`), sets `GITHUB_TOKEN` in the sandbox, and
  carries the seven endpoint rules of §5.10 as `endpoint_rules`.
  `environment.deny_vars` drops `GH_TOKEN`, `GH_ENTERPRISE_TOKEN` and
  `GITHUB_ENTERPRISE_TOKEN`, which gh would prefer over `GITHUB_TOKEN`.
- **No push over HTTPS**: `github.com` gets endpoint rules allowing `GET`,
  `HEAD` and `POST /*/*/git-upload-pack` only, so an agent that reads the token
  from the keychain still cannot push (`git-receive-pack`).
- **CI logs**: agent instructions say to read logs with `gh run view` (`--log`,
  `--log-failed`, `--job <id> --log`), not the REST job-log endpoint.
- **Code that runs outside the sandbox**: exclude the VS Code groups and deny
  `$WORKDIR/.git/hooks` (§5.4), once a live session shows git still commits.

## 7. Still Open

- GraphQL mutations (merge, delete a branch, commit) carry the agent token
  (§5.10, §5.11). Accepted for now; a fine-grained token (C4, §5.9) or a GitHub
  App would close it.
- The agent token is readable in the login keychain, because `nolabs-ai/claude`
  grants the keychain for Claude Code's own credentials (§5.2, §5.11). A
  keychain item trusting only nono, 1Password (`op://`), or not extending
  `nolabs-ai/claude` would hide it; none was tested.
- Whether nono's endpoint rules on `github.com` keep anonymous `git` fetches
  working and refuse a push (§5.6): not run.
- Whether git commits normally with `$WORKDIR/.git/hooks` denied (§5.4): not
  run. `.git/config` and `~/.claude/settings.json` stay writable either way.
- `gh pr create` through the agent token: not run (`--dry-run` may push). Issues
  and pull requests appear under the developer's name; a machine account or a
  GitHub App would separate them (not evaluated).
- Network approvals (B3, §5.3), which would replace restarts for the long tail
  of hosts: not tested.
- Linux: nothing was run there. Open: gh and the proxy's TLS interception, the
  keychain question (Secret Service), and whether `~/.cache` is writable for
  `UV_TOOL_DIR`.
- `git fetch` over the SSH remote fails in the sandbox (no SSH key, by design);
  anonymous HTTPS fetches of public repositories work.
- Classic tokens have no enforced expiry: the team sets one (90 days, §5.10) and
  a reminder to rotate it.

## 8. Remaining Work

In priority order:

1. Rewrite `nono/profiles/pfb-claude.json` (§6): `meta.name`, the `mise_manager`
   group, the cleanup of §5.1, the hosts of §5.3, the agent-token route with its
   endpoint rules, the `github.com` rules, `deny_vars`, `UV_TOOL_DIR`, the VS
   Code exclusion and the `.git/hooks` deny. `just validate` must pass.
2. Install it and run one live session with no extra flags: the checks of §5.11,
   plus the profile-only ones (`.git/hooks` and a commit, VS Code paths denied,
   `GH_TOKEN` absent, the token read by nono from the keychain, an anonymous
   HTTPS fetch allowed and a push refused).
3. Document the grants in `SECURITY.md` (the repository's rule for any new nono
   grant), the token setup (scopes, expiry, the `security` command) in the
   README or `CONTRIBUTING.md`, and the change under `Unreleased` in
   `CHANGELOG.md`.
4. Add the `gh run view` rule to the agent instructions every project receives
   (a skill or the shared settings), and point bna-api's
   `.github/CONTRIBUTING.md` ("Agents in the nono sandbox") at the published
   profile.
5. Check the profile on Linux.

[nono]: https://nono.sh/
