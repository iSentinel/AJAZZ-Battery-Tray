"""Test the exact notice transport contract with synthetic pinned manifests."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from inventory_dotnet_bundle import BundleError
from verify_windows_notice_transport import (
    NAMES, archive_bytes, archive_files, digest, tree_files, verify_files,
)


def fixture() -> dict[str, bytes]:
    """Generate nine synthetic files and an explicit manifest."""
    files = {name: name.encode() for name in NAMES if name != 'manifest.json'}
    rows = [{'path': name, 'bytes': len(data), 'sha256': digest(data)}
            for name, data in sorted(files.items())]
    files['manifest.json'] = json.dumps({'files': rows,
                                        'release_admission': 'NOT_VERIFIED'}).encode()
    return files


class NoticeTransportTests(unittest.TestCase):
    """Verify transport without inferring legal compliance."""

    def test_zip_roundtrip(self) -> None:
        """Deterministic ZIP requires all exact bytes and rejects a suffix."""
        files = fixture()
        with patch('verify_windows_notice_transport.MANIFEST_SHA', digest(files['manifest.json'])):
            raw = archive_bytes(files)
            self.assertEqual(raw, archive_bytes(dict(reversed(list(files.items())))))
            self.assertEqual(archive_files(raw), files)
            with self.assertRaises(BundleError):
                archive_files(raw + b'x')

    def test_changed_or_missing(self) -> None:
        """Reject missing files, case aliases, or changed payloads."""
        files = fixture()
        with patch('verify_windows_notice_transport.MANIFEST_SHA', digest(files['manifest.json'])):
            self.assertEqual(verify_files(files)['release_admission'], 'NOT_VERIFIED')
            for name in ('AJAZZ/LICENSE', 'manifest.json'):
                bad = dict(files)
                bad[name] += b'x'
                with self.assertRaises(BundleError):
                    verify_files(bad)
                del bad[name]
                with self.assertRaises(BundleError):
                    verify_files(bad)

    def test_tree(self) -> None:
        """Require exact directory contents and reject link substitution."""
        files = fixture()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, data in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            self.assertEqual(tree_files(root), files)
            extra = root / 'extra'
            extra.mkdir()
            with self.assertRaises(BundleError):
                tree_files(root)
            extra.rmdir()
            path = root / 'AJAZZ/LICENSE'
            path.unlink()
            try:
                path.symlink_to(root / 'manifest.json')
            except OSError:
                return
            with self.assertRaises(BundleError):
                tree_files(root)


if __name__ == '__main__':
    unittest.main()
