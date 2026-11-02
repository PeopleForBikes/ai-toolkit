# PeopleForBikes AI Toolkit

The AI resources PeopleForBikes uses across its projects: agent skills for a
specification-driven workflow, shared Claude Code permission rules, and a
sandbox profile to run AI agents safely. They are written for PeopleForBikes
contributors and shared with anyone who finds them useful.

| Resource                 | What it is                                                        | Where              |
| :----------------------- | :---------------------------------------------------------------- | :----------------- |
| **Agent skills**         | The `pfb-sdld` Claude Code plugin: specification-driven workflow  | `plugins/`         |
| **Claude Code settings** | Shared permission rules, merged into each project's settings file | `claude/settings/` |
| **nono profiles**        | Sandbox profile used to run AI agents across our projects         | `nono/profiles/`   |

Everything is released under the [MIT license](LICENSE).

## Quick start

Each resource can be used on its own.

**Agent skills.** Inside Claude Code:

```console
/plugin marketplace add PeopleForBikes/ai-toolkit
/plugin install pfb-sdld@pfb-plugins
```

Then try `/pfb-spec-new add a --version flag to the CLI`.

**Claude Code settings.** From a clone of this repository, merge the shared
rules into a project and commit the result:

```console
just sync-claude-settings path/to/project
just check-claude-settings path/to/project
```

This also registers the `pfb-plugins` marketplace and enables `pfb-sdld` for the
project, so everyone who opens it is offered the skills.

**nono profiles.** From a clone of this repository:

```console
nono pull nolabs-ai/claude
just install-nono-profiles
nono run --profile pfb-claude claude
```

Review [SECURITY.md](SECURITY.md) for what the profile grants before installing.

## Agent skills: the `pfb-sdld` plugin

`pfb-sdld` packages our Specification-Driven LLM Development (SDLD) workflow.

| Skill                | Purpose                                                                                                    |
| :------------------- | :--------------------------------------------------------------------------------------------------------- |
| `pfb-spike`          | Research a possible feature with real experiments; records evidence and a Go / No-Go verdict in `spike.md` |
| `pfb-spec-new`       | Interview-style conversation resulting in `requirements.md`, `design.md`, `tasks.md`                       |
| `pfb-spec-implement` | Execute `tasks.md` in order, ticking tasks, running the project's checks, recording `findings.md`          |
| `pfb-spec-review`    | Strict review of an implementation against its spec (report only)                                          |
| `pfb-spec-update`    | Sync a spec with what was built, or yank a cancelled feature or No-Go spike                                |
| `pfb-learning`       | Capture a solved problem or team decision in `specs/learnings/`                                            |

Examples:

```console
/pfb-spike is downloading OSM data per city faster than clipping the region?
/pfb-spec-new add a --version flag to the CLI
/pfb-spec-implement specs/0006-version-flag
/pfb-spec-review specs/0006-version-flag
/pfb-spec-update specs/0006-version-flag yank superseded by #1234
/pfb-learning the SRID mismatch we just fixed in the stress SQL
```

The fully qualified names (`/pfb-sdld:pfb-spec-new`, …) also work and are what
`/help` lists.

`pfb-spec-implement` only runs when invoked explicitly. The other skills can
also be picked up automatically when a request matches their description.

`pfb-spec-review` always runs in a fresh context (`context: fork` with
`agent: general-purpose` in its frontmatter): Claude Code starts a separate
subagent that sees none of the current conversation, only the repository, the
spec and the arguments. This keeps the reviewer from inheriting the reasoning of
the session that wrote the code. Because the subagent cannot ask questions
mid-review, pass the spec folder explicitly
(`/pfb-spec-review specs/NNNN-feature-name`); if it is missing and cannot be
inferred from the branch, the review stops and lists the candidates. The report
comes back to the main session when the subagent finishes. Other agents, such as
Copilot, may ignore these frontmatter fields and run the review inline; start a
new session before reviewing there.

### Conventions the skills rely on

- Feature specs live in `specs/NNNN-feature-name/` (four-digit, sequential),
  each with `requirements.md`, `design.md` and `tasks.md`. A folder may also
  hold:
  - `spike.md`: the research done before specifying the feature (`pfb-spike`),
    ending in a Go, Conditional Go or No-Go verdict;
  - `findings.md`: everything non-obvious learned while implementing it
    (`pfb-spec-implement`), reviewed by a teammate at the end.
- Every spike is numbered like a feature. A Go spike's folder becomes the
  feature's folder; `pfb-spec-new` adds the three documents next to `spike.md`.
- Requirements use user stories with EARS acceptance criteria.
- Cancelled features are renamed to `specs/NNNN-feature-name-yanked/` and gain a
  `yanked.md` explaining why. Their number stays reserved. A No-Go spike is
  yanked the same way and keeps only `spike.md` and `yanked.md`, so teammates
  know why the team stopped and do not repeat the investigation.
- Learnings live in `specs/learnings/<category>/<slug>.md`.
- `specs/README.md` is never modified by the skills.
- `docs/` is reserved for the published documentation website. No skill writes
  planning material there.
- Each repository's `CLAUDE.md` / `AGENTS.md` documents its stack and its
  quality command (e.g. `just ci`), which the skills read instead of assuming.
- Repo templates in `specs/xxxx-feature-templates/` override the ones bundled
  with `pfb-spec-new`.

### Typical flow

```mermaid
flowchart TD
    idea(["Feature idea"])
    sure{"Clear what to build<br/>and that it is worth it?"}
    spike["/pfb-spike<br/>experiments → spike.md"]
    verdict{"Reviewer feedback<br/>on the verdict"}
    new["/pfb-spec-new<br/>requirements.md → design.md → tasks.md"]
    senior{"Senior engineer<br/>reviews the specs"}
    implement["/pfb-spec-implement<br/>execute tasks.md, record findings.md"]
    review{"/pfb-spec-review<br/>report against the spec"}
    update["/pfb-spec-update<br/>sync design.md and tasks.md"]
    yank["/pfb-spec-update yank<br/>NNNN-name-yanked/ + yanked.md"]
    learning["/pfb-learning<br/>specs/learnings/"]
    final{"Reviewer feedback<br/>on code and findings.md"}
    done(["Merge"])

    idea --> sure
    sure -- yes --> new
    sure -- no --> spike
    spike --> verdict
    verdict -- Go / Conditional Go --> new
    verdict -- No-Go --> yank
    new --> senior
    senior -- changes requested --> new
    senior -- approved --> implement
    senior -- feature cancelled --> yank
    implement --> review
    review -- needs revision --> implement
    review -- spec diverged --> update
    update --> review
    review -- pass --> final
    final -- changes requested --> implement
    final -- approved --> done
    implement -. non-obvious problem solved .-> learning
    done -. lesson worth keeping .-> learning
```

### Adopting the skills in a project

- Make sure the project has a `specs/` folder. Adding
  `specs/xxxx-feature-templates/` is optional: the templates bundled with
  `pfb-spec-new` are used otherwise.
- Make sure the project's `CLAUDE.md` / `AGENTS.md` names its quality command
  (e.g. `just ci`, `cargo test`, `npm test`) and states that `docs/` is the
  published documentation website and must not receive planning material.
- Optionally mention `specs/learnings/` in `CLAUDE.md` / `AGENTS.md` up front;
  otherwise `pfb-learning` offers to add the line the first time it runs.

### Updating and removing the plugin

```console
claude plugin marketplace update pfb-plugins
claude plugin update pfb-sdld@pfb-plugins
```

```console
claude plugin uninstall pfb-sdld@pfb-plugins
claude plugin marketplace remove pfb-plugins
```

### GitHub Copilot CLI

Copilot CLI reads Claude-compatible plugin manifests. This has not been tested
with these skills yet; please report how it goes.

```console
copilot plugin marketplace add PeopleForBikes/ai-toolkit
copilot plugin install pfb-sdld@pfb-plugins
```

## Claude Code settings

Claude Code plugins cannot carry permission rules, and without an organization
plan there are no managed settings to push them. Shared rules therefore live in
each project's committed `.claude/settings.json`, which applies to everyone who
opens the project. `claude/settings/base.json` holds the rules every
PeopleForBikes project starts from:

- **allow**: read-only `git` and `gh` commands, and `nono why`;
- **ask**: anything that changes a repository or GitHub (`git commit`,
  `git push`, `gh pr create`, …);
- **deny**: reading `.env` files and `secrets/`, `curl`, `wget`, `sudo`.

It also registers this repository as the `pfb-plugins` marketplace and enables
`pfb-sdld`, so Claude Code offers to install the skills when a contributor
trusts the project.

A deny rule in a project's committed settings applies even if a contributor
allows the same thing in their personal settings; allow rules only save prompts.

Merge the base into a project with:

```console
just sync-claude-settings path/to/project
```

The merge only adds: project-specific rules (e.g. `Bash(uv run pytest*)` or
`Bash(cargo test*)`) and other settings are kept. Lists are combined, objects
merged, and the project's value wins for anything else. Running it again is
harmless. To keep projects in line, run the check in each project's CI; it exits
with status 1 and lists what is missing:

```console
just check-claude-settings path/to/project
```

Personal preferences (model, theme, telemetry, …) belong in each contributor's
own `~/.claude/settings.json` or the project's `.claude/settings.local.json`,
not in the base.

## nono profiles

[nono](https://nono.sh/) runs AI agents in an OS-enforced sandbox.
`nono/profiles/pfb-claude.json` is a single profile meant for all our projects
rather than one per project: most of them need the same access (Overpass and
Geofabrik downloads, services on port 3000, PostgreSQL on port 5432), and
per-project profiles would add overhead for little security gain.

It extends the `nolabs-ai/claude` pack and adds, among others, read access to
the GitHub CLI login (`~/.config/gh`), `/Library/Keychains` and `~/.docker`.
Review [SECURITY.md](SECURITY.md) for what it grants before installing.

Install and use it:

```console
nono pull nolabs-ai/claude
just install-nono-profiles
nono run --profile pfb-claude claude
```

`just install-nono-profiles` copies the profiles into
`$XDG_CONFIG_HOME/nono/profiles/` (`~/.config/nono/profiles/` by default). It
refuses to overwrite a local copy that differs and shows the difference; run
`just install-nono-profiles force` to overwrite it. Inspect the fully resolved
policy with `nono profile show pfb-claude`.

## Layout

```text
ai-toolkit/
├── .claude-plugin/marketplace.json   # marketplace "pfb-plugins"
├── .github/workflows/ci.yaml         # runs `just ci`
├── plugins/pfb-sdld/
│   ├── .claude-plugin/plugin.json
│   └── skills/
│       ├── pfb-spike/                # SKILL.md + assets/spike-template.md
│       ├── pfb-spec-new/             # SKILL.md + assets/ (spec templates)
│       ├── pfb-spec-implement/       # SKILL.md + assets/findings-template.md
│       ├── pfb-spec-review/
│       ├── pfb-spec-update/
│       └── pfb-learning/             # SKILL.md + assets/learning-template.md
├── claude/settings/base.json         # shared permission rules + marketplace
├── nono/profiles/pfb-claude.json     # organization-wide sandbox profile
├── scripts/                          # settings merge script and its tests
├── justfile
├── CLAUDE.md (AGENTS.md)             # instructions for AI agents
├── CONTRIBUTING.md · SECURITY.md · code-of-conduct.md · LICENSE
```

Each skill is a `SKILL.md` file: YAML frontmatter (`name`, `description`,
`argument-hint`) followed by the instructions the agent follows. The
`description` decides when the agent picks the skill on its own, so keep it
specific.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the requirements, how to try changes
locally and how to validate them (`just ci`).

## Releasing

For maintainers:

1. Merge the changes through pull requests and make sure CI passes.
2. Bump `version` in `plugins/pfb-sdld/.claude-plugin/plugin.json` and keep
   `metadata.version` in `.claude-plugin/marketplace.json` consistent. Installed
   copies only pick up changes when the version changes.
3. Tag the release. `claude plugin tag` checks that `plugin.json` and the
   marketplace entry agree, then creates and pushes a `pfb-sdld--v<version>`
   tag:

   ```console
   claude plugin tag ./plugins/pfb-sdld --push
   ```

Users then update with:

```console
claude plugin marketplace update pfb-plugins
claude plugin update pfb-sdld@pfb-plugins
just install-nono-profiles force
```

Projects pick up new shared permission rules the next time
`just sync-claude-settings` runs; their CI check flags when that is due.
