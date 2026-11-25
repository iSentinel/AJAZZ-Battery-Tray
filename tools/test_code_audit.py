"""Source-only engineering audit regression cases."""

from collections import Counter
from pathlib import Path
import tempfile
import unittest

from code_audit import audit_text, baseline_keys, compare, keys, scan


class CodeAuditTests(unittest.TestCase):
    """Exercise stable keys and exact debt comparison without source execution."""

    def test_source_not_executed(self) -> None:
        """A malicious top-level statement is parsed but never evaluated."""
        result = audit_text("tools/example.py", "raise RuntimeError()")
        self.assertEqual(result, [])

    def test_qualified_identity_and_constructor(self) -> None:
        """Constructor and nested symbols have distinct stable finding keys."""
        source = ("class Public:\n    def __init__(self, value):\n"
                  "        self.value = value\n    def method(self):\n"
                  "        def nested(x):\n            return x\n")
        result = keys(audit_text("tools/example.py", source))
        self.assertIn(("tools/example.py", "Public.__init__",
                       "public-parameter", "value"), result)
        self.assertIn(("tools/example.py", "Public.method.nested",
                       "public-parameter", "x"), result)

    def test_line_changes_and_private_length(self) -> None:
        """Line offsets do not alter keys; private long functions still count."""
        source = "def _long():\n" + "    pass\n" * 40
        a = audit_text("tools/example.py", source)
        b = audit_text("tools/example.py", "\n" + source)
        self.assertEqual(keys(a), keys(b))
        self.assertEqual(a[0].rule, "function-length")

    def test_exact_drift_and_duplicates(self) -> None:
        """A new finding cannot cancel a resolved finding."""
        actual = audit_text("tools/example.py", "def f():\n    pass\n")
        baseline = keys(actual)
        extra = ("tools/example.py", "other", "public-return", "missing return annotation")
        new, resolved = compare(actual, Counter({extra: 1}))
        self.assertTrue(new and resolved)
        new, resolved = compare(actual, baseline + baseline)
        self.assertFalse(new)
        self.assertEqual(resolved, baseline)

    def test_nested_sources_cannot_escape_gate(self) -> None:
        """New Python modules in subdirectories are included in the audit."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "tools" / "nested"
            nested.mkdir(parents=True)
            (nested / "new.py").write_text("def f():\n    pass\n")
            findings = scan(root)
            self.assertEqual(len(findings), 2)
            self.assertEqual(findings[0].path, "tools/nested/new.py")
            self.assertTrue(compare(findings, Counter())[0])

    def test_symlink_rejected(self) -> None:
        """Do not follow symlinked source entries into unreviewed files."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools = root / "tools"
            tools.mkdir()
            outside = root / "outside.py"
            outside.write_text("raise RuntimeError()")
            try:
                (tools / "linked.py").symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink creation unavailable on this platform")
            with self.assertRaises(ValueError):
                scan(root)

    def test_baseline_schema(self) -> None:
        """Reject malformed versions or finding keys; keep multiplicities."""
        item = ["tools/a.py", "f", "public-return", "missing return annotation"]
        self.assertEqual(baseline_keys({"schema": 1, "findings": [item, item]})[tuple(item)], 2)
        for bad in ({"schema": True, "findings": []},
                    {"schema": 1, "findings": [["x"]]},
                    {"schema": 2, "findings": []}):
            with self.assertRaises(ValueError):
                baseline_keys(bad)


if __name__ == "__main__":
    unittest.main()
