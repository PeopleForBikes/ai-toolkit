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

- **`nono/profiles/pfb-claude.json`** extends `nolabs-ai/claude` and adds, among
  others, read access to `~/.config/gh` (the GitHub CLI login),
  `/Library/Keychains` and `~/.docker`, network access to the domains listed in
  the profile, and ports 3000 and 5432. Run
  `nono profile show nono/profiles/pfb-claude.json` to see the fully resolved
  policy.
- **`claude/settings/base.json`** only allows read-only `git` and `gh` commands;
  anything that changes a repository or GitHub asks first, and reading `.env`
  files, `secrets/`, `curl`, `wget` and `sudo` are denied.

## Supported versions

Only the latest release is supported. Update with
`claude plugin update pfb-sdld@pfb-plugins` and
`just install-nono-profiles force`.
