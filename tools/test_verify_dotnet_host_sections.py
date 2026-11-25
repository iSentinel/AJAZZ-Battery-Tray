"""Synthetic checks for exact host data patch and bounded PE parsing."""

import struct
import unittest

from inventory_dotnet_bundle import BundleError, MARKER
from verify_dotnet_host_sections import APP_MARKER, data_patch, sections, template


def data_fixture() -> tuple[bytes, bytes]:
    """Construct two independent known placeholders and their exact patches."""
    original = b"before" + bytes(8) + MARKER + b"gap" + APP_MARKER + b"end"
    actual = original.replace(bytes(8) + MARKER, struct.pack("<q", 1234) + MARKER)
    actual = actual.replace(APP_MARKER, b"App.dll".ljust(len(APP_MARKER), b"\0"))
    return original, actual


class HostTests(unittest.TestCase):
    """Reject unexpected changes without exempting an entire data section."""

    def test_exact_patch(self) -> None:
        """Accept only the two reconstructed SDK fields."""
        original, actual = data_fixture()
        result = data_patch(original, actual, "App.dll", 1234)
        self.assertTrue(result["match"])
        self.assertEqual(result["unexpected_bytes"], 0)

    def test_unexpected_change(self) -> None:
        """One unexpected byte must fail the scoped comparison."""
        original, actual = data_fixture()
        result = data_patch(original, actual[:-1] + b"x", "App.dll", 1234)
        self.assertFalse(result["match"])
        self.assertEqual(result["unexpected_bytes"], 1)

    def test_wrong_name_or_offset(self) -> None:
        """A valid-looking but different app name or offset is not accepted."""
        original, actual = data_fixture()
        self.assertFalse(data_patch(original, actual, "Other.dll", 1234)["match"])
        self.assertFalse(data_patch(original, actual, "App.dll", 1235)["match"])

    def test_duplicate_placeholder(self) -> None:
        """Do not pick an arbitrary matching marker."""
        original, actual = data_fixture()
        with self.assertRaises(BundleError):
            data_patch(original + APP_MARKER, actual, "App.dll", 1234)

    def test_invalid_pe_and_pack(self) -> None:
        """Reject truncated or unpinned inputs before using their contents."""
        for raw in (b"", b"MZ" + bytes(62)):
            with self.assertRaises(BundleError):
                sections(raw)
            with self.assertRaises(BundleError):
                template(raw)


if __name__ == "__main__":
    unittest.main()
