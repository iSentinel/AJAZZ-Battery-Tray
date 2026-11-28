"""Reject altered original archives and prevent staging overwrite."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from stage_consolidated_signature_inputs import ARCHIVES, collect, stage


class SignatureInputsTests(unittest.TestCase):
    """Ensure source bytes are pinned before any archive interpretation."""

    def test_archive_pins(self) -> None:
        """Refuse missing or different archives before reading members."""
        raw = {k: b'synthetic' for k in ARCHIVES}
        with patch('stage_consolidated_signature_inputs.verify_pair') as verify:
            with self.assertRaises(ValueError):
                collect(raw)
            with self.assertRaises(ValueError):
                collect({})
            verify.assert_not_called()

    def test_no_overwrite(self) -> None:
        """Only stage into a new directory; preserve previous bytes."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'new'
            stage({'example.exe': b'old'}, root)
            with self.assertRaises(FileExistsError):
                stage({'example.exe': b'new'}, root)
            self.assertEqual((root / 'example.exe').read_bytes(), b'old')


if __name__ == '__main__':
    unittest.main()
