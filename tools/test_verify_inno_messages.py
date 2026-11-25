"""Synthetic message structure and corruption regressions."""

import struct
import unittest
import zlib

from verify_inno_messages import COUNT, HEADER, LANG_ID, OPTIONS_SIZE, verify_messages


def block(body: bytes | None = None, count: int = COUNT) -> bytes:
    """Build a scoped block with valid header and CRC."""
    if body is None:
        body = ('Example\0' * COUNT).encode('utf-16le')
    total = 80 + len(body)
    return (HEADER + struct.pack('<IIII', count, total, total ^ 0xffffffff,
                                 zlib.crc32(body)) + body
            + LANG_ID.ljust(OPTIONS_SIZE, b'\0'))


class MessageBlockTests(unittest.TestCase):
    """Reject corrupt framing without claiming message provenance."""

    def test_valid(self) -> None:
        """Check structure and explicit non-verification of meaning."""
        result = verify_messages(block())
        self.assertEqual(result['count'], COUNT)
        self.assertEqual(result['structure'], 'MATCH')
        self.assertEqual(result['message_semantics'], 'NOT_VERIFIED')

    def test_corruption(self) -> None:
        """Reject changes to ID, sizes, CRC, body and options marker."""
        raw = block()
        for offset in (0, 64, 68, 72, 76, 80, len(raw) - OPTIONS_SIZE):
            damaged = bytearray(raw)
            damaged[offset] ^= 1
            with self.assertRaises(ValueError):
                verify_messages(bytes(damaged))

    def test_text_and_extent(self) -> None:
        """Reject wrong count, malformed UTF-16, missing terminator and extras."""
        for raw in (block(count=COUNT + 1), block(b'a\0'),
                    block(b'\x00\xd8'), block()[:-1], block() + b'x',
                    block(('x\0' * COUNT + 'x').encode('utf-16le'))):
            with self.assertRaises(ValueError):
                verify_messages(raw)


if __name__ == '__main__':
    unittest.main()
