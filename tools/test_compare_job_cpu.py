"""Tests for cumulative Windows job CPU comparison."""
import csv
import tempfile
import unittest
from pathlib import Path

from compare_job_cpu import FIELDS, compare, read_run


class JobCpuTests(unittest.TestCase):
    """Use synthetic data; no Windows processes or HID required."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def fixture(self, name="normal.csv", mode="normal", sha="a"*64,
                duration=30, cpu=0.3, counts=(1, 2, 3), active=1):
        path = self.root / name
        with path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow(FIELDS)
            for i in range(3):
                writer.writerow(("2026-11-24T00:00:00Z", "beta.60", sha,
                                 mode, i * duration / 2, i * cpu / 2,
                                 counts[i], active))
        return path

    def test_cpu_and_exited_children(self):
        normal = read_run(self.fixture(), "normal")
        isolated = read_run(self.fixture("i.csv", "isolated", cpu=0.6),
                            "isolated")
        self.assertEqual(normal[4], 2)
        self.assertEqual(compare([normal], [isolated]), (1, 2))

    def test_different_sha(self):
        normal = read_run(self.fixture(), "normal")
        isolated = read_run(self.fixture("i.csv", "isolated", sha="b"*64),
                            "isolated")
        with self.assertRaisesRegex(ValueError, "SHA256"):
            compare([normal], [isolated])

    def test_wrong_mode(self):
        with self.assertRaisesRegex(ValueError, "mode"):
            read_run(self.fixture(), "isolated")

    def test_bad_counts(self):
        with self.assertRaisesRegex(ValueError, "Nonmonotonic"):
            read_run(self.fixture(counts=(2, 3, 2)), "normal")

    def test_no_active_root(self):
        with self.assertRaisesRegex(ValueError, "counters"):
            read_run(self.fixture(active=0), "normal")

    def test_nan_cpu(self):
        with self.assertRaisesRegex(ValueError, "counters"):
            read_run(self.fixture(cpu=float("nan")), "normal")

    def test_duration_mismatch(self):
        normal = read_run(self.fixture(), "normal")
        isolated = read_run(self.fixture("i.csv", "isolated", duration=60),
                            "isolated")
        with self.assertRaisesRegex(ValueError, "Durations"):
            compare([normal], [isolated])

    def test_duplicate_content(self):
        normal = read_run(self.fixture(), "normal")
        isolated = read_run(self.fixture("i.csv", "isolated"), "isolated")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            compare([normal, normal], [isolated])
