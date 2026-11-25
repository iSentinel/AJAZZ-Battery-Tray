"""Synthetic tests for bounded PE header inventory."""

import struct
import unittest

from inventory_dotnet_bundle import BundleError
from inventory_dotnet_host_headers import changes, invariants, parse_headers


def fixture(subsystem: int = 3) -> bytearray:
    """Make a minimal structurally valid x64 PE32+ header and one raw section."""
    raw = bytearray(1024)
    raw[:2] = b"MZ"
    struct.pack_into("<I", raw, 60, 64)
    raw[64:68] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", raw, 68, 0x8664, 1, 0, 0, 0, 240, 0x22)
    pos = 88
    struct.pack_into("<H", raw, pos, 0x20b)
    struct.pack_into("<IIQII", raw, pos + 16, 4096, 4096, 0x140000000,
                     4096, 512)
    struct.pack_into("<II", raw, pos + 56, 8192, 512)
    struct.pack_into("<HH", raw, pos + 68, subsystem, 0x8160)
    struct.pack_into("<I", raw, pos + 108, 16)
    raw[328:336] = b".text\0\0\0"
    struct.pack_into("<IIIIIIHHI", raw, 336, 32, 4096, 512, 512, 0, 0,
                     0, 0, 0x60000020)
    return raw


class HeaderTests(unittest.TestCase):
    """Ensure selected invariants do not imply full PE provenance."""

    def test_valid_structure(self) -> None:
        """Read the standard fixed header and exact section metadata."""
        result = parse_headers(bytes(fixture()))
        self.assertEqual(result["optional"]["entry_point"], 4096)
        self.assertEqual(result["optional"]["image_base"], 0x140000000)
        self.assertEqual(result["sections"][".text"]["raw_pointer"], 512)
        self.assertEqual(result["certificate_table"], "ABSENT")

    def test_subsystem_change(self) -> None:
        """Allow only the expected subsystem in the scoped checks."""
        host = parse_headers(bytes(fixture()))
        app = parse_headers(bytes(fixture(2)))
        self.assertTrue(all(invariants(host, app, 2).values()))
        self.assertEqual(changes(host, app), [
            {"field": "optional.subsystem", "host": 3, "actual": 2}])
        self.assertFalse(invariants(host, app, 3)["subsystem"])

    def test_entry_point_change(self) -> None:
        """Reject a changed entry point even if structurally valid."""
        raw = fixture(2)
        struct.pack_into("<I", raw, 104, 4100)
        host = parse_headers(bytes(fixture()))
        app = parse_headers(bytes(raw))
        self.assertFalse(invariants(host, app, 2)["optional.entry_point"])

    def test_padding_difference(self) -> None:
        """Report header padding differences even with passing invariants."""
        raw = fixture()
        raw[400] = 1
        host = parse_headers(bytes(fixture()))
        app = parse_headers(bytes(raw))
        self.assertTrue(all(invariants(host, app, 3).values()))
        self.assertEqual(changes(host, app)[0]["field"], "header_padding.sha256")

    def test_invalid_header_and_ranges(self) -> None:
        """Reject truncated, undersized and out-of-file structures."""
        with self.assertRaises(BundleError):
            parse_headers(bytes(fixture()[:100]))
        for offset, value in ((148, 300), (348, 1000), (196, 15)):
            raw = fixture()
            struct.pack_into("<I", raw, offset, value)
            with self.assertRaises(BundleError):
                parse_headers(bytes(raw))

    def test_certificate_extent(self) -> None:
        """Report a bounded certificate table without claiming a signature."""
        raw = fixture() + bytearray(16)
        struct.pack_into("<II", raw, 232, 1024, 16)
        self.assertEqual(parse_headers(bytes(raw))["certificate_table"],
                         "PRESENT_NOT_VERIFIED")
        struct.pack_into("<II", raw, 232, 512, 16)
        with self.assertRaises(BundleError):
            parse_headers(bytes(raw))


if __name__ == "__main__":
    unittest.main()
