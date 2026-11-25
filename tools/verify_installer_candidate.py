#!/usr/bin/env python3
"""Verify an unpublished installer artifact without executing its contents."""

import argparse
import hashlib
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
from verify_windowsdesktop_provenance import read_local

SETUP = 'AJAZZBatteryTray-Setup-win-x64.exe'
MAX_SETUP = 256 * 1024 * 1024
MAX_MANIFEST = 65536
KEYS = {'schema', 'source_sha', 'version', 'setup_sha256', 'app_sha256',
        'lifecycle_probe', 'physical_acceptance', 'release_admission'}


def digest(raw: bytes) -> str:
    """Return SHA-256 of exact bytes."""
    return hashlib.sha256(raw).hexdigest()


def manifest(raw: bytes, source: str) -> dict:
    """Require the expected checkout revision and non-probe schema."""
    data = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_object)
    if not isinstance(data, dict) or set(data) != KEYS:
        raise ValueError('invalid candidate manifest')
    if (not re.fullmatch(r'[0-9a-f]{40}', source)
            or data['source_sha'] != source or data['version'] != '0.3.0-beta.61'
            or data['schema'] != 'installer-candidate-v1'
            or data['lifecycle_probe'] is not False
            or data['physical_acceptance'] != 'NOT_VERIFIED'
            or data['release_admission'] != 'NOT_VERIFIED'):
        raise ValueError('unexpected candidate identity')
    for key in ('setup_sha256', 'app_sha256'):
        if not isinstance(data[key], str) or not re.fullmatch(r'[0-9a-f]{64}', data[key]):
            raise ValueError('invalid manifest digest')
    return data


def pe_observation(raw: bytes) -> dict:
    """Inventory the bounded PE32 GUI bootstrap header, not its payload."""
    if len(raw) < 64 or raw[:2] != b'MZ':
        raise ValueError('not a PE bootstrap')
    pos, = struct.unpack_from('<I', raw, 60)
    if pos < 64 or pos + 24 > len(raw) or raw[pos:pos + 4] != b'PE\0\0':
        raise ValueError('invalid PE signature')
    machine, sections, _, _, _, optional, flags = struct.unpack_from('<HHIIIHH', raw, pos + 4)
    start = pos + 24
    if (machine != 0x14c or not 1 <= sections <= 96 or optional < 136
            or start + optional + sections * 40 > len(raw)
            or struct.unpack_from('<H', raw, start)[0] != 0x10b
            or struct.unpack_from('<H', raw, start + 68)[0] != 2
            or not flags & 2 or flags & 0x2000):
        raise ValueError('unexpected installer bootstrap layout')
    if struct.unpack_from('<I', raw, start + 92)[0] < 5:
        raise ValueError('missing PE certificate directory')
    offset, size = struct.unpack_from('<II', raw, start + 128)
    if bool(offset) != bool(size) or (size and (offset % 8 or offset + size > len(raw))):
        raise ValueError('invalid certificate table bounds')
    return {'machine': 'x86', 'format': 'PE32', 'sections': sections,
            'certificate_table': 'PRESENT' if size else 'ABSENT',
            'authenticode_trust': 'NOT_VERIFIED'}


def members(archive: zipfile.ZipFile) -> dict:
    """Allow only two exact regular, bounded, unencrypted members."""
    infos = archive.infolist()
    if len(infos) != 2 or {x.filename for x in infos} != {SETUP, 'candidate.json'}:
        raise ValueError('unexpected archive members')
    for info in infos:
        limit = MAX_SETUP if info.filename == SETUP else MAX_MANIFEST
        if (info.orig_filename != info.filename or info.flag_bits & 1 or info.is_dir()
                or stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG)
                or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                or not 0 < info.file_size <= limit):
            raise ValueError('invalid member')
    return {i.filename: i for i in infos}


def read_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> bytes:
    """Check CRC and actual member size without extraction."""
    with archive.open(info) as stream:
        raw = stream.read(info.file_size + 1)
    if len(raw) != info.file_size:
        raise ValueError('member length differs')
    return raw


def verify(raw: bytes, expected_sha: str, source: str) -> dict:
    """Bind exact archive and setup bytes to reviewed checkout identity."""
    if not re.fullmatch(r'[0-9a-f]{64}', expected_sha) or digest(raw) != expected_sha:
        raise ValueError('archive SHA-256 differs')
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        entries = members(archive)
        data = manifest(read_member(archive, entries['candidate.json']), source)
        setup = read_member(archive, entries[SETUP])
    if digest(setup) != data['setup_sha256']:
        raise ValueError('setup SHA-256 differs')
    return {'schema': 1, 'archive_sha256': expected_sha, 'candidate': data,
            'setup_bytes': len(setup), 'bootstrap': pe_observation(setup),
            'scope': 'archive, manifest and bootstrap only',
            'app_payload_verification': 'NOT_VERIFIED',
            'source_tree_equivalence': 'NOT_VERIFIED',
            'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Validate a local artifact; emit new evidence only on success."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--source-sha', required=True, help='Actual CI checkout SHA, not PR head')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = verify(read_local(args.archive), args.sha256, args.source_sha)
        write_json(args.output, result)
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, NotImplementedError,
            zipfile.BadZipFile, zlib.error, struct.error, RecursionError):
        print('FAIL: installer candidate verification', file=sys.stderr)
        return 2
    print('PASS: scoped installer candidate; payload and trust not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
