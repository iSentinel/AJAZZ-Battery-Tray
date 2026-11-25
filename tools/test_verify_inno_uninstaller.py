"""Synthetic uninstaller mode, PE equality and message framing regressions."""
import struct
import unittest

from compare_inno_loader import digest
from test_compare_inno_loader import loader
from verify_inno_uninstaller import (
    APP_ID, MODE_OFFSET, MODE_UNINSTALL, TAIL_ID, MAX_MESSAGES, attribute,
)


def example(messages: bytes = b'messages') -> tuple[bytes, bytes]:
    """Create a synthetic PE and append the documented uninstaller frame."""
    engine = loader()
    exe = bytearray(engine)
    struct.pack_into('<I', exe, MODE_OFFSET, MODE_UNINSTALL)
    exe += bytes.fromhex(digest(APP_ID.encode('utf-16le')))
    exe += messages
    exe += struct.pack('<Iq', TAIL_ID, len(engine) + 32)
    return engine, bytes(exe)


class UninstallerAttributionTests(unittest.TestCase):
    """Require exact image and bounded framing without claiming semantics."""

    def test_exact_pe(self) -> None:
        """All original bytes except mode must match."""
        engine, exe = example()
        result = attribute(engine, exe)
        self.assertEqual(result['pe_except_mode'], 'MATCH')
        self.assertEqual(result['message_semantics'], 'NOT_VERIFIED')

    def test_changed_bytes(self) -> None:
        """Reject changed marker, header, PE payload or AppId hash."""
        engine, exe = example()
        for offset in (MODE_OFFSET, 52, len(engine) - 1, len(engine)):
            damaged = bytearray(exe)
            damaged[offset] ^= 1
            with self.assertRaises(ValueError):
                attribute(engine, bytes(damaged))

    def test_invalid_tail(self) -> None:
        """Reject incorrect tail identifiers and message offsets."""
        engine, exe = example()
        for tail in (struct.pack('<Iq', 0, len(engine) + 32),
                     struct.pack('<Iq', TAIL_ID, len(engine) + 31),
                     struct.pack('<Iq', TAIL_ID, -1)):
            with self.assertRaises(ValueError):
                attribute(engine, exe[:-12] + tail)

    def test_bounds(self) -> None:
        """Reject absent or oversized message blocks and engine overlays."""
        for messages in (b'', b'x' * (MAX_MESSAGES + 1)):
            engine, exe = example(messages)
            with self.assertRaises(ValueError):
                attribute(engine, exe)
        engine, exe = example()
        with self.assertRaises(ValueError):
            attribute(engine + b'x', exe)


if __name__ == '__main__':
    unittest.main()
