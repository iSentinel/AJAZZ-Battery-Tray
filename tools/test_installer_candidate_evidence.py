"""Keep unpublished installer evidence separate from synthetic lifecycle builds."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallerEvidenceTests(unittest.TestCase):
    """The uploaded installer must be the tested non-probe candidate."""

    def test_preserve_before_synthetic_rebuild(self) -> None:
        """Only save after beta.61 upgrade checks, before beta.62 compilation."""
        workflow = (ROOT / '.github/workflows/test-installer-upgrade.yml').read_text()
        verify = workflow.index('name: Verify baseline, upgrade')
        preserve = workflow.index('name: Preserve verified beta.61 candidate')
        probe = workflow.index('name: Verify running tray closure')
        upload = workflow.index('name: Upload verified unpublished beta.61 installer')
        self.assertTrue(verify < preserve < probe < upload)
        block = workflow[preserve:probe]
        for item in ('setup_sha256', 'app_sha256', 'source_sha',
                     'lifecycle_probe = $false', "version = '0.3.0-beta.61'",
                     "release_admission = 'NOT_VERIFIED'", 'Candidate copy mismatch'):
            self.assertIn(item, block)
        self.assertIn('ajazz-beta61-candidate/AJAZZBatteryTray-Setup-win-x64.exe',
                      workflow[upload:])
        self.assertNotIn('dist/installer/', workflow[upload:])
        self.assertNotIn('if: always()', workflow[upload:])


if __name__ == '__main__':
    unittest.main()
