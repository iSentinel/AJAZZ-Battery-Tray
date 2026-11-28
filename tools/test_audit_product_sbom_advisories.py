"""Tests for scoped advisory coverage and exact candidate identity."""

import copy
import unittest
from pathlib import Path
from unittest.mock import patch

from audit_product_sbom_advisories import audit, package_set
from build_product_notice_sbom import encode
from inventory_dotnet_pack_licenses import PACKS
from validate_scoped_sbom_schema import digest


def fixture() -> tuple[dict, dict, dict]:
    """Return a synthetic scoped BOM and bound observations."""
    bom = {'components': [
        {'type': 'library', 'bom-ref': 'pack:' + kind, 'name': name,
         'version': version, 'purl': f'pkg:nuget/{name}@{version}',
         'hashes': [{'alg': 'SHA-256', 'content': sha}]}
        for kind, (name, version, sha) in PACKS.items()],
        'metadata': {'component': {'hashes': [{'alg': 'SHA-256', 'content': 'a' * 64}]}}}
    record = {'schema': 'product-notice-sbom-v1', 'sbom_sha256': digest(encode(bom)),
              'components': 4, 'composition': 'INCOMPLETE', 'release_admission': 'NOT_VERIFIED',
              'app_sha256': 'a' * 64, 'setup_sha256': 'b' * 64, 'source_sha': 'c' * 40}
    schema = {'schema': 'scoped-sbom-schema-v1', 'sbom_sha256': record['sbom_sha256'],
              'components': 4, 'schema_validation': 'PASS', 'candidate_binding': 'MATCH',
              'release_admission': 'NOT_VERIFIED'}
    return bom, record, schema


class ProductAdvisoryTests(unittest.TestCase):
    """Do not substitute arbitrary packages or clear unverified evidence."""

    def test_package_identity(self) -> None:
        """Reject changed source package version, hash and PURL."""
        bom, _, _ = fixture()
        package_set(bom)
        for key, value in [('version', '99.0'), ('hashes', []), ('purl', 'wrong')]:
            changed = copy.deepcopy(bom)
            changed['components'][0][key] = value
            with self.assertRaises(ValueError):
                package_set(changed)

    def test_binding_and_matches(self) -> None:
        """Scope findings to exact BOM and preserve positive matches."""
        bom, record, schema = fixture()
        with patch('audit_product_sbom_advisories.load_snapshot', return_value=([{}, {}], [])):
            result = audit(encode(bom), record, schema, Path('.'))
            self.assertEqual(result['result'], 'NO_MATCHING_RANGES')
            self.assertEqual(result['other_components'], 'NOT_VERIFIED')
            with self.assertRaises(ValueError):
                audit(encode(bom), record, dict(schema, candidate_binding='NOT_PROVIDED'), Path('.'))
        name = PACKS['core'][0].lower()
        pages = [{name: [{'url': 'https://github.com/advisories/GHSA-aaaa-bbbb-cccc',
                         'severity': 2, 'versions': '[11.0.0]'}]}, {}]
        with patch('audit_product_sbom_advisories.load_snapshot', return_value=(pages, [])):
            self.assertEqual(audit(encode(bom), record, schema, Path('.'))['result'], 'MATCHES_FOUND')


if __name__ == '__main__':
    unittest.main()
