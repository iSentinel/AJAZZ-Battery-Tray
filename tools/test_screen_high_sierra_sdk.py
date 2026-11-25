"""Regression tests for scoped High Sierra SDK name screening."""

import tempfile
import unittest
from pathlib import Path

from inventory_dotnet_bundle import BundleError
from screen_high_sierra_sdk import parse_stub, qualified, screen, screen_library
from inventory_apple_archive import sha


def stub(identity: str, groups: list[dict]) -> dict:
    """Create synthetic v2 metadata without redistributing SDK stubs."""
    return parse_stub({'install-name': identity, 'platform': 'macosx',
                       'archs': ['x86_64'], 'exports': groups}, identity)


def group(**fields: list[str]) -> dict:
    """Build one x86_64 export group."""
    return {'archs': ['x86_64'], **fields}


class HighSierraScreenTests(unittest.TestCase):
    """Verify exact architecture, name classes and conservative constraints."""

    def test_reexports_and_cycles(self) -> None:
        """Handle reexport cycles and distinguish direct and inherited names."""
        graph = {'a': stub('a', [group(symbols=['_one'], **{'re-exports': ['b']})]),
                 'b': stub('b', [group(symbols=['_two'], **{'re-exports': ['a']})])}
        result = screen_library(graph, 'a', {'_one', '_two', '_missing'})
        self.assertEqual(result['direct_unrestricted'], 1)
        self.assertEqual(result['unrestricted_name_matches'], 2)
        self.assertEqual(result['missing_names'], ['_missing'])
        self.assertEqual(result['reachable_stubs'], 2)

    def test_restricted_groups(self) -> None:
        """Keep restricted names and reexport paths out of unrestricted matches."""
        graph = {'a': stub('a', [
            group(symbols=['_one'], **{'allowable-clients': ['AppKit']}),
            group(**{'allowable-clients': ['AppKit'], 're-exports': ['b']})]),
                 'b': stub('b', [group(symbols=['_two'])])}
        result = screen_library(graph, 'a', {'_one', '_two'})
        self.assertEqual(result['unrestricted_name_matches'], 0)
        self.assertEqual(result['restricted_only'], ['_one', '_two'])

    def test_objc_and_linker_directives(self) -> None:
        """Expand Objective-C names and retain unevaluated linker directives."""
        node = stub('a', [group(**{'objc-classes': ['_Class'],
                                 'objc-ivars': ['_Class.ivar'],
                                 'objc-eh-types': ['_Class'],
                                 'symbols': ['$ld$hide$os10.13$_name', '_name']})])
        names = {'_OBJC_CLASS_$_Class', '_OBJC_METACLASS_$_Class',
                 '_OBJC_IVAR_$_Class.ivar', '_OBJC_EHTYPE_$_Class', '_name'}
        result = screen_library({'a': node}, 'a', names)
        self.assertEqual(result['unrestricted_name_matches'], 5)
        self.assertEqual(result['linker_directives_not_evaluated'],
                         ['$ld$hide$os10.13$_name'])
        self.assertNotIn('$ld$hide$os10.13$_name', node['names'])

    def test_architecture_and_unknown_keys(self) -> None:
        """Ignore other architectures and reject unknown group semantics."""
        node = stub('a', [{'archs': ['arm64'], 'symbols': ['_other']},
                          group(symbols=['_one'])])
        self.assertEqual(node['names'], {'_one'})
        with self.assertRaises(BundleError):
            stub('a', [group(unknown=['x'])])

    def test_missing_reexport_and_unrelated_graph(self) -> None:
        """Reject incomplete or unrelated SDK graph evidence."""
        with self.assertRaises(BundleError):
            screen_library({'a': stub('a', [group(**{'re-exports': ['b']})])},
                           'a', {'_one'})
        imports = {'edition': 'high-sierra', 'slices': [{
            'architecture': 'x86_64', 'symbol_count': 1,
            'symbols': [{'library': 'a', 'name': '_one'}]}]}
        graph = {'a': stub('a', [group(symbols=['_one'])]),
                 'b': stub('b', [group(symbols=['_two'])])}
        with self.assertRaises(BundleError):
            screen(graph, imports)

    def test_digest_and_size(self) -> None:
        """Enforce exact digest and bounded local input size."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stub'
            path.write_bytes(b'abc')
            self.assertEqual(qualified(path, sha(b'abc'), 3), b'abc')
            for digest, limit in ((sha(b'wrong'), 3), (sha(b'abc'), 2),
                                  ('invalid', 3)):
                with self.assertRaises(BundleError):
                    qualified(path, digest, limit)


if __name__ == '__main__':
    unittest.main()
