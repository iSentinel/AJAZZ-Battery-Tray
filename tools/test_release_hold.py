"""Regression guard for the temporary source-level release safety hold."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReleaseHoldTests(unittest.TestCase):
    """Verify the intended hold structure without executing release workflows."""

    def test_no_automatic_release_triggers(self) -> None:
        """All release workflows are manual-only and have read permissions."""
        for name in ("release-beta.yml", "release-high-sierra.yml", "release-windows.yml"):
            source = (ROOT / ".github" / "workflows" / name).read_text()
            lines = source.split("on:\n", 1)[1].splitlines()
            trigger = []
            for line in lines:
                if line and not line.startswith(" "):
                    break
                if line.strip():
                    trigger.append(line.strip())
            self.assertEqual(trigger, ["workflow_dispatch:"])
            self.assertNotIn("contents: write", source)
            self.assertNotIn("--clobber", source)

    def test_explicit_blocker_before_checkout(self) -> None:
        """Publishing paths cannot execute under the unqualified hold."""
        for name in ("release-beta.yml", "release-high-sierra.yml"):
            source = (ROOT / ".github" / "workflows" / name).read_text()
            first = source.split("steps:", 1)[1].split("uses:", 1)[0]
            self.assertIn("Require qualified candidate admission", first)
            self.assertIn("exit 1", first)
        source = (ROOT / ".github/workflows/release-windows.yml").read_text()
        self.assertIn("exit 1", source)
        self.assertNotIn("gh release", source)


if __name__ == "__main__":
    unittest.main()
