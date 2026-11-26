"""Synthetic extracted-tree tests; no application execution or hardware access."""

import os
from pathlib import Path
import tempfile
import unittest

from observe_native_package_extraction import verify_tree


class NativeTreeTests(unittest.TestCase):
    """Check extracted bytes, complete inventory and executable mode bits."""

    def test_inventory_and_bytes(self) -> None:
        """Require exact files and reject extra entries or changed payloads."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'app'
            path.write_bytes(b'fixture')
            expected = {'app': (b'fixture', 0)}
            verify_tree(root, expected)
            path.write_bytes(b'changed')
            with self.assertRaises(ValueError):
                verify_tree(root, expected)
            path.write_bytes(b'fixture')
            (root / 'extra').mkdir()
            with self.assertRaises(ValueError):
                verify_tree(root, expected)

    def test_missing_and_modes(self) -> None:
        """Reject missing entries and lost executable bits."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'app'
            expected = {'app': (b'fixture', 0o755)}
            with self.assertRaises(ValueError):
                verify_tree(root, expected)
            path.write_bytes(b'fixture')
            verify_tree(root, expected)
            if os.name != 'nt':
                path.chmod(0o644)
                with self.assertRaises(ValueError):
                    verify_tree(root, expected, executable_modes=True)
                path.chmod(0o755)
                verify_tree(root, expected, executable_modes=True)


if __name__ == '__main__':
    unittest.main()
