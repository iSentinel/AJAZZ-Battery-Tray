"""Scoped portable binding tests with synthetic exact app and notice bytes."""

import unittest
from unittest.mock import patch

from build_portable_notice_prototype import APP, build, manifest, recover_app, verify_zip
from test_verify_windows_notice_transport import fixture
from verify_windows_notice_transport import digest


class PortableNoticeTests(unittest.TestCase):
    """Keep candidate and notice identity distinct from release admission."""

    def test_roundtrip(self) -> None:
        """Use the same reviewed source binding and exact ZIP members."""
        app, notices = b'synthetic app', fixture()
        files = ((APP, len(app), digest(app)),)
        with patch('build_portable_notice_prototype.FILES', files), patch(
                'verify_windows_notice_transport.MANIFEST_SHA', digest(notices['manifest.json'])):
            raw = build(app, notices)
            result = verify_zip(raw)
            self.assertEqual(result['app_sha256'], digest(app))
            self.assertEqual(result['release_admission'], 'NOT_VERIFIED')
            self.assertEqual(raw, build(app, notices))
            with self.assertRaises(ValueError):
                build(b'other', notices)

    def test_wrong_candidate(self) -> None:
        """Unknown archive identity must fail before decoding anything."""
        with self.assertRaises(ValueError):
            recover_app(b'invalid')

    def test_manifest(self) -> None:
        """Never describe this historical prototype as a released artifact."""
        self.assertIn(b'"release_admission": "NOT_VERIFIED"', manifest())


if __name__ == '__main__':
    unittest.main()
