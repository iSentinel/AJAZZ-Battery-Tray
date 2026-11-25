"""Synthetic checks for scoped PE resource byte reconstruction."""

import struct
import unittest

from inventory_dotnet_bundle import BundleError
from verify_dotnet_resource_serialization import PayloadTree, serialize


class SerializationTests(unittest.TestCase):
    """Verify deterministic order, exact records and supported key scope."""

    def test_single_leaf(self) -> None:
        """Check independently calculated directory and leaf positions."""
        raw = serialize({(16, 1, 0): b"abc"}, 4096)
        self.assertEqual(len(raw), 92)
        self.assertEqual(struct.unpack_from("<IIHHHH", raw, 0),
                         (0, 0, 4, 0, 0, 1))
        self.assertEqual(struct.unpack_from("<II", raw, 16), (16, 0x80000018))
        self.assertEqual(struct.unpack_from("<II", raw, 40), (1, 0x80000030))
        self.assertEqual(struct.unpack_from("<II", raw, 64), (0, 76))
        self.assertEqual(raw[72:76], b"abc\0")
        self.assertEqual(struct.unpack_from("<IIII", raw, 76),
                         (4096 + 72, 3, 1252, 0))

    def test_roundtrip_and_order(self) -> None:
        """Sort mixed names and numeric IDs regardless of insertion order."""
        leaves = {(10, 9, 1033): b"nine", (10, "CLRDEBUGINFO", 0): b"debug",
                  (3, 1, 0): b"icon", (10, 2, 0): b"two"}
        raw = serialize(leaves, 8192)
        self.assertEqual(raw, serialize(dict(reversed(list(leaves.items()))), 8192))
        tree = PayloadTree(raw, 8192)
        tree.visit(0)
        self.assertEqual(tree.leaves, leaves)
        self.assertEqual(list(tree.leaves), [(3, 1, 0), (10, "CLRDEBUGINFO", 0),
                                            (10, 2, 0), (10, 9, 1033)])

    def test_overlay(self) -> None:
        """An app leaf replaces the same host identity, retaining other keys."""
        host = {(10, "CLRDEBUGINFO", 0): b"host", (16, 1, 0): b"old"}
        app = {(16, 1, 0): b"new", (24, 1, 0): b"manifest"}
        tree = PayloadTree(serialize(host | app, 4096), 4096)
        tree.visit(0)
        self.assertEqual(tree.leaves, {(10, "CLRDEBUGINFO", 0): b"host",
                                      (16, 1, 0): b"new", (24, 1, 0): b"manifest"})

    def test_unsupported_keys(self) -> None:
        """Fail closed outside the reviewed numeric and named key subset."""
        for key in ((16, "UNKNOWN", 0), ("CLRDEBUGINFO", 1, 0),
                    (16, 65536, 0), (16, 1, -1)):
            with self.assertRaises(BundleError):
                serialize({key: b"x"}, 4096)

    def test_malformed_input(self) -> None:
        """Reject a corrupt reserved field or out-of-bounds leaf payload."""
        for offset, value in ((76, 1), (88, 1)):
            raw = bytearray(serialize({(16, 1, 0): b"abc"}, 4096))
            struct.pack_into("<I", raw, offset, value)
            with self.assertRaises(BundleError):
                PayloadTree(bytes(raw), 4096).visit(0)

    def test_payload_budget(self) -> None:
        """Reject oversized merged content before building resource bytes."""
        with self.assertRaises(BundleError):
            serialize({(16, 1, 0): bytes(8 * 1024 * 1024 + 1)}, 4096)


if __name__ == "__main__":
    unittest.main()
