#!/usr/bin/env python3
"""Screen reviewed High Sierra imports against local SDK text stubs."""

import argparse
import json
from pathlib import Path
import re
import struct
import sys
import zipfile
import plistlib

from inventory_apple_archive import sha
from inventory_apple_symbols import report as symbol_report
from inventory_dotnet_bundle import BundleError
from run_offline_qa import write_json
from verify_windowsdesktop_provenance import read_local

SOURCE_COMMIT = '041600eda65c6a668f66cb7d56b7d1da3e8bcc93'
HEX = re.compile(r'[0-9a-f]{64}')
EXPORT_KEYS = {'archs', 'symbols', 'weak-def-symbols', 'thread-local-symbols',
               'objc-classes', 'objc-ivars', 'objc-eh-types', 're-exports',
               'allowable-clients'}


def strings(group: dict, key: str) -> set[str]:
    """Require a bounded string sequence in the reviewed stub format."""
    values = group.get(key, [])
    if (not isinstance(values, list) or len(values) > 100000
            or any(not isinstance(x, str) or not x or len(x) > 4096
                   for x in values)):
        raise BundleError('Invalid text stub export sequence')
    return set(values)


def group_exports(group: dict) -> tuple[set[str], set[str]]:
    """Expand reviewed v2 Objective-C naming and retain linker directives."""
    names = set().union(*(strings(group, key) for key in (
        'symbols', 'weak-def-symbols', 'thread-local-symbols')))
    directives = {name for name in names if name.startswith('$ld$')}
    names -= directives
    for key, prefixes in (
            ('objc-classes', ('_OBJC_CLASS_$_', '_OBJC_METACLASS_$_')),
            ('objc-ivars', ('_OBJC_IVAR_$_',)),
            ('objc-eh-types', ('_OBJC_EHTYPE_$_',))):
        for value in strings(group, key):
            if not value.startswith('_') or len(value) < 2:
                raise BundleError('Unexpected v2 Objective-C export')
            names.update(prefix + value[1:] for prefix in prefixes)
    return names, directives


def parse_stub(doc: dict, identity: str) -> dict:
    """Collect x86_64 names and reexports; keep restricted groups separate."""
    if (not isinstance(doc, dict) or doc.get('install-name') != identity
            or doc.get('platform') != 'macosx'
            or 'x86_64' not in strings(doc, 'archs')):
        raise BundleError('Unexpected text stub identity')
    result = {key: set() for key in ('names', 'refs', 'public_names',
                                     'public_refs', 'directives')}
    exports = doc.get('exports', [])
    if not isinstance(exports, list) or len(exports) > 1024:
        raise BundleError('Invalid text stub groups')
    for group in exports:
        if not isinstance(group, dict):
            raise BundleError('Invalid export group')
        if 'x86_64' not in strings(group, 'archs'):
            continue
        if set(group) - EXPORT_KEYS:
            raise BundleError('Unsupported export group key')
        names, directives = group_exports(group)
        refs = strings(group, 're-exports')
        result['names'].update(names)
        result['refs'].update(refs)
        result['directives'].update(directives)
        if not strings(group, 'allowable-clients'):
            result['public_names'].update(names)
            result['public_refs'].update(refs)
    return result


def load_yaml(raw: bytes) -> dict:
    """Load only local hash-qualified v2 data with the optional safe parser."""
    import yaml  # Optional analysis dependency; never installed by this CLI.

    class Loader(yaml.SafeLoader):
        """Recognize the reviewed text-based dylib v2 mapping tag."""

    Loader.add_constructor('!tapi-tbd-v2', lambda loader, node:
                           loader.construct_mapping(node, deep=True))
    if not raw.startswith(b'--- !tapi-tbd-v2'):
        raise BundleError('Unsupported text stub format')
    try:
        return yaml.load(raw, Loader=Loader)
    except yaml.YAMLError as error:
        raise BundleError('Malformed text stub') from error


def qualified(path: Path, expected: str, limit: int) -> bytes:
    """Read local evidence and require a separately supplied SHA-256."""
    if not isinstance(expected, str) or not HEX.fullmatch(expected):
        raise BundleError('Invalid expected SHA-256')
    raw = read_local(path)
    if len(raw) > limit or sha(raw) != expected:
        raise BundleError('Evidence digest or size mismatch')
    return raw


def load_graph(manifest: dict, directory: Path) -> dict:
    """Recompute graph from exact stubs, rejecting missing or changed edges."""
    entries = manifest.get('stubs', {})
    if (manifest.get('commit') != SOURCE_COMMIT or not isinstance(entries, dict)
            or not 0 < len(entries) <= 160 or directory.is_symlink()):
        raise BundleError('Unexpected SDK evidence manifest')
    graph = {}
    for identity, entry in entries.items():
        if entry.get('status') != 'READ':
            raise BundleError('Incomplete SDK evidence')
        digest = entry.get('sha256', '')
        if not isinstance(digest, str) or not HEX.fullmatch(digest):
            raise BundleError('Invalid stub digest')
        node = parse_stub(load_yaml(qualified(directory / digest, digest,
                                              8 * 1024 * 1024)), identity)
        if node['refs'] != strings(entry, 'refs'):
            raise BundleError('Reexport evidence mismatch')
        graph[identity] = node
    if any(node['refs'] - graph.keys() for node in graph.values()):
        raise BundleError('Missing reexport stub')
    return graph


def reachable(graph: dict, root: str, edge: str) -> set[str]:
    """Traverse a finite reexport graph without assuming acyclic edges."""
    found, pending = set(), [root]
    while pending:
        identity = pending.pop()
        if identity in found:
            continue
        if identity not in graph:
            raise BundleError('Missing dependency in SDK graph')
        found.add(identity)
        pending.extend(graph[identity][edge] - found)
    return found


def screen_library(graph: dict, root: str, imports: set[str]) -> dict:
    """Distinguish unrestricted name candidates from restricted-only matches."""
    nodes = reachable(graph, root, 'refs')
    public = reachable(graph, root, 'public_refs')
    names = set().union(*(graph[key]['names'] for key in nodes))
    public_names = set().union(*(graph[key]['public_names'] for key in public))
    directives = set().union(*(graph[key]['directives'] for key in nodes))
    relevant = sorted(d for d in directives
                      if any(d.endswith('$' + name) for name in imports))
    return {'library': root, 'imports': len(imports),
            'direct_unrestricted': len(imports & graph[root]['public_names']),
            'unrestricted_name_matches': len(imports & public_names),
            'restricted_only': sorted((imports & names) - public_names),
            'missing_names': sorted(imports - names),
            'linker_directives_not_evaluated': relevant,
            'reachable_stubs': len(nodes)}


def screen(graph: dict, symbols: dict) -> list[dict]:
    """Require the reviewed High Sierra x86_64 symbol inventory."""
    if symbols.get('edition') != 'high-sierra':
        raise BundleError('Expected High Sierra symbol inventory')
    slices = symbols['slices']
    if len(slices) != 1 or slices[0]['architecture'] != 'x86_64':
        raise BundleError('Unexpected High Sierra slices')
    imports = {}
    for item in slices[0]['symbols']:
        imports.setdefault(item['library'], set()).add(item['name'])
    if sum(map(len, imports.values())) != slices[0]['symbol_count']:
        raise BundleError('Duplicate import evidence')
    used = set().union(*(reachable(graph, key, 'refs') for key in imports))
    if used != graph.keys():
        raise BundleError('SDK evidence graph has unrelated inputs')
    return [screen_library(graph, key, imports[key]) for key in sorted(imports)]


def main(argv: list[str] | None = None) -> int:
    """Write local name-screening evidence, never a native compatibility PASS."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--stub-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        raw = qualified(args.archive, args.sha256, 32 * 1024 * 1024)
        manifest = json.loads(qualified(args.manifest, args.manifest_sha256,
                                        256 * 1024))
        graph = load_graph(manifest, args.stub_dir)
        symbols = symbol_report(raw, 'high-sierra')
        libraries = screen(graph, symbols)
        write_json(args.output, {'schema': 1, 'scope': 'SDK name screen only',
                   'archive_sha256': args.sha256,
                   'manifest_sha256': args.manifest_sha256,
                   'source_commit': SOURCE_COMMIT, 'source_trust': 'NOT_VERIFIED',
                   'stub_count': len(graph), 'libraries': libraries,
                   'linker_directive_semantics': 'NOT_VERIFIED',
                   'native_compatibility': 'NOT_VERIFIED',
                   'release_admission': 'NOT_VERIFIED'})
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError,
            ImportError, struct.error, zipfile.BadZipFile,
            plistlib.InvalidFileException) as error:
        print(f'ERROR: SDK name screen ({type(error).__name__})', file=sys.stderr)
        return 2
    print('COMPLETE: SDK name screen; inspect matches and unresolved constraints')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
