"""Synthetic tests for cross-profile hardware acceptance aggregation."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from verify_hardware_acceptance import PROFILES, template
from verify_hardware_acceptance_set import ARCHIVE_PROFILES, review_set

SOURCE = 'a' * 40


def synthetic_identity(raw: bytes, sha: str, source: str, profile: str) -> dict:
    """Simulate the existing candidate verifier without native executable bytes."""
    return {'source_sha': source, 'archive_sha256': sha, 'profile': profile}


class HardwareAcceptanceSetTests(unittest.TestCase):
    """Ensure exact profile coverage without promoting self-reported claims."""

    def setUp(self) -> None:
        """Prepare three synthetic archives and five bound checklist records."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.archives = {}
        for index, (edition, profiles) in enumerate(ARCHIVE_PROFILES.items()):
            sha = str(index) * 64
            path = self.root / (edition + '.zip')
            path.write_bytes(b'synthetic')
            self.archives[edition] = (path, sha)
            for profile in profiles:
                identity = synthetic_identity(b'', sha, SOURCE, profile)
                self.write_checklist(profile, template(identity))

    def write_checklist(self, profile: str, row: dict) -> None:
        """Write a synthetic original checklist."""
        (self.root / (profile + '.checklist.json')).write_text(json.dumps(row))

    def aggregate(self, source: str = SOURCE) -> dict:
        """Exercise review logic with mocked native inventory parsing only."""
        with patch('verify_hardware_acceptance_set.candidate',
                   side_effect=synthetic_identity) as verify:
            result = review_set(source, self.archives, self.root)
            self.assertEqual(verify.call_count, 3)
            return result

    def test_blank_generation(self) -> None:
        """All five profiles count as NOT_RUN, never as physical PASS."""
        result = self.aggregate()
        self.assertEqual(set(result['profiles']), set(PROFILES))
        self.assertEqual(result['counts']['NOT_RUN'], 57)
        self.assertEqual(result['coverage'], 'INCOMPLETE')
        self.assertEqual(result['release_admission'], 'NOT_VERIFIED')

    def test_wrong_generation(self) -> None:
        """Reject stale source or archive bindings."""
        with self.assertRaises(ValueError):
            self.aggregate('b' * 40)
        path, _ = self.archives['windows']
        self.archives['windows'] = path, 'f' * 64
        with self.assertRaises(ValueError):
            self.aggregate()

    def test_missing_profile(self) -> None:
        """Never silently omit a required device profile."""
        (self.root / 'windows-aula.checklist.json').unlink()
        with self.assertRaises(ValueError):
            self.aggregate()

    def test_self_reported_complete(self) -> None:
        """Even 57 self-reported passes do not approve the release."""
        for edition, profiles in ARCHIVE_PROFILES.items():
            for profile in profiles:
                row = template(synthetic_identity(b'', self.archives[edition][1],
                                                  SOURCE, profile))
                row.update(os_build='synthetic', device_model={
                    'windows-aj179': 'AJ179 APEX', 'windows-aj159': 'AJ159 APEX',
                    'windows-aula': 'AULA L99'}.get(profile, 'Synthetic Mac'))
                for key in row['cases']:
                    row['cases'][key] = {'status': 'PASS', 'observation': 'Synthetic'}
                self.write_checklist(profile, row)
        result = self.aggregate()
        self.assertEqual(result['counts']['PASS'], 57)
        self.assertEqual(result['coverage'], 'COMPLETE_REPORTED')
        self.assertEqual(result['physical_acceptance'], 'NOT_INDEPENDENTLY_VERIFIED')


if __name__ == '__main__':
    unittest.main()
