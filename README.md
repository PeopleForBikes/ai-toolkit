# PeopleForBikes AI Skills (experimental)

Shared AI-assisted development skills for PeopleForBikes projects, packaged as a
Claude Code plugin marketplace.

> [!NOTE]
>
> This folder is an experiment hosted in the brokenspoke-analyzer repository.
> Once the skills are stable, it is meant to move to its own PeopleForBikes
> repository so every project can install it.

## Plugins

### `pfb-sdld`: Specification-Driven LLM Development

| Skill                | Purpose                                                                  |
| :------------------- | :----------------------------------------------------------------------- |
| `pfb-spec-new`       | Question-first drafting of `requirements.md`, `design.md`, `tasks.md`    |
| `pfb-spec-implement` | Execute `tasks.md` in order, ticking tasks, running the project's checks |
| `pfb-spec-review`    | Strict review of an implementation against its spec (report only)        |
| `pfb-spec-update`    | Sync a spec with what was built, or yank a cancelled feature             |
| `pfb-learning`       | Capture a solved problem or team decision in `specs/learnings/`          |

`pfb-spec-implement` only runs when invoked explicitly. The other skills can
also be picked up automatically when a request matches their description.

#### Conventions the skills rely on

- Feature specs live in `specs/NNNN-feature-name/` (four-digit, sequential),
  each with exactly `requirements.md`, `design.md` and `tasks.md`.
- Requirements use user stories with EARS acceptance criteria.
- Cancelled features are renamed to `specs/NNNN-feature-name-yanked/` and gain a
  `yanked.md` explaining why. Their number stays reserved.
- Learnings live in `specs/learnings/<category>/<slug>.md`.
- `specs/README.md` is never modified by the skills.
- `docs/` is reserved for the published documentation website. No skill writes
  planning material there.
- Each repository's `CLAUDE.md` / `AGENTS.md` documents its stack and its
  quality command (e.g. `just ci`), which the skills read instead of assuming.
- Repo templates in `specs/xxxx-feature-templates/` override the ones bundled
  with `pfb-spec-new`.

#### Typical flow

```text
pfb-spec-new → senior review of the specs → pfb-spec-implement
  → pfb-spec-review → (pfb-spec-update) → pfb-learning
```

## Trying the skills

All commands below are run from the repository root.

### Claude Code: load from the working tree (recommended while iterating)

Start Claude Code with the plugin loaded directly from this folder. Edits to the
skills are picked up the next time you start a session; nothing is installed.

```console
claude --plugin-dir ./pfb-skills/plugins/pfb-sdld
```

Then, inside the session:

```console
/pfb-spec-new add a --version flag to the CLI
/pfb-spec-implement specs/0006-version-flag
/pfb-spec-review specs/0006-version-flag
/pfb-spec-update specs/0006-version-flag yank superseded by #1234
/pfb-learning the SRID mismatch we just fixed in the stress SQL
```

The fully qualified names (`/pfb-sdld:pfb-spec-new`, …) also work and are what
`/help` lists.

### Claude Code: install from the local marketplace

This copies the plugin into Claude Code's plugin cache, so edits to this folder
require an update to be picked up.

```console
claude plugin marketplace add ./pfb-skills
claude plugin install pfb-sdld@pfb-plugins
```

After changing a skill:

```console
claude plugin marketplace update pfb-plugins
claude plugin update pfb-sdld@pfb-plugins
```

To remove it:

```console
claude plugin uninstall pfb-sdld@pfb-plugins
claude plugin marketplace remove pfb-plugins
```

### GitHub Copilot CLI

Copilot CLI reads Claude-compatible plugin manifests. This has not been tested
with these skills yet; please report how it goes.

```console
copilot plugin marketplace add ./pfb-skills
copilot plugin install pfb-sdld@pfb-plugins
```

### Validating changes

```console
claude plugin validate ./pfb-skills
claude plugin validate ./pfb-skills/plugins/pfb-sdld
claude --plugin-dir ./pfb-skills/plugins/pfb-sdld plugin details pfb-sdld
```

The last command lists the loaded skills and their token cost.

## Layout

```text
pfb-skills/
├── .claude-plugin/marketplace.json   # marketplace "pfb-plugins"
└── plugins/pfb-sdld/
    ├── .claude-plugin/plugin.json
    └── skills/
        ├── pfb-spec-new/              # SKILL.md + assets/ (spec templates)
        ├── pfb-spec-implement/
        ├── pfb-spec-review/
        ├── pfb-spec-update/
        └── pfb-learning/              # SKILL.md + assets/learning-template.md
```

Each skill is a `SKILL.md` file: YAML frontmatter (`name`, `description`,
`argument-hint`) followed by the instructions the agent follows. The
`description` decides when the agent picks the skill on its own, so keep it
specific.

## Feedback

While experimenting, note where a skill asked too much or too little, wrote
something it should not have, or missed a project convention, and adjust the
corresponding `SKILL.md`.
