#!/usr/bin/env python3
"""Bind a retained uninstaller to an exact unpublished installer artifact."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import re
import stat
import struct
import sys
import zipfile
import zlib

from read_diagnostic_session import unique_object
from run_offline_qa import write_json
from verify_installer_candidate import digest, pe_observation, read_member, verify
from verify_windowsdesktop_provenance import read_local

EXE = 'unins000.exe'
MANIFEST = 'uninstaller.json'
MAX_EXE = 16 * 1024 * 1024
MAX_ZIP = MAX_EXE + 1024 * 1024
KEYS = {'schema', 'source_sha', 'version', 'setup_sha256', 'app_sha256',
        'baseline_uninstaller_sha256', 'uninstaller_sha256', 'uninstaller_bytes',
        'scenario', 'uninstall_smoke', 'engine_attribution', 'release_admission'}


def members(archive: zipfile.ZipFile) -> dict:
    """Allow only exact bounded regular members, without extraction."""
    infos = archive.infolist()
    if len(infos) != 2 or {x.filename for x in infos} != {EXE, MANIFEST}:
        raise ValueError('unexpected uninstaller archive members')
    for info in infos:
        limit = MAX_EXE if info.filename == EXE else 65536
        if (info.orig_filename != info.filename or info.flag_bits & 1
                or info.is_dir() or not 0 < info.file_size <= limit
                or stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG)
                or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
            raise ValueError('invalid uninstaller member')
    return {info.filename: info for info in infos}


def validate_manifest(raw: bytes, candidate: dict) -> dict:
    """Require exact source and binary binding, never promote smoke to trust."""
    data = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_object)
    if not isinstance(data, dict) or set(data) != KEYS:
        raise ValueError('invalid uninstaller manifest')
    for key in ('source_sha', 'version', 'setup_sha256', 'app_sha256'):
        if data[key] != candidate[key]:
            raise ValueError('uninstaller candidate identity differs')
    expected = {'schema': 'installer-uninstaller-v1', 'scenario': 'beta60_to_beta61',
                'uninstall_smoke': 'PASS', 'engine_attribution': 'NOT_VERIFIED',
                'release_admission': 'NOT_VERIFIED'}
    if any(data[key] != value for key, value in expected.items()):
        raise ValueError('unexpected uninstaller scope')
    for key in ('baseline_uninstaller_sha256', 'uninstaller_sha256'):
        if not isinstance(data[key], str) or not re.fullmatch(r'[0-9a-f]{64}', data[key]):
            raise ValueError('invalid uninstaller digest')
    size = data['uninstaller_bytes']
    if type(size) is not int or not 0 < size <= MAX_EXE:
        raise ValueError('invalid uninstaller size')
    return data


def verify_pair(raw: bytes, sha: str, candidate_raw: bytes,
                candidate_sha: str, source: str) -> dict:
    """Verify both exact archives and the exercised uninstaller header."""
    if len(raw) > MAX_ZIP or not re.fullmatch(r'[0-9a-f]{64}', sha) or digest(raw) != sha:
        raise ValueError('uninstaller archive digest or extent differs')
    candidate = verify(candidate_raw, candidate_sha, source)['candidate']
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        entries = members(archive)
        data = validate_manifest(read_member(archive, entries[MANIFEST]), candidate)
        exe = read_member(archive, entries[EXE])
    if len(exe) != data['uninstaller_bytes'] or digest(exe) != data['uninstaller_sha256']:
        raise ValueError('uninstaller bytes differ')
    return {'schema': 1, 'archive_sha256': sha, 'candidate_archive_sha256': candidate_sha,
            'uninstaller': data, 'bootstrap': pe_observation(exe),
            'same_as_reported_baseline': data['uninstaller_sha256'] == data['baseline_uninstaller_sha256'],
            'engine_attribution': 'NOT_VERIFIED', 'physical_acceptance': 'NOT_VERIFIED',
            'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Verify local ZIPs and write a new scoped JSON record."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('archive', 'candidate-archive', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('sha256', 'candidate-sha256', 'source-sha'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_pair(read_local(args.archive), args.sha256,
                             read_local(args.candidate_archive), args.candidate_sha256,
                             args.source_sha)
        write_json(args.output, result)
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, NotImplementedError,
            zipfile.BadZipFile, zlib.error, struct.error, RecursionError):
        print('FAIL: uninstaller evidence verification', file=sys.stderr)
        return 2
    print('PASS: exact uninstaller evidence binding; engine attribution not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
