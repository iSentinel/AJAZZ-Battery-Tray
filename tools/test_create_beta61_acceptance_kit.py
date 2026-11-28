"""Test the exact blank acceptance kit without native binary fixtures."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from create_beta61_acceptance_kit import forms, main, stage
from review_beta61_admission import normalized_plan
from verify_hardware_acceptance_set import ARCHIVE_PROFILES


def synthetic_candidate(raw: bytes, sha: str, source: str, profile: str) -> dict:
    """Provide mocked inventory results for the three exact archive paths."""
    edition = 'windows' if profile.startswith('windows-') else profile
    key = 'app_sha256' if edition == 'windows' else 'inner_archive_sha256'
    return {'source_sha': source, 'archive_sha256': sha, 'profile': profile,
            key: normalized_plan()['assets'][edition]['release_asset_sha256']}


class BlankKitTests(unittest.TestCase):
    """Require all pinned inputs, no assumed passes and no overwritten forms."""

    def test_blank_coverage(self) -> None:
        """Generate five hardware profiles and one interactive baseline."""
        archives = {edition: Path(edition) for edition in ARCHIVE_PROFILES}
        with patch('create_beta61_acceptance_kit.normalized_identity', return_value={
                'setup_sha256': 'a' * 64}), patch(
                'create_beta61_acceptance_kit.read_local', return_value=b'fixture'), patch(
                'create_beta61_acceptance_kit.candidate', side_effect=synthetic_candidate) as parse:
            rows = forms(b'fixture', archives)
        self.assertEqual(parse.call_count, 3)
        self.assertEqual(len(rows), 6)
        self.assertEqual(sum(len(row['cases']) for row in rows.values()), 63)
        self.assertTrue(all(case == {'status': 'NOT_RUN', 'observation': ''}
                            for row in rows.values() for case in row['cases'].values()))
        self.assertEqual(len(rows['interactive-checklist.json']['cases']), 6)

    def test_invalid_identity(self) -> None:
        """Reject a substituted application identity and incomplete input sets."""
        archives = {edition: Path(edition) for edition in ARCHIVE_PROFILES}
        with patch('create_beta61_acceptance_kit.normalized_identity', return_value={}), patch(
                'create_beta61_acceptance_kit.read_local', return_value=b'fixture'), patch(
                'create_beta61_acceptance_kit.candidate', return_value={'app_sha256': 'wrong'}):
            with self.assertRaises(ValueError):
                forms(b'fixture', archives)
            with self.assertRaises(ValueError):
                forms(b'fixture', {})

    def test_output_preservation(self) -> None:
        """Do not overwrite an operator's existing checklist directory."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'kit'
            stage({'fixture.json': {'observed': True}}, root)
            original = (root / 'fixture.json').read_bytes()
            with self.assertRaises(FileExistsError):
                stage({'fixture.json': {'observed': False}}, root)
            self.assertEqual((root / 'fixture.json').read_bytes(), original)

    def test_failed_input_no_output(self) -> None:
        """An invalid input must fail before the output directory is created."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / 'evidence.zip'
            evidence.write_bytes(b'wrong')
            output = root / 'kit'
            args = ['--normalized-evidence', str(evidence), '--output-dir', str(output)]
            for edition in ARCHIVE_PROFILES:
                args.extend(['--' + edition + '-archive', edition])
            self.assertEqual(main(args), 2)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
