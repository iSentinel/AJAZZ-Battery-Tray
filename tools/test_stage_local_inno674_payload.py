"""Synthetic local payload staging and refusal tests."""

import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from stage_local_inno674_payload import EXE, checkout, stage
from validate_scoped_sbom_schema import digest
from verify_hardware_acceptance import ICONS

SOURCE = 'a' * 40


class LocalPayloadTests(unittest.TestCase):
    """Preserve exact source icons and refuse to overwrite a staged app."""

    def setUp(self) -> None:
        """Create a synthetic portable archive and matching source assets."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        assets = self.root / 'src/AjazzBatteryTray/Assets'
        assets.mkdir(parents=True)
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w') as archive:
            archive.writestr(EXE, b'synthetic app')
            for name in ICONS:
                data = name.encode()
                archive.writestr(name, data)
                (assets / Path(name).name).write_bytes(data)
        self.raw = out.getvalue()

    def stage(self, sha: str | None = None) -> dict:
        """Mock only native inventory and checkout, not archive or staging checks."""
        with patch('stage_local_inno674_payload.checkout'), patch(
                'verify_hardware_acceptance.windows',
                return_value={'app_sha256': digest(b'synthetic app')}):
            return stage(self.raw, sha or digest(self.raw), SOURCE, self.root)

    def test_exact_staging_and_no_overwrite(self) -> None:
        """Stage only the EXE and preserve existing output on repeat."""
        result = self.stage()
        target = self.root / 'dist/app'
        self.assertEqual(result['app_sha256'], digest(b'synthetic app'))
        self.assertEqual(list(target.iterdir()), [target / EXE])
        with self.assertRaises(FileExistsError):
            self.stage()
        self.assertEqual((target / EXE).read_bytes(), b'synthetic app')

    def test_wrong_archive_or_icon(self) -> None:
        """Reject invalid archive hash or different source icon before writing."""
        with self.assertRaises(ValueError):
            self.stage('f' * 64)
        (self.root / 'src/AjazzBatteryTray/Assets/AppIcon.ico').write_bytes(b'changed')
        with self.assertRaises(ValueError):
            self.stage()
        self.assertFalse((self.root / 'dist').exists())

    def test_dirty_or_wrong_checkout(self) -> None:
        """Require the exact clean tracked source before accepting local input."""
        for values in ((str(self.root), 'b' * 40),
                       (str(self.root), SOURCE, ' M installer/file')):
            with patch('stage_local_inno674_payload.subprocess.check_output',
                       side_effect=values), self.assertRaises(ValueError):
                checkout(self.root, SOURCE)

    def test_unsafe_dist(self) -> None:
        """Reject a directory symlink before staging any payload."""
        other = self.root / 'other'
        other.mkdir()
        try:
            (self.root / 'dist').symlink_to(other, target_is_directory=True)
        except OSError:
            self.skipTest('symlink unavailable')
        with self.assertRaises(ValueError):
            self.stage()
        self.assertEqual(list(other.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
