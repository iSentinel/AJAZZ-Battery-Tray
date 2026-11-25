#!/usr/bin/env python3
"""Inventory scoped undefined Mach-O symbols without claiming OS availability."""

import argparse
from collections import Counter
from pathlib import Path
import plistlib
import struct
import sys
import zipfile

from inventory_apple_archive import EDITIONS, archive_members, inspect, sha
from inventory_apple_load_commands import DYLIB, inspect_slice, library, slices
from inventory_dotnet_bundle import BundleError
from run_offline_qa import write_json
from verify_windowsdesktop_provenance import read_local


def commands(raw: bytes) -> list[tuple[int, bytes]]:
    """Read commands only after the caller validates the Mach-O header."""
    count, = struct.unpack_from('<I', raw, 16)
    pos, result = 32, []
    for _ in range(count):
        cmd, size = struct.unpack_from('<II', raw, pos)
        result.append((cmd, raw[pos:pos + size]))
        pos += size
    return result


def unique(items: list[bytes], length: int) -> bytes:
    """Reject duplicate or unexpected fixed-format commands."""
    if len(items) != 1 or len(items[0]) != length:
        raise BundleError('Missing or malformed symbol table command')
    return items[0]


def layout(raw: bytes, cmds: list[tuple[int, bytes]]) -> tuple[int, ...]:
    """Validate scoped nlist and string extents inside __LINKEDIT."""
    sym = unique([data for cmd, data in cmds if cmd == 2], 24)
    dyn = unique([data for cmd, data in cmds if cmd == 11], 80)
    _, _, offset, count, strings, size = struct.unpack('<6I', sym)
    _, _, local, nlocal, ext, nextdef, first, number = struct.unpack_from('<8I', dyn)
    segments = [data for cmd, data in cmds if cmd == 0x19 and len(data) >= 72
                and data[8:24] == b'__LINKEDIT'.ljust(16, b'\0')]
    if len(segments) != 1:
        raise BundleError('Expected one linkedit segment')
    start, length = struct.unpack_from('<QQ', segments[0], 40)
    end = start + length
    _, command_size = struct.unpack_from('<II', raw, 16)
    if (not 32 + command_size <= start < end <= len(raw)
            or not 0 < count <= 100000 or not 0 < number <= count
            or local != 0 or ext != nlocal or first != ext + nextdef
            or first + number != count
            or not start <= offset <= offset + 16 * count <= strings
            or not strings < strings + size <= end):
        raise BundleError('Invalid symbol table extents or partitions')
    return offset, strings, size, first, number


def symbol(raw: bytes, position: int, strings: int, size: int,
           libs: list[dict]) -> dict:
    """Require the reviewed external undefined symbol and library ordinal."""
    index, kind, section, desc, value = struct.unpack_from('<IBBHQ', raw, position)
    ordinal = desc >> 8
    if (kind != 1 or section or value or (desc & 0xff) not in (0, 0x40)
            or not 1 <= ordinal <= len(libs) or not 0 < index < size):
        raise BundleError('Unsupported undefined symbol record')
    stop = raw.find(b'\0', strings + index, strings + min(size, index + 4096))
    if stop <= strings + index:
        raise BundleError('Invalid symbol name extent')
    name = raw[strings + index:stop].decode('ascii')
    if not name.isprintable():
        raise BundleError('Invalid symbol name')
    return {'name': name, 'library': libs[ordinal - 1]['path'],
            'library_linkage': libs[ordinal - 1]['linkage'],
            'weak_reference': bool(desc & 0x40)}


def inspect_symbols(raw: bytes, edition: str) -> dict:
    """Attribute symbol-table imports using original dylib command order."""
    checked = inspect_slice(raw, edition)
    flags, = struct.unpack_from('<I', raw, 24)
    if not flags & 0x80 or flags & 0x100:
        raise BundleError('Expected two-level namespace')
    cmds = commands(raw)
    libs = [library(cmd, data) for cmd, data in cmds if cmd in DYLIB]
    offset, strings, size, first, number = layout(raw, cmds)
    imports = [symbol(raw, offset + i * 16, strings, size, libs)
               for i in range(first, first + number)]
    if len({item['name'] for item in imports}) != number:
        raise BundleError('Duplicate reviewed undefined symbol')
    counts = Counter(item['library'] for item in imports)
    return {'architecture': checked['architecture'], 'symbol_count': number,
            'weak_references': sum(item['weak_reference'] for item in imports),
            'library_counts': dict(sorted(counts.items())),
            'symbols': sorted(imports, key=lambda item: item['name'])}


def report(raw: bytes, edition: str) -> dict:
    """Bind the limited symbol-table evidence to the exact archive and EXE."""
    checked = inspect(raw, edition)
    app, exe, _, _, _ = EDITIONS[edition]
    binary = archive_members(raw)[app + '/Contents/MacOS/' + exe][0]
    return {'schema': 1, 'scope': 'reviewed undefined nlist symbols only',
            'edition': edition, 'archive_sha256': checked['archive_sha256'],
            'executable_sha256': sha(binary),
            'slices': [inspect_symbols(item, edition) for item in slices(binary)],
            'dyld_bind_coverage': 'NOT_VERIFIED',
            'runtime_dynamic_lookup': 'NOT_VERIFIED',
            'transitive_dependencies': 'NOT_VERIFIED',
            'symbol_availability': 'NOT_VERIFIED',
            'native_compatibility': 'NOT_VERIFIED',
            'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Generate no-replace symbol evidence from a hash-qualified local ZIP."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--edition', choices=sorted(EDITIONS), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        raw = read_local(args.archive)
        if sha(raw) != args.sha256:
            raise BundleError('Archive digest mismatch')
        write_json(args.output, report(raw, args.edition))
    except (OSError, ValueError, KeyError, RuntimeError, struct.error,
            zipfile.BadZipFile, plistlib.InvalidFileException) as error:
        print(f'ERROR: Apple symbols ({type(error).__name__})', file=sys.stderr)
        return 2
    print('PASS: scoped undefined symbols; OS availability not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
