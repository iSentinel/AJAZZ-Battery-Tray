"""Regression tests for scoped pinned package license observations."""

import io
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile

from inventory_dotnet_bundle import BundleError
from inventory_dotnet_pack_licenses import declared_license, inspect, notice_inventory

MIT = '<metadata><license type="expression">MIT</license><licenseUrl>https://licenses.nuget.org/MIT</licenseUrl></metadata>'
SDK = '<metadata><licenseUrl>https://aka.ms/WinSDKLicenseURL</licenseUrl><requireLicenseAcceptance>true</requireLicenseAcceptance></metadata>'


def archive(entries: list[tuple[str, bytes]]) -> bytes:
    """Create synthetic archive inputs without filesystem extraction."""
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as package:
        for name, data in entries:
            package.writestr(name, data)
    return stream.getvalue()


class LicenseTests(unittest.TestCase):
    """Keep declared licenses distinct from verified redistribution clearance."""

    def test_mit(self) -> None:
        """Accept reviewed MIT expression while retaining an open disposition."""
        result = declared_license(ET.fromstring(MIT), 'core')
        self.assertEqual(result['expression'], 'MIT')
        self.assertEqual(result['disposition'], 'NOTICE_DISTRIBUTION_REVIEW_REQUIRED')

    def test_sdk(self) -> None:
        """Do not invent SPDX terms for the SDK license URL."""
        result = declared_license(ET.fromstring(SDK), 'sdk')
        self.assertIsNone(result['expression'])
        self.assertTrue(result['requires_acceptance'])
        self.assertEqual(result['disposition'], 'TERMS_REVIEW_REQUIRED')

    def test_unreviewed_declarations(self) -> None:
        """Reject changed or duplicated declarations."""
        for raw in (MIT.replace('MIT</license>', 'Apache-2.0</license>'),
                    MIT.replace('</metadata>', '<licenseUrl>other</licenseUrl></metadata>'),
                    SDK.replace('true', 'false')):
            with self.assertRaises(BundleError):
                declared_license(ET.fromstring(raw), 'sdk' if 'WinSDK' in raw else 'core')

    def test_notices(self) -> None:
        """Record exact root notice bytes, not similarly named nested files."""
        raw = archive([('LICENSE.TXT', b'license'), ('nested/LICENSE.TXT', b'other'),
                       ('.signature.p7s', b'synthetic')])
        with zipfile.ZipFile(io.BytesIO(raw)) as package:
            notices, signature = notice_inventory(package)
        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0]['size'], 7)
        self.assertTrue(signature)

    def test_duplicate_and_empty(self) -> None:
        """Reject aliases and empty license notices."""
        for entries in ([('LICENSE', b'a'), ('license', b'b')], [('LICENSE', b'')]):
            with zipfile.ZipFile(io.BytesIO(archive(entries))) as package:
                with self.assertRaises(BundleError):
                    notice_inventory(package)

    def test_digest_gate(self) -> None:
        """Reject an unpinned archive before inspecting its XML."""
        with self.assertRaises(BundleError):
            inspect(b'not a package', 'host')

    def test_missing_notice_gate(self) -> None:
        """A matching test digest does not waive required notice inventory."""
        import hashlib
        raw = archive([('test.nuspec', MIT.replace('<metadata>', '<package><metadata><id>test</id><version>1</version>').replace('</metadata>', '</metadata></package>').encode()), ('.signature.p7s', b'x')])
        with patch.dict('inventory_dotnet_pack_licenses.PACKS', {'host': ('test', '1', hashlib.sha256(raw).hexdigest())}):
            with self.assertRaises(BundleError):
                inspect(raw, 'host')


if __name__ == '__main__':
    unittest.main()
