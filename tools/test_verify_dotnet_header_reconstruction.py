"""Synthetic checks for bounded SDK resource-growth header reconstruction."""

from copy import deepcopy
import unittest

from inventory_dotnet_bundle import BundleError
from inventory_dotnet_host_headers import changes
from verify_dotnet_header_reconstruction import align, expected_headers


def fixture() -> dict:
    """Model an unsigned host with one resource and one trailing section."""
    return {"certificate_table": "ABSENT", "section_order": [".rsrc", ".reloc"],
            "optional": {"subsystem": 3, "file_alignment": 512,
                         "section_alignment": 4096, "size_initialized": 2048,
                         "size_image": 12288, "entry_point": 4096},
            "sections": {".rsrc": {"virtual_size": 1000, "raw_size": 1024,
                                  "virtual_address": 4096, "raw_pointer": 512},
                         ".reloc": {"virtual_address": 8192, "raw_pointer": 1536}},
            "directories": {"resource": [4096, 1000], "relocation": [8192, 20],
                            "import": [100, 10], "security": [0, 0]}}


class ReconstructionTests(unittest.TestCase):
    """Require deterministic growth and retain all unreviewed header fields."""

    def test_growth_across_virtual_boundary(self) -> None:
        """Update raw and virtual deltas independently and retain host input."""
        host = fixture()
        original = deepcopy(host)
        result = expected_headers(host, 4100, 2)
        self.assertEqual(result["sections"][".rsrc"]["raw_size"], 4608)
        self.assertEqual(result["sections"][".reloc"]["raw_pointer"], 5120)
        self.assertEqual(result["sections"][".reloc"]["virtual_address"], 12288)
        self.assertEqual(result["optional"]["size_initialized"], 5632)
        self.assertEqual(result["optional"]["size_image"], 16384)
        self.assertEqual(result["directories"]["relocation"], [12288, 20])
        self.assertEqual(result["directories"]["import"], [100, 10])
        self.assertEqual(result["optional"]["subsystem"], 2)
        self.assertEqual(host, original)

    def test_raw_only_growth(self) -> None:
        """Do not shift RVAs when only raw alignment grows."""
        result = expected_headers(fixture(), 1500, 3)
        self.assertEqual(result["sections"][".reloc"]["raw_pointer"], 2048)
        self.assertEqual(result["sections"][".reloc"]["virtual_address"], 8192)
        self.assertEqual(result["directories"]["resource"], [4096, 1500])

    def test_same_size(self) -> None:
        """Unchanged resource size preserves all headers except subsystem."""
        host = fixture()
        self.assertEqual(changes(host, expected_headers(host, 1000, 2)),
                         [{"field": "optional.subsystem", "host": 3, "actual": 2}])

    def test_unexpected_change(self) -> None:
        """Report unapproved entry point mutations after reconstruction."""
        expected = expected_headers(fixture(), 4100, 2)
        actual = deepcopy(expected)
        actual["optional"]["entry_point"] = 4097
        self.assertEqual(changes(expected, actual)[0]["field"], "optional.entry_point")

    def test_scope_rejections(self) -> None:
        """Reject shrinking resources, signed hosts and alternate layouts."""
        with self.assertRaises(BundleError):
            expected_headers(fixture(), 999, 2)
        for key, value in (("certificate_table", "PRESENT_NOT_VERIFIED"),
                           ("section_order", [".reloc", ".rsrc"])):
            host = fixture()
            host[key] = value
            with self.assertRaises(BundleError):
                expected_headers(host, 1500, 2)

    def test_invalid_alignment(self) -> None:
        """Reject zero, non-power-of-two and oversized inputs."""
        for value, alignment in ((10, 0), (10, 3), (-1, 512), (2**31, 512)):
            with self.assertRaises(BundleError):
                align(value, alignment)


if __name__ == "__main__":
    unittest.main()
