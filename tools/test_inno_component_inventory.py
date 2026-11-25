"""Source contracts for scoped compiler observations without a trust claim."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CompilerComponentInventoryTests(unittest.TestCase):
    """Observe normal candidate inputs before and after compilation."""

    def test_scope_and_bounds(self) -> None:
        """Check the official names, file bounds and no-reparse rule."""
        code = (ROOT / 'tools/Invoke-InstallerCompiler.ps1').read_text()
        for name in ('ISCmplr.dll', 'Setup.e32', 'SetupLdr.e32', 'SetupCustomStyle.e32',
                     'ISPPBuiltins.iss', 'license.txt', 'ReparsePoint', '128MB',
                     'NOT_VERIFIED', 'FileMode]::CreateNew'):
            self.assertIn(name, code)
        self.assertIn('Compiler input inventory changed during compilation', code)
        self.assertIn('$before = @(Get-CompilerComponents', code)
        self.assertIn('$after = @(Get-CompilerComponents', code)

    def test_normal_candidate_only(self) -> None:
        """Separate the ordinary beta.61 observation from the probe and release."""
        code = (ROOT / 'tools/Invoke-InstallerCompiler.ps1').read_text()
        self.assertIn("InventoryOutput -and ($LifecycleProbe -or $AppVersion -ne '0.3.0-beta.61')", code)
        flow = (ROOT / '.github/workflows/test-installer-upgrade.yml').read_text()
        self.assertEqual(flow.count('-InventoryOutput'), 1)
        self.assertIn('AJAZZBatteryTray-beta61-inno-compiler-inventory', flow)
        self.assertIn('ajazz-beta61-inno-inventory.json', flow)
        self.assertNotIn('-InventoryOutput', (ROOT / '.github/workflows/release-beta.yml').read_text())


if __name__ == '__main__':
    unittest.main()
