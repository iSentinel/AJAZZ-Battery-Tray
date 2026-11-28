#!/usr/bin/env python3
"""Verify the reviewed exact IFPS launch policy, without executing bytecode."""

import argparse
from pathlib import Path
import struct
import sys

from compare_inno_loader import digest
from run_offline_qa import write_json
from verify_inno_inner_engine import recover
from verify_inno_setup_data import SETUP_SHA, decode_setup0, header_script
from verify_windowsdesktop_provenance import read_local

SCRIPT_SHA = '668ff74c3c55db0cd8de544d30bac23497ad6e7a38aaf6da77016c78de2b2a65'
TYPES = (13, 5, 16, 14, 24, 9, 8, 7, 17, 10, 5, 6, 4, 3, 2, 21,
         10, 28, 28, 10, 28, 19, 20, 20, 18, 1, 3, 5, 1, 1, 25, 25)
EXPORTS = {15: b'ANYMETHOD', 28: b'BOOLEAN', 30: b'TWIZARDFORM',
           31: b'TUNINSTALLPROGRESSFORM'}


class Reader:
    """Bounded sequential IFPS reader."""

    def __init__(self, raw: bytes) -> None:
        """Retain local input and current position."""
        self.raw = raw
        self.pos = 0

    def take(self, size: int) -> bytes:
        """Reject reads outside the exact byte extent."""
        if not 0 <= size <= len(self.raw) - self.pos:
            raise ValueError('truncated IFPS field')
        data = self.raw[self.pos:self.pos + size]
        self.pos += size
        return data

    def byte(self) -> int:
        """Read one byte."""
        return self.take(1)[0]

    def number(self) -> int:
        """Read a little-endian cardinal."""
        return struct.unpack('<I', self.take(4))[0]

    def string(self) -> bytes:
        """Read one length-prefixed byte string."""
        return self.take(self.number())


def check_types(reader: Reader) -> None:
    """Require the exact reviewed type table, names and absent attributes."""
    for i, base in enumerate(TYPES):
        flags = reader.byte()
        if flags != base | (128 if i in EXPORTS else 0):
            raise ValueError('unexpected IFPS type')
        if base in (21, 25):
            if reader.string() != (b'\0' if base == 21 else EXPORTS[i]):
                raise ValueError('unexpected IFPS type declaration')
        if i in EXPORTS and reader.string() != EXPORTS[i]:
            raise ValueError('unexpected IFPS type export')
        if reader.number():
            raise ValueError('unexpected IFPS type attributes')


def check_procs(reader: Reader) -> None:
    """Require all imports, exports, declarations and global variables."""
    for offset, length, name, decl in ((448, 1, b'!MAIN', b'-1'),
                                       (449, 195, b'SHOULDLAUNCHTRAY', b'28')):
        if (reader.byte(), reader.number(), reader.number(), reader.string(),
                reader.string()) != (2, offset, length, name, decl):
            raise ValueError('unexpected IFPS internal procedure')
    for name, decl in ((b'EXPANDCONSTANT', b'\x01\0'), (b'WIZARDSILENT', b'\x01')):
        if (reader.byte(), reader.take(reader.byte()), reader.string()) != (3, name, decl):
            raise ValueError('unexpected IFPS import')
    for typ, name in ((30, b'WIZARDFORM'), (31, b'UNINSTALLPROGRESSFORM')):
        if (reader.number(), reader.byte(), reader.string()) != (typ, 1, name):
            raise ValueError('unexpected IFPS global variable')
    if reader.pos != 448 or reader.byte() != 9:
        raise ValueError('unexpected IFPS main procedure')


def operand(reader: Reader) -> tuple:
    """Decode the observed stack slots and typed literal operand subset."""
    mode, typ = reader.byte(), reader.number()
    if mode == 0 and typ in (0x5fffffff, 0x60000001, 0x60000002):
        return ('slot', typ - 0x60000000)
    if mode != 1:
        raise ValueError('unsupported IFPS operand')
    if typ == 28:
        value = reader.byte()
        if value not in (0, 1):
            raise ValueError('invalid Boolean constant')
        return ('bool', value)
    if typ == 23:
        return ('char', reader.take(2).decode('utf-16le'))
    if typ == 20:
        return ('str', reader.take(reader.number() * 2).decode('utf-16le'))
    raise ValueError('unsupported IFPS literal')


def instructions(raw: bytes) -> list:
    """Decode every instruction and absolute branch target in scoped code."""
    reader, result = Reader(raw), []
    while reader.pos < len(raw):
        start, op = reader.pos, reader.byte()
        if op in (5, 11):
            args = (reader.number(),)
        elif op in (6, 18):
            distance = struct.unpack('<i', reader.take(4))[0]
            args = (reader.pos + distance,)
        elif op in (2, 3, 15):
            args = (operand(reader),)
        elif op == 0:
            args = (operand(reader), operand(reader))
        elif op == 12:
            args = (reader.byte(), operand(reader), operand(reader), operand(reader))
        elif op == 17:
            args = (operand(reader), reader.byte())
        elif op in (4, 9):
            args = ()
        else:
            raise ValueError('unsupported IFPS opcode')
        result.append((start, op, args))
    return result


def expected_instructions() -> list:
    """Describe the reviewed source policy and complete observed stack operations."""
    one, two, ret = ('slot', 1), ('slot', 2), ('slot', -1)
    return [
        (0, 11, (18,)), (5, 11, (18,)),
        (10, 0, (two, ('str', '{param:LAUNCH|}'))),
        (55, 3, (one,)), (61, 5, (2,)), (66, 4, ()), (67, 4, ()),
        (68, 11, (28,)), (73, 12, (5, two, one, ('char', '0'))),
        (92, 17, (two, 1)), (99, 4, ()), (100, 18, (122,)),
        (105, 0, (ret, ('bool', 0))), (117, 6, (194,)),
        (122, 11, (28,)), (127, 12, (5, two, one, ('char', '1'))),
        (146, 17, (two, 1)), (153, 4, ()), (154, 18, (176,)),
        (159, 0, (ret, ('bool', 1))), (171, 6, (194,)),
        (176, 3, (ret,)), (182, 5, (3,)), (187, 4, ()),
        (188, 15, (ret,)), (194, 9, ()),
    ]


def check_script(raw: bytes) -> dict:
    """Compare all bytecode tables and instructions to the reviewed policy."""
    if len(raw) != 644 or raw[:28] != struct.pack('<4s6I', b'IFPS', 23, 32, 4, 2, 0, 0):
        raise ValueError('unexpected IFPS header')
    reader = Reader(raw)
    reader.take(28)
    check_types(reader)
    check_procs(reader)
    decoded = instructions(reader.take(len(raw) - reader.pos))
    if decoded != expected_instructions():
        raise ValueError('IFPS launch policy differs')
    return {'script_sha256': digest(raw), 'types': 32, 'procedures': 4,
            'globals': 2, 'instructions': len(decoded) + 1,
            'imports': ['EXPANDCONSTANT', 'WIZARDSILENT'],
            'policy': 'MATCH_REVIEWED_SOURCE',
            'runtime_execution': 'NOT_PERFORMED', 'release_admission': 'NOT_VERIFIED'}


def verify(setup: bytes, source: bytes) -> dict:
    """Pin actual artifact and reviewed installer source before decoding."""
    if digest(setup) != SETUP_SHA or digest(source) != SCRIPT_SHA:
        raise ValueError('unexpected setup or installer source digest')
    _, offsets = recover(setup)
    first, _, _ = decode_setup0(setup[offsets['offset0']:offsets['engine_offset']])
    header_script(first)
    reader = Reader(first)
    for _ in range(42):
        reader.string()
    return {**check_script(reader.string()), 'setup_sha256': SETUP_SHA,
            'installer_source_sha256': SCRIPT_SHA}


def main(argv: list[str] | None = None) -> int:
    """Write scoped static evidence without invoking the installer."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('setup', 'installer-script', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        write_json(args.output, verify(read_local(args.setup), read_local(args.installer_script)))
    except (OSError, ValueError, KeyError, struct.error):
        print('FAIL: scoped IFPS verification', file=sys.stderr)
        return 2
    print('PASS: exact reviewed IFPS launch policy; no runtime execution')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
