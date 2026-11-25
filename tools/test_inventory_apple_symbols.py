"""Synthetic regressions for scoped two-level undefined symbol attribution."""

import struct
import unittest

from inventory_apple_load_commands import BASE
from inventory_apple_symbols import inspect_symbols
from inventory_dotnet_bundle import BundleError
from test_inventory_apple_load_commands import dylib


def sample(ordinal: int = 1, desc: int = 0x40, name: bytes = b'\0_test\0',
           duplicate: bool = False, flags: int = 0x80,
           bad_bounds: bool = False, bad_partition: bool = False) -> bytes:
    """Create reviewed link commands plus small synthetic symbol tables."""
    paths = sorted(BASE, reverse=True)
    target = struct.pack('<4I', 0x24, 16, 0x0a0d00, 0x0f0500)
    links = target + b''.join(dylib(path) for path in paths)
    offset = 32 + len(links) + 72 + 24 + 80
    count = 2 if duplicate else 1
    strings = offset + count * 16
    segment = struct.pack('<II16sQQQQIIII', 0x19, 72, b'__LINKEDIT',
                          0, 0, offset, count * 16 + len(name), 1, 1, 0, 0)
    sym = struct.pack('<6I', 2, 24, offset, count, strings,
                      len(name) + int(bad_bounds))
    dyn = struct.pack('<20I', 11, 80, 0, 0, 0, 0, int(bad_partition),
                      count, *([0] * 12))
    commands = links + segment + sym + dyn
    header = struct.pack('<8I', 0xfeedfacf, 0x01000007, 0, 2,
                         4 + len(paths), len(commands), flags, 0)
    record = struct.pack('<IBBHQ', 1, 1, 0, (ordinal << 8) | desc, 0)
    return header + commands + record * count + name


class AppleSymbolTests(unittest.TestCase):
    """Reject incomplete or unsupported symbol records, not OS versions."""

    def test_original_link_order_and_weak_reference(self) -> None:
        """Ordinals follow original command order, not sorted inventory."""
        result = inspect_symbols(sample(), 'high-sierra')
        item, = result['symbols']
        self.assertEqual(item['name'], '_test')
        self.assertEqual(item['library'], sorted(BASE, reverse=True)[0])
        self.assertEqual(item['library_linkage'], 'required')
        self.assertTrue(item['weak_reference'])
        self.assertEqual(result['weak_references'], 1)

    def test_invalid_library_ordinal(self) -> None:
        """Reject self, dynamic lookup and absent library ordinals."""
        for ordinal in (0, len(BASE) + 1, 254, 255):
            with self.subTest(ordinal=ordinal), self.assertRaises(BundleError):
                inspect_symbols(sample(ordinal=ordinal), 'high-sierra')

    def test_bad_extents_and_partition(self) -> None:
        """Reject out-of-bounds strings and inconsistent undefined ranges."""
        for raw in (sample(bad_bounds=True), sample(bad_partition=True)):
            with self.assertRaises(BundleError):
                inspect_symbols(raw, 'high-sierra')

    def test_duplicate_and_unterminated_names(self) -> None:
        """Reject repeated and unterminated symbol names."""
        for raw in (sample(duplicate=True), sample(name=b'\0_test')):
            with self.assertRaises(BundleError):
                inspect_symbols(raw, 'high-sierra')

    def test_unsupported_namespace_and_flags(self) -> None:
        """Reject flat namespace or unreviewed descriptor flags."""
        for raw in (sample(flags=0), sample(flags=0x180), sample(desc=0x80)):
            with self.assertRaises(BundleError):
                inspect_symbols(raw, 'high-sierra')


if __name__ == '__main__':
    unittest.main()
