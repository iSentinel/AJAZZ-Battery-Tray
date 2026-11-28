#!/usr/bin/env python3
"""Inventory reviewed macOS app archives without extraction or execution."""

import argparse
import hashlib
import io
from pathlib import Path, PurePosixPath
import plistlib
import stat
import struct
import sys
import zipfile

from inventory_dotnet_bundle import BundleError
from run_offline_qa import write_json
from verify_windowsdesktop_provenance import read_local

MAX_BYTES = 32 * 1024 * 1024
CPU = {0x01000007: 'x86_64', 0x0100000c: 'arm64'}
EDITIONS = {
    'universal': ('AJAZZ Battery Tray.app', 'AJAZZBatteryTray',
                  'com.isentinel.ajazzbatterytray', '13.0', {'x86_64', 'arm64'}),
    'high-sierra': ('AJAZZ Battery Tray High Sierra.app', 'AJAZZBatteryTrayHighSierra',
                    'com.isentinel.ajazzbatterytray.highsierra', '10.13', {'x86_64'}),
}


def sha(raw: bytes) -> str:
    """Return the exact byte digest."""
    return hashlib.sha256(raw).hexdigest()


def archive_members(raw: bytes) -> dict:
    """Read bounded regular entries only; reject aliases, links and traversal."""
    if len(raw) > MAX_BYTES:
        raise BundleError('Archive exceeds budget')
    result, seen = {}, set()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        if len(infos) > 64 or sum(x.file_size for x in infos) > MAX_BYTES:
            raise BundleError('Archive member budget exceeded')
        for info in infos:
            name = info.filename.rstrip('/')
            path = PurePosixPath(name)
            if (not name or name != path.as_posix() or path.is_absolute()
                    or '\\' in name or ':' in name or '..' in path.parts
                    or name.casefold() in seen or info.flag_bits & 1):
                raise BundleError('Unsupported archive path')
            seen.add(name.casefold())
            mode = info.external_attr >> 16
            if info.is_dir():
                if stat.S_IFMT(mode) not in (0, stat.S_IFDIR) or info.file_size:
                    raise BundleError('Invalid directory entry')
                continue
            if stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                raise BundleError('Unsupported archive entry type')
            result[name] = (archive.read(info), mode & 0o777)
    return result


def thin(raw: bytes) -> str:
    """Validate the reviewed little-endian 64-bit executable header."""
    if len(raw) < 32:
        raise BundleError('Short Mach-O header')
    magic, cpu, _, kind, count, size, _, _ = struct.unpack_from('<8I', raw)
    if (magic != 0xfeedfacf or cpu not in CPU or kind != 2
            or count > 1024 or not 0 < size <= len(raw) - 32):
        raise BundleError('Unsupported Mach-O header')
    pos = 32
    for _ in range(count):
        if pos + 8 > 32 + size:
            raise BundleError('Truncated load command')
        _, length = struct.unpack_from('<II', raw, pos)
        if length < 8 or length % 8 or pos + length > 32 + size:
            raise BundleError('Invalid load command size')
        pos += length
    if pos != 32 + size:
        raise BundleError('Load command size mismatch')
    return CPU[cpu]


def architectures(raw: bytes) -> set:
    """Validate thin or reviewed 32-bit FAT table with nonoverlapping slices."""
    if raw[:4] != bytes.fromhex('cafebabe'):
        return {thin(raw)}
    if len(raw) < 8:
        raise BundleError('Truncated FAT header')
    count, = struct.unpack_from('>I', raw, 4)
    if count != 2 or len(raw) < 8 + count * 20:
        raise BundleError('Unsupported FAT table')
    result, ranges = set(), []
    for i in range(count):
        cpu, _, offset, size, alignment = struct.unpack_from('>5I', raw, 8 + i * 20)
        if (cpu not in CPU or alignment > 24 or offset % (1 << alignment)
                or offset < 8 + count * 20 or not 32 <= size <= len(raw) - offset
                or any(offset < end and start < offset + size for start, end in ranges)):
            raise BundleError('Invalid FAT slice')
        actual = thin(raw[offset:offset + size])
        if actual != CPU[cpu] or actual in result:
            raise BundleError('FAT CPU mismatch')
        result.add(actual)
        ranges.append((offset, offset + size))
    return result


def inspect(raw: bytes, edition: str) -> dict:
    """Verify exact scoped file layout, plist identity and executable slices."""
    app, exe, identifier, minimum, cpus = EDITIONS[edition]
    root = app + '/Contents/'
    expected = {'Info.plist', '_CodeSignature/CodeResources', 'MacOS/' + exe}
    expected.update('Resources/AppIcon' + suffix + '.icns'
                    for suffix in ('', '-black', '-blue', '-white'))
    members = archive_members(raw)
    if set(members) != {root + name for name in expected}:
        raise BundleError('Unexpected app file inventory')
    plist = plistlib.loads(members[root + 'Info.plist'][0])
    if (plist.get('CFBundleIdentifier') != identifier or plist.get('CFBundleExecutable') != exe
            or plist.get('LSMinimumSystemVersion') != minimum):
        raise BundleError('Unexpected bundle identity or plist minimum')
    binary, mode = members[root + 'MacOS/' + exe]
    arch = architectures(binary)
    if arch != cpus or not mode & 0o111:
        raise BundleError('Unexpected executable architecture or mode')
    if any(not value[0] for value in members.values()):
        raise BundleError('Empty app member')
    return {'schema': 1, 'scope': 'reviewed macOS archive layout', 'edition': edition,
            'archive_sha256': sha(raw), 'bundle_id': identifier,
            'bundle_version': plist.get('CFBundleVersion'), 'plist_minimum': minimum,
            'architectures': sorted(arch), 'files': [
                {'path': path, 'sha256': sha(data), 'size': len(data), 'mode': mode}
                for path, (data, mode) in sorted(members.items())],
            'signature': 'NOT_VERIFIED', 'native_compatibility': 'NOT_VERIFIED',
            'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Write a new report only after matching the supplied archive digest."""
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
        write_json(args.output, inspect(raw, args.edition))
    except (OSError, ValueError, KeyError, RuntimeError, struct.error,
            zipfile.BadZipFile, plistlib.InvalidFileException) as error:
        print(f'ERROR: Apple archive ({type(error).__name__})', file=sys.stderr)
        return 2
    print('PASS: scoped Apple archive inventory; trust and compatibility not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
