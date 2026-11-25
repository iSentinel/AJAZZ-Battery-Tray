"""Synthetic fixtures for the reviewed .NET bundle manifest layout."""

import hashlib
import struct
import unittest

from inventory_dotnet_bundle import MARKER, BundleError, inventory


def fixture(name: bytes = b"System.Runtime.dll", compressed: int = 0) -> bytes:
    """Create a minimal v6 bundle with three payload records."""
    host = b"MZ" + bytes(62)
    start = len(host) + 8 + len(MARKER)
    payloads = (b"{}", b"{}", b"sample")
    boundary = start + sum(map(len, payloads))
    manifest = struct.pack("<IIi", 6, 0, 3) + b"\x0cABCDEFGHIJKL"
    manifest += struct.pack("<qqqqQ", start, 2, start + 2, 2, 0)
    for offset, value, kind, path in (
        (start, payloads[0], 3, b"app.deps.json"),
        (start + 2, payloads[1], 4, b"app.runtimeconfig.json"),
        (start + 4, payloads[2], 1, name),
    ):
        manifest += struct.pack("<qqqB", offset, len(value),
                                compressed if kind == 1 else 0, kind)
        manifest += bytes([len(path)]) + path
    return host + struct.pack("<q", boundary) + MARKER + b"".join(payloads) + manifest


class BundleTests(unittest.TestCase):
    """Exercise correct payload hashes and fail-closed manifest handling."""

    def test_payload_hash(self) -> None:
        """Inventory the actual bytes instead of inferring a package version."""
        result = inventory(fixture())
        self.assertEqual(result["bundle_version"], "6.0")
        self.assertEqual(len(result["files"]), 3)
        item = next(item for item in result["files"] if item["type"] == "assembly")
        self.assertEqual(item["sha256"], hashlib.sha256(b"sample").hexdigest())

    def test_invalid_path_and_compression(self) -> None:
        """Never treat traversal or unsupported compression as qualified."""
        for raw in (fixture(b"../evil.dll"), fixture(compressed=1)):
            with self.assertRaises(BundleError):
                inventory(raw)

    def test_duplicate_marker_and_truncated(self) -> None:
        """Reject ambiguous marker and incomplete manifest."""
        raw = fixture()
        for invalid in (raw + MARKER, raw[:-1], b"not PE"):
            with self.assertRaises(BundleError):
                inventory(invalid)

    def test_duplicate_path(self) -> None:
        """Reject case-insensitive collisions on Windows."""
        with self.assertRaises(BundleError):
            inventory(fixture(b"APP.DEPS.JSON"))

    def test_invalid_payload_offset(self) -> None:
        """Reject an entry extending beyond the manifest boundary."""
        raw = bytearray(fixture())
        marker = raw.index(MARKER)
        boundary, = struct.unpack_from("<q", raw, marker - 8)
        struct.pack_into("<q", raw, boundary + 12 + 13 + 40, len(raw))
        with self.assertRaises(BundleError):
            inventory(bytes(raw))


if __name__ == "__main__":
    unittest.main()
