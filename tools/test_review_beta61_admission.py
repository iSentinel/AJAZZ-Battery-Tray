"""Candidate-bound release review regressions."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from review_beta61_admission import main, report, review
from stage_beta61_release import ASSETS, candidate
from test_stage_beta61_release import encoded, fixture
from validate_scoped_sbom_schema import digest


def scopes(coverage: str = 'INCOMPLETE') -> tuple[dict, dict]:
    """Small synthetic reviews with no trusted approval."""
    state = 'PASS' if coverage == 'COMPLETE_REPORTED' else 'NOT_RUN'
    hardware = {'coverage': coverage, 'counts': {state: 1},
                'profiles': {'windows-aj179': {'checklist_sha256': 'a' * 64}}}
    interactive = {'coverage': coverage, 'counts': {state: 1},
                   'checklist_sha256': 'b' * 64, 'local_binary_binding': 'MATCH'}
    return hardware, interactive


class BetaAdmissionReviewTests(unittest.TestCase):
    """Keep asset identity, checklist coverage, and approval distinct."""

    def test_subject_changes_only_with_candidate(self) -> None:
        """Review updates retain the subject and changed asset pins replace it."""
        plan = candidate(encoded(fixture()))
        before = report(plan, *scopes())
        hardware, interactive = scopes('COMPLETE_REPORTED')
        interactive['checklist_sha256'] = 'c' * 64
        after = report(plan, hardware, interactive)
        self.assertEqual(before['subject_sha256'], after['subject_sha256'])
        self.assertEqual(after['reported_coverage'], 'COMPLETE_REPORTED')
        self.assertEqual(after['release_admission'], 'BLOCKED')
        plan['assets']['installer']['release_asset_sha256'] = 'e' * 64
        updated = report(plan, hardware, interactive)
        self.assertNotEqual(before['subject_sha256'], updated['subject_sha256'])

    def test_reject_mixed_installer_identity(self) -> None:
        """Reject an acceptance review bound to a different EXE."""
        plan = candidate(encoded(fixture()))
        archives = {k: Path(k) for k in ASSETS}
        payload = {'installer': b'expected setup', 'windows': b'expected app'}
        hardware, _ = scopes()
        identity = {'setup_sha256': digest(payload['installer']),
                    'app_sha256': digest(b'wrong app')}
        with (patch('review_beta61_admission.collect', return_value=(plan, payload)),
              patch('review_beta61_admission.review_set', return_value=hardware),
              patch('review_beta61_admission.archive_identity', return_value=identity)):
            with self.assertRaisesRegex(ValueError, 'interactive binaries differ'):
                review(b'manifest', archives, Path('checklists'))

    def test_incomplete_exit_and_no_overwrite(self) -> None:
        """Incomplete coverage exits nonzero and an existing report is preserved."""
        result = report(candidate(encoded(fixture())), *scopes())
        with TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, out = root / 'candidate.json', root / 'report.json'
            manifest.write_bytes(encoded(fixture()))
            args = ['--manifest', str(manifest), '--checklist-dir', temp, '--output', str(out)]
            for profile in ASSETS:
                args.extend([f'--{profile}-archive', profile])
            with patch('review_beta61_admission.review', return_value=result):
                self.assertEqual(main(args), 1)
                original = out.read_bytes()
                self.assertEqual(main(args), 2)
            self.assertEqual(out.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
