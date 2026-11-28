"""Regression checks for exact 6.7.4 product/uninstaller evidence binding."""

import unittest
from unittest.mock import patch

from build_product_notice_sbom import encode
from verify_inno674_product_binary import digest, identity, inspect_binary, qualify


def records() -> tuple[dict, dict]:
    """Create synthetic lifecycle-bound records with exact byte digests."""
    bound = {'schema': 'inno-674-product-binding-v1', 'engine_version': '6.7.4',
             'source_sha': 'a' * 40, 'setup_sha256': digest(b'setup'),
             'app_sha256': 'b' * 64, 'release_admission': 'NOT_VERIFIED'}
    exercised = {'schema': 'inno-674-exercised-uninstaller-v1',
                 'source_sha': bound['source_sha'], 'setup_sha256': bound['setup_sha256'],
                 'app_sha256': bound['app_sha256'], 'uninstaller_sha256': digest(b'exe'),
                 'uninstall_result': 'REMOVED', 'release_admission': 'NOT_VERIFIED'}
    return bound, exercised


class Inno674BinaryTests(unittest.TestCase):
    """Reject changed executable, failed lifecycle and unreviewed templates."""

    def test_identity(self) -> None:
        """Require exact setup and uninstaller digests and successful removal."""
        bound, exercised = records()
        identity(b'setup', b'exe', bound, exercised)
        for altered in (dict(exercised, uninstall_result='FAILED'),
                        dict(exercised, source_sha='c' * 40)):
            with self.assertRaises(ValueError):
                identity(b'setup', b'exe', bound, altered)
        with self.assertRaises(ValueError):
            identity(b'setup', b'other', bound, exercised)

    def test_template_and_scope(self) -> None:
        """Fail before parsing unreviewed templates; preserve incomplete scope."""
        bound, exercised = records()
        with self.assertRaises(ValueError):
            inspect_binary(b'setup', b'exe', b'wrong', b'wrong')
        with patch('verify_inno674_product_binary.inspect_binary',
                   return_value={'resource_provenance': 'NOT_VERIFIED'}):
            result = qualify(b'setup', b'exe', b'l', b'e', encode(bound), encode(exercised))
            self.assertEqual(result['release_admission'], 'NOT_VERIFIED')
            self.assertEqual(result['resource_provenance'], 'NOT_VERIFIED')
            self.assertEqual(result['binding_sha256'], digest(encode(bound)))


if __name__ == '__main__':
    unittest.main()
