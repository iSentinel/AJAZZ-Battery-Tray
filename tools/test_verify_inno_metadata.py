"""Synthetic manifest and fixed version field reconstruction tests."""

import struct
import unittest

from verify_inno_metadata import ENTRY, manifest, set_padded_string


def placeholder() -> bytearray:
    """Make one synthetic aligned version string node."""
    token = 'CompanyName\0'.encode('utf-16le')
    padding = bytes((-(6 + len(token))) % 4)
    value = '     \0'.encode('utf-16le')
    return bytearray(struct.pack('<HHH', 6 + len(token) + len(padding) + len(value),
                                 6, 1) + token + padding + value)


class MetadataTests(unittest.TestCase):
    """Require exact length-preserving edits and reject malformed fields."""

    def test_manifest_transform(self) -> None:
        """Preserve the original gap and all unrelated bytes."""
        dep = b'<dependency>' + b'x' * 100 + b'</dependency>'
        gap = b'\r\n<other/>\r\n'
        raw = b'prefix' + dep + gap + b'<file name="x"/>suffix'
        expected = b'prefix' + b' ' * (len(dep) - len(ENTRY)) + gap + ENTRY + b'<file name="x"/>suffix'
        self.assertEqual(manifest(raw), expected)
        self.assertEqual(len(raw), len(expected))

    def test_manifest_invalid(self) -> None:
        """Reject missing, duplicate or short dependency blocks."""
        for raw in (b'<file name="x"/>', b'<dependency></dependency><file name="x"/>',
                    b'<dependency><dependency></dependency><file name="x"/>'):
            with self.assertRaises(ValueError):
                manifest(raw)

    def test_version_patch(self) -> None:
        """Preserve remaining spaces, terminal NUL and header."""
        raw = placeholder()
        before = bytes(raw)
        set_padded_string(raw, 'CompanyName', 'abc')
        self.assertEqual(raw[:-12], before[:-12])
        self.assertEqual(raw[-12:], 'abc  \0'.encode('utf-16le'))

    def test_version_invalid(self) -> None:
        """Reject duplicate keys, overlong values and changed placeholders."""
        raw = placeholder()
        for invalid, value in ((raw + raw, 'a'), (raw, 'abcdef'),
                               (raw[:-2] + b'xx', 'a')):
            with self.assertRaises(ValueError):
                set_padded_string(bytearray(invalid), 'CompanyName', value)


if __name__ == '__main__':
    unittest.main()
