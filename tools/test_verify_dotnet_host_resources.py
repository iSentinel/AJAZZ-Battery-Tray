"""Synthetic resource tree and overlay regression tests."""

import hashlib
import struct
import unittest

from inventory_dotnet_bundle import BundleError
from verify_dotnet_host_resources import HIGH, ResourceTree, compare_leaves, resources


def fixture() -> bytearray:
    """Construct one numeric type/name/language tree with a four-byte payload."""
    raw = bytearray(92)
    for pos, key, target in ((0, 16, HIGH | 24),
                             (24, 1, HIGH | 48), (48, 1033, 72)):
        struct.pack_into("<HHII", raw, pos + 12, 0, 1, key, target)
    struct.pack_into("<IIII", raw, 72, 0x1000 + 88, 4, 0, 0)
    raw[88:] = b"test"
    return raw


class ResourceTests(unittest.TestCase):
    """Check bounded traversal and exact overlay status."""

    def test_numeric_tree(self) -> None:
        """Read a valid three-level tree without decoding payloads."""
        tree = ResourceTree(bytes(fixture()), 0x1000)
        tree.visit(0)
        self.assertEqual(tree.leaves, {("16", "1", "1033"):
                                      hashlib.sha256(b"test").hexdigest()})

    def test_cycle_and_outside_payload(self) -> None:
        """Reject cycles and out-of-range resource bytes."""
        for pos, value in ((20, HIGH), (72, 0x2000)):
            raw = fixture()
            struct.pack_into("<I", raw, pos, value)
            with self.assertRaises(BundleError):
                ResourceTree(bytes(raw), 0x1000).visit(0)

    def test_invalid_depth(self) -> None:
        """Do not accept premature data entries."""
        raw = fixture()
        struct.pack_into("<I", raw, 20, 72)
        with self.assertRaises(BundleError):
            ResourceTree(bytes(raw), 0x1000).visit(0)

    def test_overlay(self) -> None:
        """Preserve host-only leaves and replace exact app keys."""
        a, b, c, d = (("16", str(n), "0") for n in range(4))
        result = compare_leaves({a: "old", b: "host"}, {a: "new", c: "app"},
                                {a: "new", b: "host", d: "extra"})
        self.assertEqual([x["status"] for x in result],
                         ["match", "match", "missing", "extra"])
        self.assertEqual(result[0]["origin"], "app")

    def test_bad_pe(self) -> None:
        """Reject a truncated PE before reading its resource area."""
        with self.assertRaises(BundleError):
            resources(b"MZ" + bytes(62))


if __name__ == "__main__":
    unittest.main()
