"""Reject mixed-run evidence and missing document sets."""

import unittest
from unittest.mock import patch

from build_product_notice_sbom import encode
from verify_inno674_migration_evidence import LINKS, NAMES, verify, digest


class MigrationEvidenceTests(unittest.TestCase):
    """All links must match before downstream scope checks."""

    def test_link_chain(self) -> None:
        """Build a synthetic hash chain; change one earlier document."""
        raw = [encode({}) for _ in NAMES]
        for index in range(len(NAMES)):
            raw[index] = encode({key: digest(raw[target])
                                 for i, key, target in LINKS if i == index})
        with patch('verify_inno674_migration_evidence.identity', return_value={}), \
                patch('verify_inno674_migration_evidence.binding'), \
                patch('verify_inno674_migration_evidence.outcomes'):
            self.assertEqual(verify(raw)['release_admission'], 'NOT_VERIFIED')
            raw[2] = encode({'different': True})
            with self.assertRaises(ValueError):
                verify(raw)

    def test_missing(self) -> None:
        """A missing document cannot be treated as success."""
        with self.assertRaises(ValueError):
            verify([])


if __name__ == '__main__':
    unittest.main()
