"""Regression checks for complete product file record policy."""

import struct
import unittest

from verify_inno674_setup_records import check_files, destinations, verify
from verify_inno_ifps import Reader
from verify_inno_setup_records import MIN_VERSION


def field(value: str) -> bytes:
    """Encode a length-prefixed Unicode record field."""
    raw = value.encode('utf-16le')
    return struct.pack('<I', len(raw)) + raw


def records() -> bytes:
    """Build synthetic records with exact reviewed paths and flags."""
    result = bytearray()
    for i, dest in enumerate(destinations()):
        result.extend(b''.join(map(field, ['', dest] + [''] * 14)))
        result.extend(bytes(33) + MIN_VERSION + struct.pack('<iiqhQB',
                      i - 1, 0, 0, -1, 0x800 if i == 0 else 0x20000, int(i == 0)))
    return bytes(result)


class Inno674RecordTests(unittest.TestCase):
    """Require exact ordered destinations and reject truncation."""

    def test_file_records(self) -> None:
        """Require all 16 records and no missing path or flags."""
        raw = records()
        reader = Reader(raw)
        check_files(reader)
        self.assertEqual(reader.pos, len(raw))
        self.assertEqual(len(destinations()), 16)
        for changed in (raw[:-1], raw.replace(field(destinations()[-1]), field('wrong'))):
            with self.assertRaises(ValueError):
                check_files(Reader(changed))

    def test_prior_identity(self) -> None:
        """Reject an unrelated prior evidence document."""
        with self.assertRaises(ValueError):
            verify(b'setup', b'source', b'isl', b'ids', b'compiler', b'{}')


if __name__ == '__main__':
    unittest.main()
