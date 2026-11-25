#!/usr/bin/env python3
"""Join one scoped native product qualification; never grant release admission."""

import argparse
from pathlib import Path
import re
import sys

from run_offline_qa import write_json
from validate_scoped_sbom_schema import digest, document, read, binding
from verify_inno674_components import VENDOR
from verify_inno674_setup_records import ALIGNED_SOURCE, COMPILER, PRODUCTION_SOURCE_PINS, SOURCE_PINS, destinations
from verify_windows_notice_transport import MANIFEST_SHA

NAMES = (
    'product-components-before', 'product-components-after',
    'product-lifecycle', 'product-upgrade-lifecycle', 'product-scoped-sbom',
    'product-sbom-binding', 'inno674-product-binding', 'exercised-uninstaller',
    'binary-attribution', 'resource-attribution', 'solid-attribution', 'setup-records',
)
SCHEMAS = (
    'product-notice-probe-v1', 'product-notice-upgrade-v1',
    'product-notice-sbom-v1', 'inno-674-product-binding-v1',
    'inno-674-exercised-uninstaller-v1', 'inno-674-product-binary-v1',
    'inno-674-product-resources-v1', 'inno-674-solid-payload-v1',
    'inno-674-setup-records-v1',
)
LINKS = (
    (5, 'clean_lifecycle_sha256', 2), (5, 'upgrade_lifecycle_sha256', 3),
    (5, 'sbom_sha256', 4), (6, 'product_binding_sha256', 5),
    (6, 'component_evidence_sha256', 1), (8, 'binding_sha256', 6),
    (8, 'exercised_sha256', 7), (9, 'binary_attribution_sha256', 8),
    (10, 'resource_evidence_sha256', 9), (10, 'product_binding_sha256', 6),
    (11, 'solid_evidence_sha256', 10),
)


def require(ok: bool) -> None:
    """Fail closed for a missing or contradictory observation."""
    if not ok:
        raise ValueError('inconsistent qualification evidence')


def identity(rows: list[dict]) -> dict:
    """Require exact schemas and one setup/source/application identity."""
    root = rows[6]
    result = {k: root[k] for k in ('source_sha', 'setup_sha256', 'app_sha256')}
    for k, value in result.items():
        require(bool(re.fullmatch(r'[0-9a-f]{40}' if k == 'source_sha' else
                                  r'[0-9a-f]{64}', value)))
    for i, schema in zip((2, 3, 5, 6, 7, 8, 9, 10, 11), SCHEMAS):
        row = rows[i]
        require(row['schema'] == schema and row['release_admission'] == 'NOT_VERIFIED')
        require(all(row[k] == result[k] for k in ('source_sha', 'setup_sha256')))
        if i not in (9, 11):
            require(row['app_sha256'] == result['app_sha256'])
    return result


def outcomes(r: list[dict]) -> None:
    """Require the reviewed native observations, not a release decision."""
    require(r[0] == r[1] and len(r[1]['files']) == 38)
    require(r[1]['vendor_sha256'] == VENDOR and r[1]['component_identity'] == 'MATCH'
            and r[1]['engine_version'] == r[6]['engine_version'] == '6.7.4')
    require(r[2]['installed_notices'] == 'MATCH' and r[2]['uninstalled_notices'] == 'REMOVED')
    require(r[3]['upgrade_notices'] == 'MATCH' and r[3]['uninstall_notices'] == 'REMOVED'
            and r[3]['synthetic_user_data'] == 'PRESERVED'
            and r[3]['reinstall_restores_missing_notice'] == 'PASS')
    require(r[2]['tray_launch'] == r[3]['tray_launch'] == 'NOT_OBSERVED')
    require(r[5]['notice_manifest_sha256'] == MANIFEST_SHA
            and r[5]['sbom_sha256'] == r[6]['sbom_sha256'])
    require(r[7]['uninstall_result'] == 'REMOVED'
            and r[7]['uninstaller_sha256'] == r[8]['uninstaller']['uninstaller_sha256']
            == r[9]['uninstaller_sha256'])
    require(r[8]['loader_non_resource'] == r[8]['engine_non_resource'] == 'MATCH'
            and r[8]['engine_frame']['engine_sha256'] == r[9]['engine_sha256'])
    require(r[9]['resource_payloads'] == 'MATCH_SCOPED'
            and r[9]['messages']['message_semantics'] == 'MATCH_PINNED_ENGLISH_TEXT')
    require(r[10]['solid_stream'] == 'MATCH' and len(r[10]['files']) == 15
            and r[10]['files'][0]['sha256'] == r[6]['app_sha256'])
    require(r[11]['script'] == r[10]['script'] and r[11]['script']['policy'] == 'MATCH_REVIEWED_SOURCE')
    require(r[11]['file_records'] == 16 and r[11]['file_destinations'] == destinations()
            and r[11]['shortcut_records'] == 2 and r[11]['run_records'] == 1
            and r[11]['trailing_bytes'] == 0
            and r[11]['header_policy'] == 'MATCH_REVIEWED_SOURCE_AND_DEFAULTS'
            and r[11]['wizard_image_provenance'] == 'MATCH_PINNED_COMPILER_RCDATA'
            and r[11]['compiler_sha256'] == COMPILER
            and r[11]['installer_source_lf_sha256'] in SOURCE_PINS)


def verify(raw: list[bytes]) -> dict:
    """Check every digest edge and report scoped qualification only."""
    require(len(raw) == len(NAMES))
    rows = [document(x) for x in raw]
    hashes = [digest(x) for x in raw]
    require(raw[0] == raw[1])
    for index, key, target in LINKS:
        require(rows[index][key] == hashes[target])
    result = identity(rows)
    binding(raw[4], rows[4], rows[5])
    outcomes(rows)
    return {'schema': 'inno-674-migration-evidence-v1', **result,
            'engine_version': '6.7.4', 'documents': dict(zip(NAMES, hashes)),
            'scoped_native_evidence': 'MATCH', 'production_compiler_migration': 'NOT_AUTHORIZED',
            'independent_sbom_schema': 'NOT_VERIFIED_BY_THIS_TOOL',
            'advisory_freshness': 'NOT_VERIFIED', 'interactive_acceptance': 'NOT_VERIFIED',
            'physical_acceptance': 'NOT_VERIFIED', 'distribution_compliance': 'NOT_VERIFIED',
            'release_admission': 'NOT_VERIFIED'}


def production_shape(raw: bytes, result: dict, records: dict) -> dict:
    """Bind the exact normal-name/default-directory observation to the chain."""
    value = document(raw)
    expected = {
        'schema': 'inno-674-production-shape-v1',
        **{k: result[k] for k in ('source_sha', 'setup_sha256', 'app_sha256')},
        'output_filename': 'AJAZZBatteryTray-Setup-win-x64.exe',
        'version': '0.3.0-beta.61', 'default_program_files_install': 'MATCH',
        'default_silent_launch': 'NOT_OBSERVED', 'uninstalled': 'REMOVED',
        'release_admission': 'NOT_VERIFIED',
    }
    require(value == expected and records['installer_source_lf_sha256'] in PRODUCTION_SOURCE_PINS)
    return {**result, 'production_shape_sha256': digest(raw),
            'production_shape': 'MATCH_SCOPED'}


def local_build(raw: bytes, result: dict, solid: dict, records: dict) -> dict:
    """Bind compiler preflight evidence to the exact observed solid payload."""
    value = document(raw)
    require(result.get('production_shape') == 'MATCH_SCOPED')
    files = {row['name']: row['sha256'] for row in solid['files']}
    icons = {name: files['Icons/' + name] for name in
             ('AppIcon.ico', 'AppIcon-white.ico', 'AppIcon-black.ico', 'AppIcon-blue.ico')}
    require(records['installer_source_lf_sha256'] == ALIGNED_SOURCE
            and files['Notices/manifest.json'] == MANIFEST_SHA
            and files['AJAZZBatteryTray.exe'] == result['app_sha256'])
    expected = {
        'schema': 'local-inno674-build-v1', 'engine_version': '6.7.4',
        'setup_sha256': result['setup_sha256'], 'app_sha256': result['app_sha256'],
        'icons': icons, 'installer_source_sha256': ALIGNED_SOURCE,
        'notice_manifest_sha256': MANIFEST_SHA, 'input_identity': 'MATCH',
        'source_provenance': 'NOT_VERIFIED', 'lifecycle': 'NOT_RUN',
        'distribution_compliance': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED',
    }
    require(value == expected)
    return {**result, 'local_build_sha256': digest(raw), 'local_build': 'MATCH_SCOPED'}


def main(argv: list[str] | None = None) -> int:
    """Read fixed named JSON documents; do not run or publish anything."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--production-shape', action='store_true')
    parser.add_argument('--local-build', action='store_true')
    args = parser.parse_args(argv)
    try:
        raw = [read(args.root / (n + '.json')) for n in NAMES]
        result = verify(raw)
        records = document(raw[-1])
        if args.production_shape:
            result = production_shape(read(args.root / 'production-shape.json'), result, records)
        else:
            require(records['installer_source_lf_sha256'] not in PRODUCTION_SOURCE_PINS)
        if args.local_build:
            result = local_build(read(args.root / 'local-build-evidence.json'),
                                 result, document(raw[10]), records)
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        print('FAIL: scoped migration evidence', file=sys.stderr)
        return 2
    print('PASS: single scoped native evidence chain; migration and release not authorized')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
