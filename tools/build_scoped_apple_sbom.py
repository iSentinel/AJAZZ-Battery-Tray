#!/usr/bin/env python3
"""Build a scoped CycloneDX 1.6 BOM for a reviewed macOS app ZIP."""

import argparse
from pathlib import Path
import plistlib
import struct
import sys
import zipfile

from build_scoped_windows_sbom import hash_value, properties
from inventory_apple_archive import EDITIONS, inspect, sha
from inventory_apple_load_commands import report as load_report
from inventory_dotnet_bundle import BundleError
from run_offline_qa import write_json
from verify_apple_resource_seal import report as seal_report
from verify_windowsdesktop_provenance import read_local


def file_component(item: dict) -> dict:
    """Record one shipped archive member, not a system library."""
    return {'type': 'file', 'bom-ref': 'file:' + item['path'], 'name': item['path'],
            'hashes': hash_value(item['sha256']),
            'properties': properties(scope='shipped app member', bytes=str(item['size']),
                                     mode=oct(item['mode']))}


def system_component(item: dict, architectures: str) -> dict:
    """Record declared OS install name without inferring installed version."""
    return {'type': 'library', 'bom-ref': 'system:' + item['path'], 'name': item['path'],
            'scope': 'optional' if item['linkage'] == 'weak' else 'required',
            'properties': properties(scope='external OS dependency, not shipped',
                                     linkage=item['linkage'], architectures=architectures,
                                     macho_current_version=item['current'],
                                     macho_compatibility_version=item['compatibility'],
                                     installed_version='NOT_VERIFIED')}


def document(archive: dict, loads: dict, seal: dict) -> dict:
    """Compose bound observations and explicitly mark incomplete scope."""
    if any(r['archive_sha256'] != archive['archive_sha256'] or
           r['edition'] != archive['edition'] for r in (loads, seal)):
        raise BundleError('Evidence identity mismatch')
    edition = archive['edition']
    app, exe, identifier, minimum, cpus = EDITIONS[edition]
    executable = app + '/Contents/MacOS/' + exe
    files = [file_component(x) for x in archive['files']]
    matches = [x for x in archive['files'] if x['path'] == executable]
    if (len(matches) != 1 or len(files) != 7 or len({x['bom-ref'] for x in files}) != 7
            or any(r['executable_sha256'] != matches[0]['sha256'] for r in (loads, seal))):
        raise BundleError('File coverage or executable identity mismatch')
    observed = loads['slices']
    if (len(observed) != len(cpus) or {x['architecture'] for x in observed} != cpus
            or any(x['libraries'] != observed[0]['libraries'] for x in observed)):
        raise BundleError('Slice dependency evidence mismatch')
    libs = [system_component(x, ','.join(sorted(cpus))) for x in observed[0]['libraries']]
    if len({x['bom-ref'] for x in libs}) != len(libs):
        raise BundleError('Duplicate system dependency')
    root = {'type': 'application', 'bom-ref': 'application', 'name': identifier,
            'version': str(archive['bundle_version']), 'hashes': hash_value(archive['archive_sha256']),
            'properties': properties(hash_scope='actual app ZIP', edition=edition,
                                     plist_minimum=minimum, signature='AD_HOC_EMPTY_CMS',
                                     release_admission='NOT_VERIFIED', signer_trust='NOT_VERIFIED',
                                     native_compatibility='NOT_VERIFIED', advisories='NOT_RUN')}
    return {'bomFormat': 'CycloneDX', 'specVersion': '1.6', 'version': 1,
            'metadata': {'component': root}, 'components': files + libs,
            'dependencies': [{'ref': 'file:' + executable, 'dependsOn': [x['bom-ref'] for x in libs]}],
            'compositions': [{'aggregate': 'incomplete', 'assemblies': ['application']}]}


def create(raw: bytes, edition: str) -> dict:
    """Recompute archive, load-command and seal observations from the same bytes."""
    return document(inspect(raw, edition), load_report(raw, edition), seal_report(raw, edition))


def main(argv: list[str] | None = None) -> int:
    """Write a no-replace BOM only after matching the expected archive digest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--edition', choices=sorted(EDITIONS), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        raw = read_local(args.archive)
        if sha(raw) != args.sha256:
            raise BundleError('Archive digest mismatch')
        write_json(args.output, create(raw, args.edition))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, struct.error,
            zipfile.BadZipFile, plistlib.InvalidFileException) as error:
        print(f'ERROR: scoped Apple SBOM ({type(error).__name__})', file=sys.stderr)
        return 2
    print('PASS: scoped Apple SBOM; complete distribution coverage not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
