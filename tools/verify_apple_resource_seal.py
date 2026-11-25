#!/usr/bin/env python3
"""Verify reviewed ad-hoc Apple resource seals and CodeDirectory hashes."""

import argparse
import hashlib
from pathlib import Path
import plistlib
import struct
import sys
import zipfile

from inventory_apple_archive import EDITIONS, archive_members, inspect, sha
from inventory_apple_load_commands import slices
from inventory_dotnet_bundle import BundleError
from run_offline_qa import write_json
from verify_windowsdesktop_provenance import read_local

PAGE = 4096
HASH = 32
REQ = bytes.fromhex('fade0c010000000c00000000')
CMS = bytes.fromhex('fade0b0100000008')


def resource_seal(seal: bytes, resources: dict) -> int:
    """Verify exact observed resource entries with both hash algorithms."""
    data = plistlib.loads(seal)
    if not isinstance(data, dict) or set(data) != {'files', 'files2', 'rules', 'rules2'}:
        raise BundleError('Unexpected resource seal schema')
    if not resources or set(data['files']) != set(resources) or set(data['files2']) != set(resources):
        raise BundleError('Resource seal coverage mismatch')
    for name, raw in resources.items():
        if data['files'][name] != hashlib.sha1(raw).digest():
            raise BundleError('Resource SHA-1 mismatch')
        if data['files2'][name] != {'hash2': hashlib.sha256(raw).digest()}:
            raise BundleError('Resource SHA-256 mismatch')
    return len(resources)


def signature(raw: bytes) -> tuple[int, bytes]:
    """Locate the single trailing LC_CODE_SIGNATURE region in a validated slice."""
    count, = struct.unpack_from('<I', raw, 16)
    pos, found = 32, []
    for _ in range(count):
        cmd, size = struct.unpack_from('<II', raw, pos)
        if cmd == 0x1d:
            if size != 16:
                raise BundleError('Invalid code signature command')
            offset, length = struct.unpack_from('<II', raw, pos + 8)
            if offset < 32 or length < 12 or offset + length != len(raw):
                raise BundleError('Unsupported signature extent')
            found.append((offset, raw[offset:]))
        pos += size
    if len(found) != 1:
        raise BundleError('Expected one code signature command')
    return found[0]


def superblob(raw: bytes) -> dict:
    """Check the exact observed three-slot superblob and zero trailing padding."""
    magic, length, count = struct.unpack_from('>3I', raw)
    if magic != 0xfade0cc0 or count != 3 or not 36 <= length <= len(raw) or any(raw[length:]):
        raise BundleError('Unsupported signature superblob')
    blobs, extents = {}, []
    for index in range(count):
        slot, offset = struct.unpack_from('>II', raw, 12 + index * 8)
        if slot in blobs or not 36 <= offset <= length - 8:
            raise BundleError('Invalid signature slot')
        _, size = struct.unpack_from('>II', raw, offset)
        if not 8 <= size <= length - offset:
            raise BundleError('Invalid signature blob length')
        blobs[slot] = raw[offset:offset + size]
        extents.append((offset, offset + size))
    pos = 36
    for start, end in sorted(extents):
        if start != pos:
            raise BundleError('Overlapping or gapped signature blobs')
        pos = end
    if pos != length or set(blobs) != {0, 2, 0x10000} or blobs[2] != REQ or blobs[0x10000] != CMS:
        raise BundleError('Unsupported signature type or requirements')
    return blobs


def directory(cd: bytes, limit: int, identifier: str) -> tuple[int, int]:
    """Require reviewed SHA-256 CodeDirectory v20400 ad-hoc format."""
    if len(cd) < 88:
        raise BundleError('Short CodeDirectory')
    magic, length, version, flags, offset, ident, special, pages, code = struct.unpack_from('>9I', cd)
    if (magic != 0xfade0c02 or length != len(cd) or version != 0x20400 or flags != 2
            or code != limit or special != 3 or pages != (limit + PAGE - 1) // PAGE
            or cd[36:40] != bytes((HASH, 2, 0, 12)) or ident != 88
            or not ident < offset - special * HASH or offset + pages * HASH != length
            or any(cd[40:64])):
        raise BundleError('Unsupported CodeDirectory header')
    name = identifier.encode('ascii') + b'\0'
    if cd[ident:offset - special * HASH] != name:
        raise BundleError('CodeDirectory identifier mismatch')
    return offset, pages


def verify_slice(raw: bytes, identifier: str, plist: bytes, seal: bytes) -> dict:
    """Check every covered code page and all three observed special slots."""
    limit, region = signature(raw)
    blobs = superblob(region)
    cd = blobs[0]
    offset, pages = directory(cd, limit, identifier)
    for index, content in enumerate((plist, blobs[2], seal), 1):
        if hashlib.sha256(content).digest() != cd[offset - index * HASH:offset - (index - 1) * HASH]:
            raise BundleError('Special slot hash mismatch')
    for index in range(pages):
        start = index * PAGE
        expected = hashlib.sha256(raw[start:min(start + PAGE, limit)]).digest()
        if expected != cd[offset + index * HASH:offset + (index + 1) * HASH]:
            raise BundleError('Code page hash mismatch')
    return {'code_pages': pages, 'code_bytes': limit, 'special_slots': 3,
            'code_directory_sha256': sha(cd), 'signature_type': 'AD_HOC_EMPTY_CMS',
            'hash_algorithm': 'SHA-256'}


def report(raw: bytes, edition: str) -> dict:
    """Bind scoped integrity results to exact archive and executable hashes."""
    observed = inspect(raw, edition)
    app, exe, identifier, _, _ = EDITIONS[edition]
    prefix = app + '/Contents/'
    members = {p[len(prefix):]: b for p, (b, _) in archive_members(raw).items()}
    seal = members['_CodeSignature/CodeResources']
    resources = {p: b for p, b in members.items() if p.startswith('Resources/')}
    count = resource_seal(seal, resources)
    binary = members['MacOS/' + exe]
    entries = [verify_slice(item, identifier, members['Info.plist'], seal) for item in slices(binary)]
    return {'schema': 1, 'scope': 'reviewed ad-hoc resource and code hashes',
            'edition': edition, 'archive_sha256': observed['archive_sha256'],
            'executable_sha256': sha(binary), 'seal_sha256': sha(seal),
            'resource_files': count, 'resource_hashes': count * 2, 'slices': entries,
            'rules_semantics': 'NOT_VERIFIED', 'signer_trust': 'NOT_VERIFIED',
            'notarization': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Write no-replace scoped evidence after checking expected archive hash."""
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
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, struct.error,
            zipfile.BadZipFile, plistlib.InvalidFileException) as error:
        print(f'ERROR: Apple resource seal ({type(error).__name__})', file=sys.stderr)
        return 2
    print('PASS: scoped ad-hoc hash integrity; signer trust not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
