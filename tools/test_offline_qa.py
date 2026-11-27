"""Exercise the offline QA result contract with synthetic suites and files."""

from collections.abc import Iterator
import json
from types import SimpleNamespace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from qa_unittest import execute
from run_offline_qa import (REQUIRED, create_run, junit_counts, read_evidence,
                            verify_inventory, verify_manifest, write_json,
                            file_identity, check_directory)


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

    def test_manifest_detects_changed_and_extra_files(self) -> None:
        """Reopen a valid set and reject content replacement or extra entries."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in REQUIRED:
                (root / name).write_text("synthetic")
            write_json(root / "manifest.json", verify_inventory(root))
            verify_manifest(root)
            extra = root / "unexpected.txt"
            extra.write_text("extra")
            with self.assertRaises(ValueError):
                verify_manifest(root)
            extra.unlink()
            (root / REQUIRED[0]).write_text("different")
            with self.assertRaises(ValueError):
                verify_manifest(root)

    def test_inventory_stops_at_first_unknown_entry(self) -> None:
        """Do not exhaust an unbounded iterator of unrelated entries."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("run_offline_qa.os.scandir") as scan:
                entries = scan.return_value.__enter__.return_value

                def stream() -> Iterator[SimpleNamespace]:
                    yield SimpleNamespace(name="unexpected")
                    raise AssertionError("Unexpected further enumeration")

                entries.__iter__.side_effect = stream
                with self.assertRaises(ValueError):
                    check_directory(root)

    def test_manifest_rechecks_directory_after_reads(self) -> None:
        """Reject an additional entry appearing after the first inventory."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in REQUIRED:
                (root / name).write_text("synthetic")
            write_json(root / "manifest.json", verify_inventory(root))
            def mutate_after_first(directory: Path) -> None:
                """Simulate an extra entry between the two inventory scans."""
                check_directory(directory)
                (directory / "unexpected.txt").write_text("synthetic")

            with patch("run_offline_qa.check_directory",
                       side_effect=mutate_after_first) as check:
                with self.assertRaises(ValueError):
                    verify_manifest(root)
                self.assertEqual(check.call_count, 2)

    def test_manifest_rejects_duplicate_or_invalid_entry(self) -> None:
        """Reject duplicate required names and Boolean byte counts."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in REQUIRED:
                (root / name).write_text("synthetic")
            valid = verify_inventory(root)
            path = root / "manifest.json"
            invalid = {"schema": 1, "files": valid["files"] + valid["files"][:1]}
            path.write_text(json.dumps(invalid))
            with self.assertRaises(ValueError):
                verify_manifest(root)
            valid["files"][0]["bytes"] = True
            path.write_text(json.dumps(valid))
            with self.assertRaises(ValueError):
                verify_manifest(root)

    def test_evidence_symlink_rejected(self) -> None:
        """Refuse evidence redirected to a different local file."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.write_text("PRIVATE_CANARY")
            link = root / "link"
            try:
                link.symlink_to(source)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink unavailable on this platform")
            with self.assertRaises(ValueError):
                read_evidence(link)

    def test_windows_cross_api_timestamp(self) -> None:
        """Windows creation/change times may differ for the same file."""
        fields = dict(st_dev=1, st_ino=2, st_size=3, st_mtime_ns=4,
                      st_birthtime_ns=5, st_nlink=1)
        before = SimpleNamespace(**fields, st_ctime_ns=5)
        opened = SimpleNamespace(**fields, st_ctime_ns=6)
        self.assertEqual(file_identity(before, True, True),
                         file_identity(opened, True, True))
        self.assertNotEqual(file_identity(before, False, True),
                            file_identity(opened, False, True))
        self.assertNotEqual(file_identity(before, True, False),
                            file_identity(opened, True, False))
        opened.st_mtime_ns += 1
        self.assertNotEqual(file_identity(before, True, True),
                            file_identity(opened, True, True))

    def test_read_evidence_after_rewrite(self) -> None:
        """A stable rewritten regular file must still be readable."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence"
            path.write_bytes(b"first")
            path.write_bytes(b"second")
            self.assertEqual(read_evidence(path), b"second")

    def test_junit_count_mismatch(self) -> None:
        """Do not accept a reported total inconsistent with testcase entries."""
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "bad.xml"
            output.write_text('<testsuite tests="1" failures="0" errors="0" skipped="0"/>')
            with self.assertRaises(ValueError):
                junit_counts(output)


if __name__ == "__main__":
    unittest.main()
