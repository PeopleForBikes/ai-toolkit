#!/usr/bin/env python3
"""Install the nono profiles into the local nono configuration.

Each ``*.json`` file of the source folder (``nono/profiles/`` by default) is
copied into ``$XDG_CONFIG_HOME/nono/profiles/`` (``~/.config/nono/profiles/``
when ``XDG_CONFIG_HOME`` is unset or empty).

A local copy that differs from its source is never overwritten silently: the
script shows the difference, installs nothing and exits with status 1, unless
``--force`` is given.

Usage::

    python3 scripts/install_nono_profiles.py [--force] [--source DIR] [--dest DIR]
"""

import argparse
import contextlib
import difflib
import doctest
import io
import os
import shutil
import sys
import tempfile
import unittest
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "nono" / "profiles"


def default_destination(environ: Mapping[str, str] | None = None) -> Path:
    """
    Return the folder nono loads user profiles from.

    Parameters
    ----------
    environ : Mapping[str, str] | None
        The environment variables; ``os.environ`` when omitted.

    Returns
    -------
    Path
        ``$XDG_CONFIG_HOME/nono/profiles``, or ``~/.config/nono/profiles`` when
        ``XDG_CONFIG_HOME`` is unset or empty.

    Examples
    --------
    >>> default_destination({"XDG_CONFIG_HOME": "/cfg", "HOME": "/home/me"})
    PosixPath('/cfg/nono/profiles')
    >>> default_destination({"XDG_CONFIG_HOME": "", "HOME": "/home/me"})
    PosixPath('/home/me/.config/nono/profiles')
    """
    environ = os.environ if environ is None else environ
    config_home = environ.get("XDG_CONFIG_HOME") or str(
        Path(environ.get("HOME") or Path.home()) / ".config"
    )
    return Path(config_home) / "nono" / "profiles"


def unified_diff(installed: Path, source: Path) -> str:
    """
    Show how ``installed`` would change if ``source`` replaced it.

    Parameters
    ----------
    installed : Path
        The local copy of the profile.
    source : Path
        The profile from this repository.

    Returns
    -------
    str
        A unified diff, empty when the files are identical.
    """
    return "".join(
        difflib.unified_diff(
            installed.read_text(encoding="utf-8").splitlines(keepends=True),
            source.read_text(encoding="utf-8").splitlines(keepends=True),
            fromfile=str(installed),
            tofile=str(source),
        )
    )


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
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite local copies that differ from their source",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"folder holding the profiles (default: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=None,
        help="nono profiles folder (default: $XDG_CONFIG_HOME/nono/profiles)",
    )
    args = parser.parse_args(argv)
    dest_dir = args.dest if args.dest is not None else default_destination()

    sources = sorted(args.source.glob("*.json"))
    if not sources:
        report(f"error: no profiles found in {args.source}", error=True)
        return 1

    # Check every profile before copying any, so a conflict installs nothing.
    if not args.force:
        conflicts = 0
        for source in sources:
            installed = dest_dir / source.name
            if not installed.is_file():
                continue
            diff = unified_diff(installed, source)
            if diff:
                conflicts += 1
                report(f"error: {installed} differs from {source}:", error=True)
                report(diff.rstrip("\n"), error=True)
        if conflicts:
            them = "them" if conflicts > 1 else "it"
            report(
                f"Run 'just install-nono-profiles force' to overwrite {them}.",
                error=True,
            )
            return 1

    dest_dir.mkdir(parents=True, exist_ok=True)
    for source in sources:
        installed = dest_dir / source.name
        shutil.copyfile(source, installed)
        report(f"installed {installed}")
    return 0


# Tests: `python3 -m unittest scripts/install_nono_profiles.py` (or `just test` for every script).


class InstallNonoProfilesTest(unittest.TestCase):
    """Exercise the command line on temporary folders."""

    def setUp(self) -> None:
        """Create a source folder with two profiles and an empty destination."""
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.source = root / "source"
        self.source.mkdir()
        (self.source / "a.json").write_text('{"a": 1}\n', encoding="utf-8")
        (self.source / "b.json").write_text('{"b": 2}\n', encoding="utf-8")
        (self.source / "notes.txt").write_text("not a profile\n", encoding="utf-8")
        self.dest = root / "config" / "nono" / "profiles"

    def tearDown(self) -> None:
        """Remove the temporary files."""
        self.tmp.cleanup()

    def run_main(self, *extra: str) -> tuple[int, str]:
        """Run the script quietly and return its status and standard error."""
        stderr = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            stderr
        ):
            status = main(
                ["--source", str(self.source), "--dest", str(self.dest), *extra]
            )
        return status, stderr.getvalue()

    def test_installs_profiles_into_a_new_folder(self) -> None:
        """Every JSON profile is copied, other files are ignored."""
        status, _ = self.run_main()
        self.assertEqual(status, 0)
        self.assertEqual(sorted(p.name for p in self.dest.iterdir()), ["a.json", "b.json"])
        self.assertEqual((self.dest / "a.json").read_text(encoding="utf-8"), '{"a": 1}\n')

    def test_identical_copy_is_not_a_conflict(self) -> None:
        """Reinstalling unchanged profiles succeeds."""
        self.run_main()
        status, stderr = self.run_main()
        self.assertEqual(status, 0)
        self.assertEqual(stderr, "")

    def test_refuses_to_overwrite_a_modified_copy(self) -> None:
        """A differing local copy stops the install and nothing is copied."""
        self.dest.mkdir(parents=True)
        (self.dest / "b.json").write_text('{"b": "local"}\n', encoding="utf-8")
        status, stderr = self.run_main()
        self.assertEqual(status, 1)
        self.assertIn("differs from", stderr)
        self.assertIn('-{"b": "local"}', stderr)
        self.assertIn('+{"b": 2}', stderr)
        self.assertIn("install-nono-profiles force", stderr)
        self.assertFalse((self.dest / "a.json").exists())
        self.assertEqual(
            (self.dest / "b.json").read_text(encoding="utf-8"), '{"b": "local"}\n'
        )

    def test_force_overwrites_a_modified_copy(self) -> None:
        """With --force, the local copy is replaced."""
        self.dest.mkdir(parents=True)
        (self.dest / "b.json").write_text('{"b": "local"}\n', encoding="utf-8")
        status, _ = self.run_main("--force")
        self.assertEqual(status, 0)
        self.assertEqual((self.dest / "b.json").read_text(encoding="utf-8"), '{"b": 2}\n')

    def test_fails_without_profiles(self) -> None:
        """An empty source folder is an error, not a silent no-op."""
        for profile in self.source.glob("*.json"):
            profile.unlink()
        status, stderr = self.run_main()
        self.assertEqual(status, 1)
        self.assertIn("no profiles found", stderr)


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None
) -> unittest.TestSuite:
    """Add this module's doctests to unittest discovery."""
    tests.addTests(doctest.DocTestSuite())
    return tests


if __name__ == "__main__":
    sys.exit(main())
