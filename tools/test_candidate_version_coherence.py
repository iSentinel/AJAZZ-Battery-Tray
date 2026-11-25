"""Guard unpublished candidate metadata and unchanged release admission."""

import plistlib
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree

from compare_inno_loader import digest
from verify_inno674_setup_records import ALIGNED_SOURCE

ROOT = Path(__file__).resolve().parents[1]


class CandidateVersionTests(unittest.TestCase):
    """Require native defaults rather than masking mismatch with overrides."""

    def test_candidate_versions(self) -> None:
        """Align Windows, installer, universal Apple version and draft tag."""
        project = ROOT / 'src/AjazzBatteryTray/AjazzBatteryTray.csproj'
        version = ElementTree.parse(project).findtext('.//Version')
        self.assertEqual(version, '0.3.0-beta.61')
        installer = ROOT / 'installer/AJAZZBatteryTray.iss'
        source = installer.read_text()
        self.assertEqual(re.findall(r'^#define AppVersion "([^"]+)"$', source, re.M), [version])
        self.assertEqual(digest(installer.read_bytes().replace(b'\r\n', b'\n')), ALIGNED_SOURCE)
        plist = plistlib.loads((ROOT / 'macos/Info.plist').read_bytes())
        self.assertEqual(plist['CFBundleShortVersionString'], version.split('-')[0])
        self.assertEqual(plist['CFBundleVersion'], '65')
        workflow = (ROOT / '.github/workflows/release-beta.yml').read_text()
        self.assertEqual(re.findall(r'^\s*TAG="(v[^"]+)"$', workflow, re.M), ['v' + version])
        self.assertIn('Require qualified candidate admission', workflow)

    def test_no_candidate_override(self) -> None:
        """Exercise real metadata defaults without admitting the release."""
        workflow = (ROOT / '.github/workflows/test-inno-674-trust.yml').read_text()
        self.assertNotIn('-p:Version=0.3.0-beta.61', workflow)
        self.assertNotIn('/DAppVersion=0.3.0-beta.61', workflow)
        self.assertIn('/DProductionNoticeCandidate=1', workflow)
        self.assertIn("release_admission = 'NOT_VERIFIED'", workflow)


if __name__ == '__main__':
    unittest.main()
