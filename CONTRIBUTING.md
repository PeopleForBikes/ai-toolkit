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
3. Try it locally, e.g. `claude --plugin-dir ./plugins/pfb-sdld` or
   `just install-nono-profiles`.
4. Run `just fmt-md` and `just ci` before committing.
5. If the change should reach users, bump `version` in the plugin's
   `.claude-plugin/plugin.json`.
6. Open a pull request.

Changes to permissions, sandbox profiles or anything an agent executes are
reviewed as security-sensitive: describe what the change grants and why.

[claude code]: https://claude.com/claude-code
[just]: https://just.systems/
[node.js]: https://nodejs.org/
[nono]: https://nono.sh/
[python]: https://www.python.org/
