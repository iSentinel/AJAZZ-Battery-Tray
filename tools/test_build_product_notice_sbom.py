"""Regression checks for exact product lifecycle and SBOM identity."""

import unittest
from unittest.mock import patch

from build_product_notice_sbom import bind, digest, encode, lifecycle, qualify


def records() -> tuple[dict, dict]:
    """Return synthetic clean and upgrade observations for fixed byte inputs."""
    common = {'source_sha': 'a' * 40, 'app_sha256': digest(b'app'),
              'setup_sha256': digest(b'setup'), 'tray_launch': 'NOT_OBSERVED',
              'physical_acceptance': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}
    clean = {**common, 'schema': 'product-notice-probe-v1',
             'installed_notices': 'MATCH', 'uninstalled_notices': 'REMOVED'}
    upgrade = {**common, 'schema': 'product-notice-upgrade-v1',
               'baseline_setup_sha256': '555b957b809c2f1bb4228c10a818abadad2df78e455925871713ee7779970672',
               'baseline_app_sha256': 'b' * 64, 'upgrade_notices': 'MATCH',
               'reinstall_restores_missing_notice': 'PASS',
               'uninstall_notices': 'REMOVED', 'synthetic_user_data': 'PRESERVED'}
    return clean, upgrade


class ProductBomTests(unittest.TestCase):
    """Require same app/setup/source, reject changed lifecycle and BOM."""

    def test_binding(self) -> None:
        """Bind exact binary digests and both lifecycle observations."""
        clean, upgrade = records()
        self.assertEqual(bind(b'app', b'setup', clean, upgrade, 'a' * 40)['app_sha256'], digest(b'app'))
        for changed in (dict(upgrade, setup_sha256='c' * 64),
                        dict(upgrade, synthetic_user_data='FAILED'),
                        dict(upgrade, baseline_app_sha256=digest(b'app')),
                        dict(upgrade, release_admission='PASS')):
            with self.assertRaises(ValueError):
                bind(b'app', b'setup', clean, changed, 'a' * 40)
        with self.assertRaises(ValueError):
            bind(b'app', b'other', clean, upgrade, 'a' * 40)

    def test_bom_identity(self) -> None:
        """Bind canonical BOM bytes and reject a different application root."""
        clean, upgrade = records()
        bom = {'metadata': {'component': {'hashes': [{'alg': 'SHA-256', 'content': digest(b'app')}]}},
               'components': []}
        with patch('build_product_notice_sbom.create', return_value=bom):
            raw, evidence = qualify(b'app', b'setup', encode(clean), encode(upgrade), 'a' * 40, {})
            self.assertEqual(evidence['sbom_sha256'], digest(raw))
            self.assertEqual(evidence['release_admission'], 'NOT_VERIFIED')
            bom['metadata']['component']['hashes'] = []
            with self.assertRaises(ValueError):
                qualify(b'app', b'setup', encode(clean), encode(upgrade), 'a' * 40, {})

    def test_duplicate_json(self) -> None:
        """Reject duplicate keys in evidence instead of overriding them."""
        with self.assertRaises(ValueError):
            lifecycle(b'{"schema":1,"schema":2}')


if __name__ == '__main__':
    unittest.main()
