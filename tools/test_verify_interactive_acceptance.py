"""Regression guards for local interactive acceptance records."""

import json
from pathlib import Path
import tempfile
import unittest

from verify_interactive_acceptance import CASES, main, template, verify
from validate_scoped_sbom_schema import digest
from verify_inno674_setup_records import ALIGNED_SOURCE
from verify_windows_notice_transport import MANIFEST_SHA


def encode(row: dict) -> bytes:
    """Serialize a synthetic local record."""
    return json.dumps(row).encode()


def fixture() -> bytes:
    """Build a synthetic qualified identity, not an actual acceptance."""
    return encode({'schema': 'inno-674-migration-evidence-v1', 'production_shape': 'MATCH_SCOPED',
                   'scoped_native_evidence': 'MATCH', 'engine_version': '6.7.4',
                   'release_admission': 'NOT_VERIFIED', 'source_sha': 'a' * 40,
                   'setup_sha256': 'b' * 64, 'app_sha256': 'c' * 64})


def local_fixture() -> dict:
    """Construct a private synthetic build record, with no lifecycle qualification."""
    return {'schema': 'local-inno674-build-v1', 'engine_version': '6.7.4',
            'setup_sha256': digest(b'synthetic setup'), 'app_sha256': digest(b'synthetic app'),
            'icons': {name: 'd' * 64 for name in
                      ('AppIcon.ico', 'AppIcon-white.ico', 'AppIcon-black.ico', 'AppIcon-blue.ico')},
            'installer_source_sha256': ALIGNED_SOURCE, 'notice_manifest_sha256': MANIFEST_SHA,
            'input_identity': 'MATCH', 'source_provenance': 'NOT_VERIFIED',
            'lifecycle': 'NOT_RUN', 'distribution_compliance': 'NOT_VERIFIED',
            'release_admission': 'NOT_VERIFIED'}


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

    def test_local_binary_binding(self) -> None:
        """Require exact setup and app bytes, without claiming signature trust."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            setup, app = root / 'setup.exe', root / 'app.exe'
            setup.write_bytes(b'synthetic setup')
            app.write_bytes(b'synthetic app')
            row = json.loads(fixture())
            row.update(setup_sha256=digest(setup.read_bytes()),
                       app_sha256=digest(app.read_bytes()))
            raw = encode(row)
            checklist = encode(template(raw))
            self.assertEqual(verify(raw, checklist)['local_binary_binding'], 'NOT_PROVIDED')
            result = verify(raw, checklist, setup, app)
            self.assertEqual(result['local_binary_binding'], 'MATCH')
            self.assertEqual(result['release_admission'], 'NOT_VERIFIED')
            self.assertEqual(result['counts']['NOT_RUN'], 6)
            for left, right in ((setup, None), (None, app), (app, setup)):
                with self.assertRaises(ValueError):
                    verify(raw, checklist, left, right)
            app.write_bytes(b'changed app')
            with self.assertRaises(ValueError):
                verify(raw, checklist, setup, app)

    def test_cli_paired_binary_options(self) -> None:
        """Fail without creating output when a binary is missing or mismatched."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw, setup, app = root / 'candidate.json', root / 'setup.exe', root / 'app.exe'
            setup.write_bytes(b'synthetic setup')
            app.write_bytes(b'synthetic app')
            row = json.loads(fixture())
            row.update(setup_sha256=digest(setup.read_bytes()),
                       app_sha256=digest(app.read_bytes()))
            raw.write_bytes(encode(row))
            output = root / 'checklist.json'
            args = ['--candidate', str(raw), '--output', str(output)]
            self.assertEqual(main(args + ['--setup', str(setup)]), 2)
            self.assertFalse(output.exists())
            self.assertEqual(main(args + ['--setup', str(setup), '--app', str(setup)]), 2)
            self.assertFalse(output.exists())
            self.assertEqual(main(args + ['--setup', str(setup), '--app', str(app)]), 0)
            self.assertEqual(json.loads(output.read_text()), template(raw.read_bytes()))

    def test_private_local_build(self) -> None:
        """Require local binaries and keep native and local identities disjoint."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw, setup, app = root / 'build.json', root / 'setup.exe', root / 'app.exe'
            raw.write_bytes(encode(local_fixture()))
            setup.write_bytes(b'synthetic setup')
            app.write_bytes(b'synthetic app')
            output = root / 'checklist.json'
            args = ['--candidate', str(raw), '--output', str(output)]
            self.assertEqual(main(args), 2)
            self.assertFalse(output.exists())
            self.assertEqual(main(args + ['--setup', str(setup), '--app', str(app)]), 0)
            data = json.loads(output.read_text())
            self.assertNotIn('source_sha', data['candidate'])
            self.assertEqual(data['candidate']['native_qualification'], 'NOT_VERIFIED')
            with self.assertRaises(ValueError):
                verify(raw.read_bytes(), encode(data))
            result = verify(raw.read_bytes(), encode(data), setup, app)
            self.assertEqual(result['local_binary_binding'], 'MATCH')
            self.assertEqual(result['counts']['NOT_RUN'], 6)
            self.assertEqual(result['release_admission'], 'NOT_VERIFIED')
            with self.assertRaises(ValueError):
                verify(fixture(), encode(data), setup, app)

    def test_invalid_local_evidence(self) -> None:
        """Reject altered pins and invented native or release qualification."""
        for key, value in (
                ('installer_source_sha256', 'e' * 64),
                ('notice_manifest_sha256', 'e' * 64),
                ('lifecycle', 'MATCH'), ('release_admission', 'PASS'),
                ('source_sha', 'a' * 40), ('icons', {})):
            with self.subTest(key=key), self.assertRaises(ValueError):
                template(encode(dict(local_fixture(), **{key: value})))

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
