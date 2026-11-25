"""Keep the proposed upstream compiler qualification separate from shipping."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InnoUpgradeTests(unittest.TestCase):
    """Check exact asset pins and unchanged compiler/release selection."""

    def test_read_only_qualification(self) -> None:
        """Verify upstream trust before isolated portable execution."""
        text = (ROOT / '.github/workflows/test-inno-674-trust.yml').read_text()
        self.assertIn('is-6_7_4/innosetup-6.7.4.exe', text)
        self.assertIn('a549929319f9120716677c685535ca4671e4b937b5fdc87e2585f32d8eb30e8c', text)
        self.assertIn('10604576', text)
        self.assertIn('Get-AuthenticodeSignature -LiteralPath $asset', text)
        self.assertIn('gh release verify-asset is-6_7_4 $asset', text)
        self.assertIn("release_admission = 'NOT_VERIFIED'", text)
        before, after = text.split('      - name: Deploy verified upstream portable compiler', 1)
        self.assertNotIn('Start-Process', before)
        self.assertNotIn('& $asset', before)
        self.assertIn("'/PORTABLE=1'", after)
        self.assertIn("'/NOICONS'", after)
        self.assertIn('GITHUB_ACTIONS', after)
        self.assertIn('Compiler engine version: Inno Setup 6.7.4', after)
        self.assertIn('components-before.json', after)
        self.assertIn('components-after.json', after)
        fixture = (ROOT / 'installer/Inno674CompilerProbe.iss').read_text()
        self.assertNotIn('[Run]', fixture)
        self.assertNotIn('[Code]', fixture)
        self.assertIn('PrivilegesRequired=lowest', fixture)

    def test_no_migration(self) -> None:
        """Keep historical qualification and release tooling at 6.7.1."""
        wrapper = (ROOT / 'tools/Invoke-InstallerCompiler.ps1').read_text()
        self.assertIn("$expected = '6.7.1'", wrapper)
        for path in (ROOT / '.github/workflows').glob('release*.yml'):
            self.assertNotIn('6.7.4', path.read_text())

    def test_product_probe_is_distinct(self) -> None:
        """Use reviewed portable inputs, the same lifecycle and unique artifact names."""
        text = (ROOT / '.github/workflows/test-inno-674-trust.yml').read_text()
        self.assertIn("'/FAJAZZBatteryTray-Inno674-Notice-Probe-win-x64'", text)
        self.assertIn('product-components-before.json', text)
        self.assertIn('product-components-after.json', text)
        self.assertIn("'/LAUNCH=0'", text)
        self.assertIn("-CandidateName 'AJAZZBatteryTray-Inno674-Notice-Probe-win-x64.exe'", text)
        self.assertIn('name: inno674-product-notice-sbom-evidence', text)
        original = (ROOT / '.github/workflows/test-notice-install.yml').read_text()
        self.assertNotIn('6.7.4', original)
        self.assertIn('Compiler engine version: Inno Setup 6.7.1', original)


if __name__ == '__main__':
    unittest.main()
