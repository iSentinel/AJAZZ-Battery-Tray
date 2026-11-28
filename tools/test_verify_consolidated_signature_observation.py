"""Synthetic rejection cases for exact unsigned observation review."""

import json
import unittest
from unittest.mock import patch

from stage_consolidated_signature_inputs import FILES, SOURCE
from verify_consolidated_signature_observation import check_observation, verify


def sample() -> dict:
    """Return a synthetic observation matching the reviewed identities."""
    return {'schema': 'consolidated-authenticode-observation-v1',
            'source_sha': SOURCE, 'files': {
                n: {'sha256': h, 'status': 'NotSigned', 'signature_type': 'None',
                    'signer_present': False, 'timestamp_present': False}
                for n, h in FILES.items()},
            'trusted_signing': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}


class ObservationTests(unittest.TestCase):
    """Reject substitutions, implicit approvals and non-boolean flags."""

    def test_exact_scope(self) -> None:
        """Check complete unsigned observations without approving release."""
        row = sample()
        self.assertEqual(check_observation(json.dumps(row).encode()), row)
        for key, value in (('source_sha', 'a' * 40), ('trusted_signing', 'PASS'),
                           ('release_admission', 'PASS')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                check_observation(json.dumps(dict(row, **{key: value})).encode())

    def test_file_substitution(self) -> None:
        """Require exact hashes, statuses and boolean certificate flags."""
        for key, value in (('sha256', 'a' * 64), ('status', 'Valid'),
                           ('signature_type', 'Authenticode'), ('signer_present', 0),
                           ('timestamp_present', True)):
            row = sample()
            row['files'][next(iter(FILES))][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                check_observation(json.dumps(row).encode())

    def test_archive_pin(self) -> None:
        """Reject replacement archive before ZIP interpretation."""
        with patch('verify_consolidated_signature_observation.zipfile.ZipFile') as archive:
            with self.assertRaises(ValueError):
                verify(b'not the original archive')
            archive.assert_not_called()


if __name__ == '__main__':
    unittest.main()
