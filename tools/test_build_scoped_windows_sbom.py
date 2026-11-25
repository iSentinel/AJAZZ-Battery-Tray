"""Regression checks for scoped CycloneDX inventory evidence."""

import unittest

from build_scoped_windows_sbom import document, file_component, pack_component, validate_coverage
from inventory_dotnet_bundle import BundleError


def sample() -> dict:
    """Return a small synthetic attribution with configuration and unclaimed files."""
    return {"exe_sha256": "a" * 64,
            "components": [{"files": [{"path": "app.dll", "sha256": "b" * 64, "size": 3}]}],
            "configuration_files": [{"path": "app.deps.json", "sha256": "c" * 64, "size": 4}],
            "unmatched_files": [{"path": "other.dll", "sha256": "d" * 64, "size": 5}],
            "missing_declared_files": []}


class ScopedBomTests(unittest.TestCase):
    """Do not silently omit entries or turn scoped evidence into release admission."""

    def test_full_coverage(self) -> None:
        """Accept each observed payload exactly once."""
        a = sample()
        items = a['components'][0]['files'] + a['configuration_files'] + a['unmatched_files']
        validate_coverage(a, [file_component(x, 'test') for x in items])

    def test_missing_and_duplicate(self) -> None:
        """Reject absent, duplicate and unclaimed payloads."""
        a = sample()
        items = a['components'][0]['files'] + a['configuration_files'] + a['unmatched_files']
        files = [file_component(x, 'test') for x in items]
        for candidate in (files[:-1], files + files[:1], files + [{'name': 'extra.dll'}]):
            with self.assertRaises(BundleError):
                validate_coverage(a, candidate)
        a['missing_declared_files'] = [{'path': 'missing.dll'}]
        with self.assertRaises(BundleError):
            validate_coverage(a, files)

    def test_scope(self) -> None:
        """Bind actual EXE hash and mark incomplete composition and advisories."""
        r = document(sample(), {'id': 'app', 'version': '1.0'}, [], [])
        self.assertEqual(r['metadata']['component']['hashes'][0]['content'], 'a' * 64)
        self.assertEqual(r['compositions'][0]['aggregate'], 'incomplete')
        props = {x['name']: x['value'] for x in r['metadata']['component']['properties']}
        self.assertEqual(props['ajazz:release_admission'], 'NOT_VERIFIED')
        self.assertEqual(props['ajazz:advisories'], 'NOT_RUN')

    def test_license_identity(self) -> None:
        """Distinguish declared MIT and SDK terms without inventing a license ID."""
        mit = pack_component('core', {'license': {'expression': 'MIT'}}, 179)
        sdk = pack_component('sdk', {'license': {'expression': None, 'url': 'https://aka.ms/WinSDKLicenseURL'}}, 2)
        self.assertEqual(mit['licenses'], [{'license': {'id': 'MIT'}}])
        self.assertNotIn('id', sdk['licenses'][0]['license'])
        self.assertTrue(sdk['purl'].startswith('pkg:nuget/'))


if __name__ == '__main__':
    unittest.main()
