"""Source-level guard for the reviewed installer compiler selection."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallerCompilerContractTests(unittest.TestCase):
    """Prevent unreviewed fallback downloads and preserve release hold."""

    def test_both_workflows_use_wrapper(self) -> None:
        """Only the common compiler wrapper should run in either workflow."""
        for name, count in (("release-beta.yml", 1), ("test-installer-upgrade.yml", 2)):
            raw = (ROOT / ".github/workflows" / name).read_text()
            self.assertEqual(raw.count("./tools/Invoke-InstallerCompiler.ps1"), count)
            self.assertNotIn("choco install innosetup", raw.lower())
            self.assertNotIn("& $iscc", raw)

    def test_release_hold_and_fixture_isolation(self) -> None:
        """Do not enable publication or ship the synthetic lifecycle probe."""
        release = (ROOT / ".github/workflows/release-beta.yml").read_text()
        upgrade = (ROOT / ".github/workflows/test-installer-upgrade.yml").read_text()
        self.assertIn("BLOCKED: release admission not yet qualified", release)
        self.assertNotIn("-LifecycleProbe", release)
        self.assertIn("-AppVersion '0.3.0-beta.62' -LifecycleProbe", upgrade)
        self.assertIn("-AppVersion '0.3.0-beta.61'", upgrade)

    def test_single_compiler_path_is_array(self) -> None:
        """Avoid indexing the first character of a scalar PowerShell string."""
        raw = (ROOT / "tools/Invoke-InstallerCompiler.ps1").read_text()
        self.assertIn("$candidates = @(@(", raw)
        self.assertIn("Select-Object -Unique)", raw)
        self.assertIn("$iscc = $candidates[0]", raw)

    def test_engine_gate_not_frontend_metadata(self) -> None:
        """ISCC frontend version is observational; engine must match exactly."""
        raw = (ROOT / "tools/Invoke-InstallerCompiler.ps1").read_text()
        self.assertIn("frontend file version observation", raw)
        self.assertNotIn("if ($actual -ne $expected)", raw)
        self.assertIn(' -cne "Compiler engine version: Inno Setup $expected"', raw)

    def test_version_observation_contract(self) -> None:
        """Retain reviewed version and identity observations, not a trust claim."""
        raw = (ROOT / "tools/Invoke-InstallerCompiler.ps1").read_text()
        for marker in ("$expected = '6.7.1'", "Compiler engine version: Inno Setup",
                       "Get-FileHash", "Get-AuthenticodeSignature", "trust not verified"):
            self.assertIn(marker, raw)
        self.assertNotIn("choco install", raw.lower())


if __name__ == '__main__':
    unittest.main()
