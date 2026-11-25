"""Check the reviewed workflow pin inventory and finite job budgets."""

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SHA = re.compile(r"[0-9a-f]{40}")
USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(\S+)(?:\s+#.*)?\s*$")
JOB = re.compile(r"^  ([A-Za-z0-9_-]+):\s*$")


def action_refs(source: str) -> list[str]:
    """Read the repository's canonical block-style uses declarations."""
    refs = []
    for line in source.splitlines():
        if line.lstrip().startswith("#"):
            continue
        if re.search(r"(?:^|\s)(?:uses|['\"]uses['\"])\s*:", line):
            match = USES.fullmatch(line)
            if not match:
                raise ValueError("Noncanonical uses declaration needs review")
            refs.append(match[1])
    return refs


def require_pins(source: str, allowed: set[str]) -> None:
    """Reject floating, unknown and noncanonical action references."""
    for ref in action_refs(source):
        if ref not in allowed:
            raise ValueError("Unreviewed action reference")


def job_budgets(source: str) -> list[int]:
    """Require a bounded timeout for every current block-style job."""
    if source.count("\njobs:\n") != 1:
        raise ValueError("Expected one canonical jobs block")
    jobs = source.split("\njobs:\n", 1)[1]
    blocks = []
    for line in jobs.splitlines():
        if line and not line.startswith((" ", "#")):
            break
        if JOB.fullmatch(line):
            blocks.append([])
        elif blocks:
            blocks[-1].append(line)
    budgets = []
    for block in blocks:
        values = [line for line in block if line.startswith("    timeout-minutes:")]
        if len(values) != 1:
            raise ValueError("Missing or duplicate job timeout")
        value = values[0].split(":", 1)[1].strip()
        if not value.isdecimal() or not 1 <= int(value) <= 30:
            raise ValueError("Unreviewed job timeout")
        budgets.append(int(value))
    if not budgets:
        raise ValueError("No jobs found")
    return budgets


class CiActionPinTests(unittest.TestCase):
    """Source checks for the current canonical workflow format, not a YAML parser."""

    def test_reviewed_workflow_inventory(self) -> None:
        """All external references must match exact reviewed commits."""
        lock = json.loads((ROOT / "config/ci-actions-lock.json").read_text())
        self.assertEqual(lock["schema"], 1)
        pins = lock["actions"]
        for entry in pins.values():
            self.assertIsNotNone(SHA.fullmatch(entry["sha"]))
            self.assertTrue(entry["evidence"])
        allowed = {name + "@" + entry["sha"] for name, entry in pins.items()}
        seen = set()
        paths = sorted((ROOT / ".github/workflows").glob("*.y*ml"))
        self.assertTrue(paths)
        for path in paths:
            source = path.read_text()
            require_pins(source, allowed)
            seen.update(action_refs(source))
            self.assertTrue(job_budgets(source))
        self.assertEqual(seen, allowed)

    def test_dotnet_sdk_selection_is_exact(self) -> None:
        """Require matching global SDK selection, setup pin and version check."""
        sdk = json.loads((ROOT / "global.json").read_text())["sdk"]
        self.assertRegex(sdk["version"], r"^8\.0\.[0-9]+$")
        self.assertEqual(sdk["rollForward"], "disable")
        self.assertIs(sdk["allowPrerelease"], False)
        observed = set()
        for path in (ROOT / ".github/workflows").glob("*.yml"):
            source = path.read_text()
            if "uses: actions/setup-dotnet@" not in source:
                continue
            observed.add(path.name)
            self.assertIn("dotnet-version: '" + sdk["version"] + "'", source)
            self.assertIn("$actual = dotnet --version", source)
            self.assertIn("$actual -ne '" + sdk["version"] + "'", source)
            self.assertNotIn("dotnet-version: '8.0.x'", source)
        self.assertEqual(observed, {"build.yml", "test-ha-preview.yml",
                                   "test-installer-upgrade.yml", "release-beta.yml"})

    def test_reject_floating_or_unreviewed(self) -> None:
        """A full hash alone is insufficient without a reviewed lock entry."""
        allowed = {"actions/checkout@" + "a" * 40}
        for ref in ("actions/checkout@v4", "actions/checkout@" + "b" * 40,
                    "example/other@" + "a" * 40):
            with self.assertRaises(ValueError):
                require_pins("      - uses: " + ref, allowed)
        require_pins("      - uses: actions/checkout@" + "a" * 40, allowed)

    def test_reject_noncanonical_uses(self) -> None:
        """Alternative YAML syntax cannot silently replace canonical declarations."""
        for source in ('      - "uses": actions/checkout@v4',
                       "      - uses: 'actions/checkout@v4'",
                       "      - uses: actions/checkout@v4 # comment"):
            with self.assertRaises(ValueError):
                require_pins(source, set())

    def test_reject_missing_or_unbounded_job_timeout(self) -> None:
        """A second job cannot silently omit its finite timeout."""
        prefix = "\njobs:\n  first:\n    timeout-minutes: 10\n  second:\n"
        for suffix in ("    runs-on: ubuntu-latest\n",
                       "    timeout-minutes: 0\n",
                       "    timeout-minutes: 999\n"):
            with self.assertRaises(ValueError):
                job_budgets(prefix + suffix)
        self.assertEqual(job_budgets(prefix + "    timeout-minutes: 15\n"), [10, 15])


if __name__ == "__main__":
    unittest.main()
