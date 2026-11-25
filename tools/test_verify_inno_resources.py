"""Synthetic strict ICO and resource leaf comparison regressions."""

import struct
import unittest

from verify_inno_resources import LANG, compare_resources, expected_leaves, icon_resources, named_group


def icon() -> bytes:
    """Build seven contiguous synthetic icon entries."""
    return (struct.pack('<HHH', 0, 1, 7)
            + b''.join(struct.pack('<BBBBHHII', w, w, 0, 0, 0, 32, 1, 118 + i)
                       for i, w in enumerate((16, 24, 32, 48, 64, 128, 0)))
            + b'abcdefg')


def loader() -> dict:
    """Build the scoped loader resource key set."""
    return ({('3', str(i), LANG): str(i) for i in range(1, 27)}
            | {named_group('MAINICON'): 'main', named_group('MAINICON_DARK'): 'dark',
               ('10', '11111', LANG): 'offset', ('16', '1', LANG): 'version',
               ('24', '1', LANG): 'manifest', ('10', '99', LANG): 'unchanged'})


class ResourceAttributionTests(unittest.TestCase):
    """Keep unknown resources and metadata explicitly unqualified."""

    def test_icon_extent(self) -> None:
        """Reject trailing or overlapping icon images."""
        raw = icon()
        self.assertEqual(len(icon_resources(raw)), 8)
        changed = bytearray(raw)
        struct.pack_into('<I', changed, 6 + 12, 119)
        for invalid in (raw + b'x', bytes(changed), raw[:-1]):
            with self.assertRaises(ValueError):
                icon_resources(invalid)

    def test_exact_scope(self) -> None:
        """Permit only known unresolved leaves and exact replacement icons."""
        template, ico = loader(), icon_resources(icon())
        actual, _ = expected_leaves(template, ico, 'loader')
        actual[('16', '1', LANG)] = 'different version'
        result = compare_resources(template, actual, ico, 'loader')
        self.assertEqual(result['icon_group'], 'MATCH')
        self.assertEqual(len(result['unqualified']), 3)

    def test_reject_extra_or_changed(self) -> None:
        """Reject extra keys and all changed qualified payloads."""
        template, ico = loader(), icon_resources(icon())
        actual, _ = expected_leaves(template, ico, 'loader')
        for altered in (actual | {('3', '99', LANG): 'extra'},
                        actual | {('10', '99', LANG): 'changed'},
                        actual | {named_group('MAINICON'): 'bad group'}):
            with self.assertRaises(ValueError):
                compare_resources(template, altered, ico, 'loader')


if __name__ == '__main__':
    unittest.main()
