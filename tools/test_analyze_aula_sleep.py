"""Offline synthetic tests for three AULA L99 clipboard snapshots."""

import tempfile
from pathlib import Path
import unittest

from analyze_aula_sleep import analyze, parse_summary, read_file


START = "2026-11-23T08:00:00+00:00"
SLEEP = "2026-11-23T09:00:00+00:00"
WAKE = "2026-11-23T10:00:00+00:00"


def summary(now=START, percent=81, known=True, present=True, good=81,
            last_good=START, failures=0, cached=False, automatic=True):
    """Construct only real exported AULA diagnostic field names."""
    return (
        "AULA L99 2.4 GHz experimental battery check\n"
        "Version: 0.3.0-beta.58\n"
        f"Automatic monitoring enabled: {automatic}\n"
        f"Receiver present: {present}\n"
        f"Presence known: {known}\n"
        f"Battery percentage: {percent if percent else 'unavailable'}\n"
        "Status: synthetic test\n"
        f"Last read UTC: {now}\n"
        f"Last successful battery: {good if good else 'unavailable'}; "
        f"UTC: {last_good}; Consecutive no-reply polls: {failures}; "
        f"Cache lifetime hours: 24; Display cache active: {cached}\n"
        "Model identity unverified (dongle IDs shared with S75 Pro).\n"
        "No serial numbers or HID interface paths are included.\n"
    )


def cases():
    """Provide fresh, cached standby and recovered snapshots."""
    awake = parse_summary(summary())
    asleep = parse_summary(summary(now=SLEEP, percent=None, failures=3,
                                   cached=True))
    recovered = parse_summary(summary(now=WAKE, percent=80, good=80,
                                      last_good=WAKE))
    return awake, asleep, recovered


class AulaOfflineSummaryTests(unittest.TestCase):
    """Never invokes hardware, firmware, browser or network access."""

    def test_valid_sleep_recovery(self):
        self.assertEqual(analyze(*cases())[0], "PASS")

    def test_uncertain_presence_hides_cache(self):
        awake, _, recovered = cases()
        asleep = parse_summary(summary(now=SLEEP, percent=None, known=False,
                                       present=False, failures=2))
        result, checks = analyze(awake, asleep, recovered)
        self.assertEqual(result, "NOT OBSERVED")
        self.assertEqual(checks[1][1], "NOT OBSERVED")

    def test_uncertain_presence_exposes_cache_is_failure(self):
        awake, _, recovered = cases()
        asleep = parse_summary(summary(now=SLEEP, percent=None, known=False,
                                       present=False, cached=True))
        self.assertEqual(analyze(awake, asleep, recovered)[0], "FAIL")

    def test_no_reply_loses_last_good(self):
        awake, _, recovered = cases()
        asleep = parse_summary(summary(now=SLEEP, percent=None, good=None,
                                       last_good="never", failures=2))
        self.assertEqual(analyze(awake, asleep, recovered)[0], "FAIL")

    def test_expired_cache_cannot_be_displayed(self):
        awake, _, recovered = cases()
        late = "2026-11-24T09:00:00+00:00"
        asleep = parse_summary(summary(now=late, percent=None, failures=100,
                                       cached=True))
        self.assertEqual(analyze(awake, asleep, recovered)[0], "FAIL")

    def test_future_last_good_is_invalid(self):
        awake, _, recovered = cases()
        asleep = parse_summary(summary(now=SLEEP, percent=None,
                                       last_good=WAKE, failures=3,
                                       cached=True))
        self.assertEqual(analyze(awake, asleep, recovered)[0], "FAIL")

    def test_sleep_cache_absence_is_detected(self):
        awake, _, recovered = cases()
        asleep = parse_summary(summary(now=SLEEP, percent=None, failures=3,
                                       cached=False))
        self.assertEqual(analyze(awake, asleep, recovered)[0], "FAIL")

    def test_sleep_still_replies(self):
        awake, _, recovered = cases()
        asleep = parse_summary(summary(now=SLEEP, percent=80, good=80,
                                       last_good=SLEEP))
        self.assertEqual(analyze(awake, asleep, recovered)[0], "NOT OBSERVED")

    def test_no_wake_reply(self):
        awake, asleep, _ = cases()
        recovered = parse_summary(summary(now=WAKE, percent=None, failures=9,
                                          cached=True))
        self.assertEqual(analyze(awake, asleep, recovered)[0], "FAIL")

    def test_old_recovery_sample_is_not_fresh(self):
        awake, asleep, _ = cases()
        recovered = parse_summary(summary(now=WAKE))
        self.assertEqual(analyze(awake, asleep, recovered)[0], "FAIL")

    def test_mixed_application_versions_are_not_comparable(self):
        awake, asleep, _ = cases()
        recovered = parse_summary(summary(now=WAKE, percent=80, good=80,
                                          last_good=WAKE).replace(
            "Version: 0.3.0-beta.58", "Version: 0.3.0-beta.57"))
        status, checks = analyze(awake, asleep, recovered)
        self.assertEqual(status, "NOT OBSERVED")
        self.assertTrue(any(check[0] == "VERSION" for check in checks))

    def test_auto_disabled_during_sleep_is_not_comparable(self):
        awake, _, recovered = cases()
        asleep = parse_summary(summary(now=SLEEP, percent=None, failures=3,
                                       cached=True, automatic=False))
        self.assertEqual(analyze(awake, asleep, recovered)[0], "NOT OBSERVED")

    def test_equal_sleep_timestamp_is_not_new_poll(self):
        awake, _, recovered = cases()
        asleep = parse_summary(summary(now=START, percent=None, failures=3,
                                       cached=True))
        self.assertEqual(analyze(awake, asleep, recovered)[0], "FAIL")

    def test_equal_wake_timestamp_is_not_new_poll(self):
        awake, asleep, _ = cases()
        recovered = parse_summary(summary(now=SLEEP, good=80, percent=80,
                                          last_good=SLEEP))
        self.assertEqual(analyze(awake, asleep, recovered)[0], "FAIL")

    def test_initial_fresh_measurement_must_match_poll_time(self):
        awake, asleep, recovered = cases()
        older = "2026-11-23T07:58:00+00:00"
        awake = parse_summary(summary(last_good=older))
        self.assertEqual(analyze(awake, asleep, recovered)[0], "FAIL")

    def test_recovery_fresh_measurement_cannot_predate_poll_time(self):
        awake, asleep, _ = cases()
        midway = "2026-11-23T09:30:00+00:00"
        recovered = parse_summary(summary(now=WAKE, good=80, percent=80,
                                          last_good=midway))
        self.assertEqual(analyze(awake, asleep, recovered)[0], "FAIL")

    def test_malformed_summary(self):
        for text in ("", "random network HAR", summary().replace(
                "Presence known: True", "Presence known: not checked")):
            with self.subTest(text=text[:20]), self.assertRaises(ValueError):
                parse_summary(text)

    def test_invalid_battery(self):
        with self.assertRaises(ValueError):
            parse_summary(summary(percent=101))
        with self.assertRaises(ValueError):
            parse_summary(summary().replace(
                "Last successful battery: 81;", "Last successful battery: 0;"))

    def test_local_file_only_and_file_size_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "awake.txt"
            path.write_text(summary(), encoding="utf-8")
            self.assertEqual(read_file(path).percent, 81)
            path.write_text("X" * 65537, encoding="utf-8")
            with self.assertRaises(ValueError):
                read_file(path)


if __name__ == "__main__":
    unittest.main()
