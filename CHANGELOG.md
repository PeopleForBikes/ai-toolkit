# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Versions follow the
`pfb-sdld` plugin version and are tagged `pfb-sdld--v<version>`.

## [Unreleased]

### Added

- `scripts/test_nono_profiles.py`, run by `just ci`: fails when a change to the
  `pfb-claude` profile adds a wildcard host, lets `github.com` accept a push,
  widens what the agent's GitHub token is used for, lets the developer's GitHub
  tokens into the sandbox, re-adds an ineffective grant, or allows a host
  `SECURITY.md` does not name.

### Changed

- Each helper script in `scripts/` holds its own unit tests and doctests, and
  `just test` discovers every `*.py` file there; `test_sync_claude_settings.py`
  moved into `sync_claude_settings.py`, whose doctests now run too.
- `just install-nono-profiles` runs `scripts/install_nono_profiles.py` instead
  of an inline Bash script. It now checks every profile before copying any, so a
  conflict installs nothing, and treats an empty `XDG_CONFIG_HOME` as unset.
- `pfb-claude` nono profile 2.0.0 (spike and specification in
  `specs/0000-nono-profile-review/`):
  - the agent uses a GitHub token of its own (classic, `public_repo` and
    `read:org`), stored in the keychain and added by nono's proxy only to reads,
    GraphQL, and the creation of issues, pull requests, comments and reviews;
    the developer's GitHub tokens and gh login stay out of the sandbox;
  - `github.com` accepts reads and Git fetches only, never a push;
  - new hosts: `crates.io`, `raw.githubusercontent.com`, `pypi.org`,
    `files.pythonhosted.org`, `registry.npmjs.org`, `static.crates.io`,
    `localhost`, `release-assets.githubusercontent.com`,
    `results-receiver.actions.githubusercontent.com`, and documentation sites;
    the host list is sorted;
  - the tools installed by mise, and the Cargo and npm caches, are available in
    the sandbox; `uvx` installs tools in the cache;
  - VS Code's configuration is no longer writable from the sandbox, and Git
    hooks are no longer readable or writable there: commits made in the sandbox
    skip them;
  - `SECURITY.md` lists every grant, its reason, and the known gaps.
- Contributors must create the agent's token (see "The agent's GitHub token" in
  `README.md`) and run `just install-nono-profiles force`.

### Removed

- The profile's grants on `/Library/Keychains` and `~/.docker` (never effective:
  the base profile denies them), `~/.config/gh`, and
  `~/Library/Caches/brokenspoke-analyzer` (already granted by the base).

### Fixed

- `SECURITY.md` said that the shared permission rules do not apply with
  `--dangerously-skip-permissions`. Deny and ask rules do apply in that mode;
  the section now says so, and that the rules are not a security boundary.

## [1.1.0] - 2026-11-06

### Added

- `pfb-learning` feature review mode, which works from a feature's `findings.md`
  in a later session.
- `just` recipes to run Claude Code in the nono sandbox: `nono-claude-login` to
  log in, `nono-claude` to run Claude with the `pfb-claude` profile, and
  `nono-claude-danger` to run it with `--dangerously-skip-permissions` inside
  the sandbox.

### Changed

- In a workspace, specs and learnings that concern a single member now live in
  `<member>/specs/`; everything else stays in the root `specs/`. Numbering is
  per `specs/` folder, so features are referred to by their full path. Existing
  root folders stay where they are and are still searched.
- Skills list folder names and grep before opening files, to reduce token use as
  features and learnings accumulate. `pfb-spec-new` and `pfb-spike` open at most
  five files.
- `pfb-learning` is now the last step before merging a feature. It stays a
  manual step.

## [1.0.0] - 2026-11-02

### Added

- `pfb-sdld` Claude Code plugin implementing the Specification-Driven LLM
  Development workflow, published through the `pfb-plugins` marketplace, with
  six skills:
  - `pfb-spike`: research a possible feature through an interview and real,
    reproducible experiments, ending in a Go, Conditional Go or No-Go verdict in
    `specs/NNNN-feature-name/spike.md`.
  - `pfb-spec-new`: draft `requirements.md`, `design.md` and `tasks.md` for a
    new feature, building on a spike's conclusion when there is one.
  - `pfb-spec-implement`: implement a specification, recording what is learned
    along the way in `findings.md`.
  - `pfb-spec-review`: review an implementation strictly against its
    specification, in a fresh context that does not inherit the current
    conversation.
  - `pfb-spec-update`: bring a specification back in line with reality, or yank
    a cancelled feature or a No-Go spike.
  - `pfb-learning`: capture solved problems and team decisions in
    `specs/learnings/<category>/`.
- Shared Claude Code permission rules in `claude/settings/base.json`, which also
  register the `pfb-plugins` marketplace and enable `pfb-sdld`.
- `scripts/sync_claude_settings.py` (standard library only, with tests) to merge
  the shared settings into a project's `.claude/settings.json` or check that a
  project is in sync.
- Organization-wide nono sandbox profile `nono/profiles/pfb-claude.json`.
- `justfile` recipes to lint, validate, test, sync the shared settings and
  install the nono profiles, and a CI workflow running them.
- Documentation: `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, the code of
  conduct, and `CLAUDE.md` (with `AGENTS.md` as a symlink) for AI agents.
- MIT license.

[unreleased]:
  https://github.com/PeopleForBikes/ai-toolkit/compare/pfb-sdld--v1.1.0...HEAD
[1.1.0]:
  https://github.com/PeopleForBikes/ai-toolkit/compare/pfb-sdld--v1.0.0...pfb-sdld--v1.1.0
[1.0.0]:
  https://github.com/PeopleForBikes/ai-toolkit/releases/tag/pfb-sdld--v1.0.0
