"""Synthetic tests for preserving original Apple archive bytes."""

from io import BytesIO
import unittest
from unittest.mock import patch
import zipfile

from build_consolidated_apple_notices import encode, package_files, verify_wrapper
from verify_hardware_acceptance import APPLE_NAMES
from verify_windows_notice_transport import digest


class AppleWrapperTests(unittest.TestCase):
    """Reject archive and license substitutions without approving distribution."""

    def test_roundtrip(self) -> None:
        """Keep the exact original inner ZIP and companion checksum."""
        edition = 'universal'
        name = APPLE_NAMES[edition]
        inner, license_bytes = b'synthetic archive', b'synthetic license'
        stream = BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            archive.writestr(name + '.zip', inner)
            archive.writestr(name + '.sha256', digest(inner) + '  ' + name + '.zip')
        original = stream.getvalue()
        with patch('build_consolidated_apple_notices.PINS', {edition: (digest(original), digest(inner))}), patch(
                'build_consolidated_apple_notices.LICENSE_SHA', digest(license_bytes)), patch(
                'build_consolidated_apple_notices.apple', return_value={'inner_archive_sha256': digest(inner)}):
            files = package_files(original, license_bytes, edition)
            raw = encode(files)
            self.assertEqual(files[name + '.zip'], inner)
            self.assertEqual(verify_wrapper(raw, files, edition)['release_admission'], 'BLOCKED')
            self.assertEqual(raw, encode(files))
            with self.assertRaises(ValueError):
                verify_wrapper(encode(dict(files, LICENSE=b'changed')), files, edition)
            with self.assertRaises(ValueError):
                package_files(original, b'wrong', edition)

    def test_original_pin(self) -> None:
        """Do not parse a substituted archive."""
        with patch('build_consolidated_apple_notices.apple') as inspect:
            with self.assertRaises(ValueError):
                package_files(b'wrong', b'wrong', 'high-sierra')
            inspect.assert_not_called()


if __name__ == '__main__':
    unittest.main()
