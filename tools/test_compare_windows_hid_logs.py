"""Synthetic checks for the safe Windows F7/05 text log comparator."""

import os
import tempfile
from pathlib import Path
import unittest

from compare_windows_hid_logs import classify, compare, parse_log, read_capture


BEGIN = "BEGIN: UTC=2026-11-23T18:00:00+00:00 timeout=40s"
OPEN = "STEP: HID open succeeded"
SET_OK = "STEP: SET F7 OK Win32=0 elapsed=2ms"
GET_OK = "STEP: GET 05 OK Win32=0 elapsed=4ms"


def report(*extra: str, end: int | None = 2) -> str:
    """Build only the documented beta.57+ log markers."""
    lines = [BEGIN, "STEP: worker started (local-only, no serial numbers)",
             "STEP: found 1 matching MI_02 paths", OPEN, SET_OK, GET_OK]
    lines.extend(extra)
    if end is not None:
        lines.append(f"END: worker exited {end}")
    return "\n".join(lines) + "\n"


class WindowsHidLogTests(unittest.TestCase):
    """No device, network, data capture or subprocess is invoked."""

    def test_two_verified_reports(self) -> None:
        """Accept two completed logs with verified in-range readings."""
        first = parse_log(report("PASS: verified battery 83%", end=0))
        second = parse_log(report("PASS: verified battery 82%", end=0))
        self.assertEqual(compare([("AWAKE", first), ("SLEEP", second)])[0],
                         "PASS")

    def test_missing_battery_is_inconclusive(self) -> None:
        """A completed no-battery worker is not a verified result."""
        awake = parse_log(report("PASS: verified battery 83%", end=0))
        sleep = parse_log(report("INCONCLUSIVE: no verified battery report"))
        outcome, rows = compare([("AWAKE", awake), ("AFTER SLEEP", sleep)])
        self.assertEqual(outcome, "INCONCLUSIVE")
        self.assertIn("UNVERIFIED", rows[1])

    def test_timeout_without_end(self) -> None:
        """Recognize timeout evidence without claiming worker completion."""
        text = "\n".join([BEGIN, "STEP: worker started",
                          "STEP: SET F7 begin length=65",
                          "TIMEOUT: HID worker exceeded 40s; no level claimed"])
        capture = parse_log(text)
        self.assertTrue(capture.timed_out)
        self.assertEqual(classify(capture)[0], "TIMEOUT")

    def test_no_receiver(self) -> None:
        """Distinguish no enumerated receiver from other read failures."""
        text = "\n".join([BEGIN, "STEP: found 0 matching MI_02 paths",
                          "INCONCLUSIVE: no verified battery report",
                          "END: worker exited 2"])
        self.assertEqual(classify(parse_log(text))[0], "NO RECEIVER")

    def test_open_error(self) -> None:
        """Distinguish a failed HID open from a missing receiver."""
        text = "\n".join([BEGIN, "STEP: found 1 matching MI_02 paths",
                          "STEP: HID open failed",
                          "INCONCLUSIVE: no verified battery report",
                          "END: worker exited 2"])
        self.assertEqual(classify(parse_log(text))[0], "OPEN FAILED")

    def test_set_and_get_failure(self) -> None:
        """Classify the furthest successful stage of a failed HID chain."""
        text = report("STEP: SET F7 FAILED Win32=5 elapsed=2ms",
                      "INCONCLUSIVE: no verified battery report")
        self.assertEqual(classify(parse_log(text))[0], "UNVERIFIED")
        set_fail = "\n".join([BEGIN, OPEN,
                              "STEP: SET F7 FAILED Win32=5 elapsed=2ms",
                              "INCONCLUSIVE: no verified battery report",
                              "END: worker exited 2"])
        self.assertEqual(classify(parse_log(set_fail))[0], "SET FAILED")
        get_fail = "\n".join([BEGIN, OPEN, SET_OK,
                              "STEP: GET 05 FAILED Win32=1167 elapsed=10ms",
                              "INCONCLUSIVE: no verified battery report",
                              "END: worker exited 2"])
        self.assertEqual(classify(parse_log(get_fail))[0], "GET FAILED")

    def test_worker_error(self) -> None:
        """An explicit worker failure yields an overall failure result."""
        capture = parse_log("\n".join([BEGIN, "FAIL: worker IOException",
                                       "END: worker exited 1"]))
        self.assertEqual(classify(capture)[0], "ERROR")
        self.assertEqual(compare([("AWAKE", capture)])[0], "FAIL")

    def test_reject_fabricated_verified_battery(self) -> None:
        """Reject success without an I/O chain and out-of-range values."""
        with self.assertRaises(ValueError):
            parse_log("\n".join([BEGIN, "PASS: verified battery 83%",
                                 "END: worker exited 0"]))
        with self.assertRaises(ValueError):
            parse_log(report("PASS: verified battery 0%", end=0))
        with self.assertRaises(ValueError):
            parse_log(report("PASS: verified battery 101%", end=0))

    def test_reject_partial_verified_operation_chain(self) -> None:
        """Require all enumeration, open, SET and GET evidence."""
        for missing in ("STEP: found 1 matching MI_02 paths",
                        "STEP: HID open succeeded", SET_OK, GET_OK):
            with self.subTest(missing=missing):
                text = report("PASS: verified battery 83%", end=0)
                text = text.replace(missing + "\n", "")
                with self.assertRaises(ValueError):
                    parse_log(text)

    def test_reject_contradictory_exit(self) -> None:
        """Reject inconsistent verified, timeout and terminal markers."""
        with self.assertRaises(ValueError):
            parse_log(report("PASS: verified battery 80%", end=2))
        with self.assertRaises(ValueError):
            parse_log(report("TIMEOUT: worker timed out", end=0))
        with self.assertRaises(ValueError):
            parse_log("\n".join([BEGIN, "INCONCLUSIVE: no reply"]))

    def test_duplicate_and_malformed_singleton_markers(self) -> None:
        """Reject repeated summaries but preserve repeated native operations."""
        valid = report("PASS: verified battery 83%", end=0)
        for original in (BEGIN, "STEP: found 1 matching MI_02 paths",
                         "PASS: verified battery 83%", "END: worker exited 0"):
            with self.subTest(marker=original):
                with self.assertRaises(ValueError):
                    parse_log(valid.replace(original, original + "\n" + original))
        for malformed in ("STEP: found invalid", "PASS: invalid", "END: invalid"):
            with self.subTest(marker=malformed), self.assertRaises(ValueError):
                parse_log(valid.replace(OPEN, OPEN + "\n" + malformed))
        self.assertEqual(parse_log(valid.replace(GET_OK, GET_OK + "\n" + SET_OK + "\n" + GET_OK)).battery, 83)

    def test_terminal_order_and_conflicting_outcomes(self) -> None:
        """Prevent ambiguous final results from qualifying as verified."""
        valid = report("PASS: verified battery 83%", end=0)
        invalid = (valid + GET_OK + "\n", GET_OK + "\n" + valid,
                   report("INCONCLUSIVE: no reply", "PASS: verified battery 83%", end=0),
                   report("FAIL: worker IOException", "PASS: verified battery 83%", end=0),
                   report("INCONCLUSIVE: no reply", end=1),
                   report("FAIL: worker IOException", end=2),
                   report("INCONCLUSIVE: no reply", "INCONCLUSIVE: no reply"),
                   report("TIMEOUT: expired", "TIMEOUT: expired", end=None))
        for text in invalid:
            with self.subTest(text=text[-90:]), self.assertRaises(ValueError):
                parse_log(text)
        # Worker may report no battery just before the parent's deadline.
        timeout = report("INCONCLUSIVE: no reply", "TIMEOUT: expired", end=None)
        self.assertEqual(classify(parse_log(timeout))[0], "TIMEOUT")

    def test_verified_operation_order(self) -> None:
        """Reject unordered or cross-open transfers in verified reports."""
        count = "STEP: found 1 matching MI_02 paths"
        passed = "PASS: verified battery 83%"
        terminal = "END: worker exited 0"
        failed_open = "STEP: HID open failed"
        invalid = ((OPEN, count, SET_OK, GET_OK, passed),
                   (count, OPEN, GET_OK, SET_OK, passed),
                   (count, OPEN, SET_OK, failed_open, OPEN, GET_OK, passed),
                   (count, OPEN, SET_OK, passed, GET_OK),
                   (count, OPEN, SET_OK, GET_OK, passed, SET_OK),
                   (count, OPEN, SET_OK, GET_OK.replace("Win32=0", "Win32=5"), passed),
                   (count, OPEN, SET_OK, GET_OK, GET_OK, passed))
        for events in invalid:
            with self.subTest(events=events), self.assertRaises(ValueError):
                parse_log("\n".join((BEGIN, *events, terminal)))
        valid = (count, OPEN, SET_OK, GET_OK, failed_open, passed)
        self.assertEqual(parse_log("\n".join((BEGIN, *valid, terminal))).battery, 83)

    def test_local_file_size_guard(self) -> None:
        """Accept a small local report and reject one above the size limit."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.txt"
            path.write_text(report("PASS: verified battery 83%", end=0))
            self.assertEqual(read_capture(path).battery, 83)
            path.write_text("Z" * 1048577)
            with self.assertRaises(ValueError):
                read_capture(path)


    def test_bounded_local_file_identity(self) -> None:
        """Accept exact-cap UTF-8 BOM logs but refuse linked/nonregular files."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "capture.txt"
            raw = report("PASS: verified battery 83%", end=0).encode("utf-8-sig")
            path.write_bytes(raw + b"\n" * (1048576 - len(raw)))
            self.assertEqual(read_capture(path).battery, 83)
            with self.assertRaises(ValueError):
                read_capture(root)
            alias = root / "alias.txt"
            os.link(path, alias)
            for linked in (path, alias):
                with self.assertRaises(ValueError):
                    read_capture(linked)
            alias.unlink()
            try:
                alias.symlink_to(path)
            except OSError:
                return  # Windows runner may not grant symlink creation.
            with self.assertRaises(ValueError):
                read_capture(alias)


if __name__ == "__main__":
    unittest.main()
