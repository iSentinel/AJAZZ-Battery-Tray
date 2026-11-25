"""Tests for cumulative Windows job CPU comparison."""
import csv
import tempfile
import unittest
from pathlib import Path

from compare_job_cpu import FIELDS, compare, read_run


class JobCpuTests(unittest.TestCase):
    """Use synthetic data; no Windows processes or HID required."""

    def setUp(self) -> None:
        """Allocate an isolated temporary directory for each synthetic CSV."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def fixture(self, name: str = "normal.csv", mode: str = "normal",
                sha: str = "a" * 64, duration: float = 30, cpu: float = 0.3,
                counts: tuple[int, int, int] = (1, 2, 3), active: int = 1) -> Path:
        """Write controlled process counters, CPU time and executable identity."""
        path = self.root / name
        with path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow(FIELDS)
            for i in range(3):
                writer.writerow(("2026-11-24T00:00:00Z", "beta.60", sha,
                                 mode, i * duration / 2, i * cpu / 2,
                                 counts[i], active))
        return path

    def test_cpu_and_exited_children(self) -> None:
        """Count exited children and normalize cumulative CPU by elapsed time."""
        normal = read_run(self.fixture(), "normal")
        isolated = read_run(self.fixture("i.csv", "isolated", cpu=0.6),
                            "isolated")
        self.assertEqual(normal[4], 2)
        self.assertEqual(compare([normal], [isolated]), (1, 2))

    def test_different_sha(self) -> None:
        """Reject paired runs produced by different executable hashes."""
        normal = read_run(self.fixture(), "normal")
        isolated = read_run(self.fixture("i.csv", "isolated", sha="b"*64),
                            "isolated")
        with self.assertRaisesRegex(ValueError, "SHA256"):
            compare([normal], [isolated])

    def test_wrong_mode(self) -> None:
        """Reject a normal run labeled as an isolated comparison input."""
        with self.assertRaisesRegex(ValueError, "mode"):
            read_run(self.fixture(), "isolated")

    def test_bad_counts(self) -> None:
        """Reject a cumulative total-process counter that decreases."""
        with self.assertRaisesRegex(ValueError, "Nonmonotonic"):
            read_run(self.fixture(counts=(2, 3, 2)), "normal")

    def test_no_active_root(self) -> None:
        """Reject samples without an active process in the measured job."""
        with self.assertRaisesRegex(ValueError, "counters"):
            read_run(self.fixture(active=0), "normal")

    def test_nan_cpu(self) -> None:
        """Reject nonfinite cumulative process CPU counters."""
        with self.assertRaisesRegex(ValueError, "counters"):
            read_run(self.fixture(cpu=float("nan")), "normal")

    def test_duration_mismatch(self) -> None:
        """Reject normal and isolated windows of incompatible duration."""
        normal = read_run(self.fixture(), "normal")
        isolated = read_run(self.fixture("i.csv", "isolated", duration=60),
                            "isolated")
        with self.assertRaisesRegex(ValueError, "Durations"):
            compare([normal], [isolated])

    def test_duplicate_content(self) -> None:
        """Reject repeated CSV contents as independent measurements."""
        normal = read_run(self.fixture(), "normal")
        isolated = read_run(self.fixture("i.csv", "isolated"), "isolated")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            compare([normal, normal], [isolated])
