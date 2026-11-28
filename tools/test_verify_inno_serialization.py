"""Test exact observed Inno resource layout without executing any PE."""

import struct
import unittest

from verify_inno_serialization import check_area, check_tail, serialize


class InnoSerializationTests(unittest.TestCase):
    """Reject modified directory metadata, leaf records and padding."""

    def test_roundtrip(self) -> None:
        """Verify deterministic layout with mixed names and numeric IDs."""
        leaves = {(3, 100, 1033): b'abc', (10, 'DVCLAL', 0): b'data'}
        raw = serialize(leaves, 4096)
        self.assertEqual(raw, serialize(dict(reversed(list(leaves.items()))), 4096))
        result = check_area(raw, 4096)
        self.assertEqual(result['leaf_count'], 2)
        self.assertEqual(result['directory_count'], 5)

    def test_metadata(self) -> None:
        """Reject altered directory version or leaf codepage."""
        raw = serialize({(3, 100, 1033): b'abc'}, 4096)
        self.assertEqual(struct.unpack_from('<IIII', raw, 72), (4096 + 88, 3, 1252, 0))
        for offset in (8, 80, len(raw) - 1):
            changed = bytearray(raw)
            changed[offset] ^= 1
            with self.assertRaises(ValueError):
                check_area(bytes(changed), 4096)

    def test_tail_and_scope(self) -> None:
        """Check exact tail pattern and reject unknown names and languages."""
        check_tail(b'PADDINGXXPADDINGPAD')
        for bad in (b'PADX', bytes(512)):
            with self.assertRaises(ValueError):
                check_tail(bad)
        for key in ((3, 'UNKNOWN', 1033), (3, 100, 1049)):
            with self.assertRaises(ValueError):
                serialize({key: b'x'}, 4096)


if __name__ == '__main__':
    unittest.main()
