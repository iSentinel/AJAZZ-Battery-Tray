"""Check exact source and destination coverage of the CI-only notice fixture."""

from pathlib import Path
import re
import unittest

from verify_windows_notice_transport import NAMES

ROOT = Path(__file__).resolve().parents[1]


class NoticeInstallProbeTests(unittest.TestCase):
    """Prevent accidental inclusion of an executable or broad file wildcard."""

    def test_fixture_scope(self) -> None:
        """Require the exact reviewed notice-only source and destination paths."""
        source = (ROOT / 'installer/NoticeTransportProbe.iss').read_text()
        self.assertIn('PrivilegesRequired=lowest', source)
        self.assertIn('CreateUninstallRegKey=no', source)
        self.assertNotIn('[Run]', source)
        self.assertNotIn('[Code]', source)
        pattern = re.compile(r'^Source: "\{#NoticeRoot\}\\([^"]+)"; DestDir: "\{app\}\\Notices(?:\\([^"]+))?"; Flags: ignoreversion$', re.M)
        rows = pattern.findall(source)
        self.assertEqual(len(rows), len(NAMES))
        self.assertEqual({name.replace('\\', '/') for name, _ in rows}, NAMES)
        for name, destination in rows:
            parent = name.rpartition('\\')[0]
            self.assertEqual(destination, parent)

    def test_no_release_integration(self) -> None:
        """Keep the isolated fixture outside every release workflow."""
        for path in (ROOT / '.github/workflows').glob('release*.yml'):
            self.assertNotIn('NoticeTransportProbe', path.read_text())


if __name__ == '__main__':
    unittest.main()
