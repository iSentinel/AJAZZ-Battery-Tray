#!/usr/bin/env python3
"""Check every scoped 6.7.4 product Setup.0 record and wizard image."""

import argparse
import lzma
from pathlib import Path
import struct
import sys
import zlib

from compare_inno_loader import digest
from run_offline_qa import write_json
from validate_scoped_sbom_schema import document
from verify_dotnet_host_resources import resources
from verify_inno674_solid_payload import NOTICES
from verify_inno_ifps import Reader, check_script
from verify_inno_inner_engine import recover
from verify_inno_message_sources import ISL_SHA, IDS_SHA
from verify_inno_setup_data import COUNTS, FILES, decode_setup0
from verify_inno_setup_records import (
    APP, EXE, URL, FLAGS, HEADER, MIN_VERSION, check_language,
    check_shortcuts_and_run, check_task, require, strings, wizard_data,
)
from verify_inno_wizard import compare
from verify_windowsdesktop_provenance import read_local

COMPILER = '236555054ca65194c69544b4ef1d49ea345259745f5c4a2005aca7b5674e7cff'
SOURCE = 'd2876f4209f244033dd92dd19a6f9e9d641ca3cbed441b4dbd020923492f9ef8'
PRODUCTION_SOURCE = 'b93648632e4cacdee0b683842d77c0804c0e468a26d7b6de727f8e05c8f34cd0'
ALIGNED_SOURCE = 'a41fc727e7ff0a9b680958c981f668dca6bb7979c379e562ff136fe7159538bc'
PRODUCTION_SOURCE_PINS = (PRODUCTION_SOURCE, ALIGNED_SOURCE)
SOURCE_PINS = (SOURCE, *PRODUCTION_SOURCE_PINS)

def check_header(reader: Reader) -> dict:
    """Validate all reviewed header strings and fixed settings."""
    expected = [APP, '', '{{9829045F-37F0-4AC3-ACBD-1B5E4129A179}', '',
                'iSentinel', URL, '', URL + '/issues', URL + '/releases',
                '0.3.0-beta.61', r'{autopf}\AJAZZ Battery Tray', APP, '',
                '{app}', APP, EXE, '', '{sysuserinfoname}', '{sysuserinfoorg}',
                '', '', '', '', '', 'yes', 'yes', 'ajazzbatterytray.exe', '',
                'no', 'no', 'x64compatible', 'x64compatible', '', '',
                'yes', 'yes', 'yes', 'yes', 'yes']
    require(strings(reader, 39), expected, 'setup header strings')
    require([reader.string() for _ in range(3)], [b''] * 3, 'license/info fields')
    script = check_script(reader.string())
    counts = list(COUNTS)
    counts[8], counts[9] = 16, 15
    expected_fixed = (*counts, 0, 0x06010000, 256, 0, 0, 0, 120, 120, 0, 0,
                      0xf9f3e8, 0x1fffffff, 0x1fffffff, 0, 0, 0x1fffffff,
                      255, 255, 0, 0, 1, 0, 0, 2, 0, 0, 0, 4, 0, 2, 0,
                      sum(1 << i for i in FLAGS))
    require(HEADER.unpack(reader.take(HEADER.size)), expected_fixed, 'fixed header')
    return script


def destinations() -> list[str]:
    """Enumerate exact generated uninstaller and fifteen product destinations."""
    return (['', EXE] + [r'{app}\Icons' + chr(92) + row[0] for row in FILES[1:]]
            + [r'{app}\Notices' + chr(92) + name.replace('/', chr(92))
               for name in NOTICES])


def check_files(reader: Reader) -> None:
    """Validate every destination, location index and file policy."""
    for index, dest in enumerate(destinations()):
        require(strings(reader, 15), ['', dest] + [''] * 13, 'file strings')
        require(reader.string(), b'', 'file signature key list')
        fixed = (bytes(33) + MIN_VERSION + struct.pack('<iiqhQB',
                 index - 1, 0, 0, -1, 0x800 if index == 0 else 0x20000,
                 1 if index == 0 else 0))
        require(reader.take(80), fixed, 'file metadata')


def verify(setup: bytes, source: bytes, isl: bytes, ids: bytes,
           compiler: bytes, prior: bytes) -> dict:
    """Check exact previous attribution and all decoded installation records."""
    record = document(prior)
    require(record.get('schema'), 'inno-674-solid-payload-v1', 'prior schema')
    require(record.get('setup_sha256'), digest(setup), 'setup digest')
    require(record.get('solid_stream'), 'MATCH', 'solid stream')
    require(record.get('release_admission'), 'NOT_VERIFIED', 'admission')
    source_sha = digest(source.replace(b'\r\n', b'\n'))
    require(source_sha in SOURCE_PINS, True, 'installer source')
    require(digest(isl), ISL_SHA, 'Default.isl digest')
    require(digest(ids), IDS_SHA, 'message enum digest')
    require(digest(compiler), COMPILER, 'compiler digest')
    _, offsets = recover(setup)
    first, _, framing = decode_setup0(setup[offsets['offset0']:offsets['engine_offset']])
    require(framing, record['framing'], 'prior framing')
    reader = Reader(first)
    script = check_header(reader)
    require(script, record['script'], 'prior script')
    language = check_language(reader, isl, ids)
    check_task(reader)
    check_files(reader)
    check_shortcuts_and_run(reader)
    images = compare(wizard_data(reader), resources(compiler))
    return {'schema': 'inno-674-setup-records-v1', 'setup_sha256': digest(setup),
            'source_sha': record['source_sha'], 'solid_evidence_sha256': digest(prior),
            'installer_source_lf_sha256': source_sha, 'compiler_sha256': COMPILER,
            'header_policy': 'MATCH_REVIEWED_SOURCE_AND_DEFAULTS', 'script': script,
            'language': language, 'file_records': len(destinations()),
            'file_destinations': destinations(), 'shortcut_records': 2, 'run_records': 1,
            'wizard_images': images, 'wizard_image_provenance': 'MATCH_PINNED_COMPILER_RCDATA',
            'decoded_header_bytes': len(first), 'trailing_bytes': 0,
            'interactive_acceptance': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Write scoped attribution without executing input files."""
    parser = argparse.ArgumentParser(description=__doc__)
    names = ('setup', 'source', 'isl', 'ids', 'compiler', 'prior')
    for name in (*names, 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        write_json(args.output, verify(*(read_local(getattr(args, n)) for n in names)))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, struct.error,
            zlib.error, lzma.LZMAError, RecursionError):
        print('FAIL: scoped Inno 6.7.4 Setup.0 records', file=sys.stderr)
        return 2
    print('PASS: all scoped Setup.0 records and wizard images; release not admitted')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
