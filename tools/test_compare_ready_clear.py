"""Synthetic complete-matrix checks; no device or network access."""

import os
from pathlib import Path
import tempfile
import unittest

from compare_ready_clear import compare, disagreement, ordinary_field, parse_matrix, ready_clear, read_report
from compare_apex_reports import SECTION


def report(field: int = 100, time: str = "21:22:33",
           omit: tuple[int, int] | None = None,
           altered: tuple[int, int] | None = None) -> str:
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
            lines.append(f"Attempt UTC=2026-11-24T{time}+00:00; delay={delay}ms; TX[{length}]={tx}")
            lines.append(f"GET request buffer[{length}]=" +
                         bytes([5]).ljust(length, bytes(1)).hex().upper())
            lines.append(f"SET F7 / GET 05 ({length} bytes): OK; header={rx[:8]}; no valid battery")
            if omit != (delay, length):
                lines.append(f"RX buffer[{length}]={rx}")
    lines.append("Matrix result: 0/6 valid replies; first valid=unavailable")
    return chr(10).join(lines)


class ReadyClearTests(unittest.TestCase):
    """Compare observations without inferring battery validity."""

    def test_changed_and_unchanged(self) -> None:
        """Distinguish changing and equal unverified fields in full matrices."""
        first = parse_matrix(report())
        self.assertEqual(first[1], 100)
        self.assertEqual(compare(first, parse_matrix(report(98, "21:35:12"))),
                         "CHANGED FIELD")
        self.assertEqual(compare(first, parse_matrix(report(100, "21:35:12"))),
                         "UNCHANGED FIELD")

    def test_missing_and_disagreeing_response(self) -> None:
        """Missing or conflicting replies cannot establish matrix agreement."""
        for text in (report(omit=(30, 65)), report(altered=(250, 67))):
            self.assertIsNone(parse_matrix(text)[1])

    def test_nonmatching_identity(self) -> None:
        """Require revision 0002, one receiver and the expected descriptor size."""
        for before, after in (("0x0002", "0x0300"), ("paths: 1", "paths: 2"),
                              ("Feature report size: 65", "Feature report size: 67")):
            self.assertIsNone(parse_matrix(report().replace(before, after))[1])

    def test_bad_link_and_range(self) -> None:
        """Reject non-ready-clear flags, wrong slots and invalid charge fields."""
        for offset, value in ((1, 1), (3, 0), (3, 101), (4, 2),
                              (5, 1), (6, 0), (7, 3), (9, 1)):
            data = bytearray([5, 0, 0, 100, 1, 0, 1, 2, 0, 0])
            data[offset] = value
            self.assertIsNone(ready_clear(data))

    def test_duplicate_response(self) -> None:
        """Reject multiple RX buffers associated with one probe."""
        lines = report().splitlines()
        index = next(i for i, line in enumerate(lines) if line.startswith("RX buffer"))
        lines.insert(index, lines[index])
        with self.assertRaises(ValueError):
            parse_matrix(chr(10).join(lines))

    def test_duplicate_attempt(self) -> None:
        """Reject repeated attempts at the same timing and length."""
        lines = report().splitlines()
        index = next(i for i, line in enumerate(lines) if line.startswith("Attempt UTC"))
        lines.insert(index, lines[index])
        with self.assertRaises(ValueError):
            parse_matrix(chr(10).join(lines))

    def test_timestamp_and_incomplete(self) -> None:
        """Reject equal timestamps; incomplete later evidence is inconclusive."""
        first = parse_matrix(report())
        with self.assertRaises(ValueError):
            compare(first, first)
        self.assertEqual(compare(first, parse_matrix(report(time="21:35:12",
                                 omit=(30, 65)))), "INCONCLUSIVE")

    def test_wrong_request_and_header(self) -> None:
        """Reject non-F7 requests, wrong GET ID and mismatched RX header."""
        text = report()
        for old, new in (("TX[65]=00F7", "TX[65]=00F6"),
                         ("GET request buffer[65]=05", "GET request buffer[65]=00"),
                         ("header=05000064", "header=05000063")):
            with self.subTest(old=old), self.assertRaises(ValueError):
                parse_matrix(text.replace(old, new, 1))

    def test_failed_or_missing_get(self) -> None:
        """A failed GET or missing request marker cannot establish agreement."""
        text = report()
        self.assertIsNone(parse_matrix(text.replace("): OK; header=", "): FAILED; header=", 1))[1])
        lines = [line for line in text.splitlines()
                 if not line.startswith("GET request buffer")]
        self.assertIsNone(parse_matrix(chr(10).join(lines))[1])

    def test_wrong_order_and_orphan(self) -> None:
        """Reject out-of-order or unassociated response evidence."""
        lines = report().splitlines()
        index = next(i for i, line in enumerate(lines) if line.startswith("RX buffer"))
        lines[index], lines[index - 1] = lines[index - 1], lines[index]
        self.assertIsNone(parse_matrix(chr(10).join(lines))[1])
        lines.insert(8, lines[index - 1])
        with self.assertRaises(ValueError):
            parse_matrix(chr(10).join(lines))

    def test_owner_prefix_replay(self) -> None:
        # Sanitized reconstruction of the two reported times and identical
        # ten-byte prefixes; no claim of independently read device data.
        """Replay two reconstructed owner prefixes without claiming a fresh sample."""
        first = parse_matrix(report(100, "21:22:33"))
        second = parse_matrix(report(100, "21:35:12"))
        self.assertEqual(compare(first, second), "UNCHANGED FIELD")

    @staticmethod
    def with_ordinary(text: str, field: int) -> str:
        """Add a synthetic prior ordinary poll with two matching headers."""
        prefix = chr(10).join([
            "[AJAZZ last ordinary poll — not a fresh request]",
            "Receiver present: True; presence known: True",
            "Battery: unavailable; status: No valid battery status report",
            f"unverified mouse field (not telemetry)={field}",
            "Matching MI_02 paths: 1", "Interface: 3151:5007 MI_02 COL--",
            "USB revision: 0x0002", "Feature report size: 65",
            f"SET F7 / GET 05 (65 bytes): OK; header=050000{field:02X}; no valid battery",
            f"SET F7 / GET 05 (67 bytes): OK; header=050000{field:02X}; no valid battery",
            "[Independent AJAZZ receivers]", SECTION])
        return text.replace(SECTION, prefix)

    def test_ordinary_full_disagreement(self) -> None:
        """Flag a prior ordinary field of 98 against a full matrix of 100."""
        text = self.with_ordinary(report(100), 98)
        self.assertEqual(disagreement(text, parse_matrix(text)), (98, True))

    def test_ordinary_full_agreement(self) -> None:
        """Matching prior and full observations do not flag a conflict."""
        text = self.with_ordinary(report(100), 100)
        self.assertEqual(disagreement(text, parse_matrix(text)), (100, False))

    def test_ordinary_invalid_header(self) -> None:
        """Do not trust the prior field if one stated header disagrees."""
        text = self.with_ordinary(report(100), 98).replace("header=05000062", "header=05000063", 1)
        self.assertIsNone(ordinary_field(text))

    def test_missing_ordinary_is_not_conflict(self) -> None:
        """An absent prior poll is not evidence of a conflicting value."""
        text = report()
        self.assertEqual(disagreement(text, parse_matrix(text)), (None, False))

    def test_local_reader_identity(self) -> None:
        """Preserve BOM and exact cap while rejecting linked/nonregular reports."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "report.txt"
            raw = report().encode("utf-8-sig")
            path.write_bytes(raw + b"\n" * (1048576 - len(raw)))
            self.assertEqual(read_report(path), (parse_matrix(report()), None, False))
            with self.assertRaises(ValueError):
                read_report(root)
            alias = root / "alias.txt"
            os.link(path, alias)
            for linked in (path, alias):
                with self.assertRaises(ValueError):
                    read_report(linked)
            alias.unlink()
            try:
                alias.symlink_to(path)
            except (OSError, NotImplementedError):
                return
            with self.assertRaises(ValueError):
                read_report(alias)

    def test_size_guard(self) -> None:
        """Reject a local full diagnostic report larger than one MiB."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.txt"
            path.write_bytes(b"x" * 1048577)
            with self.assertRaises(ValueError):
                read_report(path)


if __name__ == "__main__":
    unittest.main()
