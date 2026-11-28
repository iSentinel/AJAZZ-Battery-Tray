"""Synthetic regressions for the private consolidated portable package."""

from io import BytesIO
import unittest
from unittest.mock import patch
import zipfile

from build_consolidated_portable_notices import APP, PAYLOAD, build, verify_zip
from test_verify_windows_notice_transport import fixture
from verify_windows_notice_transport import digest


class ConsolidatedNoticeTests(unittest.TestCase):
    """Keep exact payload and notice transport distinct from admission."""

    def test_roundtrip(self) -> None:
        """Preserve all five files and verify every staged notice."""
        files = {name: name.encode() for name in PAYLOAD}
        pins = {name: (len(raw), digest(raw)) for name, raw in files.items()}
        stream = BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            for name, raw in files.items():
                archive.writestr(name, raw)
        original, notices = stream.getvalue(), fixture()
        with patch('build_consolidated_portable_notices.pins', return_value=pins), patch(
                'build_consolidated_portable_notices.ARCHIVES', {'windows': digest(original)}), patch(
                'build_consolidated_portable_notices.FILES', {APP: digest(files[APP])}), patch(
                'verify_windows_notice_transport.MANIFEST_SHA', digest(notices['manifest.json'])):
            raw = build(original, notices)
            self.assertEqual(raw, build(original, notices))
            self.assertEqual(verify_zip(raw)['release_admission'], 'BLOCKED')
            with zipfile.ZipFile(BytesIO(raw)) as archive:
                self.assertEqual({k: archive.read(k) for k in PAYLOAD}, files)
            with self.assertRaises(ValueError):
                build(original, dict(notices, extra=b'bad'))

    def test_original_pin(self) -> None:
        """Reject substituted CI archive before interpreting its members."""
        with patch('build_consolidated_portable_notices.members') as parse:
            with self.assertRaises(ValueError):
                build(b'wrong', {})
            parse.assert_not_called()


if __name__ == '__main__':
    unittest.main()
