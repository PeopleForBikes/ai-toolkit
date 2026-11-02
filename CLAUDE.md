# CLAUDE.md

Guidance for AI agents working in this repository. `AGENTS.md` is a symlink to
this file.

## What this repository is

The PeopleForBikes AI Toolkit: shared AI resources for PeopleForBikes projects,
published publicly under the MIT license.

- `plugins/pfb-sdld/`: a Claude Code plugin with six agent skills (`pfb-spike`,
  `pfb-spec-new`, `pfb-spec-implement`, `pfb-spec-review`, `pfb-spec-update`,
  `pfb-learning`), published through the marketplace
  `.claude-plugin/marketplace.json` (marketplace name `pfb-plugins`).
- `claude/settings/base.json`: shared Claude Code permission rules (plus the
  marketplace and plugin entries), merged into each project's committed
  `.claude/settings.json` by `scripts/sync_claude_settings.py`.
- `nono/profiles/pfb-claude.json`: the single, organization-wide nono sandbox
  profile. Do not split it per project; the team decided against it.

See `README.md` for the full layout and user-facing documentation, and
`CONTRIBUTING.md` for local development.

## Commands

- `just ci`: lint, validate and test. Run it before committing.
- `just fmt-md`: format the Markdown with Prettier (`--prose-wrap always`). Run
  it after editing any `.md` file; `just lint-md` must pass.
- `just validate`: `claude plugin validate` on the marketplace and each plugin,
  `nono profile validate` on each profile.
- `just test`: unit tests and doctests of the helper scripts (Python 3.10+,
  standard library only).
- `just sync-claude-settings <project>` /
  `just check-claude-settings <project>`: merge or check the shared settings in
  another project.
- `just install-nono-profiles [force]`: copy the profiles to the local nono
  configuration.

## Conventions

- All skills keep the `pfb-` prefix. A skill's `description` decides when agents
  pick it on their own: keep it specific.
- The skills work on spec folders named `specs/NNNN-feature-name/` (four digits,
  sequential) holding `requirements.md` (user stories + EARS acceptance
  criteria), `design.md`, `tasks.md`, and optionally `spike.md` and
  `findings.md`. Cancelled features and No-Go spikes are renamed with a
  `-yanked` suffix and gain a `yanked.md`.
- Skills never modify `specs/README.md` and never write planning material under
  `docs/`, which is reserved for the published documentation website.
- When a change should reach users, bump `version` in
  `plugins/pfb-sdld/.claude-plugin/plugin.json` and keep `metadata.version` in
  `.claude-plugin/marketplace.json` consistent.
- Contributors use their own Claude plans: there are no managed settings, so
  shared rules only travel through `claude/settings/base.json`.
- Personal preferences (model, theme, …) do not belong in the base settings.

## Security

The repository is public and its content controls what AI agents may do on
contributors' machines. Treat these as security-sensitive:

- permission rules in `claude/settings/base.json` (a loose wildcard can allow
  destructive commands);
- grants in `nono/profiles/` (file, network and port access);
- skill instructions that make an agent run commands or write files.

Never widen a permission or a sandbox grant without saying so explicitly and
explaining why; document new nono grants in `SECURITY.md`. Never commit secrets.
Do not commit or push unless asked.
