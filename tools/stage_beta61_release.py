#!/usr/bin/env python3
"""Stage exact beta.61 CI assets locally for release review."""

import argparse
from io import BytesIO
from pathlib import Path
import re
import shutil
import struct
import sys
import zipfile
import zlib

from compare_release_builds import inspect_archive
from run_offline_qa import write_json
from stage_local_inno674_payload import directory
from validate_scoped_sbom_schema import digest, document, read
from verify_hardware_acceptance import APPLE_NAMES
from verify_installer_candidate import SETUP
from verify_windowsdesktop_provenance import read_local

PORTABLE = 'AJAZZBatteryTray-win-x64.exe'
ASSETS = {
    'windows': ('Windows portable', 'AJAZZBatteryTray.exe', PORTABLE),
    'installer': ('Windows setup', SETUP, SETUP),
    'universal': ('macOS Universal', APPLE_NAMES['universal'] + '.zip',
                  APPLE_NAMES['universal'] + '.zip'),
    'high-sierra': ('macOS High Sierra Intel', APPLE_NAMES['high-sierra'] + '.zip',
                    APPLE_NAMES['high-sierra'] + '.zip'),
}


def hex_value(value: object, length: int) -> str:
    """Require an exact lowercase Git object ID or SHA-256 digest."""
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{%d}' % length, value):
        raise ValueError('invalid source identity or digest')
    return value


def candidate(raw: bytes) -> dict:
    """Read the published acceptance kit's source and reviewed asset hashes."""
    plan = document(raw)
    if plan.get('schema') != 'beta61-acceptance-kit-v1' or not isinstance(plan.get('assets'), list):
        raise ValueError('unsupported acceptance kit manifest')
    by_platform = {labels[0]: profile for profile, labels in ASSETS.items()}
    rows = {}
    if len(plan['assets']) != len(ASSETS):
        raise ValueError('unexpected asset count')
    for entry in plan['assets']:
        if not isinstance(entry, dict):
            raise ValueError('invalid asset row')
        profile = by_platform[entry['platform']]
        if profile in rows or type(entry['artifact']) is not int or entry['artifact'] <= 0:
            raise ValueError('invalid or duplicate artifact')
        rows[profile] = {'artifact': entry['artifact'],
                         'archive_sha256': hex_value(entry['archive_sha256'], 64),
                         'release_asset_sha256': hex_value(entry['release_asset_sha256'], 64)}
    if len({r['artifact'] for r in rows.values()}) != len(rows):
        raise ValueError('artifact ID reused across platforms')
    return {'source_sha': hex_value(plan['candidate_sha'], 40),
            'source_tree': hex_value(plan['tree'], 40), 'assets': rows}


def checked_asset(path: Path, profile: str, source: str, row: dict) -> tuple[bytes, dict]:
    """Reuse bounded archive validation before extracting a fixed member name."""
    raw = read_local(path)
    recorded = inspect_archive(raw, row['archive_sha256'], source, profile)
    if recorded['asset_sha256'] != row['release_asset_sha256']:
        raise ValueError('release asset digest differs from manifest')
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        asset = archive.read(ASSETS[profile][1])
    if digest(asset) != row['release_asset_sha256']:
        raise ValueError('extracted release asset differs')
    return asset, recorded


def collect(raw: bytes, paths: dict[str, Path]) -> tuple[dict, dict[str, bytes]]:
    """Match all archives and bind the installer app to the portable app."""
    plan = candidate(raw)
    payload, identities = {}, {}
    if set(paths) != set(ASSETS):
        raise ValueError('all four archives are required')
    for profile in ASSETS:
        payload[profile], identities[profile] = checked_asset(
            paths[profile], profile, plan['source_sha'], plan['assets'][profile])
    if identities['installer']['app_sha256'] != identities['windows']['asset_sha256']:
        raise ValueError('installer app differs from portable app')
    return plan, payload


def stage(output: Path, plan: dict, payload: dict[str, bytes]) -> None:
    """Write separate staging folders and leave existing destinations intact."""
    directory(output.parent)
    output.mkdir(mode=0o700)
    try:
        beta, legacy = output / 'beta', output / 'high-sierra'
        beta.mkdir()
        legacy.mkdir()
        for profile, raw in payload.items():
            name = ASSETS[profile][2]
            folder = legacy if profile == 'high-sierra' else beta
            with (folder / name).open('xb') as stream:
                stream.write(raw)
            sha = plan['assets'][profile]['release_asset_sha256']
            with (folder / Path(name).with_suffix('.sha256')).open('x', encoding='ascii') as stream:
                stream.write(f'{sha}  {name}\n')
        write_json(output / 'staging-evidence.json',
                   {'schema': 'beta61-release-staging-v1', **plan,
                    'source_provenance': 'CALLER_REVIEW_REQUIRED',
                    'release_admission': 'NOT_VERIFIED'})
    except BaseException:
        shutil.rmtree(output)
        raise


def main(argv: list[str] | None = None) -> int:
    """Verify inputs and optionally materialize the reviewed bytes locally."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    for profile in ASSETS:
        parser.add_argument(f'--{profile}-archive', type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--dry-run', action='store_true')
    action.add_argument('--output', type=Path, help='New local staging directory')
    args = parser.parse_args(argv)
    paths = {p: getattr(args, p.replace('-', '_') + '_archive') for p in ASSETS}
    try:
        plan, payload = collect(read(args.manifest), paths)
        if args.output is not None:
            stage(args.output, plan, payload)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            NotImplementedError, zipfile.BadZipFile, struct.error, zlib.error):
        print('FAIL: release artifact identity or local staging', file=sys.stderr)
        return 2
    mode = 'dry-run matched' if args.dry_run else 'staged'
    print(f'PASS: {mode} four release assets for {plan["source_sha"]}')
    for profile, row in plan['assets'].items():
        print(f'{ASSETS[profile][2]} {row["release_asset_sha256"]}')
    print('Release admission: NOT_VERIFIED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
