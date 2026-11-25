"""Synthetic installer archive regressions, never executing a bootstrap."""

from io import BytesIO
import json
import struct
import unittest
import zipfile

from verify_installer_candidate import SETUP, digest, verify

SOURCE = 'a' * 40


def bootstrap() -> bytes:
    """Construct just the observed PE32 header layout."""
    raw = bytearray(512)
    raw[:2] = b'MZ'
    struct.pack_into('<I', raw, 60, 64)
    raw[64:68] = b'PE\0\0'
    struct.pack_into('<HHIIIHH', raw, 68, 0x14c, 1, 0, 0, 0, 224, 2)
    struct.pack_into('<H', raw, 88, 0x10b)
    struct.pack_into('<H', raw, 88 + 68, 2)
    struct.pack_into('<I', raw, 88 + 92, 16)
    return bytes(raw)


def artifact(changes: dict | None = None, setup: bytes | None = None,
             extra: str | None = None) -> bytes:
    """Build a bounded synthetic ZIP in the emitter format."""
    setup = bootstrap() if setup is None else setup
    data = {'schema': 'installer-candidate-v1', 'source_sha': SOURCE,
            'version': '0.3.0-beta.61', 'setup_sha256': digest(setup),
            'app_sha256': 'b' * 64, 'lifecycle_probe': False,
            'physical_acceptance': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}
    data.update(changes or {})
    output = BytesIO()
    with zipfile.ZipFile(output, 'w') as archive:
        archive.writestr(SETUP, setup)
        archive.writestr('candidate.json', json.dumps(data))
        if extra:
            archive.writestr(extra, 'extra')
    return output.getvalue()


class InstallerCandidateTests(unittest.TestCase):
    """Keep source, integrity and trust separate."""

    def test_valid_scope(self) -> None:
        """An unsigned synthetic header does not imply payload acceptance."""
        raw = artifact()
        result = verify(raw, digest(raw), SOURCE)
        self.assertEqual(result['bootstrap']['certificate_table'], 'ABSENT')
        self.assertEqual(result['app_payload_verification'], 'NOT_VERIFIED')
        self.assertEqual(result['release_admission'], 'NOT_VERIFIED')

    def test_hashes_and_source(self) -> None:
        """Reject different archive, checkout or setup identity."""
        raw = artifact()
        with self.assertRaises(ValueError):
            verify(raw, '0' * 64, SOURCE)
        with self.assertRaises(ValueError):
            verify(raw, digest(raw), 'c' * 40)
        raw = artifact({'setup_sha256': '0' * 64})
        with self.assertRaises(ValueError):
            verify(raw, digest(raw), SOURCE)

    def test_wrong_manifest(self) -> None:
        """Reject probe builds, unqualified acceptance claims and extra fields."""
        for changes in ({'lifecycle_probe': True}, {'version': '0.3.0-beta.62'},
                        {'release_admission': 'PASS'}, {'extra': True}):
            raw = artifact(changes)
            with self.assertRaises(ValueError):
                verify(raw, digest(raw), SOURCE)

    def test_bad_members_and_bootstrap(self) -> None:
        """Reject unexpected files and malformed bootstrap bytes."""
        for raw in (artifact(extra='../outside'), artifact(setup=b'MZ')):
            with self.assertRaises(ValueError):
                verify(raw, digest(raw), SOURCE)


if __name__ == '__main__':
    unittest.main()
