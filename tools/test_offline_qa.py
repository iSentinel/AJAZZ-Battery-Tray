"""Exercise the offline QA result contract with synthetic suites and files."""

from collections.abc import Iterator
import json
import stat
import subprocess
import sys
from types import SimpleNamespace
from typing import TextIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from qa_unittest import execute
from run_offline_qa import (REQUIRED, create_run, junit_counts, read_evidence,
                            verify_inventory, verify_manifest, write_json,
                            file_identity, check_directory, publish_manifest,
                            private_directory)


INTERRUPTED_PUBLISHER = """
import os
from pathlib import Path
import sys
from unittest.mock import patch
from run_offline_qa import publish_manifest
real_link = os.link

def interrupt(source, destination):
    if sys.argv[2] == "after":
        real_link(source, destination)
    os._exit(73)

with patch("run_offline_qa.os.link", side_effect=interrupt):
    publish_manifest(Path(sys.argv[1]))
"""


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

    def test_private_directory_refuses_reparse_and_non_directory(self) -> None:
        """Refuse a reparse directory or a non-directory before creation."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file = root / "ordinary-file"
            file.write_text("synthetic")
            with self.assertRaises(ValueError):
                create_run(file)
            info = SimpleNamespace(st_mode=stat.S_IFDIR | 0o700,
                                   st_ino=1, st_file_attributes=0x400)
            with patch("run_offline_qa.stat.FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
                with patch.object(Path, "lstat", return_value=info):
                    with self.assertRaises(ValueError):
                        create_run(root)

    def test_private_directory_refuses_public_posix_root(self) -> None:
        """Reject group/other permission bits without changing existing mode."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            info = SimpleNamespace(st_mode=stat.S_IFDIR | 0o755, st_ino=1,
                                   st_uid=100, st_file_attributes=0)
            with patch("run_offline_qa.os.name", "posix"):
                with patch("run_offline_qa.os.geteuid", return_value=100, create=True):
                    with patch.object(Path, "lstat", return_value=info):
                        with self.assertRaisesRegex(ValueError, "owner-private"):
                            private_directory(root)

    def test_create_run_refuses_root_identity_change(self) -> None:
        """Detect parent replacement observed across fresh directory creation."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            before = SimpleNamespace(st_dev=1, st_ino=2)
            after = SimpleNamespace(st_dev=1, st_ino=3)
            with patch("run_offline_qa.private_directory",
                       side_effect=[before, after]):
                with self.assertRaisesRegex(ValueError, "root changed"):
                    create_run(root)

    def test_interrupted_manifest_publication(self) -> None:
        """A killed producer must leave refused evidence and allow a fresh run."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for stage in ("before", "after"):
                with self.subTest(stage=stage):
                    run = create_run(root)
                    for name in REQUIRED:
                        (run / name).write_bytes(b"synthetic")
                    result = subprocess.run(
                        [sys.executable, "-c", INTERRUPTED_PUBLISHER, str(run), stage],
                        cwd=Path(__file__).resolve().parent,
                        capture_output=True, timeout=15, check=False)
                    self.assertEqual(result.returncode, 73)
                    manifest = run / "manifest.json"
                    self.assertEqual(manifest.exists(), stage == "after")
                    pending = list(run.glob(".manifest-*"))
                    self.assertEqual(len(pending), 1)
                    self.assertEqual(pending[0].stat().st_nlink,
                                     2 if stage == "after" else 1)
                    original = {p.name for p in run.iterdir()}
                    with self.assertRaises(ValueError):
                        verify_manifest(run)
                    self.assertEqual({p.name for p in run.iterdir()}, original)
            fresh = create_run(root)
            for name in REQUIRED:
                (fresh / name).write_bytes(b"synthetic")
            publish_manifest(fresh)
            verify_manifest(fresh)
            self.assertEqual(len(list(root.iterdir())), 3)

    def test_publish_manifest_no_replace(self) -> None:
        """Publish a complete single-link manifest and refuse overwriting it."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in REQUIRED:
                (root / name).write_text("synthetic")
            publish_manifest(root)
            verify_manifest(root)
            manifest = root / "manifest.json"
            original = manifest.read_bytes()
            self.assertEqual(manifest.stat().st_nlink, 1)
            with self.assertRaises(FileExistsError):
                publish_manifest(root)
            self.assertEqual(manifest.read_bytes(), original)
            self.assertEqual(set(p.name for p in root.iterdir()),
                             set(REQUIRED) | {"manifest.json"})

    def test_publish_manifest_interrupted_serialization(self) -> None:
        """Do not expose a partially serialized completion marker."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in REQUIRED:
                (root / name).write_text("synthetic")

            def fail_dump(value: dict, output: TextIO, **options: object) -> None:
                """Simulate a write failure after emitting partial JSON."""
                output.write('{"schema":')
                raise OSError("synthetic write failure")

            with patch("run_offline_qa.json.dump", side_effect=fail_dump):
                with self.assertRaises(OSError):
                    publish_manifest(root)
            self.assertEqual(set(p.name for p in root.iterdir()), set(REQUIRED))
            with self.assertRaises(ValueError):
                verify_manifest(root)

    def test_publish_manifest_link_failure(self) -> None:
        """Fail closed when the filesystem cannot publish without replacement."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in REQUIRED:
                (root / name).write_text("synthetic")
            with patch("run_offline_qa.os.link", side_effect=OSError("unsupported")):
                with self.assertRaises(OSError):
                    publish_manifest(root)
            self.assertEqual(set(p.name for p in root.iterdir()), set(REQUIRED))

    def test_publish_manifest_sync_failure(self) -> None:
        """Never expose the completion marker if synchronizing data fails."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in REQUIRED:
                (root / name).write_text("synthetic")
            with patch("run_offline_qa.os.fsync", side_effect=OSError("sync failure")):
                with self.assertRaises(OSError):
                    publish_manifest(root)
            self.assertEqual(set(p.name for p in root.iterdir()), set(REQUIRED))

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
                    """Yield one unexpected entry and forbid further enumeration."""
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

    def test_manifest_rejects_late_file_mutation(self) -> None:
        """Catch a mutation after an earlier file has already been verified."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in REQUIRED:
                (root / name).write_text("synthetic")
            write_json(root / "manifest.json", verify_inventory(root))

            def mutate_after_read(path: Path) -> bytes:
                """Change the first evidence file after reading the last."""
                raw = read_evidence(path)
                if path.name == REQUIRED[-1]:
                    (root / REQUIRED[0]).write_text("late mutation")
                return raw

            with patch("run_offline_qa.read_evidence",
                       side_effect=mutate_after_read):
                with self.assertRaisesRegex(ValueError, "inventory changed"):
                    verify_manifest(root)

    def test_manifest_rejects_late_manifest_replacement(self) -> None:
        """Reject a new manifest inode even when its contents are identical."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in REQUIRED:
                (root / name).write_text("synthetic")
            manifest = root / "manifest.json"
            write_json(manifest, verify_inventory(root))

            def replace_after_read(path: Path) -> bytes:
                """Replace the already-read manifest with identical bytes."""
                raw = read_evidence(path)
                if path.name == REQUIRED[-1]:
                    replacement = root / "replacement"
                    replacement.write_bytes(manifest.read_bytes())
                    replacement.replace(manifest)
                return raw

            with patch("run_offline_qa.read_evidence",
                       side_effect=replace_after_read):
                with self.assertRaisesRegex(ValueError, "inventory changed"):
                    verify_manifest(root)

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
