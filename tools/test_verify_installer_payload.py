"""Regression checks for exact independently extracted file inventories."""

import hashlib
from pathlib import Path
import tempfile
import unittest

from verify_installer_payload import APP, ICONS, payload, file_digest


def fixture(root: Path) -> tuple[Path, Path, str]:
    """Create a synthetic five-file payload and reference icon directory."""
    extracted, refs = root / 'extracted', root / 'refs'
    (extracted / 'app/Icons').mkdir(parents=True)
    refs.mkdir()
    (extracted / APP).write_bytes(b'synthetic app')
    for name in ICONS:
        (refs / name).write_bytes(name.encode())
        (extracted / 'app/Icons' / name).write_bytes(name.encode())
    return extracted, refs, hashlib.sha256(b'synthetic app').hexdigest()


class PayloadVerificationTests(unittest.TestCase):
    """The declared file list and each digest must agree."""

    def test_exact_files(self) -> None:
        """Match all five files, no claim about the setup engine."""
        with tempfile.TemporaryDirectory() as directory:
            extracted, refs, app = fixture(Path(directory))
            self.assertEqual(len(payload(extracted, refs, app)), 5)

    def test_mismatched_app_and_icon(self) -> None:
        """Reject changed app or source icon."""
        with tempfile.TemporaryDirectory() as directory:
            extracted, refs, app = fixture(Path(directory))
            with self.assertRaises(ValueError):
                payload(extracted, refs, '0' * 64)
            (extracted / 'app/Icons' / ICONS[0]).write_bytes(b'changed')
            with self.assertRaises(ValueError):
                payload(extracted, refs, app)

    def test_unexpected_and_missing_entries(self) -> None:
        """Reject extra files, missing files and unexpected empty directories."""
        with tempfile.TemporaryDirectory() as directory:
            extracted, refs, app = fixture(Path(directory))
            extra = extracted / 'extra'
            extra.mkdir()
            with self.assertRaises(ValueError):
                payload(extracted, refs, app)
            extra.rmdir()
            (extracted / 'app/Icons' / ICONS[0]).unlink()
            with self.assertRaises(ValueError):
                payload(extracted, refs, app)

    def test_symlink_and_size(self) -> None:
        """Reject links and excessive files without following a final link."""
        with tempfile.TemporaryDirectory() as directory:
            extracted, refs, app = fixture(Path(directory))
            with self.assertRaises(ValueError):
                file_digest(extracted / APP, 1)
            path = extracted / 'app/Icons' / ICONS[0]
            path.unlink()
            try:
                path.symlink_to(refs / ICONS[0])
            except (OSError, NotImplementedError):
                self.skipTest('symlinks unavailable')
            with self.assertRaises(ValueError):
                payload(extracted, refs, app)


if __name__ == '__main__':
    unittest.main()
