"""Reject mixed-run evidence and missing document sets."""

import unittest
from unittest.mock import patch

from build_product_notice_sbom import encode
from verify_inno674_migration_evidence import LINKS, NAMES, verify, digest, production_shape, local_build
from verify_inno674_setup_records import ALIGNED_SOURCE, PRODUCTION_SOURCE
from verify_windows_notice_transport import MANIFEST_SHA


class MigrationEvidenceTests(unittest.TestCase):
    """All links must match before downstream scope checks."""

    def test_link_chain(self) -> None:
        """Build a synthetic hash chain; change one earlier document."""
        raw = [encode({}) for _ in NAMES]
        for index in range(len(NAMES)):
            raw[index] = encode({key: digest(raw[target])
                                 for i, key, target in LINKS if i == index})
        with patch('verify_inno674_migration_evidence.identity', return_value={}), \
                patch('verify_inno674_migration_evidence.binding'), \
                patch('verify_inno674_migration_evidence.outcomes'):
            self.assertEqual(verify(raw)['release_admission'], 'NOT_VERIFIED')
            raw[2] = encode({'different': True})
            with self.assertRaises(ValueError):
                verify(raw)

    def test_missing(self) -> None:
        """A missing document cannot be treated as success."""
        with self.assertRaises(ValueError):
            verify([])

    def test_production_shape(self) -> None:
        """Require the exact source, identity and observed default install."""
        result = {'source_sha': 'a' * 40, 'setup_sha256': 'b' * 64,
                  'app_sha256': 'c' * 64, 'release_admission': 'NOT_VERIFIED'}
        record = {'installer_source_lf_sha256': PRODUCTION_SOURCE}
        shape = {'schema': 'inno-674-production-shape-v1', **result,
                 'output_filename': 'AJAZZBatteryTray-Setup-win-x64.exe',
                 'version': '0.3.0-beta.61', 'default_program_files_install': 'MATCH',
                 'default_silent_launch': 'NOT_OBSERVED', 'uninstalled': 'REMOVED'}
        self.assertEqual(production_shape(encode(shape), result, record)['production_shape'],
                         'MATCH_SCOPED')
        for bad in (dict(shape, setup_sha256='d' * 64),
                    dict(shape, default_program_files_install='FAILED'),
                    dict(shape, output_filename='other.exe')):
            with self.assertRaises(ValueError):
                production_shape(encode(bad), result, record)
        with self.assertRaises(ValueError):
            production_shape(encode(shape), result, {'installer_source_lf_sha256': 'wrong'})

    def test_local_build_binding(self) -> None:
        """Reject stale setup, icon, notice and source observations."""
        result = {'setup_sha256': 'a' * 64, 'app_sha256': 'b' * 64,
                  'production_shape': 'MATCH_SCOPED'}
        icons = {name: 'c' * 64 for name in ('AppIcon.ico', 'AppIcon-white.ico',
                 'AppIcon-black.ico', 'AppIcon-blue.ico')}
        files = {'AJAZZBatteryTray.exe': result['app_sha256'],
                 'Notices/manifest.json': MANIFEST_SHA,
                 **{'Icons/' + name: sha for name, sha in icons.items()}}
        solid = {'files': [{'name': name, 'sha256': sha} for name, sha in files.items()]}
        records = {'installer_source_lf_sha256': ALIGNED_SOURCE}
        row = {'schema': 'local-inno674-build-v1', 'engine_version': '6.7.4',
               'setup_sha256': result['setup_sha256'], 'app_sha256': result['app_sha256'],
               'icons': icons, 'installer_source_sha256': ALIGNED_SOURCE,
               'notice_manifest_sha256': MANIFEST_SHA, 'input_identity': 'MATCH',
               'source_provenance': 'NOT_VERIFIED', 'lifecycle': 'NOT_RUN',
               'distribution_compliance': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}
        self.assertEqual(local_build(encode(row), result, solid, records)['local_build'],
                         'MATCH_SCOPED')
        for bad in (dict(row, setup_sha256='d' * 64), dict(row, icons={}),
                    dict(row, notice_manifest_sha256='d' * 64),
                    dict(row, source_provenance='VERIFIED')):
            with self.assertRaises(ValueError):
                local_build(encode(bad), result, solid, records)
        with self.assertRaises(ValueError):
            local_build(encode(row), result, solid,
                        {'installer_source_lf_sha256': PRODUCTION_SOURCE})


if __name__ == '__main__':
    unittest.main()
