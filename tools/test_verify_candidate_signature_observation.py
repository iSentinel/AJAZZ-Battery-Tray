"""Test candidate-bound unsigned observations without inventing signer trust."""

import json
import unittest

from compare_inno_loader import digest
from verify_candidate_signature_observation import verify


def encode(value: dict) -> bytes:
    """Encode a synthetic evidence document."""
    return json.dumps(value, sort_keys=True).encode()


def fixture() -> tuple[dict, dict, dict]:
    """Build a complete synthetic unsigned observation and identity chain."""
    identity = {'source_sha': 'a' * 40, 'setup_sha256': 'b' * 64, 'app_sha256': 'c' * 64}
    removed = {'schema': 'inno-674-exercised-uninstaller-v1', **identity,
               'uninstaller_sha256': 'd' * 64, 'uninstall_result': 'REMOVED',
               'release_admission': 'NOT_VERIFIED'}
    joined = {'schema': 'inno-674-migration-evidence-v1', **identity,
              'production_shape': 'MATCH_SCOPED', 'scoped_native_evidence': 'MATCH',
              'documents': {'exercised-uninstaller': digest(encode(removed))},
              'release_admission': 'NOT_VERIFIED'}
    observed = {'schema': 'candidate-authenticode-observation-v1',
                'source_sha': identity['source_sha'], 'release_admission': 'NOT_VERIFIED',
                'files': {role: {'sha256': sha, 'status': 'NotSigned',
                                 'signature_type': 'None', 'signer_present': False,
                                 'timestamp_present': False}
                          for role, sha in (('setup', 'b' * 64), ('app', 'c' * 64),
                                            ('uninstaller', 'd' * 64))}}
    return observed, joined, removed


class SignatureObservationTests(unittest.TestCase):
    """Reject unrelated bytes, unreviewed signing and incomplete observations."""

    def test_unsigned(self) -> None:
        """A valid unsigned observation is not release admission."""
        result = verify(*(encode(x) for x in fixture()))
        self.assertEqual(result['native_unsigned_observation'], 'MATCH')
        self.assertEqual(result['trusted_signing'], 'NOT_VERIFIED')
        self.assertEqual(result['release_admission'], 'NOT_VERIFIED')

    def test_reject(self) -> None:
        """Reject changed hash, missing role and unexpected native signature."""
        for field, value in (('sha256', 'e' * 64), ('status', 'Valid'),
                             ('signer_present', True), ('signature_type', 'Catalog')):
            observed, joined, removed = fixture()
            observed['files']['setup'][field] = value
            with self.assertRaises(ValueError):
                verify(encode(observed), encode(joined), encode(removed))
        observed, joined, removed = fixture()
        del observed['files']['app']
        with self.assertRaises(ValueError):
            verify(encode(observed), encode(joined), encode(removed))
        observed, joined, removed = fixture()
        removed['uninstaller_sha256'] = 'f' * 64
        with self.assertRaises(ValueError):
            verify(encode(observed), encode(joined), encode(removed))


if __name__ == '__main__':
    unittest.main()
