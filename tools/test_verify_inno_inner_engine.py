"""Synthetic bounds, CRC, LZMA and relative-address transform regressions."""

import lzma
import struct
import unittest
import zlib

from compare_inno_loader import compare
from test_compare_inno_loader import loader
from verify_inno_inner_engine import (
    CHUNK, MAX_ENGINE, TABLE_ID, chunk_stream, decompress,
    offset_record, reverse_calls,
)


def record(exe: int = 9000, decoded: int = 5000) -> bytes:
    """Build an exact synthetic v2 offset record."""
    data = struct.pack('<12sIqqIIqqI', TABLE_ID, 2, 10000,
                       exe, decoded, 1, 8000, 1000, 0)
    return data + struct.pack('<I', zlib.crc32(data))


def block(data: bytes) -> bytes:
    """Frame synthetic bytes with the documented block and chunk CRCs."""
    chunks = b''.join(struct.pack('<I', zlib.crc32(data[i:i + CHUNK])) +
                      data[i:i + CHUNK] for i in range(0, len(data), CHUNK))
    header = struct.pack('<qB', len(chunks), 1)
    return struct.pack('<I', zlib.crc32(header)) + header + chunks


def compressed(data: bytes) -> bytes:
    """Generate a raw LZMA1 stream with explicit properties and EOS."""
    dictionary = 65536
    raw = lzma.compress(data, format=lzma.FORMAT_RAW, filters=[{
        'id': lzma.FILTER_LZMA1, 'dict_size': dictionary,
        'lc': 3, 'lp': 0, 'pb': 2}])
    return bytes([93]) + struct.pack('<I', dictionary) + raw


class InnerEngineTests(unittest.TestCase):
    """Reject corrupted framing and recover only exact bounded streams."""

    def test_offset_bounds_and_crc(self) -> None:
        """Check exact extent, offset ordering and decoded size."""
        self.assertEqual(offset_record(record(), 10000, 1000)['engine_offset'], 9000)
        damaged = bytearray(record())
        damaged[-1] ^= 1
        for bad in (bytes(damaged), record(7000), record(decoded=MAX_ENGINE + 1),
                    record()[:-1]):
            with self.assertRaises(ValueError):
                offset_record(bad, 10000, 1000)
        with self.assertRaises(ValueError):
            offset_record(record(), 10000, 999)

    def test_chunk_crc_and_extent(self) -> None:
        """Check every chunk, including a short final chunk."""
        data = b'x' * (CHUNK + 7)
        valid = block(data)
        self.assertEqual(chunk_stream(valid, 0), (data, 2))
        for offset in (0, 17, len(valid) - 1):
            bad = bytearray(valid)
            bad[offset] ^= 1
            with self.assertRaises(ValueError):
                chunk_stream(bytes(bad), 0)
        with self.assertRaises(ValueError):
            chunk_stream(valid + b'x', 0)

    def test_lzma_terminal_and_budget(self) -> None:
        """Require exact output, dictionary budget, EOS and no trailing data."""
        plain = b'test engine' * 100
        packed = compressed(plain)
        self.assertEqual(decompress(packed, len(plain)), plain)
        for bad in (packed + b'x', packed[:-1],
                    packed[:1] + struct.pack('<I', 128 * 1024 * 1024) + packed[5:]):
            with self.assertRaises((ValueError, lzma.LZMAError)):
                decompress(bad, len(plain))
        with self.assertRaises(ValueError):
            decompress(packed, len(plain) - 1)

    def test_relative_transform(self) -> None:
        """Check positive and negative displacement and unaffected instructions."""
        self.assertEqual(reverse_calls(bytes.fromhex('e805000000')), bytes.fromhex('e800000000'))
        self.assertEqual(reverse_calls(bytes.fromhex('e904000000')), bytes.fromhex('e9ffffffff'))
        self.assertEqual(reverse_calls(bytes.fromhex('e81234561290')), bytes.fromhex('e81234561290'))
        self.assertEqual(reverse_calls(b'\xe8\x00'), b'\xe8\x00')

    def test_no_overlay_engine(self) -> None:
        """Reuse the scoped PE comparison only for an exact inner image."""
        self.assertEqual(compare(loader(), loader(1024), overlay_expected=False)['overlay_bytes'], 0)
        with self.assertRaises(ValueError):
            compare(loader(), loader(1024, b'x'), overlay_expected=False)


if __name__ == '__main__':
    unittest.main()
