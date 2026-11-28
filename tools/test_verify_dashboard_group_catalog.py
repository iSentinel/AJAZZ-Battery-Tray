"""Test the Dashboard group catalog without starting WinForms or accessing HID."""

import json
import unittest

from verify_dashboard_group_catalog import REFERENCE, catalog, verify


class DashboardGroupCatalogTests(unittest.TestCase):
    """Check the observed reference and fail-closed coverage checks."""

    def test_reference(self) -> None:
        """Retain all groups and nine synthetic scaling observations."""
        names = catalog(REFERENCE.read_bytes())
        self.assertEqual(len(names), 24)
        self.assertEqual(sum('not real DPI' in name for name in names), 9)
        raw = ('\r\n'.join('PASS: ' + name for name in names) + '\r\n').encode()
        result = verify(raw, names)
        self.assertEqual(result['coverage'], 'MATCH')
        self.assertEqual(result['real_dpi'], 'NOT_VERIFIED')
        self.assertEqual(result['release_admission'], 'BLOCKED')

    def test_capture(self) -> None:
        """Reject absent, duplicate, reordered, failed or substituted groups."""
        names = ['first', 'second']
        good = b'PASS: first\nPASS: second\n'
        self.assertEqual(verify(good, names)['group_count'], 2)
        for raw in (good.replace(b'PASS: first\n', b''),
                    good.replace(b'first', b'second'),
                    b'PASS: second\nPASS: first\n',
                    good.replace(b'second', b'other'),
                    good.replace(b'PASS: first', b'FAIL: first'),
                    good.replace(b'PASS: first', b'SKIP: first'),
                    good + b'PASS: late\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                verify(raw, names)

    def test_catalog(self) -> None:
        """Reject duplicate, empty and nonprintable reference labels."""
        for groups in ([], ['a', 'a'], [''], ['a\nb'], [True]):
            raw = json.dumps({'schema': 'windows-dashboard-group-catalog-v1',
                              'groups': groups}).encode()
            with self.subTest(groups=groups), self.assertRaises(ValueError):
                catalog(raw)


if __name__ == '__main__':
    unittest.main()
