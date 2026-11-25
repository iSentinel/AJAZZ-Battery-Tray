"""Keep the proposed upstream compiler qualification separate from shipping."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InnoUpgradeTests(unittest.TestCase):
    """Check exact asset pins and unchanged compiler/release selection."""

    def test_read_only_qualification(self) -> None:
        """Only verify the proposed vendor binary, never execute it."""
        text = (ROOT / '.github/workflows/test-inno-674-trust.yml').read_text()
        self.assertIn('is-6_7_4/innosetup-6.7.4.exe', text)
        self.assertIn('a549929319f9120716677c685535ca4671e4b937b5fdc87e2585f32d8eb30e8c', text)
        self.assertIn('10604576', text)
        self.assertIn('Get-AuthenticodeSignature -LiteralPath $asset', text)
        self.assertIn('gh release verify-asset is-6_7_4 $asset', text)
        self.assertIn("release_admission = 'NOT_VERIFIED'", text)
        self.assertNotIn('Start-Process', text)
        self.assertNotIn('& $asset', text)

    def test_no_migration(self) -> None:
        """Keep historical qualification and release tooling at 6.7.1."""
        wrapper = (ROOT / 'tools/Invoke-InstallerCompiler.ps1').read_text()
        self.assertIn("$expected = '6.7.1'", wrapper)
        for path in (ROOT / '.github/workflows').glob('release*.yml'):
            self.assertNotIn('6.7.4', path.read_text())


if __name__ == '__main__':
    unittest.main()
