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

    def test_uninstaller_evidence_bound_to_exercised_upgrade(self) -> None:
        """Capture before uninstall; publish only after successful lifecycle checks."""
        workflow = (ROOT / '.github/workflows/test-installer-upgrade.yml').read_text()
        capture = workflow.index('# Retain only the exact executable')
        execute = workflow.index('Start-Process -FilePath $uninstaller', capture)
        checked = workflow.index("throw 'Uninstall failed'", execute)
        manifest = workflow.index("schema = 'installer-uninstaller-v1'")
        probe = workflow.index('name: Verify running tray closure')
        upload = workflow.index('name: Upload exercised unpublished beta.61 uninstaller')
        end = workflow.index('name: Upload normal candidate compiler inventory')
        self.assertTrue(capture < execute < checked < manifest < probe < upload < end)
        for item in ('Uninstaller copy mismatch', 'ReparsePoint', '16777216'):
            self.assertIn(item, workflow[capture:execute])
        for item in ('source_sha', 'setup_sha256', 'app_sha256',
                     'baseline_uninstaller_sha256', 'uninstaller_sha256',
                     "uninstall_smoke = 'PASS'", "engine_attribution = 'NOT_VERIFIED'",
                     "release_admission = 'NOT_VERIFIED'"):
            self.assertIn(item, workflow[manifest:probe])
        block = workflow[upload:end]
        self.assertIn('ajazz-beta61-uninstaller/unins000.exe', block)
        self.assertIn('ajazz-beta61-uninstaller/uninstaller.json', block)
        self.assertNotIn('unins000.dat', block)
        self.assertNotIn('if: always()', block)


if __name__ == '__main__':
    unittest.main()
