"""Candidate-bound release review regressions."""

from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile
from unittest.mock import patch

from review_beta61_admission import (
    local_form_identity, main, normalized_form, normalized_identity, report, review, review_normalized,
)
from verify_interactive_acceptance import template_identity
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


def local_fixture() -> tuple[dict, bytes]:
    """Return a synthetic local-build record and its hosted ZIP."""
    from verify_inno674_setup_records import ALIGNED_SOURCE
    from verify_windows_notice_transport import MANIFEST_SHA
    row = {'schema': 'local-inno674-build-v1', 'engine_version': '6.7.4',
           'setup_sha256': 'a' * 64, 'app_sha256': 'b' * 64,
           'icons': {name: 'c' * 64 for name in (
               'AppIcon.ico', 'AppIcon-white.ico', 'AppIcon-black.ico', 'AppIcon-blue.ico')},
           'installer_source_sha256': ALIGNED_SOURCE, 'notice_manifest_sha256': MANIFEST_SHA,
           'input_identity': 'MATCH', 'source_provenance': 'NOT_VERIFIED',
           'lifecycle': 'NOT_RUN', 'distribution_compliance': 'NOT_VERIFIED',
           'release_admission': 'NOT_VERIFIED'}
    stream = BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('ajazz-notice-probe/local-build-evidence.json', encoded(row))
    return row, stream.getvalue()


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

    def test_normalized_setup_required_for_observed_case(self) -> None:
        """Only known Setup bytes can bind a completed interactive case."""
        actual = b'local normalized setup fixture'
        identity = {'app_sha256': 'a' * 64, 'setup_sha256': digest(actual)}
        form = template_identity(identity)
        self.assertEqual(normalized_form(identity, encoded(form), None)['local_binary_binding'],
                         'NOT_PROVIDED')
        form['os_build'] = '10.0.22631'
        form['cases']['RG01'] = {'status': 'PASS', 'observation': 'Observed fixture install'}
        with self.assertRaisesRegex(ValueError, 'require the exact local Setup'):
            normalized_form(identity, encoded(form), None)
        with TemporaryDirectory() as folder:
            setup = Path(folder) / 'installer.exe'
            setup.write_bytes(b'different setup')
            with self.assertRaisesRegex(ValueError, 'local Setup differs'):
                normalized_form(identity, encoded(form), setup)
            setup.write_bytes(actual)
            result = normalized_form(identity, encoded(form), setup)
        self.assertEqual(result['local_binary_binding'], 'MATCH')
        self.assertEqual(result['counts']['PASS'], 1)

    def test_local_form_semantic_equivalence(self) -> None:
        """Retain the local evidence digest while rejecting changed input identities."""
        from verify_interactive_acceptance import candidate as interactive_candidate
        row, hosted = local_fixture()
        identity = interactive_candidate(encoded(row))
        with patch('review_beta61_admission.normalized_identity', return_value=identity):
            local = json.dumps(row, separators=(',', ':')).encode()
            result = local_form_identity(local, hosted)
            self.assertEqual(result['local_build_evidence_sha256'], digest(local))
            self.assertNotEqual(result, identity)
            self.assertEqual(normalized_form(result, encoded(template_identity(result)), None)
                             ['counts']['NOT_RUN'], 6)
            for key in ('setup_sha256', 'app_sha256', 'icons', 'release_admission'):
                altered = dict(row, **{key: 'changed'})
                with self.subTest(key=key), self.assertRaises(ValueError):
                    local_form_identity(encoded(altered), hosted)

    def test_local_build_requires_setup(self) -> None:
        """No local evidence path can bypass the retained Setup requirement."""
        with self.assertRaisesRegex(ValueError, 'requires exact Setup'):
            review_normalized(b'hosted', {}, Path('checklists'), local_build=Path('local.json'))

    def test_normalized_archive_pin(self) -> None:
        """Require the exact hosted evidence archive before decoding members."""
        with self.assertRaisesRegex(ValueError, 'evidence archive differs'):
            normalized_identity(b'other hosted evidence')

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
