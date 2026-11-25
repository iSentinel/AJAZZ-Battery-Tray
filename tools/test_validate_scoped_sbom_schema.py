"""Test strict local input handling and scoped candidate binding."""

from pathlib import Path
import tempfile
import unittest

from validate_scoped_sbom_schema import PINS, binding, digest, document, schemas


class ScopedSchemaTests(unittest.TestCase):
    """Verify input pinning without installing optional validator packages."""

    def test_wrong_schema(self) -> None:
        """Do not let altered schema bytes reach the validator."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in PINS:
                (root / name).write_bytes(b'{}')
            with self.assertRaises(ValueError):
                schemas(root)

    def test_duplicate_json(self) -> None:
        """Reject duplicate keys and non-object evidence."""
        for raw in (b'{"a":1,"a":2}', b'[]'):
            with self.assertRaises(ValueError):
                document(raw)

    def test_binding(self) -> None:
        """Refuse altered BOM bytes, count or application identity."""
        raw = b'synthetic BOM'
        bom = {'components': [], 'metadata': {'component': {
            'hashes': [{'alg': 'SHA-256', 'content': 'a' * 64}]}}}
        record = {'schema': 'product-notice-sbom-v1', 'sbom_sha256': digest(raw),
                  'components': 0, 'composition': 'INCOMPLETE',
                  'release_admission': 'NOT_VERIFIED', 'app_sha256': 'a' * 64}
        binding(raw, bom, record)
        for bad in (dict(record, components=1), dict(record, app_sha256='b' * 64),
                    dict(record, release_admission='PASS')):
            with self.assertRaises(ValueError):
                binding(raw, bom, bad)
        with self.assertRaises(ValueError):
            binding(raw + b'x', bom, record)


if __name__ == '__main__':
    unittest.main()
