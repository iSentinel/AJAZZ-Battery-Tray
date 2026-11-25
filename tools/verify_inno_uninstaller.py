#!/usr/bin/env python3
"""Attribute the exercised unsigned Inno 6.7.1 uninstaller PE and frame."""
import argparse
from io import BytesIO
from pathlib import Path
import struct
import sys
import zipfile
import zlib
import lzma

from compare_inno_loader import TEMPLATE_SHA, compare, digest, layout
from run_offline_qa import write_json
from verify_inno_inner_engine import ENGINE_SHA, recover
from verify_inno_messages import verify_messages
from verify_installer_candidate import SETUP
from verify_uninstaller_evidence import EXE, verify_pair
from verify_windowsdesktop_provenance import read_local

APP_ID = '{9829045F-37F0-4AC3-ACBD-1B5E4129A179}'
MODE_OFFSET = 0x30
MODE_UNINSTALL = 0x6e556e49
TAIL_ID = 0x67734d49
MAX_MESSAGES = 1024 * 1024


def attribute(engine: bytes, exe: bytes) -> dict:
    """Require complete PE equality except documented uninstall mode marker."""
    end = layout(engine)['end']
    if end != len(engine) or not 44 < len(exe) - end <= MAX_MESSAGES + 44:
        raise ValueError('unexpected uninstall overlay extent')
    expected = bytearray(engine)
    if expected[MODE_OFFSET:MODE_OFFSET + 4] != bytes(4):
        raise ValueError('unexpected initial engine mode')
    struct.pack_into('<I', expected, MODE_OFFSET, MODE_UNINSTALL)
    if exe[:end] != expected or layout(exe)['end'] != end:
        raise ValueError('uninstaller PE differs beyond mode marker')
    app_hash = digest(APP_ID.encode('utf-16le'))
    if exe[end:end + 32].hex() != app_hash:
        raise ValueError('uninstaller AppId hash differs')
    ident, offset = struct.unpack('<Iq', exe[-12:])
    if ident != TAIL_ID or offset != end + 32 or offset >= len(exe) - 12:
        raise ValueError('invalid uninstaller message tail')
    messages = exe[offset:-12]
    return {'pe_bytes': end, 'engine_sha256': digest(engine),
            'uninstaller_sha256': digest(exe), 'pe_except_mode': 'MATCH',
            'mode_offset': MODE_OFFSET, 'mode': MODE_UNINSTALL,
            'app_id_sha256': app_hash, 'message_offset': offset,
            'message_bytes': len(messages), 'message_sha256': digest(messages),
            'message_frame': 'MATCH', 'message_semantics': 'NOT_VERIFIED'}


def verify_attribution(raw: bytes, sha: str, candidate_raw: bytes,
                       candidate_sha: str, source: str, loader: bytes,
                       template: bytes) -> dict:
    """Bind both CI archives and pinned templates before recovering the engine."""
    binding = verify_pair(raw, sha, candidate_raw, candidate_sha, source)
    if digest(loader) != TEMPLATE_SHA or digest(template) != ENGINE_SHA:
        raise ValueError('official template digest differs')
    with zipfile.ZipFile(BytesIO(candidate_raw)) as archive:
        setup = archive.read(SETUP)
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        exe = archive.read(EXE)
    compare(loader, setup)
    engine, record = recover(setup)
    match = compare(template, engine, overlay_expected=False)
    return {'schema': 1, 'binding': binding, 'recovery': record,
            'official_engine_sections': match['sections'],
            'attribution': attribute(engine, exe),
            'messages': verify_messages(exe[len(engine) + 32:-12]),
            'engine_non_resource_bytes': 'MATCH',
            'engine_resource_provenance': 'NOT_VERIFIED',
            'compiled_script': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Verify scoped local bytes without execution or extracting an archive."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('archive', 'candidate-archive', 'loader-template', 'engine-template', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('sha256', 'candidate-sha256', 'source-sha'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_attribution(read_local(args.archive), args.sha256,
                                    read_local(args.candidate_archive),
                                    args.candidate_sha256, args.source_sha,
                                    read_local(args.loader_template),
                                    read_local(args.engine_template))
        write_json(args.output, result)
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, NotImplementedError,
            struct.error, zipfile.BadZipFile, zlib.error, lzma.LZMAError, RecursionError):
        print('FAIL: scoped Inno uninstaller attribution', file=sys.stderr)
        return 2
    print('PASS: exact uninstaller PE and message frame; message semantics not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
