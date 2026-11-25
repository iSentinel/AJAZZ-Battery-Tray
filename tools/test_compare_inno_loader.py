"""Synthetic PE32 loader tests for exact scoped comparison."""

import struct
import unittest

from compare_inno_loader import ORDER, compare


def loader(resource_size: int = 512, overlay: bytes = b'') -> bytes:
    """Build a minimal observed-layout PE with deterministic section bytes."""
    raw = bytearray(1024)
    raw[:2] = b'MZ'
    pe, o = 256, 280
    struct.pack_into('<I', raw, 60, pe)
    raw[pe:pe + 4] = b'PE\0\0'
    struct.pack_into('<HHIIIHH', raw, pe + 4, 0x14c, len(ORDER), 0, 0, 0, 224, 0x102)
    struct.pack_into('<H', raw, o, 0x10b)
    struct.pack_into('<I', raw, o + 8, 8 * 512 + resource_size)
    struct.pack_into('<II', raw, o + 32, 4096, 512)
    struct.pack_into('<II', raw, o + 56, 12 * 4096, 1024)
    struct.pack_into('<I', raw, o + 92, 16)
    struct.pack_into('<II', raw, o + 112, 11 * 4096, resource_size)
    for i, name in enumerate(ORDER):
        pos = o + 224 + 40 * i
        raw[pos:pos + len(name)] = name.encode()
        size = resource_size if name == '.rsrc' else 512
        empty = name in ('.bss', '.tls')
        struct.pack_into('<IIIIIIHHI', raw, pos + 8, size, (i + 1) * 4096,
                         0 if empty else size, 0 if empty else len(raw), 0, 0, 0, 0, 0)
        if not empty:
            raw.extend(bytes((i + 1,)) * size)
    return bytes(raw) + overlay


class LoaderComparisonTests(unittest.TestCase):
    """The comparison cannot qualify resources or overlay by association."""

    def test_resource_growth(self) -> None:
        """Accept resource growth and overlay, explicitly leave them unqualified."""
        result = compare(loader(), loader(1024, b'payload'))
        self.assertEqual(sum(row['state'] == 'MATCH' for row in result['sections']), 10)
        self.assertEqual(result['resource_section'], 'NOT_QUALIFIED')
        self.assertEqual(result['overlay_bytes'], 7)
        self.assertEqual(result['embedded_engine'], 'NOT_VERIFIED')

    def test_nonresource_or_header_mutation(self) -> None:
        """Reject a changed loader instruction, header or initialized size."""
        for offset in (1024, 280 + 16, 280 + 8, 280 + 128):
            actual = bytearray(loader(1024, b'payload'))
            actual[offset] ^= 1
            with self.assertRaises(ValueError):
                compare(loader(), bytes(actual))

    def test_section_bounds_and_overlay(self) -> None:
        """Reject overlapping raw regions, truncated input and missing overlay."""
        actual = bytearray(loader(1024, b'payload'))
        struct.pack_into('<I', actual, 280 + 224 + 40 + 20, 1024)
        for bad in (bytes(actual), loader(1024), loader(1024, b'payload')[:2000]):
            with self.assertRaises(ValueError):
                compare(loader(), bad)


if __name__ == '__main__':
    unittest.main()
