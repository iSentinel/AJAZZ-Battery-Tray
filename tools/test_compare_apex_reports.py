"""Synthetic regression cases for offline APEX report analysis."""

import unittest
from compare_apex_reports import legacy_percent, vendor_candidate, read_attempts, SECTION


class ApexComparisonTests(unittest.TestCase):
    """No hardware or network needed."""

    def test_legacy(self):
        self.assertEqual(legacy_percent(bytes([5, 0, 0, 83])), 83)
        self.assertIsNone(legacy_percent(bytes([5, 1, 0, 83])))

    def test_vendor_alternative(self):
        data = bytes([5, 1, 54, 83, 0, 0, 1, 3, 0, 0])
        self.assertIsNone(legacy_percent(data))
        self.assertEqual(vendor_candidate(data), ("candidate-only", 83))

    def test_offline_and_boot(self):
        self.assertEqual(vendor_candidate(bytes([5, 1, 0, 83, 0, 1, 1, 2, 0, 0]))[1], None)
        self.assertEqual(vendor_candidate(bytes([5, 1, 0, 83, 0, 0, 1, 2, 0, 1]))[1], None)

    def test_invalid_or_nonmouse(self):
        self.assertIsNone(vendor_candidate(bytes([5, 1, 0, 101, 0, 0, 1, 2, 0, 0]))[1])
        self.assertIsNone(vendor_candidate(bytes([5, 1, 0, 83, 0, 0, 1, 1, 0, 0]))[1])
        self.assertIsNone(vendor_candidate(bytes([5, 0, 0, 83]))[1])

    def test_capture_section(self):
        report = ("RX buffer[4]=05000064\n" + SECTION +
                  "\n[Receiver #1]\n  Attempt UTC=example; delay=30ms; TX[4]=00F70000\n"
                  "  RX buffer[4]=05000053\n")
        self.assertEqual(list(read_attempts(report)), [
            ("1", 30, 4, None), ("1", 30, 4, bytes.fromhex("05000053"))])

    def test_aj179_reference_prefix(self):
        """Reconstruct the observed status prefix; do not store raw captures."""
        prefix = bytes([5, 0, 0, 100, 1, 0, 1, 2, 0, 0])
        for size in (65, 67):
            with self.subTest(size=size):
                data = prefix.ljust(size, b"\x00")
                self.assertEqual(legacy_percent(data), 100)
                self.assertEqual(vendor_candidate(data), ("candidate-only", 100))

    def test_aj179_bridge_flags(self):
        """Observed flag variants; normalization is offline hypothetical only."""
        for ready, send, count in ((0, 1, 258), (1, 1, 6), (0, 0, 2)):
            with self.subTest(ready=ready, send=send, count=count):
                bridge = bytes([0, ready, 0, 100, 1, 0, send, 2, 0, 0])
                self.assertIsNone(legacy_percent(bridge))
                self.assertIsNone(vendor_candidate(bridge)[1])
                windows = bytes([5]) + bridge[1:]
                self.assertEqual(legacy_percent(windows), None if ready else 100)
                self.assertEqual(vendor_candidate(windows), ("candidate-only", 100))

    def test_malformed(self):
        with self.assertRaises(ValueError):
            list(read_attempts("no capture"))
        with self.assertRaises(ValueError):
            list(read_attempts(SECTION +
                 "\n  Attempt UTC=example; delay=30ms; TX[65]=00F7\n  RX buffer[65]=05000053"))


if __name__ == "__main__":
    unittest.main()
