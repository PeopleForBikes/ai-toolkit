# Contributing

## General guidelines

The PeopleForBikes AI Toolkit follows the
[BNA Mechanics Contributing Guidelines](https://peopleforbikes.github.io/contributing/).
Refer to them for general principles.

## Requirements

- [Just]
- [Python] 3.10+ (standard library only)
- [Node.js] (for `npx`, used by the Markdown linters)
- [Claude Code] (for `claude plugin validate`)
- [nono] (for `nono profile validate`)

## Making changes

1. Fork the repository and create a branch.
2. Make your change:
   - **Skills** live in `plugins/<plugin>/skills/<skill>/SKILL.md`. Keep the
     `pfb-` prefix and a specific `description`: it decides when agents pick the
     skill on their own.
   - **Claude Code settings** live in `claude/settings/base.json`. Only add
     rules that make sense for every PeopleForBikes project; project-specific
     rules belong in that project's `.claude/settings.json`.
   - **nono profiles** live in `nono/profiles/`. Explain any new grant in the
     pull request and in [SECURITY.md](SECURITY.md).
3. Try it locally (see [Local development](#local-development)).
4. Run `just fmt-md` and `just ci` before committing.
5. If the change should reach users, bump `version` in the plugin's
   `.claude-plugin/plugin.json` and the marketplace `metadata.version`.
6. Open a pull request.

Changes to permissions, sandbox profiles or anything an agent executes are
reviewed as security-sensitive: describe what the change grants and why.

## Local development

### Load the skills from the working tree

Start Claude Code with the plugin loaded directly from your clone. Edits to the
skills are picked up the next time you start a session; nothing is installed.

```console
claude --plugin-dir ./plugins/pfb-sdld
```

To use the skills on another project while developing them, pass the absolute
path to this folder instead.

### Install from the local marketplace

This copies the plugin into Claude Code's plugin cache, so edits require an
update to be picked up.

```console
claude plugin marketplace add ./
claude plugin install pfb-sdld@pfb-plugins
```

After changing a skill:

```console
claude plugin marketplace update pfb-plugins
claude plugin update pfb-sdld@pfb-plugins
```

If you already installed the marketplace from GitHub, remove it first
(`claude plugin marketplace remove pfb-plugins`): both use the same name.

### Validate

```console
just ci
```

It lints the Markdown, validates the plugin marketplace, the plugins and the
nono profiles, and runs the tests of the helper scripts. To see the loaded
skills and their token cost:

```console
claude --plugin-dir ./plugins/pfb-sdld plugin details pfb-sdld
```

[claude code]: https://claude.com/claude-code
[just]: https://just.systems/
[node.js]: https://nodejs.org/
[nono]: https://nono.sh/
[python]: https://www.python.org/
