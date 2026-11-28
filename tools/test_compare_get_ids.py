"""Synthetic tests of redacted GET-ID pair association."""
from contextlib import redirect_stderr, redirect_stdout
import io
import os
from pathlib import Path
import tempfile
import unittest
from compare_get_ids import MODE, END, LIMIT, OUTCOME, main, parse, summarize


def fixture(missing: bool = False, changed: bool = False) -> str:
    """Build the documented 65/67-byte comparison matrix."""
    lines = ["BEGIN: UTC=2026-11-24T00:00:00Z timeout=40s", MODE,
             "STEP: found 1 matching MI_02 paths",
             "STEP: experimental receiver #1"]
    for delay in (30, 100, 250):
        for length in (65, 67):
            for report in ("05", "00"):
                lines.append(f"PAIR: delay={delay}ms length={length} request={report}")
                if missing and (delay, length, report) == (30, 65, "00"):
                    continue
                prefix = report + ("010053010001020000" if changed and report == "05"
                                   else "000000010001020000")
                lines.append(f"OBSERVED: request={report} returned={report} "
                             f"length={length} delay={delay}ms status10={prefix}; "
                             "existing-parser candidate=unavailable (not telemetry)")
    return "\n".join(lines + [
        "INCONCLUSIVE: experimental GET ID comparison; no battery claimed", END])


class GetIdTests(unittest.TestCase):
    """No HID or live logs are required for these tests."""

    def test_complete_same_status(self) -> None:
        """Require twelve observations and identical non-ID status bytes."""
        self.assertEqual(len(parse(fixture())), 12)
        self.assertTrue(all(row[-1] == "SAME STATUS BYTES"
                            for row in summarize(parse(fixture()))))

    def test_different_status(self) -> None:
        """Detect distinct payloads even when report IDs are expected."""
        self.assertTrue(all(row[-1] == "DIFFERENT STATUS BYTES"
                            for row in summarize(parse(fixture(changed=True)))))

    def test_missing_reply(self) -> None:
        """An unanswered probe leaves its timing/length pair incomplete."""
        self.assertEqual(summarize(parse(fixture(missing=True)))[0][-1],
                         "INCOMPLETE")

    def test_timeout(self) -> None:
        """A timed-out experimental worker cannot establish a complete matrix."""
        self.assertIsNone(parse(fixture().replace(END, "TIMEOUT: worker exceeded 40s")))

    def test_multiple_receivers_inconclusive(self) -> None:
        """Reject comparison scope with more than one receiver."""
        self.assertIsNone(parse(fixture().replace("found 1", "found 2")))

    def test_duplicate_probe_rejected(self) -> None:
        """Reject a repeated delay, length and report-ID probe."""
        marker = "PAIR: delay=30ms length=65 request=05"
        with self.assertRaises(ValueError):
            parse(fixture().replace(marker, marker + "\n" + marker))

    def test_wrong_association_rejected(self) -> None:
        """Reject observations assigned to the wrong requested report ID."""
        with self.assertRaises(ValueError):
            parse(fixture().replace("request=05 returned=05", "request=00 returned=05", 1))

    def test_wrong_returned_id_rejected(self) -> None:
        """Require the observed prefix to match the stated returned ID."""
        with self.assertRaises(ValueError):
            parse(fixture().replace("returned=05", "returned=00", 1))


    def test_session_framing(self) -> None:
        """Reject ambiguous experimental starts, modes and terminal outcomes."""
        valid = fixture()
        invalid = ("prefix\n" + valid, valid.replace("00Z", "00+02:00"),
                   valid.replace(MODE, MODE + "\nMODE: other"),
                   valid.replace(OUTCOME, ""),
                   valid.replace(OUTCOME, OUTCOME + "\n" + OUTCOME),
                   valid.replace(OUTCOME, OUTCOME + "\nSTEP: extra"),
                   valid.replace("found 1 matching MI_02 paths",
                                 "found 1 matching MI_02 paths\nSTEP: found 2 matching MI_02 paths"),
                   valid + "\nTIMEOUT: worker exceeded 40s",
                   valid.replace(END, "TIMEOUT: worker exceeded 40s\nTIMEOUT: repeated"),
                   valid.replace(OUTCOME, "PASS: verified battery 83%").replace(
                       END, "TIMEOUT: worker exceeded 40s"))
        for text in invalid:
            with self.subTest(text=text[-90:]), self.assertRaises(ValueError):
                parse(text)
        self.assertIsNone(parse(valid.replace(OUTCOME + "\n" + END,
                                              "TIMEOUT: worker exceeded 40s")))

    def test_cli_local_evidence_reader(self) -> None:
        """Preserve exit codes and BOM while refusing linked/oversized input."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "capture.txt"
            path.write_bytes(fixture().encode("utf-8-sig"))
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--log", str(path)]), 0)
                self.assertEqual(main(["--log", str(root)]), 1)
                alias = root / "alias.txt"
                os.link(path, alias)
                self.assertEqual(main(["--log", str(path)]), 1)
                self.assertEqual(main(["--log", str(alias)]), 1)
                alias.unlink()
                path.write_bytes(b"Z" * (LIMIT + 1))
                self.assertEqual(main(["--log", str(path)]), 1)
                try:
                    alias.symlink_to(path)
                except OSError:
                    return
                self.assertEqual(main(["--log", str(alias)]), 1)
