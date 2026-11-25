"""Regression tests for exact wizard resource attribution."""

import unittest

from verify_inno_wizard import compare, key, verify


class WizardTests(unittest.TestCase):
    """Check exact resource keys, ordering and pinned compiler identity."""

    def test_compare(self) -> None:
        """Match both known named RCDATA resources."""
        leaves = {key('WIZARDIMAGE150'): 'a' * 64, key('WIZARDSMALLIMAGE250'): 'b' * 64}
        images = [{'index': 0, 'bytes': 5767, 'sha256': 'a' * 64},
                  {'index': 1, 'bytes': 10005, 'sha256': 'b' * 64}]
        self.assertEqual(len(compare(images, leaves)), 2)
        for bad in (images[::-1], images[:1], [dict(images[0], bytes=1), images[1]]):
            with self.assertRaises(ValueError):
                compare(bad, leaves)
        with self.assertRaises(ValueError):
            compare(images, {key('WIZARDIMAGE150_DARK'): 'a' * 64})

    def test_unpinned_compiler(self) -> None:
        """Fail before parsing any untrusted setup for an unknown compiler."""
        with self.assertRaisesRegex(ValueError, 'compiler digest'):
            verify(b'', b'', b'', b'', b'')


if __name__ == '__main__':
    unittest.main()
