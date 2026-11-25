"""Synthetic regressions for the reviewed Apple archive inventory."""

import io
import plistlib
import stat
import struct
import unittest
import zipfile

from inventory_apple_archive import EDITIONS, architectures, archive_members, inspect
from inventory_dotnet_bundle import BundleError


def thin(cpu: int = 0x01000007) -> bytes:
    """Construct a bounded synthetic 64-bit executable header and command."""
    return struct.pack('<10I', 0xfeedfacf, cpu, 0, 2, 1, 8, 0, 0, 0x24, 8)


def fat() -> bytes:
    """Construct two nonoverlapping reviewed slices with aligned offsets."""
    first, second = thin(), thin(0x0100000c)
    return (struct.pack('>12I', 0xcafebabe, 2, 0x01000007, 0, 48, 40, 3,
                        0x0100000c, 0, 88, 40, 3) + first + second)


def zipped(entries: dict) -> bytes:
    """Write synthetic members with explicit Unix modes."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        for name, (raw, mode) in entries.items():
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = mode << 16
            archive.writestr(info, raw)
    return buffer.getvalue()


def app_members(edition: str) -> dict:
    """Provide the seven expected app files with synthetic plist and Mach-O."""
    app, exe, identifier, minimum, _ = EDITIONS[edition]
    root = app + '/Contents/'
    result = {root + 'Resources/AppIcon' + s + '.icns': (b'icon', 0o100644)
              for s in ('', '-black', '-blue', '-white')}
    plist = plistlib.dumps({'CFBundleIdentifier': identifier,
                            'CFBundleExecutable': exe,
                            'LSMinimumSystemVersion': minimum,
                            'CFBundleVersion': '1'})
    result[root + 'Info.plist'] = (plist, 0o100644)
    result[root + '_CodeSignature/CodeResources'] = (b'not trust', 0o100644)
    result[root + 'MacOS/' + exe] = (fat() if edition == 'universal' else thin(), 0o100755)
    return result


class AppleArchiveTests(unittest.TestCase):
    """Verify both supported editions and fail closed on changed inputs."""

    def test_editions(self) -> None:
        """Verify exact file coverage, architectures and non-admission state."""
        for edition, spec in EDITIONS.items():
            result = inspect(zipped(app_members(edition)), edition)
            self.assertEqual(set(result['architectures']), spec[4])
            self.assertEqual(len(result['files']), 7)
            self.assertEqual(result['signature'], 'NOT_VERIFIED')

    def test_archive_paths(self) -> None:
        """Reject traversal, duplicate-case paths and symbolic links."""
        for entries in ({'../a': (b'x', 0o100644)}, {'/a': (b'x', 0o100644)},
                        {'a': (b'x', 0o100644), 'A': (b'y', 0o100644)},
                        {'a': (b'elsewhere', stat.S_IFLNK | 0o777)}):
            with self.assertRaises(BundleError):
                archive_members(zipped(entries))

    def test_missing_or_extra(self) -> None:
        """Reject incomplete and expanded file layouts."""
        entries = app_members('universal')
        with self.assertRaises(BundleError):
            inspect(zipped({**entries, 'extra': (b'x', 0o100644)}), 'universal')
        entries.pop(next(iter(entries)))
        with self.assertRaises(BundleError):
            inspect(zipped(entries), 'universal')

    def test_wrong_edition_or_mode(self) -> None:
        """Reject mismatched editions and non-executable binary modes."""
        entries = app_members('high-sierra')
        with self.assertRaises(BundleError):
            inspect(zipped(entries), 'universal')
        key = next(k for k in entries if '/MacOS/' in k)
        entries[key] = (entries[key][0], 0o100644)
        with self.assertRaises(BundleError):
            inspect(zipped(entries), 'high-sierra')

    def test_malformed_macho(self) -> None:
        """Reject invalid magic, command length and overlapping FAT slices."""
        overlapping = bytearray(fat())
        struct.pack_into('>I', overlapping, 36, 48)
        malformed = bytearray(thin())
        struct.pack_into('<I', malformed, 36, 4)
        for raw in (b'x', bytes(overlapping), bytes(malformed), fat()[:-1]):
            with self.assertRaises(BundleError):
                architectures(raw)

    def test_fat_cpu_mismatch(self) -> None:
        """Reject disagreement between declared and actual slice architecture."""
        raw = bytearray(fat())
        struct.pack_into('<I', raw, 92, 0x01000007)
        with self.assertRaises(BundleError):
            architectures(raw)


if __name__ == '__main__':
    unittest.main()
