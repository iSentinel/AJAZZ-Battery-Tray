"""Synthetic regressions for scoped Setup.0 framing and header parsing."""

import struct
import unittest
import zlib

from test_verify_inno_inner_engine import block as frame, compressed
from verify_inno_setup_data import COUNTS, SETUP_ID, decode_setup0, header_script, locations


def setup0() -> bytes:
    """Build two framed compressed blocks and an unencrypted header."""
    enc = bytes(49)
    return SETUP_ID + struct.pack('<I', zlib.crc32(enc)) + enc + frame(
        compressed(b'first')) + frame(compressed(b'second'))


class SetupDataTests(unittest.TestCase):
    """Reject corrupt framing, lengths, identity and location records."""

    def test_blocks(self) -> None:
        """Require both exact compressed frames."""
        a, b, report = decode_setup0(setup0())
        self.assertEqual((a, b), (b'first', b'second'))
        self.assertEqual(len(report['blocks']), 2)

    def test_corruption(self) -> None:
        """Reject corrupted header, CRC and trailing bytes."""
        raw = setup0()
        for index in (0, 64, 68, 117, len(raw) - 1):
            changed = bytearray(raw)
            changed[index] ^= 1
            with self.assertRaises(ValueError):
                decode_setup0(bytes(changed))
        with self.assertRaises(ValueError):
            decode_setup0(raw + b'x')

    def test_header(self) -> None:
        """Read code separately from the scoped header and validate counts."""
        fields = [b''] * 43
        fields[0] = 'AJAZZ Battery Tray'.encode('utf-16le')
        fields[9] = '0.3.0-beta.61'.encode('utf-16le')
        fields[42] = b'IFPS' + bytes(24)
        raw = b''.join(struct.pack('<I', len(x)) + x for x in fields)
        raw += struct.pack('<17i', *COUNTS)
        self.assertEqual(header_script(raw)['script_semantics'], 'NOT_VERIFIED')
        for bad in (raw[:-1], b'\xff' * 4 + raw[4:], raw[:-4] + b'\xff' * 4):
            with self.assertRaises(ValueError):
                header_script(bad)

    def test_location_invalid(self) -> None:
        """Reject wrong location record or solid payload extent."""
        with self.assertRaises(ValueError):
            locations(bytes(445), b'zlb\x1a')
        with self.assertRaises(ValueError):
            locations(b'', b'')


if __name__ == '__main__':
    unittest.main()
