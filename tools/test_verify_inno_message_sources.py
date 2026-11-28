"""Synthetic English message source and reviewed appearance comparisons."""

import struct
import unittest
import zlib

from verify_inno_message_sources import compare_content, compare_sources, expected_body, expected_options
from verify_inno_messages import COUNT, HEADER


def inputs() -> tuple[bytes, bytes, bytes]:
    """Construct ordered IDs, reverse-order ISL and matching framed messages."""
    ids = ('TSetupMessageID = (' + ','.join(f'msgM{i}' for i in range(COUNT)) + ');').encode()
    isl = ('[Messages]\n' + '\n'.join(f'M{i}=Value{i}%n' for i in reversed(range(COUNT)))).encode()
    body = expected_body(isl, ids)
    total = 80 + len(body)
    raw = HEADER + struct.pack('<IIII', COUNT, total, total ^ 0xffffffff, zlib.crc32(body))
    return raw + body + expected_options(), isl, ids


class MessageSourceTests(unittest.TestCase):
    """Reject source, order, content and appearance changes."""

    def test_source_order_and_newline(self) -> None:
        """Recreate enum order instead of file order and expand CR/LF."""
        raw, isl, ids = inputs()
        self.assertTrue(expected_body(isl, ids).startswith('Value0\r\n\0'.encode('utf-16le')))
        result = compare_content(raw, isl, ids)
        self.assertEqual(result['message_semantics'], 'MATCH_PINNED_ENGLISH_TEXT')

    def test_source_mismatch(self) -> None:
        """Reject duplicate keys, enum IDs and changed message text."""
        raw, isl, ids = inputs()
        for changed in (isl + b'\nM0=Duplicate', isl.replace(b'Value0%', b'Other0%')):
            with self.assertRaises(ValueError):
                compare_content(raw, changed, ids)
        with self.assertRaises(ValueError):
            compare_content(raw, isl, ids.replace(b'msgM1,', b'msgM0,'))

    def test_options_and_pinning(self) -> None:
        """Reject changed appearance and unreviewed source digests."""
        raw, isl, ids = inputs()
        with self.assertRaises(ValueError):
            compare_content(raw[:-1] + b'\x23', isl, ids)
        with self.assertRaises(ValueError):
            compare_sources(raw, isl, ids, b'synthetic script')


if __name__ == '__main__':
    unittest.main()
