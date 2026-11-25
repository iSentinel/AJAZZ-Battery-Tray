"""Check reviewed notice staging without requiring real NuGet inputs."""

import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from inventory_dotnet_bundle import BundleError
from inventory_dotnet_pack_licenses import PACKS
from stage_windows_notices import PACKAGE_NOTICES, ROOT, repository_notices, stage


def fake_collect(raw: bytes, kind: str) -> tuple[dict, dict]:
    """Return synthetic package notice inputs."""
    return {'package': kind}, {name: raw for name in PACKAGE_NOTICES[kind]}


class WindowsNoticeTests(unittest.TestCase):
    """Keep notice bytes exact, scope explicit, and output fail-closed."""

    def test_repository(self) -> None:
        """Require the four exact reviewed repository notices."""
        self.assertEqual(len(repository_notices(ROOT)), 4)

    def test_stage_and_no_replace(self) -> None:
        """Verify nine files and reject repeated staging."""
        with tempfile.TemporaryDirectory() as temp, patch(
                'stage_windows_notices.collect', side_effect=fake_collect):
            output = Path(temp) / 'notices'
            packs = dict.fromkeys(PACKS, b'exact notice')
            result = stage(packs, output)
            self.assertEqual(len(result['files']), 9)
            self.assertEqual((output / 'DotNet/host/license.txt').read_bytes(), b'exact notice')
            self.assertEqual(result['release_admission'], 'NOT_VERIFIED')
            self.assertEqual(result['distribution_compliance'], 'NOT_VERIFIED')
            with self.assertRaises(BundleError):
                stage(packs, output)

    def test_invalid_before_output(self) -> None:
        """Missing packages and altered repository bytes cannot produce a manifest."""
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'notices'
            with self.assertRaises(BundleError):
                stage({}, output)
            self.assertFalse(output.exists())
            with self.assertRaises(BundleError):
                stage(dict.fromkeys(PACKS, b'invalid'), output)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
