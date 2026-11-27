"""Check catalog coverage without opening hardware or altering existing forms."""

from pathlib import Path
import tempfile
import unittest

from export_acceptance_catalog import HARDWARE, INSTALLER, catalog, main, rows
from run_offline_qa import ROOT


class AcceptanceCatalogTests(unittest.TestCase):
    """Verify the canonical table and strict rejection of case drift."""

    def test_canonical_coverage(self) -> None:
        """All six profiles retain their existing case IDs and instance counts."""
        value = catalog((ROOT / HARDWARE).read_bytes(), (ROOT / INSTALLER).read_bytes())
        self.assertEqual(len(value['definitions']), 35)
        self.assertEqual(value['physical_instances'], 57)
        self.assertEqual(value['interactive_instances'], 6)
        self.assertEqual({key: len(row['cases']) for key, row in value['profiles'].items()},
                         {'windows-aj179': 17, 'windows-aj159': 17, 'windows-aula': 1,
                          'universal': 11, 'high-sierra': 11, 'interactive': 6})
        self.assertEqual(value['observations'], 'NOT_COLLECTED')
        self.assertEqual(value['release_admission'], 'NOT_VERIFIED')

    def test_case_drift(self) -> None:
        """Reject duplicate, omitted, unknown or malformed table definitions."""
        valid = b'| W01 | Action | Expected |'
        self.assertEqual(rows(valid, {'W01'})['W01']['action'], 'Action')
        for raw in (b'', valid + b'\n' + valid, valid + b'\n| W99 | x | y |',
                    b'| W01 | Action | |', b'| W01 | Action | Expected | Extra |'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                rows(raw, {'W01'})

    def test_cli_no_clobber(self) -> None:
        """Export a new catalog but refuse to overwrite an existing one."""
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'catalog.json'
            self.assertEqual(main(['--output', str(output)]), 0)
            before = output.read_bytes()
            self.assertEqual(main(['--output', str(output)]), 2)
            self.assertEqual(output.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
