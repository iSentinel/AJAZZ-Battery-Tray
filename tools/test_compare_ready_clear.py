"""Synthetic complete-matrix checks; no device or network access."""

from pathlib import Path
import tempfile
import unittest

from compare_ready_clear import compare, parse_matrix, ready_clear, read_report
from compare_apex_reports import SECTION


def report(field=100, time="21:22:33", omit=None, altered=None):
    """Reconstruct only the observed 10-byte prefix, not the private capture."""
    lines = ["AJAZZ APEX full comparison report (one capture)",
             f"UTC: 2026-11-24T{time}+00:00", SECTION,
             "Matching MI_02 paths: 1", "[Receiver #1]",
             "Interface: 3151:5007 MI_02 COL--", "USB revision: 0x0002",
             "Feature report size: 65", "Usage: FFFF:0002; input=0; output=0"]
    for delay in (30, 100, 250):
        for length in (65, 67):
            prefix = bytes([5, 0, 0, field, 1, 0, 1, 2, 0, 0])
            if altered == (delay, length):
                prefix = bytes([5, 0, 0, 99, 1, 0, 1, 2, 0, 0])
            tx = bytes([0, 247]).ljust(length, bytes(1)).hex().upper()
            rx = prefix.ljust(length, bytes(1)).hex().upper()
            lines.append(f"Attempt UTC=example; delay={delay}ms; TX[{length}]={tx}")
            if omit != (delay, length):
                lines.append(f"RX buffer[{length}]={rx}")
    lines.append("Matrix result: 0/6 valid replies; first valid=unavailable")
    return chr(10).join(lines)


class ReadyClearTests(unittest.TestCase):
    """Compare observations without inferring battery validity."""

    def test_changed_and_unchanged(self):
        first = parse_matrix(report())
        self.assertEqual(first[1], 100)
        self.assertEqual(compare(first, parse_matrix(report(98, "21:35:12"))),
                         "CHANGED FIELD")
        self.assertEqual(compare(first, parse_matrix(report(100, "21:35:12"))),
                         "UNCHANGED FIELD")

    def test_missing_and_disagreeing_response(self):
        for text in (report(omit=(30, 65)), report(altered=(250, 67))):
            self.assertIsNone(parse_matrix(text)[1])

    def test_nonmatching_identity(self):
        for before, after in (("0x0002", "0x0300"), ("paths: 1", "paths: 2"),
                              ("Feature report size: 65", "Feature report size: 67")):
            self.assertIsNone(parse_matrix(report().replace(before, after))[1])

    def test_bad_link_and_range(self):
        for offset, value in ((1, 1), (3, 0), (3, 101), (4, 2),
                              (5, 1), (6, 0), (7, 3), (9, 1)):
            data = bytearray([5, 0, 0, 100, 1, 0, 1, 2, 0, 0])
            data[offset] = value
            self.assertIsNone(ready_clear(data))

    def test_duplicate_response(self):
        lines = report().splitlines()
        index = next(i for i, line in enumerate(lines) if line.startswith("RX buffer"))
        lines.insert(index, lines[index])
        with self.assertRaises(ValueError):
            parse_matrix(chr(10).join(lines))

    def test_duplicate_attempt(self):
        lines = report().splitlines()
        index = next(i for i, line in enumerate(lines) if line.startswith("Attempt UTC"))
        lines.insert(index, lines[index])
        with self.assertRaises(ValueError):
            parse_matrix(chr(10).join(lines))

    def test_timestamp_and_incomplete(self):
        first = parse_matrix(report())
        with self.assertRaises(ValueError):
            compare(first, first)
        self.assertEqual(compare(first, parse_matrix(report(time="21:35:12",
                                 omit=(30, 65)))), "INCONCLUSIVE")

    def test_size_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.txt"
            path.write_bytes(b"x" * 1048577)
            with self.assertRaises(ValueError):
                read_report(path)


if __name__ == "__main__":
    unittest.main()
