"""Regression tests for proposed compiler input identity."""

import hashlib
from pathlib import Path
import tempfile
import unittest

from compare_inno_compiler import NAMES
from verify_inno674_components import VENDOR, verify


class Inno674ComponentTests(unittest.TestCase):
    """Require exact hashes, paths and all reviewed names."""

    def test_exact_and_changed(self) -> None:
        """All synthetic input files must match their reviewed pins."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rows = []
            for name in sorted(NAMES):
                data = name.encode()
                (root / name).write_bytes(data)
                rows.append({'name': name, 'bytes': len(data),
                             'sha256': hashlib.sha256(data).hexdigest()})
            pins = {'schema': 'inno-674-component-pins-v1', 'engine_version': '6.7.4',
                    'vendor_sha256': VENDOR, 'files': rows}
            self.assertEqual(len(verify(root, pins)['files']), 38)
            with self.assertRaises(ValueError):
                verify(root, dict(pins, files=rows[:-1]))
            (root / rows[0]['name']).write_bytes(b'other')
            with self.assertRaises(ValueError):
                verify(root, pins)


if __name__ == '__main__':
    unittest.main()
