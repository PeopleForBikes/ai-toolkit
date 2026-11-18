---
title: unittest discover does not run doctests unless the module adds them
date: 2026-11-18
updated: 2026-11-18
category: test-failures
status: active
tags: [python, unittest, doctest, just, testing]
modules: [justfile, scripts/test_nono_profiles.py]
spec: specs/0000-nono-profile-review
related:
  - specs/0000-nono-profile-review/findings.md
superseded_by:
---

# unittest discover does not run doctests unless the module adds them

## Context

`just test` runs `python3 -m unittest discover -s scripts -v` (`justfile:34`),
and `CLAUDE.md:31` describes it as running the "unit tests and doctests of the
helper scripts". The path helpers added to `scripts/test_nono_profiles.py` were
given doctests.

## Symptom

The doctests never appeared in the `just test` output, and a wrong expected
value in one would not have failed CI. No module in `scripts/` had a doctest
that actually ran, despite `CLAUDE.md`.

## What Did Not Work

- Writing `>>>` examples in docstrings and relying on discovery: `unittest` only
  collects `TestCase` classes.

## Root Cause

`unittest discover` imports `test_*.py` modules and loads their `TestCase`
classes. Doctests are only collected when the module defines the `load_tests`
protocol and adds a `doctest.DocTestSuite`.

## Solution

Add a `load_tests` hook to the test module
(`scripts/test_nono_profiles.py:224-229`):

```python
def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None
) -> unittest.TestSuite:
    """Add this module's doctests (path helpers) to unittest discovery."""
    tests.addTests(doctest.DocTestSuite())
    return tests
```

`DocTestSuite()` with no argument takes the calling module. `just test -v` then
lists `Doctest: test_nono_profiles.normalize_path ... ok`.

## Prevention

- When adding doctests to a module under `scripts/`, add `load_tests` (for a
  helper module, `DocTestSuite("module_name")` from its test module), and check
  that `just test` lists them.
- Revisit if `just test` moves to pytest with `--doctest-modules`.
