"""Synthetic solid stream and block-offset transformation tests."""

import hashlib
import lzma
import unittest

from verify_inno_inner_engine import reverse_calls
from verify_inno_solid import CHUNK, file_hashes


def packed(data: bytes) -> bytes:
    """Build a raw LZMA2 stream with a 64 KiB dictionary."""
    return b'zlb\x1a\x08' + lzma.compress(data, format=lzma.FORMAT_RAW,
                                            filters=[{'id': lzma.FILTER_LZMA2,
                                                      'dict_size': 65536}])


def spec(name: str, data: bytes) -> tuple:
    """Create a synthetic expected file record."""
    return name, len(data), hashlib.sha256(data).hexdigest()


class SolidTests(unittest.TestCase):
    """Require all decoded bytes, per-file hashes and exact EOS."""

    def test_block_offset(self) -> None:
        """Reverse an instruction at a nonzero file block offset."""
        self.assertEqual(reverse_calls(bytes.fromhex('e805000100'), CHUNK),
                         bytes.fromhex('e800000000'))

    def test_files(self) -> None:
        """Verify separate files across a 64 KiB transform boundary."""
        first = b'a' * CHUNK + bytes.fromhex('e800000000')
        encoded = b'a' * CHUNK + bytes.fromhex('e805000100')
        second = b'icon'
        rows = file_hashes(packed(encoded + second),
                          (spec('app', first), spec('icon', second)))
        self.assertEqual(len(rows), 2)

    def test_reject_corruption(self) -> None:
        """Reject trailing decoded data, compressed suffix and bad hash."""
        data = b'abc'
        for raw, expected in ((packed(data + b'x'), spec('app', data)),
                              (packed(data) + b'x', spec('app', data)),
                              (packed(data), spec('app', b'bad'))):
            with self.assertRaises(ValueError):
                file_hashes(raw, (expected,))


if __name__ == '__main__':
    unittest.main()
