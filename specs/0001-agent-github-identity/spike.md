# Spike: A GitHub identity for sandboxed agents

## Status

In progress: No-Go for letting agents push, agreed on 2026-11-25. Replacing the
agent's classic token with a fine-grained one met the success bar on a stand-in
repository; ai-toolkit confirms it once the organization approves the token
(expected 2026-12-01). See §6.

## 1. Intent

The team wanted agents running in the `pfb-claude` sandbox to push branches and
to open pull requests and issues. Today an agent can open issues, and pull
requests from branches already on GitHub, with a classic token of the
contributor's account; it cannot push (`specs/0000-nono-profile-review`). nono's
proxy filters the method and path of a request, not the branch or tag a push
updates, so what a push may change depends on the GitHub identity behind it.

The spike asked: **which GitHub identity lets a sandboxed agent push and open
pull requests, without being able to push to, tag or merge in PeopleForBikes
repositories?**

**Constraints that shaped scope**:

- A login shared by the team is not possible.
- One nono profile for the organization, not one per project or person.
- **Contractors** (added 2026-11-25, see §1.1): contributors who also work for
  other organizations must remain free to do so. Nothing may use up a limited
  personal resource, and a PeopleForBikes session should not reach other
  clients' repositories or secrets.
- This document is public: the state of the branch and tag protections of each
  repository was reviewed separately and is not recorded here.

**Success bar** (agreed 2026-11-25): the agent pushes a branch to a fork, opens
a pull request and an issue and reads CI logs; GitHub refuses its pushes, tags
and merges in PeopleForBikes repositories and its approval does not count; one
profile serves every contributor. Superseded by §1.1.

### 1.1 Reframe (2026-11-25, before any live session)

Two questions from the maintainer changed the spike:

- **Contractors**: a machine account per contributor, the leading candidate,
  uses the only free one GitHub allows a person. It cannot be required (§5.1).
- **Doing nothing**: the fallback of the remaining design (the agent pushes to a
  fork, a person opens the pull request) is today's workflow with more setup.
  The current setup had not been listed as a candidate; it is now (§3, H).

The question becomes: **keeping today's workflow, where a person pushes, does a
fine-grained token close the gaps of the classic one?** Success bar: with the
fine-grained token and no change to the profile,

1. the agent reads pull requests, issues and CI logs, opens and comments on
   issues, and opens a pull request from a branch a person pushed;
2. GitHub refuses, GraphQL included, creating a branch or tag, committing and
   merging in a PeopleForBikes repository, and writing outside the organization.

The machine-account setup and experiments written for the first question were
never run and are left out; their desk findings stay in §5.

## 2. Current Baseline

Measured on 2026-11-25 in a `pfb-claude` session (nono 0.82.0, gh 2.105.0, git
2.56.1, macOS arm64):

- The agent's token is a classic token of the contributor's account
  (`gh api -i user`: `X-Oauth-Scopes: public_repo, read:org`). GitHub gives it
  the contributor's role in every public repository of every organization. The
  REST rules of the `github_agent` route (`nono/profiles/pfb-claude.json`) limit
  it; GraphQL mutations are not limited (`SECURITY.md`, "Known gaps").
- Pushing is refused: SSH has no agent socket
  (`nono why --self --unix-socket "$SSH_AUTH_SOCK"`: `unix_socket_not_granted`)
  and the `github.com` rules refuse `git-receive-pack`. A person pushes, which
  is also the point where the work is looked at before it reaches CI.
- The token is readable in the login keychain, which `nolabs-ai/claude` grants
  (`0000-nono-profile-review/spike.md` §5.11). A child profile cannot drop the
  grant ([nono #2269](https://github.com/nolabs-ai/nono/issues/2269), open).
- The installed profile differs from the published one by one host,
  `nominatim.openstreetmap.org` (`diff`, keys sorted). §4.1 uses a copy of the
  published one.

## 3. Candidates Considered

| Candidate                                                  | Verdict                                | Why                                                                                                               |
| ---------------------------------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| A. One machine account per contributor                     | Rejected before testing — §5.1         | Uses the one free machine account GitHub allows a person, which contractors may need for another client.          |
| B. Two fine-grained tokens, pushing to a fork              | Rejected before testing — §5.2         | Neither token can write to both the fork and the organization, which opening the pull request appears to require. |
| C. One machine account shared by the team                  | Rejected before testing — §5.1         | GitHub's terms: "a single login may not be shared by multiple people".                                            |
| D. GitHub App                                              | Set aside, not tested                  | A private key or a token service to distribute and run, to save one manual command.                               |
| E. SSH with a dedicated key                                | Rejected before testing — §5.4         | No path rule applies to SSH, and an account key cannot be limited to chosen repositories.                         |
| F. Three tokens, chosen by nono per request                | Set aside, validated statically — §5.3 | Contained only while the agent cannot read the classic token; breaks `gh pr create` and `gh issue create`.        |
| G. Agent pushes to a fork, a person opens the pull request | Rejected before testing                | Automates only `git push` compared with H, for forks, a token and a profile change.                               |
| H. Keep today's setup unchanged                            | Baseline — §2                          | Works; the classic token's reach remains.                                                                         |
| I. H with one fine-grained token                           | Met the bar on a stand-in — §5.8       | Same workflow and profile; GitHub itself limits the token. Candidate C4 of `0000-nono-profile-review`.            |
| J. Apple Passwords for the token                           | Rejected before testing — §5.4         | nono reads it with `security`, which the sandbox can also run.                                                    |

## 4. Evaluation Method

One live session started by the maintainer, since nono cannot be nested
(`0000-nono-profile-review/spike.md` §4). `LOGIN` is the contributor's GitHub
login. Never paste a token in a Claude session, on a command line or here.

### 4.1 Manual setup

Outside the sandbox, as the maintainer. The current token stays in place, so
going back needs nothing.

1. **Token.** _Settings → Developer settings → Personal access tokens →
   Fine-grained tokens_: resource owner **PeopleForBikes**, only `ai-toolkit`,
   expiry 7 days, and these repository permissions only:

   | Permission    | Access         |
   | ------------- | -------------- |
   | Metadata      | Read (forced)  |
   | Contents      | Read           |
   | Issues        | Read and write |
   | Pull requests | Read and write |
   | Actions       | Read           |

   If PeopleForBikes is not offered as an owner, or the token stays pending, an
   organization owner allows or approves it in _Organization settings → Personal
   access tokens_.

2. **Keychain.** The command prompts for the token; choose _Always Allow_ if
   macOS asks whether nono may read it:

   ```sh
   security add-generic-password -s nono -a github_agent_fine -w
   ```

3. **Profile.** A copy of the published one, reading the new item:

   ```sh
   sed -E 's/(credential_key": "github_agent)"/\1_fine"/' \
     nono/profiles/pfb-claude.json \
     > ~/.config/nono/profiles/pfb-spike-token.json
   nono profile validate pfb-spike-token
   ```

4. **Branches.** A throwaway base and a head with one empty commit:

   ```sh
   git fetch origin
   git push origin origin/main:refs/heads/spike-0001-base
   head=$(git commit-tree 'origin/main^{tree}' -p origin/main -m 'spike 0001')
   git push origin "$head:refs/heads/spike-0001-head"
   ```

5. **Session**, from the ai-toolkit clone:

   ```sh
   nono run --allow-cwd --profile pfb-spike-token \
     -- claude --dangerously-skip-permissions --continue
   ```

### 4.2 Stand-in while the approval is pending

The token of §4.1 waits for an organization owner, expected on 2026-12-01; until
then it only reads public resources, so a refusal would prove nothing. A token
whose owner is the contributor needs no approval and uses the same permissions.
The stand-in is `LOGIN/sdld-explore`: public, no protected branch
(`gh api …/branches`) and no workflow, so a refused write can only come from the
token. The contributor owns the repository, a wider role than in the
organization.

1. **Token**: as in §4.1 with the same permissions and expiry, but resource
   owner **`LOGIN`** and only **`sdld-explore`**. The pending token stays as it
   is.
2. **Keychain**: `security add-generic-password -s nono -a github_agent_own -w`
3. **Profile**:

   ```sh
   sed -E 's/(credential_key": "github_agent)"/\1_own"/' \
     nono/profiles/pfb-claude.json \
     > ~/.config/nono/profiles/pfb-spike-own.json
   nono profile validate pfb-spike-own
   ```

4. **Branches**, from a temporary clone of `LOGIN/sdld-explore`: the commands of
   §4.1, step 4.
5. **Session**, from the ai-toolkit clone: as in §4.1 with
   `--profile pfb-spike-own`.

T1 to T10 then run on `LOGIN/sdld-explore`, except:

- T2, T3: the CI part reads ai-toolkit, since the stand-in has no workflow. It
  shows what a fine-grained token reads on a public repository of another owner,
  not what the Actions permission adds.
- T10 is reversed: `createIssue` on ai-toolkit, which has another owner.

What only ai-toolkit can show: the organization accepts and approves such a
token; the CI part of T2 and T3; and T5, T6, T7, T9 and T10 once more, with the
contributor's role in the organization.

### 4.3 Experiments

Run by the agent on `PeopleForBikes/ai-toolkit`, in this order. Nothing targets
`main`.

| #   | Experiment                                                                              | Expected                                               |
| --- | --------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| T1  | `gh api -i user`; `GITHUB_TOKEN` compared with `NONO_PROXY_TOKEN`                       | `LOGIN`, no classic scopes; a placeholder              |
| T2  | `gh pr list`, `gh pr view`, `gh issue list`, `gh run view --log`                        | Work                                                   |
| T3  | `gh pr checks`                                                                          | Unknown: fine-grained tokens cannot use the Checks API |
| T4  | Read a public repository outside the organization (`gh issue view` on `nolabs-ai/nono`) | Works, read-only                                       |
| T5  | `gh issue create`, then a comment on it                                                 | Work                                                   |
| T6  | `gh pr create` from `spike-0001-head` to `spike-0001-base`                              | Works; the documentation is ambiguous (§5.5)           |
| T7  | GraphQL `createRef`: branch, then tag, `spike-0001-denied`                              | Refused by GitHub                                      |
| T8  | GraphQL `createCommitOnBranch` on `spike-0001-head`                                     | Refused by GitHub                                      |
| T9  | GraphQL `mergePullRequest` on the pull request of T6                                    | Refused by GitHub                                      |
| T10 | GraphQL `createIssue` on `LOGIN/sdld-explore`                                           | Refused by GitHub                                      |

T7 to T9 decide containment: if one succeeds, the session stops. If T6 is
refused, the maintainer opens the pull request for T9, and agents keep only
issues.

T10 is allowed by the maintainer (2026-11-25). A refusal meets the success bar,
and confirms that the new token cannot report issues to our dependencies (§5.6).

Approvals are not tested: they need another person's pull request, and the Pull
requests permission allows reviews.

### 4.4 Cleanup

Close the issue and the pull request; delete `spike-0001-base`,
`spike-0001-head` and any `spike-0001-denied`, in both repositories; revoke both
tokens; then:

```sh
security delete-generic-password -s nono -a github_agent_fine
security delete-generic-password -s nono -a github_agent_own
rm ~/.config/nono/profiles/pfb-spike-token.json \
  ~/.config/nono/profiles/pfb-spike-own.json
```

## 5. Findings

### 5.1 Machine accounts — allowed, but one free account per person (desk review)

A machine account is a GitHub user account that one person creates and answers
for, used only for automation. The
[terms of service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service)
(B.3, read 2026-11-25): "You may maintain no more than one free machine account
in addition to your free Personal Account", and "a single login may not be
shared by multiple people".

With no role in the organization, it contains an agent very well: to GitHub it
is an outside contributor, whose pushes, tags and merges are refused and whose
approvals do not count, and its pull requests can be approved by the
contributor. It would have been the recommendation, but:

- a contractor whose slot goes to PeopleForBikes cannot create a free one for
  another client, and one who already has one cannot create ours;
- one account for several clients is not safe: classic tokens cannot be limited
  to an organization, and fine-grained ones cannot contribute where the account
  is not a member;
- the terms only limit free accounts. Whether a paid second one is allowed was
  not checked with GitHub.

Nothing prevents a contributor from choosing to use one; it cannot be required.

### 5.2 Two fine-grained tokens — probably cannot open the pull request (desk review)

A fine-grained token has a single resource owner, so one token would write to
the fork and the other to the organization. GitHub's
[API documentation](https://docs.github.com/en/rest/pulls/pulls#create-a-pull-request)
requires "write access to the head or the source branch", and users report the
failure for forks
([community discussion 106661](https://github.com/orgs/community/discussions/106661),
[create-pull-request 1791](https://github.com/peter-evans/create-pull-request/issues/1791)).
Not tested.

### 5.3 Three tokens chosen by nono — expressible, not worth it (static)

nono accepts several credential routes on one host, so each request could carry
a different token: a read-only one for `GET` and GraphQL, one limited to the
forks for Git, and the classic one for three REST calls on PeopleForBikes
repositories. A draft passes `nono profile validate` (nono 0.82.0). In the
source, a credential route whose rules do not match is skipped, and a matching
one replaces the request's own credential header
(`crates/nono-proxy/src/tls_intercept/handle.rs`). Rule paths are globs within
one segment, so `/*-suffix/*/git-receive-pack` is also possible
(`crates/nono-proxy/src/config.rs`).

Set aside: containment would rest on nono and on hiding the classic token, which
the keychain grant defeats; `gh pr create` and `gh issue create` use GraphQL and
would stop working; and it saves one manual command. This is the design to test
if the team decides later that agents must push.

### 5.4 SSH and Apple Passwords — rejected (desk review)

- **SSH**: nono can lend the SSH agent's socket to `git` only
  (`tool-sandbox-examples/git-ssh` in nono), but its macOS example gives `ssh`
  unrestricted network (`allow_all`).
- **Apple Passwords**: `apple-password://` runs
  `security find-internet-password` (`crates/nono/src/keystore.rs`).

### 5.5 One fine-grained token — expected to close most gaps (desk review)

From GitHub's
[permissions reference](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens)
and
[token documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
(read 2026-11-25):

| Action                                 | Permission           | Agent's token |
| -------------------------------------- | -------------------- | ------------- |
| Open an issue                          | Issues: write        | Yes           |
| Open a pull request                    | Pull requests: write | Yes (T6)      |
| Review, approve                        | Pull requests: write | Yes           |
| Create a branch or tag, merge          | Contents: write      | No            |
| Write to a repository of another owner | One owner per token  | No            |
| Read any public repository             | Always included      | Yes           |

Opening a pull request also requires "write access to the head or the source
branch"; whether that means the person's role or the token's permission is what
T6 answers.

Limits known in advance: approvals still count, in the contributor's name; the
Checks API is not available; outside contributors cannot use such a token on
repositories of an organization they do not belong to, and would keep a classic
one.

### 5.6 Reporting issues to dependencies — lost with the swap (desk review)

The team would like an agent that finds a bug in a dependency to submit an issue
and, if possible, a tested patch. The classic token can open such an issue today
(the route allows `POST /repos/*/*/issues`, and GraphQL). A fine-grained token
owned by PeopleForBikes cannot (§5.5), which is the same property that keeps it
out of contractors' other repositories. A patch also needs a push to a fork,
which is the No-Go of §6.

| Option                                                                   | Assessment                                                                                                                                                    |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| U1. The agent prepares, a person submits                                 | **Chosen** by the maintainer (2026-11-25). The agent reads upstream, checks for duplicates, writes the issue and a tested patch to files. No grant, no token. |
| U2. A route with a classic token, for `POST …/issues` on named upstreams | Possible in nono (§5.3), not tested. Keeps a classic token in the keychain, so only after the keychain spike (§8.1). No pull request.                         |
| U3. Keep the classic token instead of the swap                           | Keeps today's gaps for an occasional need.                                                                                                                    |

With U1, a person also reads what is published in their name in another project.
The patch is written with `git format-patch` from a clone inside the working
directory, and the person pushes it from their own fork.

### 5.7 Live session with the pending token — reads work, writes refused as pending

Run on 2026-11-25 in a session started with `pfb-spike-token` (nono 0.82.0, gh
2.105.0). The token of §4.1 was waiting for the organization's approval. It is
read as the pending one because it is the only test token in the keychain and
its write was refused; GitHub does not report the status to the token.

| #   | Command                                                           | Result                                                                   |
| --- | ----------------------------------------------------------------- | ------------------------------------------------------------------------ |
| T1  | `gh api -i user`; `GITHUB_TOKEN` compared with `NONO_PROXY_TOKEN` | `LOGIN`, no `X-Oauth-Scopes`, expires 2026-12-02; equal (a placeholder)  |
| T2  | `gh pr list`, `gh pr view 5`, `gh issue list` on ai-toolkit       | Exit 0                                                                   |
| T2  | `gh run view 44409422186 --log` on ai-toolkit                     | Exit 0                                                                   |
| T2  | `gh run view 45204978780 --log-failed` on bna-api                 | Exit 0, though the token does not select bna-api                         |
| T3  | `gh pr checks 5` on ai-toolkit, `gh pr checks 559` on bna-api     | Both list the checks                                                     |
| T4  | `gh issue view 2269 -R nolabs-ai/nono`                            | Exit 0                                                                   |
| T5  | `gh issue create` on ai-toolkit                                   | `Resource not accessible by personal access token (createIssue)`, exit 1 |

- Every read an agent needs works with public read access alone, CI logs and
  checks included: a token with no permission at all would serve a read-only
  agent. The Checks API limit of §5.5 did not show in `gh pr checks`.
- `GET /repos/PeopleForBikes/ai-toolkit` reports `"admin": true` for this token:
  that field is the person's role, not what the token may do.
- T5 says nothing about the approved token. T6 to T10 were not run, because a
  refusal would be just as inconclusive; they need §4.2 or the approval.

### 5.8 Live session on the stand-in — works and is contained

Run on 2026-11-25 in a session started with `pfb-spike-own` (§4.2; nono 0.82.0,
gh 2.105.0). The token expires 13 minutes after the one of §5.7, so it is
another one; the contributor is the repository's administrator
(`viewerPermission: ADMIN`).

| #   | Experiment                                                     | Result                                                                    |
| --- | -------------------------------------------------------------- | ------------------------------------------------------------------------- |
| T1  | Identity, placeholder                                          | `LOGIN`, no `X-Oauth-Scopes`; equal to `NONO_PROXY_TOKEN`                 |
| T2  | `gh pr list`; `gh run view … --log` on ai-toolkit              | Exit 0                                                                    |
| T3  | `gh pr checks 5` on ai-toolkit                                 | Exit 0                                                                    |
| T4  | `gh issue view 2269 -R nolabs-ai/nono`                         | Exit 0                                                                    |
| T5  | `gh issue create`, `gh issue comment`                          | Both created                                                              |
| T6  | `gh pr create` from `spike-0001-head` to `spike-0001-base`     | Created                                                                   |
| T7  | GraphQL `createRef`, branch then tag                           | `FORBIDDEN`, `Resource not accessible by personal access token`, for both |
| T8  | GraphQL `createCommitOnBranch` on `spike-0001-head`            | `FORBIDDEN`, same message                                                 |
| T9  | GraphQL `mergePullRequest` (pull request `MERGEABLE`, `CLEAN`) | `FORBIDDEN`, same message                                                 |
| T10 | `gh issue create` on ai-toolkit (reversed)                     | `Resource not accessible by personal access token (createIssue)`          |

- Contents: read is enough to open a pull request from a branch of the same
  repository: the "write access" of GitHub's documentation is the person's. It
  says nothing about forks (§5.2).
- GitHub refuses GraphQL writes to code and merges, even to an administrator's
  token: the GraphQL gap of the classic token is closed for those.
- T7 to T10 left no trace: `git ls-remote` shows the branches unchanged and no
  tag, and ai-toolkit has no new issue.
- `gh issue close` and `gh pr close` also work, through GraphQL: the token can
  close and edit, which the REST rules of the route do not allow. Both test
  items were closed this way.

## 6. Conclusion & Recommendation

**No-Go for letting agents push**, agreed with the maintainer on 2026-11-25. The
identity that contains a push best cannot be required from contractors (§5.1),
the others rely on hiding a token that the sandbox can read (§5.3), and the gain
is one manual command that doubles as a checkpoint. This is a judgment on cost
and constraints: no push was tested.

**Replacing the classic token** (candidate I) met the success bar of §1.1 on the
stand-in (§5.8). Proposed verdict, to settle with the maintainer after the
confirmation on ai-toolkit: **Conditional Go**, on the condition that the
organization approves such tokens and that T2, T3, T5, T6, T7, T9 and T10 give
the same results there.

## 7. Still Open

- The confirmation on ai-toolkit: T2, T3, T5, T6, T7, T9, T10 (§4.2).
- **The keychain grant**: a session may be able to read any secret stored with
  `security`, including one a contractor keeps for another client. The token
  swap does not change that. It gets its own spike (§8.1).
- Approvals in the contributor's name, through GraphQL and the reviews route.
- Outside contributors, who keep a classic token.
- Whether the organization allows fine-grained tokens, and with which maximum
  lifetime.
- Linux: not tested.

## 8. Remaining Work

1. Confirm on ai-toolkit with the approved token (§4.1) and settle the verdict.
2. If it meets the bar: `README.md` ("The agent's GitHub token"), `SECURITY.md`
   (token, GraphQL gap) and `CHANGELOG.md`; each contributor creates the token
   and replaces the keychain item. The profile does not change.
3. Remove the reviews rule from the route, if agents do not need it.
4. Describe U1 (§5.6) in the agent instructions.
5. Spike the keychain grant (§8.1).

### 8.1 How to start the keychain spike

It does not depend on the token swap and can start at any time, in a normal
session from the ai-toolkit clone (`just nono-claude-danger`). Paste:

```text
/pfb-spike Can the pfb-claude nono profile stop giving agents the macOS login
keychain, without breaking Claude Code, the GitHub token route or contributors'
work for other clients? Start from section 8.1 of
specs/0001-agent-github-identity/spike.md.
```

**Why**: `nolabs-ai/claude` grants `~/Library/Keychains` for Claude Code's own
login. The sandbox can then read secrets stored through `security`: our GitHub
token (`0000-nono-profile-review/spike.md` §5.11) and possibly contributors'
tokens for other clients.

**Known**:

- A child profile cannot remove the grant, not even with `filesystem.deny`
  ([nono #2269](https://github.com/nolabs-ai/nono/issues/2269), open on
  2026-11-25 with nono 0.82.0: check it and the newest nono first).
- nono reads a bare `credential_key` and `keyring://` from the default keychain;
  it cannot name a keychain file. A `cmd://` capture can, as nono runs it
  outside the sandbox (`nono profile guide`, "credential_capture").
- An item's access list can name the nono binary only (`-T`), but Homebrew's
  nono is signed ad hoc (`codesign -dv`: `Signature=adhoc`), so macOS may ask
  again after each upgrade.

**Candidates**:

| #   | Candidate                                                                                   | Protects                             | Question                                                             |
| --- | ------------------------------------------------------------------------------------------- | ------------------------------------ | -------------------------------------------------------------------- |
| 1   | Not inheriting the grant: extend `default`, copy what is needed from the pack               | Every secret                         | What has to be maintained by hand; does Claude Code still log in?    |
| 2   | With 1: a token from `claude setup-token`, injected by a nono route for `api.anthropic.com` | Every secret, and Claude's own login | Does Claude Code accept a placeholder in `CLAUDE_CODE_OAUTH_TOKEN`?  |
| 3   | Items trusting only nono (`-T`)                                                             | Our token only                       | Does `security` in the sandbox prompt or fail? After a nono upgrade? |
| 4   | A keychain file outside `~/Library/Keychains`, read by a `cmd://` capture                   | Our token only                       | Can the sandbox reach it once it is unlocked?                        |
| 5   | Waiting for nono #2269                                                                      | Every secret                         | Is there a date? Could we contribute the change?                     |

**Proposed success bar** (to agree in the interview): from a session, no
keychain item can be read; Claude Code logs in and refreshes its login; `gh`
still works; one profile for everyone; sessions not started with `pfb-claude`
are unaffected.

**Manual setup**: dummy items, never real secrets. Outside the sandbox:

```sh
security add-generic-password -s nono -a canary_default -w canary
security add-generic-password -s nono -a canary_nono \
  -T /opt/homebrew/bin/nono -w canary
mkdir -p ~/.local/share/pfb-spike
security create-keychain -P ~/.local/share/pfb-spike/agent.keychain-db
security add-generic-password -s nono -a canary_file -w canary \
  ~/.local/share/pfb-spike/agent.keychain-db
```

**During the tests**: the agent reads only the dummy items
(`security find-generic-password -s nono -a canary_nono -w`); choose _Deny_ if
macOS shows a prompt for one, since a prompt is already a result. To store a
real secret in a keychain file, do not end the command with `-w` followed by the
file: `security` takes the path as the password. Use Keychain Access.

**Cleanup**:

```sh
security delete-generic-password -s nono -a canary_default
security delete-generic-password -s nono -a canary_nono
security delete-keychain ~/.local/share/pfb-spike/agent.keychain-db
```
