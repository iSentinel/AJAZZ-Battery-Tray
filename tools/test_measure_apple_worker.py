"""Offline regression tests for the Apple startup measurement helper."""
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import measure_apple_worker as worker


class AppleWorkerTests(unittest.TestCase):
    """Use mocked subprocess responses; no actual device or app required."""

    def test_nearest_rank(self):
        self.assertEqual(worker.quantile(list(range(1, 21)), .95), 19)

    @patch("measure_apple_worker.subprocess.run")
    def test_fixed_sample(self, run):
        run.return_value = subprocess.CompletedProcess(
            [], 0, json.dumps(worker.EXPECTED).encode(), b"",
        )
        elapsed, count = worker.measure(Path("/app"), 5)
        self.assertGreaterEqual(elapsed, 0)
        self.assertGreater(count, 0)
        run.assert_called_once_with(
            [str(Path("/app")), "--internal-poll-sample"],
            capture_output=True, check=True, timeout=5,
        )

    @patch("measure_apple_worker.subprocess.run")
    def test_reject_real_or_malformed_data(self, run):
        for payload in (b'{"percent":83}', b"invalid"):
            run.return_value = subprocess.CompletedProcess([], 0, payload, b"")
            with self.assertRaises(ValueError):
                worker.measure(Path("/app"), 5)

    @patch("measure_apple_worker.subprocess.run")
    def test_timeout(self, run):
        run.side_effect = subprocess.TimeoutExpired(["app"], 5)
        with self.assertRaises(subprocess.TimeoutExpired):
            worker.measure(Path("/app"), 5)

    @patch("measure_apple_worker.measure", return_value=(10.5, 60))
    def test_csv_and_no_overwrite(self, measure):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "worker.csv"
            self.assertEqual(worker.collect(Path("/app"), output, 5, 5),
                             [10.5] * 5)
            before = output.read_bytes()
            self.assertEqual(len(before.splitlines()), 6)
            with self.assertRaises(FileExistsError):
                worker.collect(Path("/app"), output, 5, 5)
            self.assertEqual(output.read_bytes(), before)
            self.assertEqual(measure.call_count, 5)

    @patch("measure_apple_worker.measure")
    def test_dry_run(self, measure):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "worker.csv"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(worker.main([
                    "--dry-run", "--output", str(output),
                ]), 0)
            self.assertFalse(output.exists())
            measure.assert_not_called()


if __name__ == "__main__":
    unittest.main()
