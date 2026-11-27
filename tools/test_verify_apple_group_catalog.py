"""Check Apple group coverage using synthetic console fixtures only."""

import json
import unittest

from verify_apple_group_catalog import REFERENCE, catalog, verify


class AppleGroupCatalogTests(unittest.TestCase):
    """Verify both edition references and reject incomplete evidence."""

    def test_references(self) -> None:
        """Retain the observed groups without counting internal assertions."""
        for edition, count in (('universal', 21), ('high-sierra', 6)):
            names = catalog(REFERENCE.read_bytes(), edition)
            package = '/tmp/package.zip'
            raw = ('\n'.join('PASS: ' + name for name in names)
                   + '\nPASS: ' + package + '\n').encode()
            self.assertEqual(verify(raw, names, package)['group_count'], count)

    def test_capture(self) -> None:
        """Require exact group order and a single final package marker."""
        names = ['first', 'second']
        good = b'PASS: first\nPASS: second\nPASS: /tmp/package.zip\n'
        self.assertEqual(verify(good, names, '/tmp/package.zip')['coverage'], 'MATCH')
        for raw in (good.replace(b'PASS: first\n', b''),
                    good.replace(b'first', b'second'),
                    good.replace(b'second', b'other'),
                    good.replace(b'PASS: first', b'SKIP: first'),
                    good.replace(b'PASS: first', b'FAIL: first'),
                    good.replace(b'/tmp/package.zip', b'/tmp/other.zip'),
                    good + b'PASS: late\n', good + b'PASS: /tmp/package.zip\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                verify(raw, names, '/tmp/package.zip')

    def test_catalog(self) -> None:
        """Reject missing profiles, duplicate groups and changed package names."""
        for change in ('profile', 'duplicate', 'package'):
            row = json.loads(REFERENCE.read_bytes())
            if change == 'profile':
                del row['profiles']['high-sierra']
            elif change == 'duplicate':
                row['profiles']['universal']['groups'].append(
                    row['profiles']['universal']['groups'][0])
            else:
                row['profiles']['universal']['package_name'] = 'other.zip'
            with self.subTest(change=change), self.assertRaises(ValueError):
                catalog(json.dumps(row).encode(), 'universal')


if __name__ == '__main__':
    unittest.main()
