"""Synthetic package proposal regressions without executable inputs."""

from pathlib import Path
import unittest
from unittest.mock import patch

from review_normalized_package_set import PACKAGES, check_package, proposal, review, subject_hash
from validate_scoped_sbom_schema import digest


class PackageProposalTests(unittest.TestCase):
    """Separate proposal identity, local availability and release approval."""

    def test_subject_scope(self) -> None:
        """Keep notice wrappers distinct from original application acceptance."""
        subject = proposal()
        self.assertEqual(set(subject['assets']), set(PACKAGES) | {'installer'})
        for edition in PACKAGES:
            row = subject['assets'][edition]
            self.assertNotEqual(row['sha256'], row['original_application_sha256'])
        self.assertNotEqual(subject_hash(subject), subject['acceptance_subject_sha256'])

    def test_no_setup_or_wrong_setup(self) -> None:
        """Retain immutable proposal identity and reject substituted Setup bytes."""
        paths = {k: Path(k) for k in PACKAGES}
        with patch('review_normalized_package_set.normalized_identity'), patch(
                'review_normalized_package_set.read_local', return_value=b'fixture'), patch(
                'review_normalized_package_set.check_package'):
            baseline = review(b'evidence', paths, paths, b'license')
            self.assertEqual(baseline['local_files']['installer'], 'NOT_PROVIDED')
            self.assertEqual(baseline['release_admission'], 'BLOCKED')
            with self.assertRaisesRegex(ValueError, 'Setup differs'):
                review(b'evidence', paths, paths, b'license', Path('wrong.exe'))
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                review(b'evidence', {}, paths, b'license')

    def test_setup_availability_does_not_approve(self) -> None:
        """Matching fixture bytes change availability, never subject or approval."""
        paths = {k: Path(k) for k in PACKAGES}
        subject = proposal()
        subject['assets']['installer']['sha256'] = digest(b'fixture')
        with patch('review_normalized_package_set.normalized_identity'), patch(
                'review_normalized_package_set.read_local', return_value=b'fixture'), patch(
                'review_normalized_package_set.check_package'), patch(
                'review_normalized_package_set.proposal', return_value=subject):
            baseline = review(b'evidence', paths, paths, b'license')
            matched = review(b'evidence', paths, paths, b'license', Path('setup.exe'))
        self.assertEqual(matched['local_files']['installer'], 'MATCH')
        self.assertEqual(matched['proposal_sha256'], baseline['proposal_sha256'])
        self.assertEqual(matched['package_selection'], 'NOT_VERIFIED')
        self.assertEqual(matched['release_admission'], 'BLOCKED')

    def test_package_substitution(self) -> None:
        """Reject a changed wrapper before parsing its members."""
        with patch('review_normalized_package_set.verify_zip') as verify:
            with self.assertRaisesRegex(ValueError, 'package digest differs'):
                check_package(b'wrong', 'windows', b'original', b'license')
            verify.assert_not_called()
        with patch('review_normalized_package_set.PACKAGES', {
                'windows': ('fixture.zip', digest(b'fixture'), 'beta')}), patch(
                'review_normalized_package_set.verify_zip') as verify:
            with self.assertRaisesRegex(ValueError, 'original application archive differs'):
                check_package(b'fixture', 'windows', b'wrong', b'license')
            verify.assert_not_called()


if __name__ == '__main__':
    unittest.main()
