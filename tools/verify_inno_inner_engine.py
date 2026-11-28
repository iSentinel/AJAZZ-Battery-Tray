#!/usr/bin/env python3
"""Recover the scoped Inno 6.7.1 inner PE from bounded verified local bytes."""

import argparse
import hashlib
import lzma
from pathlib import Path
import struct
import sys
import zlib

from compare_inno_loader import compare, layout, TEMPLATE_SHA
from run_offline_qa import write_json
from verify_dotnet_host_resources import ResourceTree, resource_area, unpack
from verify_windowsdesktop_provenance import read_local

ENGINE_SHA = '34105d458e138b5af63a1bea82b6519856f309904e1e2b0ed7cebed52c7a374b'
TABLE_ID = b'rDlPtS\xcd\xe6\xd7\x7b\x0b\x2a'
MAX_ENGINE = 16 * 1024 * 1024
CHUNK = 4096


class OffsetResource(ResourceTree):
    """Capture only the expected numeric RCDATA resource after tree validation."""

    def __init__(self, raw: bytes, rva: int) -> None:
        """Initialize the bounded resource walker."""
        super().__init__(raw, rva)
        self.table = None

    def leaf(self, pos: int, path: tuple) -> None:
        """Require a unique English-language 64-byte offset record."""
        super().leaf(pos, path)
        if path[:2] == ('10', '11111'):
            address, length, _, _ = unpack(self.raw, pos, '<IIII')
            if self.table is not None or path[2] != '1033' or length != 64:
                raise ValueError('unexpected offset resource')
            start = address - self.rva
            self.table = self.raw[start:start + length]


def offset_record(raw: bytes, total: int, loader_end: int) -> dict:
    """Validate the observed v2 record with exact single-file bounds and CRC."""
    if len(raw) != 64 or zlib.crc32(raw[:-4]) != struct.unpack_from('<I', raw, 60)[0]:
        raise ValueError('offset table CRC differs')
    ident, version, size, exe, decoded, crc, off0, off1, pad, _ = struct.unpack(
        '<12sIqqIIqqII', raw)
    if (ident != TABLE_ID or version != 2 or size != total or pad
            or not 0 < loader_end == off1 < off0 < exe < total
            or not 0 < decoded <= MAX_ENGINE or total - exe < 18):
        raise ValueError('unsupported offset record')
    return {'engine_offset': exe, 'engine_bytes': decoded, 'engine_crc32': crc,
            'offset0': off0, 'offset1': off1}


def chunk_stream(raw: bytes, offset: int) -> tuple[bytes, int]:
    """Require exact compressed block extent and CRC of every framed chunk."""
    header = raw[offset + 4:offset + 13]
    if len(header) != 9 or zlib.crc32(header) != unpack(raw, offset, '<I')[0]:
        raise ValueError('compressed header CRC differs')
    stored, flag = struct.unpack('<qB', header)
    if flag != 1 or not 5 < stored <= MAX_ENGINE or offset + 13 + stored != len(raw):
        raise ValueError('unsupported compressed block')
    pos = offset + 13
    chunks = []
    while pos < len(raw):
        crc, = unpack(raw, pos, '<I')
        pos += 4
        chunk = raw[pos:pos + CHUNK]
        if not chunk or zlib.crc32(chunk) != crc:
            raise ValueError('compressed chunk CRC differs')
        chunks.append(chunk)
        pos += len(chunk)
    return b''.join(chunks), len(chunks)


def decompress(raw: bytes, size: int) -> bytes:
    """Bound LZMA1 dictionary/output and require the exact terminal state."""
    if len(raw) < 6 or not 0 < size <= MAX_ENGINE:
        raise ValueError('invalid compressed engine extent')
    prop = raw[0]
    lc, lp, pb = prop % 9, (prop // 9) % 5, prop // 45
    dictionary = int.from_bytes(raw[1:5], 'little')
    if pb > 4 or lc + lp > 4 or not 4096 <= dictionary <= 64 * 1024 * 1024:
        raise ValueError('invalid LZMA properties')
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[{
        'id': lzma.FILTER_LZMA1, 'dict_size': dictionary,
        'lc': lc, 'lp': lp, 'pb': pb}])
    data = decoder.decompress(raw[5:], max_length=size + 1)
    if len(data) != size or not decoder.eof or decoder.unused_data:
        raise ValueError('compressed engine terminal state differs')
    return data


def reverse_calls(raw: bytes, offset: int = 0) -> bytes:
    """Reverse documented version-3 relative address transform, including file block offset."""
    data = bytearray(raw)
    i = 0
    while i < len(data) - 4:
        if data[i] not in (0xe8, 0xe9):
            i += 1
            continue
        i += 1
        if data[i + 3] in (0, 255):
            rel = (int.from_bytes(data[i:i + 3], 'little') - offset - i - 4) & 0xffffff
            if rel & 0x800000:
                data[i + 3] ^= 255
            data[i:i + 3] = rel.to_bytes(3, 'little')
        i += 4
    return bytes(data)


def recover(raw: bytes) -> tuple[bytes, dict]:
    """Read only the unique offset resource and recover CRC-verified inner PE."""
    loader = layout(raw)
    area, rva = resource_area(raw)
    tree = OffsetResource(area, rva)
    tree.visit(0)
    if tree.table is None:
        raise ValueError('missing offset resource')
    record = offset_record(tree.table, len(raw), loader['end'])
    packed, count = chunk_stream(raw, record['engine_offset'])
    engine = reverse_calls(decompress(packed, record['engine_bytes']))
    if zlib.crc32(engine) != record['engine_crc32']:
        raise ValueError('recovered engine CRC differs')
    return engine, {**record, 'offset_table_sha256': hashlib.sha256(tree.table).hexdigest(),
                    'compressed_chunks': count, 'engine_sha256': hashlib.sha256(engine).hexdigest()}


def main(argv: list[str] | None = None) -> int:
    """Verify exact local setup and both official template digests, no execution."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('setup', 'loader-template', 'engine-template', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--setup-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        raw, loader, template = (read_local(p) for p in
                                 (args.setup, args.loader_template, args.engine_template))
        if [hashlib.sha256(x).hexdigest() for x in (raw, loader, template)] != [
                args.setup_sha256, TEMPLATE_SHA, ENGINE_SHA]:
            raise ValueError('input digest differs')
        compare(loader, raw)
        engine, record = recover(raw)
        match = compare(template, engine, overlay_expected=False)
        write_json(args.output, {'schema': 1, 'setup_sha256': args.setup_sha256,
                   'engine': record, 'sections': match['sections'],
                   'engine_template_sha256': ENGINE_SHA,
                   'inner_non_resource_bytes': 'MATCH',
                   'resources': 'NOT_QUALIFIED', 'compiled_script': 'NOT_VERIFIED',
                   'uninstaller': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'})
    except (OSError, ValueError, TypeError, KeyError, struct.error, lzma.LZMAError):
        print('FAIL: scoped Inno inner engine verification', file=sys.stderr)
        return 2
    print('PASS: recovered engine CRC and non-resource bytes; uninstaller not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
