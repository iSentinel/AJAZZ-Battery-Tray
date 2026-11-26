"""Synthetic checks of candidate identity and scoped lifecycle evidence."""

import unittest
from unittest.mock import patch

from stage_consolidated_signature_inputs import FILES, SOURCE
from verify_consolidated_notice_setup import (
    APP, SETUP_SHA, UNINSTALLER_SHA, check_lifecycle, unpack,
)


def lifecycle() -> dict:
    """Create synthetic clean lifecycle observations with no approval."""
    common = {'source_sha': SOURCE, 'setup_sha256': SETUP_SHA,
              'app_sha256': FILES[APP], 'release_admission': 'NOT_VERIFIED'}
    return {
        'product-lifecycle': {**common, 'schema': 'product-notice-probe-v1',
                              'installed_notices': 'MATCH', 'uninstalled_notices': 'REMOVED',
                              'tray_launch': 'NOT_OBSERVED', 'physical_acceptance': 'NOT_VERIFIED'},
        'production-shape': {**common, 'schema': 'inno-674-production-shape-v1',
                             'output_filename': 'AJAZZBatteryTray-Setup-win-x64.exe',
                             'version': '0.3.0-beta.61', 'default_program_files_install': 'MATCH',
                             'default_silent_launch': 'NOT_OBSERVED', 'uninstalled': 'REMOVED'},
        'exercised-uninstaller': {**common, 'schema': 'inno-674-exercised-uninstaller-v1',
                                  'uninstaller_sha256': UNINSTALLER_SHA,
                                  'uninstall_result': 'REMOVED'},
    }


class NoticeSetupReviewTests(unittest.TestCase):
    """Do not accept altered archive, cross-candidate or implicit approvals."""

    def test_original_archive(self) -> None:
        """Reject unknown original archives before ZIP interpretation."""
        with patch('verify_consolidated_notice_setup.zipfile.ZipFile') as archive:
            with self.assertRaises(ValueError):
                unpack(b'not the reviewed archive')
            archive.assert_not_called()

    def test_lifecycle_identity(self) -> None:
        """Require exact source, app and setup across the three records."""
        check_lifecycle(lifecycle())
        for name in lifecycle():
            for field in ('source_sha', 'app_sha256', 'setup_sha256', 'release_admission'):
                rows = lifecycle()
                rows[name][field] = 'changed'
                with self.subTest(name=name, field=field), self.assertRaises(ValueError):
                    check_lifecycle(rows)

    def test_scope(self) -> None:
        """Reject an altered uninstall outcome or implicit physical acceptance."""
        for name, field, value in (
                ('product-lifecycle', 'physical_acceptance', 'PASS'),
                ('product-lifecycle', 'tray_launch', 'OBSERVED'),
                ('exercised-uninstaller', 'uninstall_result', 'FAILED')):
            rows = lifecycle()
            rows[name][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                check_lifecycle(rows)


if __name__ == '__main__':
    unittest.main()
