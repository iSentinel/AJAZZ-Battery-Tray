"""Regression coverage for Apple external OS dependency classifications."""

import unittest

from audit_apple_os_dependency_scope import classify


def fixture() -> dict:
    """Create seven shipped files and one external library observation."""
    files = [{'type': 'file', 'name': str(i), 'bom-ref': 'file:' + str(i),
              'properties': [{'name': 'ajazz:scope', 'value': 'shipped app member'}]}
             for i in range(7)]
    name = '/usr/lib/libSystem.B.dylib'
    library = {'type': 'library', 'name': name, 'bom-ref': 'system:' + name,
               'scope': 'required', 'properties': [
                   {'name': 'ajazz:scope', 'value': 'external OS dependency, not shipped'},
                   {'name': 'ajazz:installed_version', 'value': 'NOT_VERIFIED'},
                   {'name': 'ajazz:linkage', 'value': 'required'}]}
    return {'components': files + [library]}


class AppleScopeTests(unittest.TestCase):
    """Avoid inferring installed patch levels from build-time linkage."""

    def test_external(self) -> None:
        """Preserve OS build requirement and separate shipped members."""
        files, libraries = classify(fixture())
        self.assertEqual(len(files), 7)
        self.assertEqual(libraries[0]['advisory_disposition'], 'OS_BUILD_REQUIRED')

    def test_reject_inferred_version(self) -> None:
        """Reject a claim that a linked library version is installed."""
        data = fixture()
        data['components'][-1]['properties'][1]['value'] = '15.5.0'
        with self.assertRaises(ValueError):
            classify(data)


if __name__ == '__main__':
    unittest.main()
