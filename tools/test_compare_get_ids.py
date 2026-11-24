"""Synthetic tests of redacted GET-ID pair association."""
import unittest
from compare_get_ids import MODE, END, parse, summarize


def fixture(missing=False, changed=False):
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

    def test_complete_same_status(self):
        self.assertEqual(len(parse(fixture())), 12)
        self.assertTrue(all(row[-1] == "SAME STATUS BYTES"
                            for row in summarize(parse(fixture()))))

    def test_different_status(self):
        self.assertTrue(all(row[-1] == "DIFFERENT STATUS BYTES"
                            for row in summarize(parse(fixture(changed=True)))))

    def test_missing_reply(self):
        self.assertEqual(summarize(parse(fixture(missing=True)))[0][-1],
                         "INCOMPLETE")

    def test_timeout(self):
        self.assertIsNone(parse(fixture().replace(END, "TIMEOUT: worker exceeded 40s")))

    def test_multiple_receivers_inconclusive(self):
        self.assertIsNone(parse(fixture().replace("found 1", "found 2")))

    def test_duplicate_probe_rejected(self):
        marker = "PAIR: delay=30ms length=65 request=05"
        with self.assertRaises(ValueError):
            parse(fixture().replace(marker, marker + "\n" + marker))

    def test_wrong_association_rejected(self):
        with self.assertRaises(ValueError):
            parse(fixture().replace("request=05 returned=05", "request=00 returned=05", 1))

    def test_wrong_returned_id_rejected(self):
        with self.assertRaises(ValueError):
            parse(fixture().replace("returned=05", "returned=00", 1))
