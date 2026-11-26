# Yanked

This spike was yanked because it concluded **No-Go** on 2026-11-25, decided by
the maintainer.

**Question**: can the `pfb-claude` nono profile stop giving agents the macOS
login keychain, without breaking Claude Code, the GitHub token route or
contributors' work for other clients?

**Main reasons**:

- It is feasible, but only by leaving the `nolabs-ai/claude` pack and letting
  nono capture Claude Code's login (`oauth_capture`, candidate 7b). That setup
  met the success bar in live sessions, except one part: with two sessions open,
  a login refresh in one logged the other out
  ([spike.md §5.5](spike.md#55-second-live-session-7b--refresh-works-a-parallel-session-is-logged-out),
  K7). The cause is a nono bug,
  [nono #2087](https://github.com/nolabs-ai/nono/issues/2087), whose fix
  ([nono #2088](https://github.com/nolabs-ai/nono/pull/2088)) was unmerged and
  inactive since 2026-10-09.
- Leaving the pack also costs a copy of it in our profile and nono's Claude Code
  preparation, and the login isolation relies on an undocumented Claude Code
  variable
  ([spike.md §5.3](spike.md#53-claude-codes-login--falls-back-to-a-file-which-can-be-isolated),
  [§5.4](spike.md#54-first-live-session--login-captured-gh-works-two-gaps-found)).
- A child profile cannot drop the pack's keychain grant
  ([spike.md §5.1](spike.md#51-candidate-1--the-keychain-is-denied-at-the-cost-of-a-copy-of-the-pack),
  [nono #2269](https://github.com/nolabs-ai/nono/issues/2269)).

No stopgap was adopted for the agent's GitHub token alone; `SECURITY.md` keeps
documenting the keychain as a known gap.

**When to reopen**: once a nono release fixes #2087 (or #2269), start from
candidate 7b ([spike.md §4.1](spike.md#41-live-session)) and repeat K7, K8 and
K9 first. The verdict and the full evidence are in
[spike.md §6](spike.md#6-conclusion--recommendation).
