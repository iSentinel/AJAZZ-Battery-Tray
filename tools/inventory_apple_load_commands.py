#!/usr/bin/env python3
"""Inventory reviewed Mach-O deployment and direct linked library commands."""

import argparse
from pathlib import Path
import struct
import sys
import zipfile
import plistlib

from inventory_apple_archive import EDITIONS, archive_members, architectures, inspect, sha
from inventory_dotnet_bundle import BundleError
from run_offline_qa import write_json
from verify_windowsdesktop_provenance import read_local

DYLIB = {0xc: 'required', 0x80000018: 'weak'}
OTHER_LINK = {0x18, 0x1f, 0x8000001f, 0x20, 0x23, 0x80000023, 0x8000001c, 0x1c,
              0xd, 0x80000020, 0x27}
HIGH = {
    'AppKit.framework/Versions/C/AppKit', 'Foundation.framework/Versions/C/Foundation',
    'CoreBluetooth.framework/Versions/A/CoreBluetooth', 'IOKit.framework/Versions/A/IOKit',
    'CoreFoundation.framework/Versions/A/CoreFoundation',
}
BASE = {'/System/Library/Frameworks/' + x for x in HIGH} | {
    '/usr/lib/libobjc.A.dylib', '/usr/lib/libSystem.B.dylib'}
MODERN = BASE | {'/System/Library/Frameworks/' + x + '.framework/Versions/A/' + x
                 for x in ('UserNotifications', 'ServiceManagement', 'CoreGraphics')}
MODERN |= {'/usr/lib/swift/libswift' + x + '.dylib' for x in (
    'Core', 'CoreFoundation', 'CoreImage', 'Darwin', 'DataDetection', 'Dispatch',
    'IOKit', 'Metal', 'OSLog', 'ObjectiveC', 'QuartzCore', 'UniformTypeIdentifiers',
    'XPC', 'os')}

WEAK = {'/usr/lib/swift/libswift' + x + '.dylib' for x in (
    'CoreImage', 'DataDetection', 'IOKit', 'Metal', 'OSLog', 'QuartzCore',
    'UniformTypeIdentifiers', 'XPC', 'os')}


def version(value: int) -> str:
    """Decode packed Mach-O major/minor/patch fields."""
    return f'{value >> 16}.{(value >> 8) & 255}.{value & 255}'


def slices(raw: bytes) -> list[bytes]:
    """Reuse reviewed FAT bounds before extracting in-memory slices."""
    architectures(raw)
    if raw[:4] != bytes.fromhex('cafebabe'):
        return [raw]
    count, = struct.unpack_from('>I', raw, 4)
    result = []
    for i in range(count):
        _, _, offset, length, _ = struct.unpack_from('>5I', raw, 8 + 20 * i)
        result.append(raw[offset:offset + length])
    return result


def deployment(cmd: int, raw: bytes) -> dict:
    """Decode the two reviewed macOS deployment command formats."""
    if cmd == 0x24 and len(raw) == 16:
        minimum, sdk = struct.unpack_from('<II', raw, 8)
        tools = []
    elif cmd == 0x32 and len(raw) >= 24:
        platform, minimum, sdk, count = struct.unpack_from('<4I', raw, 8)
        if platform != 1 or count > 16 or len(raw) != 24 + count * 8:
            raise BundleError('Unsupported build platform or tools')
        tools = [{'id': tool, 'version': version(v)} for tool, v in
                 struct.iter_unpack('<II', raw[24:])]
    else:
        raise BundleError('Unsupported deployment command')
    if not 0 < minimum <= sdk:
        raise BundleError('Invalid deployment version')
    return {'command': hex(cmd), 'minimum': version(minimum), 'sdk': version(sdk),
            'tools': tools}


def library(cmd: int, raw: bytes) -> dict:
    """Read a bounded absolute install name and recorded dylib versions."""
    if len(raw) < 32:
        raise BundleError('Short dylib command')
    offset, _, current, compatibility = struct.unpack_from('<4I', raw, 8)
    if not 24 <= offset < len(raw) or b'\0' not in raw[offset:]:
        raise BundleError('Invalid dylib name offset')
    name, padding = raw[offset:].split(b'\0', 1)
    if any(padding) or not name:
        raise BundleError('Invalid dylib name padding')
    path = name.decode('ascii')
    if path not in MODERN:
        raise BundleError('Unreviewed dylib install name')
    return {'path': path, 'linkage': DYLIB[cmd], 'current': version(current),
            'compatibility': version(compatibility)}


def inspect_slice(raw: bytes, edition: str) -> dict:
    """Require exact reviewed target and direct link inventory per architecture."""
    arch, = architectures(raw)
    count, = struct.unpack_from('<I', raw, 16)
    pos, targets, libraries = 32, [], []
    for _ in range(count):
        cmd, length = struct.unpack_from('<II', raw, pos)
        data = raw[pos:pos + length]
        if cmd in (0x24, 0x32):
            targets.append(deployment(cmd, data))
        elif cmd in DYLIB:
            libraries.append(library(cmd, data))
        elif cmd in OTHER_LINK or cmd in (0x25, 0x2f, 0x30):
            raise BundleError('Unsupported link or deployment command')
        pos += length
    target, paths = ('13.0.0', MODERN) if edition == 'universal' else ('10.13.0', BASE)
    if (len(targets) != 1 or targets[0]['minimum'] != target
            or targets[0]['command'] != ('0x32' if edition == 'universal' else '0x24')):
        raise BundleError('Unexpected Mach-O minimum')
    if len(libraries) != len(paths) or {x['path'] for x in libraries} != paths:
        raise BundleError('Unexpected direct library inventory')
    weak = {x['path'] for x in libraries if x['linkage'] == 'weak'}
    if weak != (WEAK if edition == 'universal' else set()):
        raise BundleError('Unexpected weak linkage inventory')
    return {'architecture': arch, 'deployment': targets[0],
            'libraries': sorted(libraries, key=lambda x: x['path'])}


def report(raw: bytes, edition: str) -> dict:
    """Bind direct load-command observations to the verified archive and binary."""
    result = inspect(raw, edition)
    app, exe, _, _, _ = EDITIONS[edition]
    binary = archive_members(raw)[app + '/Contents/MacOS/' + exe][0]
    entries = [inspect_slice(item, edition) for item in slices(binary)]
    if len(entries) == 2 and entries[0]['libraries'] != entries[1]['libraries']:
        raise BundleError('Universal slice library metadata differs')
    return {'schema': 1, 'scope': 'direct reviewed Mach-O load commands',
            'edition': edition, 'archive_sha256': result['archive_sha256'],
            'executable_sha256': sha(binary), 'slices': entries,
            'transitive_dependencies': 'NOT_VERIFIED', 'signature': 'NOT_VERIFIED',
            'native_compatibility': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Write scoped no-replace evidence only for a matching archive digest."""
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
        print(f'ERROR: Apple load commands ({type(error).__name__})', file=sys.stderr)
        return 2
    print('PASS: reviewed direct load commands; compatibility and trust not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
