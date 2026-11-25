#!/usr/bin/env python3
"""Bind private hardware observations to exact local CI artifact bytes."""

import argparse
import io
from pathlib import Path
import re
import stat
import sys
import zipfile

from inventory_apple_archive import EDITIONS, inspect
from inventory_dotnet_components import report
from run_offline_qa import write_json
from validate_scoped_sbom_schema import digest, document, read
from verify_interactive_acceptance import STATUSES, check_case
from verify_windowsdesktop_provenance import read_local

WINDOWS = tuple(f'W{i:02d}' for i in range(1, 19))
MAC = tuple(f'M{i:02d}' for i in range(1, 12))
PROFILES = {'windows-aj179': tuple(x for x in WINDOWS if x != 'W14'),
            'windows-aj159': tuple(x for x in WINDOWS if x != 'W14'),
            'windows-aula': ('W14',), 'universal': MAC, 'high-sierra': MAC}
APPLE_NAMES = {'universal': 'AJAZZBatteryTray-macOS-universal',
               'high-sierra': 'AJAZZBatteryTray-macOS-HighSierra-Intel'}
ICONS = {'Icons/AppIcon' + suffix + '.ico' for suffix in ('', '-black', '-blue', '-white')}
LIMIT = 256 * 1024 * 1024


def members(raw: bytes, names: set[str]) -> dict[str, bytes]:
    """Read only the exact bounded outer artifact file inventory."""
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        if (len(infos) != len(names) or {x.filename for x in infos} != names
                or sum(x.file_size for x in infos) > LIMIT):
            raise ValueError('unexpected artifact members')
        for item in infos:
            if (item.orig_filename != item.filename or item.flag_bits & 1
                    or stat.S_IFMT(item.external_attr >> 16) not in (0, stat.S_IFREG)
                    or item.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                    or item.file_size <= 0):
                raise ValueError('invalid artifact member')
        return {x.filename: archive.read(x) for x in infos}


def windows(raw: bytes) -> dict:
    """Identify the actual portable app, not the independently built setup."""
    exe = 'AJAZZBatteryTray.exe'
    files = members(raw, ICONS | {exe})
    data = report(files[exe])
    projects = [x for x in data['components'] if x['type'] == 'project']
    if (len(projects) != 1 or projects[0]['id'] != 'AJAZZBatteryTray'
            or projects[0]['version'] != '0.3.0-beta.61'):
        raise ValueError('unexpected Windows project or version')
    return {'app_sha256': data['exe_sha256'], 'version': projects[0]['version'],
            'payload_sha256': {k: digest(v) for k, v in sorted(files.items())}}


def apple(raw: bytes, edition: str) -> dict:
    """Verify the companion checksum and the exact Apple application inventory."""
    base = APPLE_NAMES[edition]
    name = base + '.zip'
    files = members(raw, {name, base + '.sha256'})
    inner = files[name]
    sha = digest(inner)
    if files[base + '.sha256'].decode('ascii').split() != [sha, name]:
        raise ValueError('inner Apple checksum differs')
    data = inspect(inner, edition)
    app, exe, _, _, _ = EDITIONS[edition]
    path = app + '/Contents/MacOS/' + exe
    binary, = [x for x in data['files'] if x['path'] == path]
    return {'app_sha256': binary['sha256'], 'bundle_build': data['bundle_version'],
            'inner_archive_sha256': sha, 'architectures': data['architectures'],
            'payload_sha256': {x['path']: x['sha256'] for x in data['files']}}


def candidate(raw: bytes, sha: str, source: str, profile: str) -> dict:
    """Bind archive bytes; source and CI provenance remain caller assertions."""
    if digest(raw) != sha or not re.fullmatch('[0-9a-f]{40}', source):
        raise ValueError('archive digest or source identity differs')
    identity = windows(raw) if profile.startswith('windows-') else apple(raw, profile)
    return {'profile': profile, 'archive_sha256': sha, 'source_sha': source,
            'source_provenance': 'CALLER_REVIEW_REQUIRED', **identity}


def template(identity: dict) -> dict:
    """Initialize each profile independently with no assumed test passes."""
    return {'schema': 'hardware-acceptance-checklist-v1', 'candidate': identity,
            'os_build': '', 'device_model': '',
            'cases': {key: {'status': 'NOT_RUN', 'observation': ''}
                      for key in PROFILES[identity['profile']]}}


def review(identity: dict, raw: bytes) -> dict:
    """Validate coverage and identity without authenticating observations."""
    expected, row = template(identity), document(raw)
    if (set(row) != set(expected) or row['schema'] != expected['schema']
            or row['candidate'] != identity or not isinstance(row['cases'], dict)
            or set(row['cases']) != set(expected['cases'])):
        raise ValueError('checklist identity or coverage differs')
    results = {key: check_case(key, value) for key, value in row['cases'].items()}
    for key in ('os_build', 'device_model'):
        value = row[key]
        if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9 ._-]{0,50}', value):
            raise ValueError('invalid test context')
        if not value.strip() and any(x != 'NOT_RUN' for x in results.values()):
            raise ValueError('missing test context')
    model = {'windows-aj179': 'AJ179 APEX', 'windows-aj159': 'AJ159 APEX',
             'windows-aula': 'AULA L99'}.get(identity['profile'])
    if model and row['device_model'] and row['device_model'] != model:
        raise ValueError('wrong device profile')
    counts = {status: list(results.values()).count(status) for status in STATUSES}
    return {'schema': 'hardware-acceptance-review-v1', 'candidate': identity,
            'checklist_sha256': digest(raw), 'case_statuses': results, 'counts': counts,
            'coverage': 'COMPLETE_REPORTED' if counts['PASS'] == len(results) else 'INCOMPLETE',
            'human_observations': 'SELF_REPORTED_NOT_AUTHENTICATED',
            'physical_acceptance': 'NOT_INDEPENDENTLY_VERIFIED',
            'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Generate or validate a local record; no device I/O or network access."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--archive-sha256', required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--profile', choices=sorted(PROFILES), required=True)
    parser.add_argument('--checklist', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        identity = candidate(read_local(args.archive), args.archive_sha256,
                             args.source_sha, args.profile)
        result = review(identity, read(args.checklist)) if args.checklist else template(identity)
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile):
        print('FAIL: hardware artifact/checklist identity', file=sys.stderr)
        return 2
    print('PASS: local hardware checklist format; no independent acceptance')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
