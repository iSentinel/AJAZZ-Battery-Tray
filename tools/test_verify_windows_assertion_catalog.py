"""Check native assertion catalog coverage without executing native code."""

import json
import unittest

from verify_windows_assertion_catalog import REFERENCE, catalog, verify


class WindowsAssertionCatalogTests(unittest.TestCase):
    """Exercise exact labels, summary and failure rejection."""

    def test_reference(self) -> None:
        """Retain the observed reference and the significant trailing space."""
        names = catalog(REFERENCE.read_bytes())
        self.assertEqual(len(names), 1028)
        self.assertIn('No streak for invalid candidate ', names)
        raw = ('\n'.join('PASS ' + name for name in names)
               + '\nSummary: PASS=1028, FAIL=0\n').encode()
        self.assertEqual(verify(raw, names)['coverage'], 'MATCH')

    def test_invalid_capture(self) -> None:
        """Reject substitutions, duplicates, failures and incomplete summaries."""
        good = b'PASS first\r\nPASS second \r\nSummary: PASS=2, FAIL=0\r\n'
        names = ['first', 'second ']
        self.assertEqual(verify(good, names)['assertion_count'], 2)
        for raw in (good.replace(b'PASS first\r\n', b''),
                    good.replace(b'first', b'second '),
                    good.replace(b'second ', b'second'),
                    good.replace(b'PASS first', b'FAIL first'),
                    good.replace(b'PASS=2', b'PASS=3'),
                    good + b'PASS late\n', good + b'Summary: PASS=2, FAIL=0\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                verify(raw, names)

    def test_invalid_catalog(self) -> None:
        """Reject duplicate and nonprintable labels."""
        for names in ([], ['a', 'a'], ['a\nb'], [True]):
            raw = json.dumps({'schema': 'windows-native-assertion-catalog-v1',
                              'assertions': names}).encode()
            with self.subTest(names=names), self.assertRaises(ValueError):
                catalog(raw)


if __name__ == '__main__':
    unittest.main()
