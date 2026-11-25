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


if __name__ == '__main__':
    unittest.main()
