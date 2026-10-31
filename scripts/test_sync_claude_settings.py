"""Tests for sync_claude_settings."""

import json
import tempfile
import unittest
from pathlib import Path

from sync_claude_settings import main

BASE = {
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
        self.base.write_text(json.dumps(BASE), encoding="utf-8")
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
        self.assertEqual(self.read_project(), BASE)

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


if __name__ == "__main__":
    unittest.main()
