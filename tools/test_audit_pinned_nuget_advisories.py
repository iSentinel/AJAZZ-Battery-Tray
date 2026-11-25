"""Regressions for scoped stable-version vulnerability interval checks."""

import json
from pathlib import Path
import tempfile
import unittest

from audit_pinned_nuget_advisories import affected, load_snapshot, scan
from inventory_dotnet_bundle import BundleError


class AdvisoryTests(unittest.TestCase):
    """Reject unsupported evidence rather than silently clearing a version."""

    def test_boundaries(self) -> None:
        """Check exact, inclusive and exclusive endpoints."""
        for interval in ('[11.0.0]', '[11.0, 12.0)', '(10.0, 11.0]', '(, 11.0]', '[11.0, )'):
            self.assertTrue(affected('11.0.0', interval))
        for interval in ('[10.0, 11.0)', '(11.0, 12.0]', '[10.0.0]'):
            self.assertFalse(affected('11.0.0', interval))

    def test_prerelease(self) -> None:
        """Stable releases follow preview and RC versions of the same core."""
        self.assertFalse(affected('11.0.0', '[11.0.0-preview.1, 11.0.0-rc.3.26522.148]'))
        self.assertTrue(affected('11.0.0', '[11.0.0-preview.1, 11.0.0]'))
        self.assertTrue(affected('10.0.19041.87', '[10.0.19041.86, 10.0.19041.88)'))

    def test_invalid_intervals(self) -> None:
        """Refuse unreviewed range syntax and invalid bounds."""
        for interval in ('11.*', '[11.0, 10.0]', '[, 11.0]', '[11.0, ]', '(, )', '[11.0+meta]'):
            with self.assertRaises(BundleError):
                affected('11.0.0', interval)
        with self.assertRaises(BundleError):
            affected('11.0.0-rc.1', '[11.0, 12.0)')

    def test_both_pages(self) -> None:
        """Scan both partitions and deduplicate matching ranges."""
        row = {'url': 'https://github.com/advisories/GHSA-aaaa-bbbb-cccc',
               'severity': 2, 'versions': '[11.0, 12.0)'}
        result = scan([{'test': [row]}, {'test': [row]}], 'Test', '11.0.0')
        self.assertEqual(result['ranges_examined'], 2)
        self.assertEqual(len(result['matches']), 1)
        with self.assertRaises(BundleError):
            scan([{'test': [{**row, 'severity': 9}]}], 'Test', '11.0.0')

    def test_missing_page(self) -> None:
        """A missing update page cannot yield a clean result."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = [{'@name': name, '@id': f'https://api.nuget.org/v3-vulnerabilities/2026.01.01/vulnerability.{name}.json', '@updated': '2026-01-01T00:00:00Z'} for name in ('base', 'update')]
            (root / 'index.json').write_text(json.dumps(index))
            (root / 'base.json').write_text('{"test": []}')
            with self.assertRaises(BundleError):
                load_snapshot(root)
            (root / 'update.json').write_text('{}')
            pages, evidence = load_snapshot(root)
            self.assertEqual(len(pages), 2)
            self.assertEqual(len(evidence), 3)

    def test_duplicate_keys(self) -> None:
        """Do not silently replace duplicated advisory package entries."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'index.json').write_text('[{"@name":"base","@name":"update"},{}]')
            with self.assertRaises(ValueError):
                load_snapshot(root)


if __name__ == '__main__':
    unittest.main()
