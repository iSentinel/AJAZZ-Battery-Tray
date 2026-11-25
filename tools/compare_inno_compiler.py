#!/usr/bin/env python3
"""Compare observed compiler inputs to an independently extracted official package."""

import argparse
from io import BytesIO
import json
from pathlib import Path
import re
import stat
import sys
import zipfile
import zlib

from read_diagnostic_session import unique_object
from run_offline_qa import write_json
from verify_installer_candidate import digest, verify
from verify_installer_payload import file_digest
from verify_windowsdesktop_provenance import read_local

REQUIRED = ('ISCC.exe', 'ISCmplr.dll', 'ISPP.dll', 'Setup.e32',
            'SetupCustomStyle.e32', 'SetupLdr.e32', 'SetupLdr.e64',
            'ISPPBuiltins.iss', 'Default.isl', 'license.txt')
OPTIONAL = ('islzma.dll', 'islzma32.exe', 'islzma64.exe', 'is7z.dll',
            'is7zxa.dll', 'is7zxr.dll', 'isbunzip.dll', 'isbzip.dll',
            'isscint.dll', 'isunzlib.dll', 'iszlib.dll')
NAMES = frozenset(REQUIRED + OPTIONAL + tuple(
    name + '.issig' for name in REQUIRED + OPTIONAL
    if name != 'ISCC.exe' and name.endswith(('.dll', '.exe', '.e32', '.e64'))))
LIMIT = 128 * 1024 * 1024
ENTRY = 'ajazz-beta61-inno-inventory.json'


def inventory(raw: bytes, expected_sha: str, candidate: dict) -> list[dict]:
    """Bind bounded inventory JSON to the verified normal candidate."""
    if digest(raw) != expected_sha or len(raw) > 1024 * 1024:
        raise ValueError('inventory archive digest or size differs')
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        infos = archive.infolist()
        if len(infos) != 1 or infos[0].filename != ENTRY:
            raise ValueError('unexpected inventory member')
        info = infos[0]
        if (info.orig_filename != ENTRY or info.flag_bits & 1
                or stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG)
                or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                or not 0 < info.file_size <= 65536):
            raise ValueError('invalid inventory member')
        data = json.loads(archive.read(info).decode('utf-8-sig'),
                          object_pairs_hook=unique_object)
    if not isinstance(data, dict) or set(data) != {
            'schema', 'source_sha', 'engine_version', 'setup_sha256',
            'scope', 'trust', 'files'}:
        raise ValueError('invalid inventory schema')
    if (data['schema'], data['source_sha'], data['engine_version'],
            data['setup_sha256'], data['trust'], data['scope']) != (
                'inno-compiler-inventory-v1', candidate['source_sha'], '6.7.1',
                candidate['setup_sha256'], 'NOT_VERIFIED',
                'observed top-level compiler inputs, not actual loaded or embedded components'):
        raise ValueError('inventory candidate identity differs')
    if not isinstance(data['files'], list) or len(data['files']) != len(NAMES):
        raise ValueError('invalid component count')
    return data['files']


def compare(rows: list[dict], root: Path) -> list[dict]:
    """Require exact allowlist coverage, present files and matching official bytes."""
    if not stat.S_ISDIR(root.lstat().st_mode):
        raise ValueError('invalid official component directory')
    seen = set()
    result = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'name', 'state', 'bytes', 'sha256'}:
            raise ValueError('invalid component record')
        name = row['name']
        if not isinstance(name, str) or name not in NAMES or name in seen:
            raise ValueError('unexpected or duplicate component name')
        seen.add(name)
        if (row['state'] != 'PRESENT' or type(row['bytes']) is not int
                or not 0 < row['bytes'] <= LIMIT or not isinstance(row['sha256'], str)
                or not re.fullmatch(r'[0-9a-f]{64}', row['sha256'])):
            raise ValueError('component not qualified')
        path = root / name
        if file_digest(path, LIMIT) != row['sha256'] or path.stat().st_size != row['bytes']:
            raise ValueError('official component bytes differ')
        result.append({'name': name, 'bytes': row['bytes'], 'sha256': row['sha256']})
    if seen != NAMES:
        raise ValueError('incomplete component set')
    return sorted(result, key=lambda row: row['name'])


def main(argv: list[str] | None = None) -> int:
    """Verify trusted immutable local artifacts; never execute or extract them."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('inventory', 'candidate', 'official', 'official-dir', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('inventory-sha256', 'candidate-sha256', 'official-sha256', 'source-sha'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args(argv)
    try:
        candidate = verify(read_local(args.candidate), args.candidate_sha256, args.source_sha)
        if file_digest(args.official, LIMIT) != args.official_sha256:
            raise ValueError('official package digest differs')
        rows = inventory(read_local(args.inventory), args.inventory_sha256, candidate['candidate'])
        files = compare(rows, args.official_dir)
        write_json(args.output, {'schema': 1, 'source_sha': args.source_sha,
                   'setup_sha256': candidate['candidate']['setup_sha256'],
                   'inventory_sha256': args.inventory_sha256,
                   'official_sha256': args.official_sha256, 'files': files,
                   'scope': 'observed compiler files compared to supplied extracted directory',
                   'extraction_provenance': 'CALLER_REVIEW_REQUIRED',
                   'signature_trust': 'NOT_VERIFIED', 'embedded_engine': 'NOT_VERIFIED',
                   'release_admission': 'NOT_VERIFIED'})
    except (OSError, ValueError, TypeError, KeyError, RuntimeError,
            zipfile.BadZipFile, zlib.error, NotImplementedError):
        print('FAIL: compiler component comparison', file=sys.stderr)
        return 2
    print('PASS: 38 scoped compiler inputs; trust and embedded engine not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
