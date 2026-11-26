"""Check release asset comparison and evidence input validation."""

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from compare_release_builds import compare, inspect, run


class ReleaseBuildComparisonTests(unittest.TestCase):
    """Exercise differences, missing files and ambiguous input provenance."""

    def test_equal_assets(self) -> None:
        """Exact release asset match is independent of the outer CI ZIP."""
        self.assertEqual(compare({'asset_sha256': 'a'}, {'asset_sha256': 'a'}),
                         {'result': 'MATCH', 'changed_members': []})

    def test_packaging_differs(self) -> None:
        """Equal member hashes cannot turn different packaged bytes into a pass."""
        left = {'asset_sha256': 'a', 'payload_sha256': {'app': 'b'}}
        right = {'asset_sha256': 'c', 'payload_sha256': {'app': 'b'}}
        self.assertEqual(compare(left, right),
                         {'result': 'PACKAGING_DIFFERS', 'changed_members': []})

    def test_asset_differs(self) -> None:
        """Report modified and removed members in deterministic order."""
        left = {'asset_sha256': 'a', 'payload_sha256': {'app': 'b', 'extra': 'c'}}
        right = {'asset_sha256': 'd', 'payload_sha256': {'app': 'e'}}
        self.assertEqual(compare(left, right),
                         {'result': 'ASSET_DIFFERS', 'changed_members': ['app', 'extra']})

    def test_wrong_digest_and_repeated_run(self) -> None:
        """Reject wrong integrity input and accidental reuse of one CI run."""
        args = argparse.Namespace(source_sha='a' * 40, run_ids=[1, 1])
        with self.assertRaisesRegex(ValueError, 'distinct'):
            run(args)
        with TemporaryDirectory() as root:
            path = Path(root) / 'candidate.zip'
            path.write_bytes(b'bad input')
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                inspect(path, 'b' * 64, 'a' * 40, 'windows')


if __name__ == '__main__':
    unittest.main()
