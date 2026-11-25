"""Regression guards for local interactive acceptance records."""

import json
import unittest

from verify_interactive_acceptance import CASES, template, verify


def encode(row: dict) -> bytes:
    """Serialize a synthetic local record."""
    return json.dumps(row).encode()


def fixture() -> bytes:
    """Build a synthetic qualified identity, not an actual acceptance."""
    return encode({'schema': 'inno-674-migration-evidence-v1', 'production_shape': 'MATCH_SCOPED',
                   'scoped_native_evidence': 'MATCH', 'engine_version': '6.7.4',
                   'release_admission': 'NOT_VERIFIED', 'source_sha': 'a' * 40,
                   'setup_sha256': 'b' * 64, 'app_sha256': 'c' * 64})


class InteractiveAcceptanceTests(unittest.TestCase):
    """Never transfer observations between different builds."""

    def test_untested(self) -> None:
        """A generated checklist is entirely untested."""
        raw = fixture()
        result = verify(raw, encode(template(raw)))
        self.assertEqual(result['counts']['NOT_RUN'], 6)
        self.assertEqual(result['release_admission'], 'NOT_VERIFIED')

    def test_wrong_identity_and_coverage(self) -> None:
        """Reject a missing row or mismatched artifact."""
        raw = fixture()
        data = template(raw)
        data['candidate']['app_sha256'] = 'd' * 64
        with self.assertRaises(ValueError):
            verify(raw, encode(data))
        data = template(raw)
        del data['cases']['RG01']
        with self.assertRaises(ValueError):
            verify(raw, encode(data))

    def test_reported_pass_not_admitted(self) -> None:
        """Complete self-reports do not establish independent acceptance."""
        raw = fixture()
        data = template(raw)
        for key in CASES:
            data['cases'][key] = {'status': 'PASS', 'observation': 'Synthetic test observation'}
        with self.assertRaises(ValueError):
            verify(raw, encode(data))
        data['os_build'] = '10.0.26100'
        result = verify(raw, encode(data))
        self.assertEqual(result['coverage'], 'COMPLETE_REPORTED')
        self.assertEqual(result['interactive_acceptance'], 'NOT_INDEPENDENTLY_VERIFIED')
        self.assertEqual(result['release_admission'], 'NOT_VERIFIED')
        data['cases']['RG01']['observation'] = ''
        with self.assertRaises(ValueError):
            verify(raw, encode(data))


if __name__ == '__main__':
    unittest.main()
