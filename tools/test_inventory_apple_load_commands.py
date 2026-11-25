"""Regressions for bounded Mach-O direct dependency observations."""

import struct
import unittest

from inventory_apple_load_commands import BASE, MODERN, WEAK, deployment, inspect_slice, library, version
from inventory_dotnet_bundle import BundleError


def dylib(path: str, weak: bool = False) -> bytes:
    """Build a synthetic aligned dylib command."""
    name = path.encode('ascii') + b'\0'
    name += b'\0' * (-len(name) % 8)
    return struct.pack('<6I', 0x80000018 if weak else 0xc, 24 + len(name),
                       24, 0, 0x10000, 0x10000) + name


def binary(edition: str, extra: bytes = b'', omit: str = '',
           weak_override: str = '') -> bytes:
    """Build one reviewed synthetic architecture with optional mutations."""
    modern = edition == 'universal'
    target = (struct.pack('<8I', 0x32, 32, 1, 0x0d0000, 0x0f0500, 1, 3, 0x48f0500)
              if modern else struct.pack('<4I', 0x24, 16, 0x0a0d00, 0x0f0500))
    paths = MODERN if modern else BASE
    commands = [target] + [dylib(path, (modern and path in WEAK) != (path == weak_override))
                           for path in sorted(paths) if path != omit]
    if extra:
        commands.append(extra)
    raw = b''.join(commands)
    return struct.pack('<8I', 0xfeedfacf, 0x01000007, 0, 2, len(commands), len(raw), 0, 0) + raw


class AppleLoadCommandTests(unittest.TestCase):
    """Do not confuse direct declared linkage with native compatibility."""

    def test_reviewed_editions(self) -> None:
        """Decode both target forms and required/weak dependencies."""
        for edition, count, weak, minimum in (('universal', 24, 9, '13.0.0'),
                                             ('high-sierra', 7, 0, '10.13.0')):
            data = inspect_slice(binary(edition), edition)
            self.assertEqual(data['deployment']['minimum'], minimum)
            self.assertEqual(data['deployment']['sdk'], '15.5.0')
            self.assertEqual(len(data['libraries']), count)
            self.assertEqual(sum(x['linkage'] == 'weak' for x in data['libraries']), weak)

    def test_bad_deployment(self) -> None:
        """Reject foreign platform, malformed size and inverted versions."""
        for raw in (struct.pack('<6I', 0x32, 24, 2, 1, 2, 0),
                    struct.pack('<6I', 0x32, 24, 1, 1, 2, 1),
                    struct.pack('<4I', 0x24, 16, 3, 2)):
            with self.assertRaises(BundleError):
                deployment(struct.unpack_from('<I', raw)[0], raw)
        self.assertEqual(version(0x0a0d06), '10.13.6')

    def test_bad_library(self) -> None:
        """Reject unreviewed paths and out-of-bounds or unterminated names."""
        path = sorted(BASE)[0]
        valid = bytearray(dylib(path))
        struct.pack_into('<I', valid, 8, 9999)
        for raw in (dylib('@rpath/unknown.dylib'), bytes(valid), dylib(path).rstrip(b'\0')):
            with self.assertRaises(BundleError):
                library(0xc, raw)

    def test_missing_duplicate_or_weak_change(self) -> None:
        """Reject missing, repeated or reclassified direct dependencies."""
        path = sorted(BASE)[0]
        for edition, raw in (('high-sierra', binary('high-sierra', omit=path)),
                             ('high-sierra', binary('high-sierra', extra=dylib(path))),
                             ('universal', binary('universal', weak_override=path))):
            with self.assertRaises(BundleError):
                inspect_slice(raw, edition)

    def test_extra_load_commands(self) -> None:
        """Reject rpath and duplicate deployment commands in reviewed scope."""
        for extra in (struct.pack('<2I', 0x8000001c, 8),
                      struct.pack('<4I', 0x24, 16, 0x0a0d00, 0x0f0500)):
            with self.assertRaises(BundleError):
                inspect_slice(binary('high-sierra', extra=extra), 'high-sierra')


if __name__ == '__main__':
    unittest.main()
