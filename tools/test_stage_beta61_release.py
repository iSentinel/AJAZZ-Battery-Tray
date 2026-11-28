"""Release asset staging regressions using local synthetic evidence."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from stage_beta61_release import ASSETS, candidate, checked_asset, collect, main, stage
from test_verify_installer_candidate import SOURCE, artifact, bootstrap
from validate_scoped_sbom_schema import digest


def fixture() -> dict:
    """Build an acceptance manifest without inventing acceptance claims."""
    return {'schema': 'beta61-acceptance-kit-v1', 'candidate_sha': SOURCE,
            'tree': 'b' * 40, 'assets': [
                {'platform': labels[0], 'artifact': i, 'archive_sha256': 'c' * 64,
                 'release_asset_sha256': 'd' * 64}
                for i, labels in enumerate(ASSETS.values(), 1)]}


def encoded(plan: dict) -> bytes:
    """Serialize a synthetic manifest."""
    return json.dumps(plan).encode()


class BetaReleaseStagingTests(unittest.TestCase):
    """Check pinning, layout and a non-mutating dry run."""

    def test_validate_candidate_identity(self) -> None:
        """Reject missing or duplicate roles, reused artifact IDs and bad hashes."""
        for changes in ('delete', 'duplicate', 'reused', 'digest'):
            with self.subTest(changes=changes):
                data = fixture()
                rows = data['assets']
                if changes == 'delete':
                    rows.pop()
                elif changes == 'duplicate':
                    rows[1] = rows[0].copy()
                elif changes == 'reused':
                    rows[1]['artifact'] = rows[0]['artifact']
                else:
                    rows[1]['archive_sha256'] = 'bad'
                with self.assertRaises((ValueError, KeyError)):
                    candidate(encoded(data))

    def test_verified_setup_member(self) -> None:
        """Return only the reviewed bootstrap member of a real synthetic ZIP."""
        raw = artifact()
        row = {'archive_sha256': digest(raw), 'release_asset_sha256': digest(bootstrap())}
        with TemporaryDirectory() as temp:
            path = Path(temp) / 'setup.zip'
            path.write_bytes(raw)
            payload, proof = checked_asset(path, 'installer', SOURCE, row)
            self.assertEqual(payload, bootstrap())
            self.assertEqual(proof['asset_sha256'], row['release_asset_sha256'])
            row['release_asset_sha256'] = 'e' * 64
            with self.assertRaises(ValueError):
                checked_asset(path, 'installer', SOURCE, row)

    def test_cross_check_installed_and_portable(self) -> None:
        """Refuse a setup that reports a different application hash."""
        paths = {k: Path(k) for k in ASSETS}
        proofs = [(b'bytes', {'asset_sha256': 'x'}),
                  (b'bytes', {'asset_sha256': 'y', 'app_sha256': 'other'}),
                  (b'bytes', {'asset_sha256': 'z'}),
                  (b'bytes', {'asset_sha256': 'legacy'})]
        with patch('stage_beta61_release.checked_asset', side_effect=proofs):
            with self.assertRaisesRegex(ValueError, 'installer app differs'):
                collect(encoded(fixture()), paths)

    def test_layout_and_existing_directory(self) -> None:
        """Keep the separate legacy asset and refuse to replace an existing output."""
        data = candidate(encoded(fixture()))
        payload = {k: k.encode() for k in ASSETS}
        for profile in ASSETS:
            data['assets'][profile]['release_asset_sha256'] = digest(payload[profile])
        with TemporaryDirectory() as temp:
            output = Path(temp) / 'candidate'
            stage(output, data, payload)
            for profile, (_, _, name) in ASSETS.items():
                folder = output / ('high-sierra' if profile == 'high-sierra' else 'beta')
                self.assertEqual((folder / name).read_bytes(), payload[profile])
                self.assertEqual((folder / Path(name).with_suffix('.sha256')).read_text().split(),
                                 [digest(payload[profile]), name])
            evidence = (output / 'staging-evidence.json').read_bytes()
            with self.assertRaises(FileExistsError):
                stage(output, data, payload)
            self.assertEqual((output / 'staging-evidence.json').read_bytes(), evidence)

    def test_dry_run_and_failed_write(self) -> None:
        """Dry-run leaves the folder untouched and an incomplete stage is removed."""
        data = candidate(encoded(fixture()))
        payload = {k: k.encode() for k in ASSETS}
        with TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / 'candidate.json'
            manifest.write_bytes(encoded(fixture()))
            argv = ['--manifest', str(manifest), '--dry-run']
            for profile in ASSETS:
                argv.extend([f'--{profile}-archive', profile])
            with patch('stage_beta61_release.collect', return_value=(data, payload)):
                self.assertEqual(main(argv), 0)
            self.assertEqual(list(root.iterdir()), [manifest])
            output = root / 'staging'
            with patch('stage_beta61_release.write_json', side_effect=OSError):
                with self.assertRaises(OSError):
                    stage(output, data, payload)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
