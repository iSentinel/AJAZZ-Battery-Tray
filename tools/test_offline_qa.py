"""Exercise the offline QA result contract with synthetic suites and files."""

from pathlib import Path
import tempfile
import unittest

from qa_unittest import execute
from run_offline_qa import REQUIRED, create_run, junit_counts, verify_inventory


def sample_case(kind: str) -> unittest.TestCase:
    """Create a private in-memory fixture without adding discovered tests."""
    class _Case(unittest.TestCase):
        def runTest(self) -> None:
            if kind == "failure":
                self.fail("PRIVATE_CANARY")
            if kind == "skipped":
                self.skipTest("PRIVATE_CANARY")

    return _Case()


class OfflineQaTests(unittest.TestCase):
    """Validate evidence and test-status behavior without launching a lab."""

    def test_pass_and_no_overwrite(self) -> None:
        """A completed case produces accurate JUnit and immutable output."""
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "report.xml"
            self.assertEqual(execute(unittest.TestSuite([sample_case("pass")]), output), 0)
            self.assertEqual(junit_counts(output)["tests"], 1)
            original = output.read_bytes()
            with self.assertRaises(FileExistsError):
                execute(unittest.TestSuite([sample_case("pass")]), output)
            self.assertEqual(output.read_bytes(), original)

    def test_failure_and_skip_are_not_pass(self) -> None:
        """Assertions and skipped-only suites fail without leaking canary text."""
        with tempfile.TemporaryDirectory() as tmp:
            for case, key in ((sample_case("failure"), "failures"),
                              (sample_case("skipped"), "skipped")):
                output = Path(tmp) / f"{key}.xml"
                self.assertEqual(execute(unittest.TestSuite([case]), output), 1)
                self.assertEqual(junit_counts(output)[key], 1)
                self.assertNotIn(b"PRIVATE_CANARY", output.read_bytes())

    def test_empty_suite_not_pass(self) -> None:
        """A zero-test discovery result is not successful QA."""
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "empty.xml"
            self.assertEqual(execute(unittest.TestSuite(), output), 1)
            self.assertEqual(junit_counts(output)["tests"], 0)

    def test_required_inventory_and_unique_runs(self) -> None:
        """Require named evidence, not merely files that happen to exist."""
        with tempfile.TemporaryDirectory() as tmp:
            first, second = create_run(Path(tmp)), create_run(Path(tmp))
            self.assertNotEqual(first, second)
            with self.assertRaises(ValueError):
                verify_inventory(first)
            for name in REQUIRED:
                (first / name).write_text("synthetic")
            manifest = verify_inventory(first)
            self.assertEqual({entry["name"] for entry in manifest["files"]}, set(REQUIRED))
            self.assertTrue(all(entry["bytes"] == 9 for entry in manifest["files"]))

    def test_junit_count_mismatch(self) -> None:
        """Do not accept a reported total inconsistent with testcase entries."""
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "bad.xml"
            output.write_text('<testsuite tests="1" failures="0" errors="0" skipped="0"/>')
            with self.assertRaises(ValueError):
                junit_counts(output)


if __name__ == "__main__":
    unittest.main()
