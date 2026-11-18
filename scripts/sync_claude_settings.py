#!/usr/bin/env python3
"""Merge the shared Claude Code settings into a project's settings file.

The shared settings (``claude/settings/base.json``) are merged into a project's
committed ``.claude/settings.json``. The merge only ever adds: entries the
project defines on its own are kept, so each project can extend the base with
its own rules (e.g. ``Bash(uv run pytest*)``).

Merge rules:

- objects are merged key by key, recursively;
- lists are combined: the project's entries first, in their order, followed by
  the base entries the project does not have yet;
- for any other value, the project's value wins when it has one.

Usage::

    python3 scripts/sync_claude_settings.py BASE PROJECT_SETTINGS [--check]

With ``--check``, nothing is written: the script exits with status 1 and lists
the missing entries when the project settings are out of sync with the base.
"""

import argparse
import doctest
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

JsonValue = Any


def merge(base: JsonValue, project: JsonValue) -> JsonValue:
    """
    Merge ``base`` into ``project`` without removing anything from ``project``.

    Parameters
    ----------
    base : JsonValue
        The shared settings.
    project : JsonValue
        The project's settings.

    Returns
    -------
    JsonValue
        The merged settings.

    Examples
    --------
    >>> merged = merge(
    ...     {"permissions": {"deny": ["Read(./.env)"], "allow": ["Bash(git status)"]}},
    ...     {"permissions": {"allow": ["Bash(uv sync)"]}},
    ... )
    >>> merged["permissions"]["allow"]
    ['Bash(uv sync)', 'Bash(git status)']
    >>> merged["permissions"]["deny"]
    ['Read(./.env)']
    """
    if isinstance(base, dict) and isinstance(project, dict):
        merged = dict(project)
        for key, value in base.items():
            merged[key] = merge(value, project[key]) if key in project else value
        return merged
    if isinstance(base, list) and isinstance(project, list):
        return project + [item for item in base if item not in project]
    return project


def missing_entries(base: JsonValue, project: JsonValue, path: str = "") -> list[str]:
    """
    List the base entries that ``project`` lacks, as readable paths.

    Parameters
    ----------
    base : JsonValue
        The shared settings.
    project : JsonValue
        The project's settings.
    path : str
        The location of the values being compared, used in the messages.

    Returns
    -------
    list[str]
        One message per missing entry.

    Examples
    --------
    >>> missing_entries(
    ...     {"permissions": {"deny": ["Read(./.env)", "Bash(sudo:*)"]}},
    ...     {"permissions": {"deny": ["Read(./.env)"]}},
    ... )
    ['permissions.deny: Bash(sudo:*)']
    """
    if isinstance(base, dict) and isinstance(project, dict):
        messages = []
        for key, value in base.items():
            child = f"{path}.{key}" if path else key
            if key in project:
                messages.extend(missing_entries(value, project[key], child))
            else:
                messages.append(f"{child}: missing")
        return messages
    if isinstance(base, list) and isinstance(project, list):
        return [f"{path}: {item}" for item in base if item not in project]
    return []


def conflicting_permissions(settings: JsonValue) -> list[str]:
    """
    List permission rules that appear in more than one of allow, ask and deny.

    Claude Code applies deny before ask and ask before allow, so the stricter
    rule wins, but the duplicate is usually a mistake worth reporting.

    Parameters
    ----------
    settings : JsonValue
        Merged settings.

    Returns
    -------
    list[str]
        One message per conflicting rule.

    Examples
    --------
    >>> conflicting_permissions(
    ...     {"permissions": {"allow": ["Bash(curl:*)"], "deny": ["Bash(curl:*)"]}}
    ... )
    ['Bash(curl:*) is in both allow and deny']
    """
    permissions = settings.get("permissions", {}) if isinstance(settings, dict) else {}
    levels = ["allow", "ask", "deny"]
    messages = []
    for index, lower in enumerate(levels):
        for higher in levels[index + 1 :]:
            messages.extend(
                f"{rule} is in both {lower} and {higher}"
                for rule in permissions.get(lower, [])
                if rule in permissions.get(higher, [])
            )
    return messages


def render(settings: JsonValue) -> str:
    r"""
    Serialize settings the way they are written to disk.

    Parameters
    ----------
    settings : JsonValue
        The settings to serialize.

    Returns
    -------
    str
        Indented JSON followed by a newline.

    Examples
    --------
    >>> render({"a": [1]})
    '{\n  "a": [\n    1\n  ]\n}\n'
    """
    return json.dumps(settings, indent=2, ensure_ascii=False) + "\n"


def report(message: str, *, error: bool = False) -> None:
    """
    Print a message for the user.

    Parameters
    ----------
    message : str
        The message to print.
    error : bool
        Print to standard error instead of standard output.
    """
    stream = sys.stderr if error else sys.stdout
    stream.write(f"{message}\n")


def main(argv: list[str] | None = None) -> int:
    """
    Run the command line interface.

    Parameters
    ----------
    argv : list[str] | None
        Command line arguments, without the program name.

    Returns
    -------
    int
        The process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("base", type=Path, help="shared settings file")
    parser.add_argument("project", type=Path, help="project .claude/settings.json")
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit with status 1 if the project is out of sync",
    )
    args = parser.parse_args(argv)

    base = json.loads(args.base.read_text(encoding="utf-8"))
    project = (
        json.loads(args.project.read_text(encoding="utf-8"))
        if args.project.exists()
        else {}
    )
    merged = merge(base, project)

    for message in conflicting_permissions(merged):
        report(f"warning: {message}", error=True)

    missing = missing_entries(base, project)
    if args.check:
        if missing:
            report(f"{args.project} is out of sync with {args.base}:", error=True)
            for message in missing:
                report(f"  {message}", error=True)
            return 1
        report(f"{args.project} is in sync with {args.base}")
        return 0

    if not missing and args.project.exists():
        report(f"{args.project} is already in sync with {args.base}")
        return 0
    args.project.parent.mkdir(parents=True, exist_ok=True)
    args.project.write_text(render(merged), encoding="utf-8")
    report(f"updated {args.project} ({len(missing)} entries added)")
    return 0


# Tests: `python3 -m unittest scripts/sync_claude_settings.py` (or `just test` for every script).


TEST_BASE = {
    "$schema": "https://json.schemastore.org/claude-code-settings.json",
    "permissions": {
        "allow": ["Bash(git status)"],
        "deny": ["Read(./.env)"],
    },
}


class SyncClaudeSettingsTest(unittest.TestCase):
    """Exercise the command line on temporary files."""

    def setUp(self) -> None:
        """Create a temporary base file and project directory."""
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.base = root / "base.json"
        self.base.write_text(json.dumps(TEST_BASE), encoding="utf-8")
        self.project = root / "project" / ".claude" / "settings.json"

    def tearDown(self) -> None:
        """Remove the temporary files."""
        self.tmp.cleanup()

    def read_project(self) -> dict:
        """Load the project settings written by the script."""
        return json.loads(self.project.read_text(encoding="utf-8"))

    def test_creates_missing_project_settings(self) -> None:
        """A project without settings receives a copy of the base."""
        self.assertEqual(main([str(self.base), str(self.project)]), 0)
        self.assertEqual(self.read_project(), TEST_BASE)

    def test_keeps_project_entries(self) -> None:
        """Project rules and keys survive the merge, base rules are appended."""
        self.project.parent.mkdir(parents=True)
        self.project.write_text(
            json.dumps(
                {
                    "env": {"FOO": "1"},
                    "permissions": {"allow": ["Bash(uv sync)", "Bash(git status)"]},
                }
            ),
            encoding="utf-8",
        )
        main([str(self.base), str(self.project)])
        settings = self.read_project()
        self.assertEqual(settings["env"], {"FOO": "1"})
        self.assertEqual(
            settings["permissions"]["allow"], ["Bash(uv sync)", "Bash(git status)"]
        )
        self.assertEqual(settings["permissions"]["deny"], ["Read(./.env)"])

    def test_check_fails_when_out_of_sync(self) -> None:
        """--check reports missing entries without writing anything."""
        self.project.parent.mkdir(parents=True)
        self.project.write_text("{}", encoding="utf-8")
        self.assertEqual(main([str(self.base), str(self.project), "--check"]), 1)
        self.assertEqual(self.read_project(), {})

    def test_check_passes_after_sync(self) -> None:
        """--check succeeds once the project has been synced."""
        main([str(self.base), str(self.project)])
        self.assertEqual(main([str(self.base), str(self.project), "--check"]), 0)

    def test_sync_is_idempotent(self) -> None:
        """Running the sync twice leaves the file unchanged."""
        main([str(self.base), str(self.project)])
        first = self.project.read_text(encoding="utf-8")
        main([str(self.base), str(self.project)])
        self.assertEqual(self.project.read_text(encoding="utf-8"), first)


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None
) -> unittest.TestSuite:
    """Add this module's doctests to unittest discovery."""
    tests.addTests(doctest.DocTestSuite())
    return tests


if __name__ == "__main__":
    sys.exit(main())
