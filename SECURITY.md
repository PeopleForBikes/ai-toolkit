# Security Policy

This repository ships configuration that controls what AI coding agents may do
on a contributor's machine: Claude Code permission rules, `nono` sandbox
profiles and agent skills. A mistake in any of them can grant an agent more
access than intended, so we treat them as security-sensitive.

## Reporting a vulnerability

Please do **not** open a public issue for security problems. Report them
privately through GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability):
open the repository's **Security** tab and select **Report a vulnerability**.

Examples of what to report:

- a permission rule in `claude/settings/base.json` that allows more than its
  intent (e.g. a wildcard that matches destructive commands);
- a `nono` profile grant that exposes credentials or files beyond what is
  documented;
- a skill or hook instruction that could make an agent leak data, run unexpected
  commands or write outside the folders it documents.

## What the shared configuration grants

Before installing, review what you are opting into:

- **`nono/profiles/pfb-claude.json`**: see
  [The `pfb-claude` nono profile](#the-pfb-claude-nono-profile) below.
- **`claude/settings/base.json`** only allows read-only `git` and `gh` commands;
  anything that changes a repository or GitHub asks first, and reading `.env`
  files, `secrets/`, `curl`, `wget` and `sudo` are denied. It also registers
  this repository as the `pfb-plugins` marketplace and enables the `pfb-sdld`
  plugin, so syncing a project offers its skills to everyone who opens it. These
  rules do not apply when Claude Code runs with `--dangerously-skip-permissions`
  (`just nono-claude-danger`): in that mode, the nono profile is the only limit.

### The `pfb-claude` nono profile

Version 2.0.0. It extends the `nolabs-ai/claude` pack, which already gives the
agent read and write access to the working directory, `~/.claude`, the user
caches and the login keychain (for Claude Code's own credentials), read access
to the Rust, Node.js and Python toolchains and to the Git configuration, and
denies credentials, shell history and browser data. Run
`nono profile show nono/profiles/pfb-claude.json` to see the fully resolved
policy. `scripts/test_nono_profiles.py`, run by `just ci`, fails when a change
weakens the properties below or adds a host this section does not name.

#### Network

Only these hosts are reachable, through nono's proxy; none is a wildcard:

| Hosts                                                                                                                 | Why                                                                                               |
| :-------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------ |
| `127.0.0.1`, `localhost`                                                                                              | Local services, with ports 3000 (applications) and 5432 (PostgreSQL)                              |
| `api.anthropic.com`, `downloads.claude.ai`, `mcp-proxy.anthropic.com`, `platform.claude.com`, `statsig.anthropic.com` | Claude Code itself                                                                                |
| `github.com`                                                                                                          | Reading and Git fetches only; see [GitHub](#github)                                               |
| `api.github.com`                                                                                                      | The GitHub API, used by `gh`; see [GitHub](#github)                                               |
| `codeload.github.com`, `objects.githubusercontent.com`, `release-assets.githubusercontent.com`                        | Repository archives and release downloads                                                         |
| `raw.githubusercontent.com`                                                                                           | Files of public repositories (schemas, documentation), also reachable through the two hosts above |
| `results-receiver.actions.githubusercontent.com`                                                                      | GitHub Actions logs, as read by `gh run view`                                                     |
| `crates.io`, `index.crates.io`, `static.crates.io`                                                                    | Rust crates: search and information (`cargo search`, `cargo info`), index, downloads              |
| `registry.npmjs.org`                                                                                                  | npm packages (`npx`)                                                                              |
| `pypi.org`, `files.pythonhosted.org`                                                                                  | Python packages, for tools run with `uvx`                                                         |
| `code.claude.com`, `doc.rust-lang.org`, `docs.github.com`, `docs.rs`, `hurl.dev`, `mise.jdx.dev`, `nono.sh`           | Documentation the agent reads; static sites                                                       |
| `download.geofabrik.de`, `overpass-api.de`, `overpass.kumi.systems`, `overpass.openstreetmap.fr`                      | OpenStreetMap data for the Bicycle Network Analysis                                               |

Deliberately left out: the sigstore and TUF hosts and `nodejs.org`, which only
installing tools needs (install them outside the sandbox);
`*.blob.core.windows.net`, which would match any Azure storage account,
including one an attacker owns (read Actions logs with `gh run view` instead of
the REST job-log endpoint, which redirects there); and the Docker socket, which
would give the agent everything Docker Desktop shares. Grant those for one
session only, with `nono run` flags.

#### GitHub

- **No push over HTTPS**: on `github.com`, the proxy lets through only `GET`,
  `HEAD` and the `POST` of a Git fetch (`git-upload-pack`); a push
  (`git-receive-pack`) is refused. Pushing stays with the developer, over SSH,
  which the sandbox cannot use.
- **A token for the agent**: each contributor creates a classic personal access
  token with the `public_repo` and `read:org` scopes only, stored in the login
  keychain under the service `nono` and the account `github_agent` (see
  [README.md](README.md#the-agents-github-token)). The profile's `github_agent`
  credential route reads it outside the sandbox; the agent sees only a
  placeholder in `GITHUB_TOKEN`. nono adds the real token to requests to
  `api.github.com` that read (`GET`), use GraphQL (`POST /graphql`), or create
  an issue, a pull request, a comment on either, or a pull request review (which
  can approve the pull request or request changes, see "Known gaps"). Any other
  request reaches GitHub without the token and is refused as unauthenticated
  (`401`): merging, deleting, writing files or branches and changing settings
  through the REST API do not work.
- **The developer's own tokens stay out**: the profile removes `GITHUB_TOKEN`,
  `GH_TOKEN`, `GH_ENTERPRISE_TOKEN` and `GITHUB_ENTERPRISE_TOKEN` from the
  sandbox's environment, and points `GH_CONFIG_DIR` at an empty directory
  (`~/.cache/nono/gh`), so `gh` never falls back to the developer's login.
  `~/.config/gh` is no longer readable.
- **Without the agent token**, the session starts, `GITHUB_TOKEN` is not set and
  `gh` is not logged in. The proxy answers the requests the route covers with
  `503 credential_unavailable` instead of sending them anonymously, so even
  public reads through `api.github.com` fail; other requests reach GitHub
  without a token (`401`).

#### Files

- **Added to the base**: read access to mise's executable, configuration and
  installed tools (the built-in `mise_manager` group), read and write access to
  `~/.local/state/mise` and `~/.npm`, and write access to `~/.cargo/git` and
  `~/.cargo/registry`.
- **Removed from the base**: VS Code's configuration and extensions (groups
  `vscode_macos` and `vscode_linux`), and the working directory's `.git/hooks`
  (denied): both run code outside the sandbox. The deny covers reads too, so Git
  finds no hooks and commits made in the sandbox skip them silently; a project
  that relies on a pre-commit hook gets its checks from its CI recipe instead.
- **Removed since version 1.0.0**: `/Library/Keychains` and `~/.docker` (the
  base's deny rules made them ineffective), `~/.config/gh`, and
  `~/Library/Caches/brokenspoke-analyzer` (already covered by the base's user
  caches).

#### Environment

- `GITHUB_TOKEN`, `GH_TOKEN`, `GH_ENTERPRISE_TOKEN` and
  `GITHUB_ENTERPRISE_TOKEN` are removed (nono sets `GITHUB_TOKEN` to its
  placeholder).
- `GH_CONFIG_DIR` is `~/.cache/nono/gh` (see [GitHub](#github)), and
  `UV_TOOL_DIR` is `~/.cache/uv/tools`, so `uvx` installs tools where the
  sandbox can write.

#### Known gaps

The team accepted these; report anything worse.

- **GraphQL**: `gh` needs `POST /graphql`, and nono cannot tell a GraphQL query
  from a mutation, so GraphQL mutations (merging, deleting a branch, committing)
  carry the agent token, within its scopes.
- **Pull request approvals**: the agent may create pull request reviews, and
  GitHub accepts an approval through the same request, so the agent can approve
  a pull request in the contributor's name. On a repository where one approval
  allows a merge, an agent following an injected instruction could approve a
  change that a human then merges, or that auto-merge merges. Check who approved
  before merging, and do not count an approval made from an agent session as a
  review.
- **The keychain**: the `nolabs-ai/claude` base gives the sandbox the login
  keychain for Claude Code's credentials, so the agent can read the agent token
  there, and any other secret stored through macOS's `security` tool. Keep
  tokens with wider scopes, such as a `repo` token used by `gh`, out of the
  login keychain.
- **Files read outside the sandbox**: `.git/config` and `~/.claude` stay
  writable (git and Claude Code need them), and settings in them can run
  commands outside the sandbox later. Review unexpected changes to them.
- **Linux**: the profile is valid on Linux but only verified on macOS.

## Supported versions

Only the latest release is supported. Update with
`claude plugin update pfb-sdld@pfb-plugins` and
`just install-nono-profiles force`.
