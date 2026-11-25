"""Synthetic regressions for exact installer/uninstaller archive binding."""
from io import BytesIO
import json
import unittest
import zipfile

from test_verify_installer_candidate import SOURCE, artifact, bootstrap
from verify_installer_candidate import digest
from verify_uninstaller_evidence import EXE, MANIFEST, verify_pair


def evidence(changes=None, exe=None, extra=None):
    """Build a synthetic CI uninstaller archive without executable code."""
    exe = bootstrap() if exe is None else exe
    data = {'schema': 'installer-uninstaller-v1', 'source_sha': SOURCE,
            'version': '0.3.0-beta.61', 'setup_sha256': digest(bootstrap()),
            'app_sha256': 'b' * 64, 'baseline_uninstaller_sha256': 'c' * 64,
            'uninstaller_sha256': digest(exe), 'uninstaller_bytes': len(exe),
            'scenario': 'beta60_to_beta61', 'uninstall_smoke': 'PASS',
            'engine_attribution': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}
    data.update(changes or {})
    stream = BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr(EXE, exe)
        archive.writestr(MANIFEST, json.dumps(data))
        if extra:
            archive.writestr(extra, 'unexpected')
    return stream.getvalue()


class UninstallerEvidenceTests(unittest.TestCase):
    """Ensure artifact integrity is not mistaken for attribution."""

    def verify(self, raw, candidate=None):
        """Use exact synthetic digests and source."""
        candidate = artifact() if candidate is None else candidate
        return verify_pair(raw, digest(raw), candidate, digest(candidate), SOURCE)

    def test_scope(self):
        """Record baseline equality without granting release admission."""
        result = self.verify(evidence({'baseline_uninstaller_sha256': digest(bootstrap())}))
        self.assertTrue(result['same_as_reported_baseline'])
        self.assertEqual(result['engine_attribution'], 'NOT_VERIFIED')
        self.assertEqual(result['release_admission'], 'NOT_VERIFIED')

    def test_cross_artifact_binding(self):
        """Reject different checkout or candidate binary hashes."""
        for change in ({'source_sha': 'd' * 40}, {'setup_sha256': 'd' * 64},
                       {'app_sha256': 'd' * 64}, {'version': '0.3.0-beta.62'}):
            with self.assertRaises(ValueError):
                self.verify(evidence(change))

    def test_invalid_scope_and_bytes(self):
        """Reject false acceptance, mismatched hashes, size or extra members."""
        for change in ({'uninstall_smoke': 'FAIL'}, {'engine_attribution': 'PASS'},
                       {'uninstaller_bytes': True}, {'uninstaller_bytes': 1},
                       {'uninstaller_sha256': '0' * 64}):
            with self.assertRaises(ValueError):
                self.verify(evidence(change))
        for raw in (evidence(extra='unins000.dat'), evidence(exe=b'MZ')):
            with self.assertRaises(ValueError):
                self.verify(raw)

    def test_archive_hashes(self):
        """Require independent digests for both archives."""
        raw, candidate = evidence(), artifact()
        for sha, candidate_sha in (('0' * 64, digest(candidate)),
                                   (digest(raw), '0' * 64)):
            with self.assertRaises(ValueError):
                verify_pair(raw, sha, candidate, candidate_sha, SOURCE)


if __name__ == '__main__':
    unittest.main()
