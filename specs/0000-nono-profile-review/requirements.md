# Requirements Document: Review of the pfb-claude nono profile

## Introduction

PeopleForBikes contributors run AI agents in the nono sandbox with
`nono/profiles/pfb-claude.json`, a single profile shared by every project. The
spike in this folder (`spike.md`, verdict Conditional Go) found that the
published profile is older than the copies contributors use, holds grants that
never apply, blocks hosts agents need daily, and lets the agent use the
developer's own GitHub token, which on the maintainer's machine had
organization-admin scopes. Every missing grant meant stopping the session and
restarting it with extra flags.

This feature publishes version 2.0.0 of the profile, built on the spike's
recommendation (§6) and remaining work (§8): a cleaned-up profile, a reviewed
list of hosts, a classic GitHub token dedicated to the agent and injected by
nono's proxy, no push over HTTPS, fewer paths that run code outside the sandbox,
automated checks of these properties in `just ci`, and documentation of what the
profile grants and what it leaves open.

**In scope** (ai-toolkit only): `nono/profiles/pfb-claude.json`, a test of the
profile's security properties run by `just ci`, `SECURITY.md`, `README.md` and
`CHANGELOG.md`.

**Out of scope**: changes in other repositories (bna-api's nono material is
removed there later); creating or rotating agent tokens for contributors;
closing the gaps the team accepted (GraphQL mutations carry the agent token; the
agent token is readable in the login keychain); a fine-grained token or a GitHub
App; network approvals; the Docker socket, which stays a one-off grant;
verification on Linux (the profile stays valid there, but is only verified on
macOS); a warning at launch when the Agent_Token is missing (dropped during
implementation: macOS-specific, little value; the agent warns instead,
Requirement 7.7); bumping the `pfb-sdld` plugin version, which happens at
release time.

## Glossary

- **Profile**: `nono/profiles/pfb-claude.json`, the organization-wide nono
  profile, as published in this repository.
- **Installed_Profile**: the copy of the Profile in the contributor's nono
  configuration (`~/.config/nono/profiles/pfb-claude.json` by default), written
  by `just install-nono-profiles`.
- **Session**: Claude Code running in nono with the Installed_Profile and no
  extra grant flags, as started by `just nono-claude` or
  `just nono-claude-danger`.
- **Developer_Token**: any GitHub token belonging to the contributor's own
  login: the `GITHUB_TOKEN`, `GH_TOKEN`, `GH_ENTERPRISE_TOKEN` or
  `GITHUB_ENTERPRISE_TOKEN` environment variables of the shell that starts the
  Session, and gh's own login.
- **Agent_Token**: a classic GitHub personal access token dedicated to the
  agent, with the `public_repo` and `read:org` scopes only, stored in the macOS
  login keychain under the service `nono` and the account `github_agent`.
- **Session_Token**: the placeholder nono puts in the Session's environment in
  place of a credential; it is not a GitHub token.
- **Credential_Route**: the Profile's nono credential definition that reads the
  Agent_Token outside the sandbox and adds it to requests sent to
  `api.github.com`.
- **Allowed_Call**: a request to `api.github.com` that the Credential_Route
  sends with the Agent_Token: any `GET`, a `POST` to `/graphql`, and a `POST`
  that creates an issue, a pull request, a comment on either, or a pull request
  review.
- **Invariant_Test**: the automated test of the Profile's security properties,
  run by `just ci`.

## Requirements

### Requirement 1: A clean, identifiable profile

**User Story:** As a contributor, I want the published profile to contain only
grants that take effect, so that what I install is what the documentation
describes and what my agents actually get.

#### Acceptance Criteria

1. The Profile SHALL be named `pfb-claude` and carry the version `2.0.0`.
2. The Profile SHALL extend `nolabs-ai/claude`.
3. The Profile SHALL NOT grant access to `/Library/Keychains`, `~/.docker` or
   `~/Library/Caches/brokenspoke-analyzer`.
4. The Profile SHALL give read access to mise's executable, configuration and
   installed tools, and read and write access to mise's state directory, so that
   tools installed by mise run in a Session.
5. The Profile SHALL give write access to Cargo's registry and Git caches and
   read and write access to npm's cache.
6. WHEN `nono profile validate` runs on the Profile, it SHALL report the Profile
   valid.

### Requirement 2: Reviewed network access

**User Story:** As a contributor, I want my agent to reach the package
registries, GitHub content and documentation it needs, so that it finishes its
work without me restarting the Session with extra flags.

#### Acceptance Criteria

1. The Profile SHALL allow exactly these hosts, plus `github.com` under
   Requirement 4: `127.0.0.1`, `localhost`, `api.anthropic.com`,
   `downloads.claude.ai`, `mcp-proxy.anthropic.com`, `platform.claude.com`,
   `statsig.anthropic.com`, `api.github.com`, `codeload.github.com`,
   `objects.githubusercontent.com`, `raw.githubusercontent.com`,
   `release-assets.githubusercontent.com`,
   `results-receiver.actions.githubusercontent.com`, `crates.io`,
   `index.crates.io`, `static.crates.io`, `registry.npmjs.org`, `pypi.org`,
   `files.pythonhosted.org`, `code.claude.com`, `doc.rust-lang.org`,
   `docs.github.com`, `docs.rs`, `hurl.dev`, `mise.jdx.dev`, `nono.sh`,
   `download.geofabrik.de`, `overpass-api.de`, `overpass.kumi.systems` and
   `overpass.openstreetmap.fr`.
2. The Profile SHALL NOT allow a host pattern containing a wildcard.
3. The Profile SHALL allow local connections on ports 3000 and 5432.
4. IF an agent in a Session connects to a host the Profile does not allow, THEN
   the Session SHALL refuse the connection.
5. WHILE a Session runs, `cargo search`, fetching a file from
   `raw.githubusercontent.com`, and resolving a package from PyPI through `uvx`
   SHALL succeed.
6. The Profile SHALL list its allowed hosts in alphabetical order of host name,
   the `github.com` entry included.

### Requirement 3: A dedicated agent token, injected by the proxy

**User Story:** As a contributor, I want my agent to use its own limited GitHub
token without ever seeing it, so that it can read GitHub, open issues and pull
requests and comment, without holding my own token.

#### Acceptance Criteria

1. WHILE a Session runs, the environment visible to the agent SHALL NOT contain
   a Developer_Token or the Agent_Token.
2. WHILE a Session runs and the Agent_Token exists in the keychain, `gh` in the
   Session SHALL authenticate to `api.github.com` with the Agent_Token, without
   any extra flag or environment variable set by the contributor.
3. WHEN the agent sends an Allowed_Call, the Session SHALL send it to GitHub
   with the Agent_Token.
4. IF the agent sends a request to `api.github.com` that is not an Allowed_Call,
   THEN the Session SHALL NOT add the Agent_Token to it.
5. IF the Agent_Token does not exist in the keychain, THEN the Session SHALL
   start, and `gh` in the Session SHALL NOT authenticate with a Developer_Token.
6. WHILE a Session runs with the Agent_Token, `gh pr list`, `gh issue list`,
   `gh pr checks` and `gh run view --log-failed` SHALL succeed on a public
   PeopleForBikes repository.

### Requirement 4: No push over HTTPS

**User Story:** As a maintainer, I want the sandbox to refuse pushes to GitHub
over HTTPS, so that an agent that obtains a token still cannot push code.

#### Acceptance Criteria

1. The Profile SHALL allow on `github.com` only `GET` and `HEAD` requests and
   the `POST` requests of a Git fetch (`git-upload-pack`).
2. WHILE a Session runs, an anonymous Git fetch over HTTPS from a public GitHub
   repository SHALL succeed.
3. IF an agent in a Session sends a Git push over HTTPS to `github.com`, THEN
   the Session SHALL refuse it.

### Requirement 5: Fewer paths that run code outside the sandbox

**User Story:** As a contributor, I want the agent unable to change Git hooks or
VS Code's configuration, so that a mistake or an injected instruction in the
sandbox does not run code on my machine outside it.

#### Acceptance Criteria

1. The Profile SHALL deny access to the `.git/hooks` directory of the working
   directory.
2. The Profile SHALL remove the inherited VS Code configuration grants.
3. WHILE a Session runs, `git commit` in the working directory SHALL succeed.
4. IF the agent in a Session writes to `.git/hooks` or to VS Code's
   configuration, THEN the Session SHALL refuse the write.

### Requirement 6: Python tools through uv

**User Story:** As a contributor, I want `uvx` to run Python tools in the
sandbox, so that tasks such as `just test-schemathesis` work without a one-off
grant.

#### Acceptance Criteria

1. WHILE a Session runs, uv SHALL install tools in a directory the Session can
   write, without a grant on uv's default tool directory.

### Requirement 7: Documented grants and gaps

**User Story:** As a contributor, I want the documentation to say what the
profile grants, how to set up the agent token and what stays open, so that I
know what I opt into before installing it.

#### Acceptance Criteria

1. `SECURITY.md` SHALL list every host, path, port, environment change and
   credential the Profile adds to `nolabs-ai/claude`, with the reason for each.
2. `SECURITY.md` SHALL state the gaps the team accepted: GraphQL mutations carry
   the Agent_Token, the Agent_Token is readable in the login keychain, and the
   Profile is not verified on Linux.
3. `README.md` SHALL explain how to create the Agent_Token (scopes `public_repo`
   and `read:org`, an expiry) and store it in the keychain, and what happens
   without it.
4. `README.md` SHALL no longer state that the Profile grants
   `/Library/Keychains` or `~/.docker`.
5. `README.md`'s guidance for adopting the toolkit in a project SHALL recommend
   telling agents to read CI logs with `gh run view` (`--log`, `--log-failed`,
   `--job <id> --log`) rather than the REST job-log endpoint.
6. `CHANGELOG.md` SHALL describe the change under `Unreleased`, including that
   contributors must reinstall the Profile and create the Agent_Token.
7. `README.md`'s guidance for adopting the toolkit in a project SHALL recommend
   telling agents that, when gh reports it is not logged in, GitHub answers
   `401 Bad credentials`, or nono's proxy answers `503` with
   `credential_unavailable`, they stop and ask the contributor to set up the
   Agent_Token rather than look for another way to authenticate.

### Requirement 8: Automated checks of the security properties

**User Story:** As a maintainer, I want CI to fail when a change to the profile
weakens its security properties or adds an undocumented grant, so that reviews
do not depend on spotting it by eye.

#### Acceptance Criteria

1. WHEN `just ci` runs, the Invariant_Test SHALL run.
2. IF the Profile allows a host pattern containing a wildcard, THEN the
   Invariant_Test SHALL fail.
3. IF the Profile's rules for `github.com` allow anything other than `GET`,
   `HEAD` and the `POST` of `git-upload-pack`, THEN the Invariant_Test SHALL
   fail.
4. IF the Credential_Route sends the Agent_Token on anything other than the
   Allowed_Calls, or to an upstream other than `https://api.github.com`, THEN
   the Invariant_Test SHALL fail.
5. IF the Profile stops removing a Developer_Token variable from the Session's
   environment, THEN the Invariant_Test SHALL fail.
6. IF the Profile grants a path the base profile's deny rules make ineffective
   (`/Library/Keychains`, `~/.docker`), or stops denying `.git/hooks` or
   excluding the VS Code groups, THEN the Invariant_Test SHALL fail.
7. IF a host the Profile allows is not named in `SECURITY.md`, THEN the
   Invariant_Test SHALL fail.
8. IF the Profile's allowed hosts are not in alphabetical order of host name,
   THEN the Invariant_Test SHALL fail.
