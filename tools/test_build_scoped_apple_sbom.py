"""Regressions for scoped Apple CycloneDX evidence composition."""

import copy
import unittest

from build_scoped_apple_sbom import document
from inventory_apple_archive import EDITIONS
from inventory_dotnet_bundle import BundleError


def evidence(edition: str) -> tuple[dict, dict, dict]:
    """Construct small coherent synthetic evidence for composition tests."""
    app, exe, _, _, cpus = EDITIONS[edition]
    root = app + '/Contents/'
    names = ['MacOS/' + exe, 'Info.plist', '_CodeSignature/CodeResources']
    names += ['Resources/AppIcon' + s + '.icns' for s in ('', '-black', '-blue', '-white')]
    files = [{'path': root + name, 'sha256': 'b' * 64, 'size': 1, 'mode': 0o644}
             for name in names]
    identity = {'edition': edition, 'archive_sha256': 'a' * 64}
    archive = {**identity, 'bundle_version': '1', 'files': files}
    libraries = [{'path': '/usr/lib/libSystem.B.dylib', 'linkage': 'required',
                  'current': '1.0.0', 'compatibility': '1.0.0'}]
    if edition == 'universal':
        libraries.append({'path': '/usr/lib/swift/libswiftos.dylib', 'linkage': 'weak',
                          'current': '1.0.0', 'compatibility': '1.0.0'})
    loads = {**identity, 'executable_sha256': 'b' * 64,
             'slices': [{'architecture': cpu, 'libraries': copy.deepcopy(libraries)}
                        for cpu in sorted(cpus)]}
    seal = {**identity, 'executable_sha256': 'b' * 64}
    return archive, loads, seal


class AppleBomTests(unittest.TestCase):
    """Ensure external OS libraries are not represented as shipped payloads."""

    def test_scope_and_edges(self) -> None:
        """Preserve file hashes, weak linkage and direct edges without trust claims."""
        result = document(*evidence('universal'))
        files = [x for x in result['components'] if x['type'] == 'file']
        libs = [x for x in result['components'] if x['type'] == 'library']
        self.assertEqual(len(files), 7)
        self.assertTrue(all(x['hashes'] for x in files))
        self.assertTrue(all('hashes' not in x and 'version' not in x for x in libs))
        self.assertEqual({x['scope'] for x in libs}, {'required', 'optional'})
        self.assertEqual(result['dependencies'][0]['dependsOn'], [x['bom-ref'] for x in libs])
        self.assertEqual(result['compositions'][0]['aggregate'], 'incomplete')

    def test_identity_mismatch(self) -> None:
        """Reject mixed archive or executable evidence."""
        for key in ('archive_sha256', 'executable_sha256', 'edition'):
            archive, loads, seal = evidence('high-sierra')
            seal[key] = 'wrong'
            with self.assertRaises(BundleError):
                document(archive, loads, seal)

    def test_file_coverage(self) -> None:
        """Reject missing or duplicate shipped member records."""
        archive, loads, seal = evidence('high-sierra')
        item = archive['files'].pop()
        with self.assertRaises(BundleError):
            document(archive, loads, seal)
        archive['files'].append(archive['files'][0])
        with self.assertRaises(BundleError):
            document(archive, loads, seal)
        archive['files'][-1] = item
        self.assertEqual(len(document(archive, loads, seal)['components']), 8)

    def test_slice_disagreement(self) -> None:
        """Reject incomplete architectures or inconsistent library metadata."""
        archive, loads, seal = evidence('universal')
        loads['slices'][1]['libraries'][0]['current'] = '9.0.0'
        with self.assertRaises(BundleError):
            document(archive, loads, seal)
        loads['slices'].pop()
        with self.assertRaises(BundleError):
            document(archive, loads, seal)

    def test_duplicate_library(self) -> None:
        """Reject duplicate dependency references."""
        archive, loads, seal = evidence('high-sierra')
        libs = loads['slices'][0]['libraries']
        libs.append(libs[0])
        with self.assertRaises(BundleError):
            document(archive, loads, seal)


if __name__ == '__main__':
    unittest.main()
