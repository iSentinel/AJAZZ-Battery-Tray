"""Test exact Apple archive pinning before native signature observation."""

from io import BytesIO
import unittest
from unittest.mock import patch
import zipfile

from stage_consolidated_apple_signature import collect
from verify_hardware_acceptance import APPLE_NAMES
from verify_windows_notice_transport import digest


class AppleSignatureInputTests(unittest.TestCase):
    """Never transfer signature observations between candidate archives."""

    def test_wrong_original(self) -> None:
        """Reject a substituted envelope before interpreting any members."""
        with patch('stage_consolidated_apple_signature.apple') as inspect:
            with self.assertRaises(ValueError):
                collect(b'wrong', 'universal')
            inspect.assert_not_called()

    def test_exact_inner(self) -> None:
        """Pass exact inner bytes through the scoped ad-hoc verifier."""
        edition = 'universal'
        base = APPLE_NAMES[edition]
        payload = b'synthetic inner'
        stream = BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            archive.writestr(base + '.zip', payload)
            archive.writestr(base + '.sha256', b'checksum')
        raw = stream.getvalue()
        with patch('stage_consolidated_apple_signature.PINS', {
                edition: (digest(raw), digest(payload))}), patch(
                'stage_consolidated_apple_signature.apple', return_value={
                    'inner_archive_sha256': digest(payload)}), patch(
                'stage_consolidated_apple_signature.report') as seal:
            self.assertEqual(collect(raw, edition), payload)
            seal.assert_called_once_with(payload, edition)


if __name__ == '__main__':
    unittest.main()
