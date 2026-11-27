"""Synthetic profile backup tests; no live profile or device data."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from backup_windows_profile import backup, collect, main, rehearse, verify

HISTORY = 'ajazz-' + 'A' * 64 + '-history.csv'


class ProfileBackupTests(unittest.TestCase):
    """Exercise private backup integrity, no-clobber and bounded reads."""

    def setUp(self) -> None:
        """Create only synthetic local data."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'settings.json').write_bytes(b'{"Language":"uk"}')
        (self.source / HISTORY).write_bytes(b'utc_timestamp,percent,state\n')
        (self.source / 'app.log').write_bytes(b'private log canary')
        self.target = self.root / 'backup'

    def test_copy_and_verify(self) -> None:
        """Keep exact selected bytes, exclude logs and leave the source intact."""
        before = collect(self.source)
        row = backup(self.source, self.target)
        self.assertEqual(verify(self.target), row)
        self.assertEqual(collect(self.source), before)
        self.assertFalse((self.target / 'app.log').exists())
        self.assertEqual(len(row['files']), 2)

    def test_no_clobber_or_nested_output(self) -> None:
        """Reject existing destinations and writes inside the source."""
        backup(self.source, self.target)
        with self.assertRaises(OSError):
            backup(self.source, self.target)
        with self.assertRaises(ValueError):
            backup(self.source, self.source / 'nested')
        self.assertFalse((self.source / 'nested').exists())

    def test_modified_or_extra_file(self) -> None:
        """Fail verification on modified bytes or added files."""
        backup(self.source, self.target)
        path = self.target / 'settings.json'
        original = path.read_bytes()
        path.write_bytes(b'{}')
        with self.assertRaises(ValueError):
            verify(self.target)
        path.write_bytes(original)
        (self.target / 'extra.txt').write_bytes(b'unknown')
        with self.assertRaises(ValueError):
            verify(self.target)

    def test_size_and_count_limits(self) -> None:
        """Refuse an oversized or excessive selected file set."""
        with patch('backup_windows_profile.LIMIT', 1):
            with self.assertRaises(ValueError):
                collect(self.source)
        with patch('backup_windows_profile.COUNT', 1):
            with self.assertRaises(ValueError):
                collect(self.source)

    def test_dry_run_and_verify_cli(self) -> None:
        """Dry-run writes nothing; verify cannot accept a source argument."""
        self.assertEqual(main(['--source', str(self.source), '--dry-run']), 0)
        self.assertFalse(self.target.exists())
        self.assertEqual(main(['--source', str(self.source),
                               '--backup', str(self.target)]), 0)
        self.assertEqual(main(['--verify', str(self.target)]), 0)
        self.assertEqual(main(['--verify', str(self.target),
                               '--source', str(self.source)]), 2)

    def test_link_and_nonregular_rejection(self) -> None:
        """Refuse selected directory entries and hard-linked files."""
        path = self.source / 'aula-l99-history.csv'
        path.mkdir()
        with self.assertRaises(ValueError):
            collect(self.source)
        path.rmdir()
        path.hardlink_to(self.source / HISTORY)
        with self.assertRaises(ValueError):
            collect(self.source)


    def test_rehearsal_exact_bytes(self) -> None:
        """Restore a verified copy only to a fresh dedicated sibling."""
        before = backup(self.source, self.target)
        dest = self.root / 'AJAZZ-rehearsal-test'
        self.assertEqual(rehearse(self.target, dest), before)
        self.assertEqual(collect(dest, strict=True), collect(self.source))
        self.assertEqual(verify(self.target), before)
        self.assertFalse((dest / 'backup.json').exists())
        with self.assertRaises(OSError):
            rehearse(self.target, dest)

    def test_rehearsal_invalid_destination(self) -> None:
        """Reject live-profile names and nested or unrelated destinations."""
        backup(self.source, self.target)
        for dest in (self.root / 'AJAZZBatteryTray',
                     self.target / 'AJAZZ-rehearsal-test'):
            with self.subTest(dest=dest.name), self.assertRaises(ValueError):
                rehearse(self.target, dest)
            self.assertFalse(dest.exists())

    def test_rehearsal_rejects_tampering(self) -> None:
        """Do not create a destination for a modified backup."""
        backup(self.source, self.target)
        (self.target / 'settings.json').write_bytes(b'{}')
        dest = self.root / 'AJAZZ-rehearsal-test'
        self.assertEqual(main(['--source', str(self.target),
                               '--rehearse', str(dest)]), 2)
        self.assertFalse(dest.exists())


if __name__ == '__main__':
    unittest.main()
