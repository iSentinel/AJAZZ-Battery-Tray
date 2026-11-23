#!/usr/bin/env python3
"""Synthetic regression tests for the offline resource comparison."""

import csv
import tempfile
import unittest
from pathlib import Path

from compare_tray_resources import FIELDS, compare, main, read_run


class ResourceComparisonTests(unittest.TestCase):
    """Validate input checks and calculations with temporary CSV exports."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def fixture(self, name="test.csv", version="0.3.0-beta.50",
                duration=30, cpu=0.3, memory=10485760):
        """Write three controlled samples with a known CPU delta."""
        path = self.root / name
        with path.open("w", encoding="utf-8", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(FIELDS)
            for index in range(3):
                writer.writerow([
                    "2026-11-23T00:00:00Z", version,
                    index * duration / 2, index * cpu / 2, "",
                    memory, memory / 2, 100, 5,
                ])
        return path

    def test_known_metrics(self):
        run = read_run(self.fixture())
        self.assertAlmostEqual(run["cpu_one_core_percent"], 1)
        self.assertEqual(run["working_set_mib"], 10)
        self.assertEqual(run["private_mib"], 5)
        self.assertEqual(run["handles"], 100)

    def test_median_and_delta(self):
        baseline = [
            read_run(self.fixture(f"b{i}.csv", cpu=cpu))
            for i, cpu in enumerate((0.3, 0.6, 0.9))
        ]
        candidate = [
            read_run(self.fixture("c.csv", version="beta.51", cpu=0.3))
        ]
        metric, old, new, delta = compare(baseline, candidate)[0]
        self.assertEqual(metric, "cpu_one_core_percent")
        self.assertAlmostEqual(old, 2)
        self.assertAlmostEqual(new, 1)
        self.assertAlmostEqual(delta, -50)

    def test_zero_baseline(self):
        run = read_run(self.fixture(cpu=0))
        self.assertIsNone(compare([run], [run])[0][3])

    def test_duration_mismatch(self):
        old = read_run(self.fixture("old.csv"))
        new = read_run(self.fixture("new.csv", duration=60))
        with self.assertRaisesRegex(ValueError, "durations"):
            compare([old], [new])

    def test_inconsistent_versions(self):
        old = read_run(self.fixture("old.csv"))
        new = read_run(self.fixture("new.csv", version="different"))
        with self.assertRaisesRegex(ValueError, "single version"):
            compare([old, new], [new])

    def test_nonfinite_input(self):
        with self.assertRaisesRegex(ValueError, "cpu_seconds"):
            read_run(self.fixture(cpu=float("nan")))

    def test_decreasing_cpu(self):
        with self.assertRaises(ValueError):
            read_run(self.fixture(cpu=-1))

    def test_truncated_header(self):
        path = self.root / "bad.csv"
        path.write_text("version,elapsed_seconds\na,0\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "header"):
            read_run(path)

    def test_too_short(self):
        with self.assertRaisesRegex(ValueError, "duration"):
            read_run(self.fixture(duration=10))

    def test_duplicate_input(self):
        path = str(self.fixture())
        self.assertEqual(main(["--baseline", path, "--candidate", path]), 1)

    def test_duplicate_copy(self):
        original = self.fixture("original.csv")
        copy = self.root / "copy.csv"
        copy.write_bytes(original.read_bytes())
        self.assertEqual(main(["--baseline", str(original),
                               "--candidate", str(copy)]), 1)

    def test_malformed_row(self):
        path = self.fixture()
        rows = path.read_text().splitlines()
        rows[1] += ",unrecognized"
        path.write_text("\n".join(rows) + "\n")
        with self.assertRaisesRegex(ValueError, "malformed CSV row"):
            read_run(path)

    def test_invalid_timestamp(self):
        path = self.fixture()
        path.write_text(path.read_text().replace(
            "2026-11-23T00:00:00Z", "not-a-timestamp"))
        with self.assertRaisesRegex(ValueError, "UTC timestamp"):
            read_run(path)

    def test_non_utc_timestamp(self):
        path = self.fixture()
        path.write_text(path.read_text().replace(
            "2026-11-23T00:00:00Z", "2026-11-23T00:00:00+02:00"))
        with self.assertRaisesRegex(ValueError, "UTC timestamp"):
            read_run(path)

    def test_powershell_timestamp_precision(self):
        path = self.fixture()
        path.write_text(path.read_text().replace(
            "2026-11-23T00:00:00Z", "2026-11-23T00:00:00.1234567+00:00"))
        self.assertAlmostEqual(read_run(path)["cpu_one_core_percent"], 1)


if __name__ == "__main__":
    unittest.main()
