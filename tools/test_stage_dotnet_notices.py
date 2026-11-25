"""Tests for bounded, no-replace notice staging."""

import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from inventory_dotnet_bundle import BundleError
from inventory_dotnet_pack_licenses import PACKS
from stage_dotnet_notices import stage


def sample(kind: str) -> tuple[dict, dict]:
    """Return a scoped synthetic notice observation."""
    return {"package": kind}, {} if kind == "sdk" else {"LICENSE": b"exact bytes"}


class NoticeStageTests(unittest.TestCase):
    """Keep output local, exact and fail closed on invalid inputs."""

    def test_exact_staging(self) -> None:
        """Preserve package identity and notice bytes without claiming approval."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "notices"
            with patch("stage_dotnet_notices.collect", side_effect=lambda raw, kind: sample(kind)):
                result = stage(dict.fromkeys(PACKS, b"x"), output)
            self.assertEqual((output / "host" / "LICENSE").read_bytes(), b"exact bytes")
            self.assertEqual(list((output / "sdk").iterdir()), [])
            self.assertTrue((output / "manifest.json").is_file())
            self.assertEqual(result["release_admission"], "NOT_VERIFIED")

    def test_invalid_input_no_output(self) -> None:
        """Reject missing or invalid package inputs before writing any files."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "notices"
            for packs in ({}, dict.fromkeys(PACKS, b"invalid")):
                with self.assertRaises(BundleError):
                    stage(packs, output)
                self.assertFalse(output.exists())

    def test_no_overwrite(self) -> None:
        """Do not overwrite a previous evidence directory."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch("stage_dotnet_notices.collect", side_effect=lambda raw, kind: sample(kind)):
                with self.assertRaises(BundleError):
                    stage(dict.fromkeys(PACKS, b"x"), output)
            self.assertEqual(list(output.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
