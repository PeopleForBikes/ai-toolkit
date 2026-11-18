"""Tests for the security properties of the pfb-claude nono profile.

Each test checks one property of nono/profiles/pfb-claude.json that a review
could miss: widening one of them must change this file too, so the change is
reviewed as security-sensitive (see SECURITY.md).
"""

import doctest
import json
import posixpath
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = ROOT / "nono" / "profiles" / "pfb-claude.json"
SECURITY_PATH = ROOT / "SECURITY.md"

# The only credential route: its name, the keychain account it reads (service
# nono), and where it sends the token.
AGENT_ROUTE = "github_agent"
AGENT_ROUTE_KEY = "github_agent"
AGENT_ROUTE_UPSTREAM = "https://api.github.com"

# Requests to github.com: reads and Git fetches only, never a push
# (git-receive-pack).
GITHUB_WEB_RULES = {
    ("GET", "/**"),
    ("HEAD", "/**"),
    ("POST", "/*/*/git-upload-pack"),
}

# Requests that carry the agent's token: reads, GraphQL (which gh needs), and
# creating issues, pull requests, their comments and pull request reviews.
AGENT_ROUTE_RULES = {
    ("GET", "/**"),
    ("POST", "/graphql"),
    ("POST", "/repos/*/*/issues"),
    ("POST", "/repos/*/*/issues/*/comments"),
    ("POST", "/repos/*/*/pulls"),
    ("POST", "/repos/*/*/pulls/*/comments"),
    ("POST", "/repos/*/*/pulls/*/reviews"),
}

# Environment variables that can hold the developer's own GitHub token.
DEVELOPER_TOKEN_VARIABLES = {
    "GH_ENTERPRISE_TOKEN",
    "GH_TOKEN",
    "GITHUB_ENTERPRISE_TOKEN",
    "GITHUB_TOKEN",
}

# gh's configuration in the sandbox: an empty directory, so gh never falls back
# to the developer's login.
GH_CONFIG_DIR = "$HOME/.cache/nono/gh"

# Paths the profile must not grant, nor anything inside or above them: the base
# profile's deny rules make the first two ineffective, and the gh configuration
# may hold the developer's token.
FORBIDDEN_GRANTS = ("/Library/Keychains", "~/.docker", "~/.config/gh")

FILESYSTEM_GRANT_FIELDS = (
    "allow",
    "read",
    "write",
    "allow_file",
    "read_file",
    "write_file",
    "bypass_protection",
)

GIT_HOOKS = "$WORKDIR/.git/hooks"
VSCODE_GROUPS = {"vscode_linux", "vscode_macos"}


def load_profile() -> dict[str, Any]:
    """Load the published pfb-claude profile."""
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def host_entries(profile: dict[str, Any]) -> list[Any]:
    """Return the profile's allow_domain entries, plain hosts and objects."""
    return profile.get("network", {}).get("allow_domain", [])


def host_name(entry: Any) -> str:
    """Return the host of an allow_domain entry, plain or with endpoint rules."""
    return entry if isinstance(entry, str) else entry["domain"]


def rule_set(rules: list[dict[str, str]]) -> set[tuple[str, str]]:
    """Turn a list of endpoint rules into a set of (method, path) pairs."""
    return {(rule["method"], rule["path"]) for rule in rules}


def normalize_path(path: str) -> str:
    """Spell a profile path one way: ~ for the home directory, no trailing /.

    >>> normalize_path("$HOME/.docker/")
    '~/.docker'
    >>> normalize_path("${HOME}/.config//gh/./hosts.yml")
    '~/.config/gh/hosts.yml'
    >>> normalize_path("$HOME")
    '~'
    """
    for home in ("${HOME}", "$HOME"):
        if path == home or path.startswith(home + "/"):
            path = "~" + path[len(home) :]
            break
    return posixpath.normpath(path)


def overlaps(path: str, forbidden: str) -> bool:
    """Tell whether granting path also grants forbidden, or part of it.

    >>> overlaps("~/.config/gh/hosts.yml", "~/.config/gh")
    True
    >>> overlaps("~/.config", "~/.config/gh")
    True
    >>> overlaps("~/.config/ghostty", "~/.config/gh")
    False
    """
    path, forbidden = normalize_path(path), normalize_path(forbidden)
    return (
        path == forbidden
        or path.startswith(forbidden + "/")
        or forbidden.startswith(path + "/")
    )


class PfbClaudeProfileTest(unittest.TestCase):
    """Check the security properties of nono/profiles/pfb-claude.json."""

    def setUp(self) -> None:
        """Load the profile."""
        self.profile = load_profile()

    def agent_route(self) -> dict[str, Any]:
        """Return the definition of the agent's GitHub credential route."""
        routes = self.profile.get("network", {}).get("custom_credentials", {})
        self.assertIn(AGENT_ROUTE, routes, "the agent token route is missing")
        return routes[AGENT_ROUTE]

    def test_identity(self) -> None:
        """The profile is pfb-claude and extends nolabs-ai/claude."""
        self.assertEqual(self.profile.get("meta", {}).get("name"), "pfb-claude")
        extends = self.profile.get("extends")
        if isinstance(extends, str):
            extends = [extends]
        self.assertEqual(extends, ["nolabs-ai/claude"])

    def test_no_wildcard_hosts(self) -> None:
        """No allowed host is a wildcard pattern."""
        for host in map(host_name, host_entries(self.profile)):
            with self.subTest(host=host):
                self.assertNotIn("*", host)

    def test_hosts_sorted(self) -> None:
        """Allowed hosts are unique and sorted by host name."""
        hosts = [host_name(entry) for entry in host_entries(self.profile)]
        self.assertEqual(len(hosts), len(set(hosts)), "duplicate hosts")
        self.assertEqual(hosts, sorted(hosts))

    def test_github_web_allows_reads_and_fetch(self) -> None:
        """github.com allows reads and Git fetches, never a push."""
        entries = [
            entry
            for entry in host_entries(self.profile)
            if host_name(entry) == "github.com"
        ]
        self.assertEqual(len(entries), 1, "github.com must be allowed once")
        self.assertIsInstance(
            entries[0], dict, "github.com must carry endpoint rules"
        )
        self.assertEqual(rule_set(entries[0]["endpoints"]), GITHUB_WEB_RULES)

    def test_agent_route(self) -> None:
        """The agent token goes to api.github.com, on the allowed calls only.

        The agent's route is the only credential: nono's built-in routes (such
        as github, which reads the developer's GITHUB_TOKEN) and other custom
        routes are refused, and the token comes from the agent's keychain item.
        """
        network = self.profile.get("network", {})
        self.assertEqual(network.get("credentials"), [AGENT_ROUTE])
        self.assertEqual(set(network.get("custom_credentials", {})), {AGENT_ROUTE})
        route = self.agent_route()
        self.assertEqual(route.get("credential_key"), AGENT_ROUTE_KEY)
        self.assertEqual(route.get("upstream"), AGENT_ROUTE_UPSTREAM)
        self.assertEqual(route.get("env_var"), "GITHUB_TOKEN")
        self.assertEqual(rule_set(route.get("endpoint_rules", [])), AGENT_ROUTE_RULES)

    def test_developer_tokens_removed(self) -> None:
        """The developer's GitHub tokens and gh login stay out of the sandbox."""
        environment = self.profile.get("environment", {})
        self.assertLessEqual(
            DEVELOPER_TOKEN_VARIABLES, set(environment.get("deny_vars", []))
        )
        self.assertEqual(
            environment.get("set_vars", {}).get("GH_CONFIG_DIR"), GH_CONFIG_DIR
        )

    def test_no_dead_or_open_paths(self) -> None:
        """No ineffective or token-bearing grant; hooks and VS Code are closed."""
        filesystem = self.profile.get("filesystem", {})
        for field in FILESYSTEM_GRANT_FIELDS:
            for path in filesystem.get(field, []):
                for forbidden in FORBIDDEN_GRANTS:
                    with self.subTest(field=field, path=path, forbidden=forbidden):
                        self.assertFalse(overlaps(path, forbidden))
        self.assertIn(GIT_HOOKS, filesystem.get("deny", []))
        self.assertLessEqual(
            VSCODE_GROUPS, set(self.profile.get("groups", {}).get("exclude", []))
        )

    def test_hosts_documented(self) -> None:
        """SECURITY.md names every allowed host in a code span."""
        security = SECURITY_PATH.read_text(encoding="utf-8")
        for host in map(host_name, host_entries(self.profile)):
            with self.subTest(host=host):
                self.assertIn(f"`{host}`", security)


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None
) -> unittest.TestSuite:
    """Add this module's doctests (path helpers) to unittest discovery."""
    tests.addTests(doctest.DocTestSuite())
    return tests


if __name__ == "__main__":
    unittest.main()
