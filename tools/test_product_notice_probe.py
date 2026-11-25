"""Check the candidate-only notice mode without altering release defaults."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ProductNoticeProbeTests(unittest.TestCase):
    """Require opt-in exact payload and separate CI-only output."""

    def test_guarded_notice_payload(self) -> None:
        """Require the same exact notice files as the proven isolated fixture."""
        source = (ROOT / 'installer/AJAZZBatteryTray.iss').read_text()
        fixture = (ROOT / 'installer/NoticeTransportProbe.iss').read_text()
        rows = fixture.split('[Files]\n', 1)[1].strip()
        self.assertIn('#ifdef ProductNoticeProbe\n' + rows + '\n#endif', source)
        self.assertIn('#error NoticeRoot requires ProductNoticeProbe', source)
        self.assertIn('#error ProductNoticeProbe requires NoticeRoot', source)
        self.assertIn('#error ProductNoticeProbe cannot be combined with InstallerLifecycleProbe', source)
        self.assertIn('OutputBaseFilename=AJAZZBatteryTray-Notice-Probe-win-x64', source)
        self.assertIn('#else\nOutputBaseFilename=AJAZZBatteryTray-Setup-win-x64\n#endif', source)

    def test_candidate_only_workflow(self) -> None:
        """Keep explicit probe mode out of release workflows and disable launch."""
        for path in (ROOT / '.github/workflows').glob('release*.yml'):
            self.assertNotIn('ProductNoticeProbe', path.read_text())
        workflow = (ROOT / '.github/workflows/test-notice-install.yml').read_text()
        self.assertIn("'/DProductNoticeProbe=1'", workflow)
        self.assertIn("'/LAUNCH=0'", workflow)
        self.assertIn("name: product-notice-probe-evidence", workflow)
        self.assertIn("release_admission = 'NOT_VERIFIED'", workflow)

    def test_upgrade_probe_scope(self) -> None:
        """Keep baseline pinned, no launch and repair checks explicit."""
        source = (ROOT / 'tools/Test-ProductNoticeUpgrade.ps1').read_text()
        self.assertIn("GITHUB_ACTIONS -cne 'true'", source)
        self.assertIn("555b957b809c2f1bb4228c10a818abadad2df78e455925871713ee7779970672", source)
        self.assertIn("Install-Checked $baseline '0.3.0-beta.60'", source)
        self.assertEqual(source.count("Install-Checked $candidate '0.3.0-beta.61'"), 2)
        self.assertIn("Check-Candidate 'product-upgrade-notices.json'", source)
        self.assertIn("Check-Candidate 'product-reinstall-notices.json'", source)
        self.assertIn("'/LAUNCH=0'", source)
        self.assertIn("synthetic_user_data = 'PRESERVED'", source)
        self.assertIn("release_admission = 'NOT_VERIFIED'", source)
        workflow = (ROOT / '.github/workflows/test-notice-install.yml').read_text()
        self.assertIn('./tools/Test-ProductNoticeUpgrade.ps1', workflow)
        self.assertIn('name: product-notice-upgrade-evidence', workflow)


if __name__ == '__main__':
    unittest.main()
