#!/usr/bin/env python3
"""Compare scoped beta.61 Setup.0 installation records with reviewed source policy."""

import argparse
from pathlib import Path
import struct
import sys
import zlib

from compare_inno_loader import digest
from run_offline_qa import write_json
from verify_inno_ifps import Reader, SCRIPT_SHA, check_script
from verify_inno_inner_engine import recover
from verify_inno_message_sources import ISL_SHA, IDS_SHA, expected_body
from verify_inno_messages import HEADER as MESSAGE_HEADER, COUNT
from verify_inno_setup_data import COUNTS, FILES, SETUP_SHA, decode_setup0
from verify_windowsdesktop_provenance import read_local

APP = 'AJAZZ Battery Tray'
EXE = r'{app}\AJAZZBatteryTray.exe'
URL = 'https://github.com/iSentinel/AJAZZ-Battery-Tray'
MIN_VERSION = struct.pack('<IIHIIH', 0, 0x06010000, 256, 0, 0, 0)
HEADER = struct.Struct('<17iIIHIIHiiBB6iBBBqi9BqQ')
FLAGS = (0, 1, 9, 11, 12, 13, 17, 20, 22, 23, 24, 25, 28, 29,
         30, 32, 35, 37, 39, 40)


def strings(reader: Reader, count: int) -> list[str]:
    """Decode length-prefixed Unicode fields."""
    return [reader.string().decode('utf-16le') for _ in range(count)]


def require(actual: object, expected: object, label: str) -> None:
    """Reject a difference in a reviewed record."""
    if actual != expected:
        raise ValueError('unexpected ' + label)


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
    expected_fixed = (*COUNTS, 0, 0x06010000, 256, 0, 0, 0, 120, 120, 0, 0,
                      0xf9f3e8, 0x1fffffff, 0x1fffffff, 0, 0, 0x1fffffff,
                      255, 255, 0, 0, 1, 0, 0, 2, 0, 0, 0, 4, 0, 2, 0,
                      sum(1 << i for i in FLAGS))
    require(HEADER.unpack(reader.take(HEADER.size)), expected_fixed, 'fixed header')
    return script


def custom_messages(isl: bytes) -> list:
    """Read the reviewed Default.isl custom messages in source order."""
    result = []
    active = False
    for line in isl.decode('utf-8-sig').splitlines():
        if line.startswith('['):
            active = line == '[CustomMessages]'
        elif active and line.strip() and not line.lstrip().startswith(';'):
            key, sep, value = line.partition('=')
            if not sep or not key or any(row[0] == key for row in result):
                raise ValueError('invalid custom message')
            result.append([key, value.replace('%n', '\r\n')])
    return result


def check_language(reader: Reader, isl: bytes, ids: bytes) -> dict:
    """Check reviewed language settings and record bounded message bytes."""
    require(strings(reader, 4), ['english', 'English', 'Segoe UI', 'Segoe UI'],
            'language strings')
    data = reader.string()
    body = expected_body(isl, ids)
    size = 80 + len(body)
    expected = MESSAGE_HEADER + struct.pack('<IIII', COUNT, size, size ^ 0xffffffff,
                                            zlib.crc32(body)) + body
    require(data, expected, 'language message bytes')
    require([reader.string() for _ in range(3)], [b''] * 3, 'language info fields')
    require(reader.take(19), struct.pack('<H4iB', 1033, 9, 15, 7, 14, 0),
            'language settings')
    custom = []
    for _ in range(12):
        custom.append(strings(reader, 2))
        require(reader.number(), 0, 'custom message language index')
    require(custom, custom_messages(isl), 'custom messages')
    return {'message_sha256': digest(data), 'standard_message_count': COUNT,
            'custom_message_count': len(custom), 'message_content': 'MATCH_PINNED_SOURCE'}


def check_task(reader: Reader) -> None:
    """Require the optional unchecked desktop shortcut task."""
    require(strings(reader, 6), ['desktopicon', 'Create a desktop shortcut',
                                 'Additional shortcuts:', '', '', ''], 'task')
    require(reader.take(23), b'\0\1' + MIN_VERSION + b'\2', 'task flags')


def check_files(reader: Reader) -> None:
    """Require one generated uninstaller and five expected file destinations."""
    destinations = [''] + [EXE] + [r'{app}\Icons' + chr(92) + row[0] for row in FILES[1:]]
    for index, dest in enumerate(destinations):
        require(strings(reader, 15), ['', dest] + [''] * 13, 'file strings')
        require(reader.string(), b'', 'file signature key list')
        fixed = (bytes(33) + MIN_VERSION + struct.pack('<iiqhQB',
                 index - 1, 0, 0, -1, 0x800 if index == 0 else 0x20000,
                 1 if index == 0 else 0))
        require(reader.take(80), fixed, 'file metadata')


def check_shortcuts_and_run(reader: Reader) -> None:
    """Require exact shortcut destinations and the single reviewed run entry."""
    for desktop in (False, True):
        name = ('{autodesktop}' + chr(92) if desktop else '{autoprograms}' + chr(92)) + APP
        fields = [name, EXE, '', '' if desktop else '{app}', '', '', '',
                  'desktopicon' if desktop else '', '', '', '', '', '']
        require(strings(reader, 13), fields, 'shortcut strings')
        require(reader.take(48), bytes(16) + MIN_VERSION + struct.pack('<iiBHB', 0, 1, 0, 0, 0),
                'shortcut settings')
    require(strings(reader, 13), [EXE, '', '{app}', '', 'Starting AJAZZ Battery Tray...',
                                  '', '', '', '', '', 'ShouldLaunchTray', '', ''], 'run strings')
    require(reader.take(27), MIN_VERSION + struct.pack('<iBH', 1, 1, 0x200), 'run flags')


def wizard_data(reader: Reader) -> list[dict]:
    """Record two bounded wizard images and require no other data."""
    result = []
    for index, size in enumerate((5767, 10005, 0, 0, 0, 0)):
        require(reader.number(), int(bool(size)), 'wizard image count')
        if size:
            data = reader.string()
            require(len(data), size, 'wizard image size')
            if not data.startswith(b'\x89PNG\r\n\x1a\n'):
                raise ValueError('unexpected wizard image format')
            result.append({'index': index, 'bytes': size, 'sha256': digest(data)})
    require(reader.pos, len(reader.raw), 'setup data trailing extent')
    return result


def verify(setup: bytes, source: bytes, isl: bytes, ids: bytes) -> dict:
    """Bind exact artifact and source, compare records and account for the block."""
    require(digest(setup), SETUP_SHA, 'setup digest')
    require(digest(source), SCRIPT_SHA, 'installer source digest')
    require(digest(isl), ISL_SHA, 'Default.isl digest')
    require(digest(ids), IDS_SHA, 'message enum digest')
    _, offsets = recover(setup)
    first, _, _ = decode_setup0(setup[offsets['offset0']:offsets['engine_offset']])
    reader = Reader(first)
    script = check_header(reader)
    language = check_language(reader, isl, ids)
    check_task(reader)
    check_files(reader)
    check_shortcuts_and_run(reader)
    images = wizard_data(reader)
    return {'schema': 1, 'setup_sha256': SETUP_SHA, 'script': script,
            'header_policy': 'MATCH_REVIEWED_SOURCE_AND_DEFAULTS',
            'file_records': 6, 'shortcut_records': 2, 'run_records': 1,
            'language': language, 'wizard_images': images,
            'wizard_image_provenance': 'NOT_VERIFIED',
            'trailing_bytes': 0, 'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Write local evidence for scoped setup policy, not release admission."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('setup', 'installer-script', 'default-isl', 'message-ids', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        write_json(args.output, verify(read_local(args.setup), read_local(args.installer_script),
                                           read_local(args.default_isl), read_local(args.message_ids)))
    except (OSError, ValueError, KeyError, struct.error):
        print('FAIL: scoped setup records', file=sys.stderr)
        return 2
    print('PASS: scoped setup record policy and complete framing')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
