#!/usr/bin/env python3
"""Verify the exact scoped beta.61 Setup.0 framing and file location inventory."""

import argparse
import lzma
from pathlib import Path
import struct
import sys
import zlib

from compare_inno_loader import digest
from run_offline_qa import write_json
from verify_inno_inner_engine import chunk_stream, recover
from verify_windowsdesktop_provenance import read_local

SETUP_SHA = 'b37f077969d01bfbe1b3b1411a53b00ba1baf28b89f33e6fcb0e980b44d7b929'
SETUP_ID = b'Inno Setup Setup Data (6.7.0)'.ljust(64, b'\0')
MAX_BLOCK = 8 * 1024 * 1024
COUNTS = (1, 12, 0, 0, 0, 1, 0, 0, 6, 5, 2, 0, 0, 0, 0, 1, 0)
FILES = (
    ('AJAZZBatteryTray.exe', 149610595, '429613466f2e44d8f65d80d4e77c3532d59b6c72e4bc9f613c7faa86ff9dd955'),
    ('AppIcon.ico', 156214, 'be6d9849acd8c768725d73a4b1a70a4aba9284770dff72bbb5d355694bef3b16'),
    ('AppIcon-white.ico', 150976, '6e2c46c8d462ce4a05a5e8dcc6d6885b3ab5dfcd1970df91439ed3ecc654668e'),
    ('AppIcon-black.ico', 129068, '7610dab806674ec1265d016bf071e6fba3ceadeb25e06a94e3cb7dec387721d2'),
    ('AppIcon-blue.ico', 152003, 'cdefedcb227d3502324e5a6b41d4f26c1c28d75a72aacdd50053f694ee8361ec'),
)
LOCATION = struct.Struct('<iiqqqq32sQIIB')


def block(raw: bytes, pos: int) -> tuple[bytes, int, dict]:
    """Decode one exact bounded LZMA1 frame and validate every chunk CRC."""
    if not 0 <= pos <= len(raw) - 13:
        raise ValueError('missing block header')
    stored, flag = struct.unpack_from('<qB', raw, pos + 4)
    end = pos + 13 + stored
    if flag != 1 or not 5 < stored <= MAX_BLOCK or end > len(raw):
        raise ValueError('unsupported compressed extent')
    packed, chunks = chunk_stream(raw[pos:end], 0)
    if len(packed) < 6:
        raise ValueError('missing LZMA properties')
    prop = packed[0]
    lc, lp, pb = prop % 9, prop // 9 % 5, prop // 45
    dictionary = int.from_bytes(packed[1:5], 'little')
    if pb > 4 or lc + lp > 4 or not 4096 <= dictionary <= 64 * 1024 * 1024:
        raise ValueError('unsupported LZMA properties')
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[{
        'id': lzma.FILTER_LZMA1, 'dict_size': dictionary, 'lc': lc, 'lp': lp, 'pb': pb}])
    data = decoder.decompress(packed[5:], max_length=MAX_BLOCK + 1)
    if len(data) > MAX_BLOCK or not decoder.eof or decoder.unused_data:
        raise ValueError('invalid LZMA terminal state')
    return data, end, {'stored_bytes': stored, 'decoded_bytes': len(data),
                       'chunks': chunks, 'decoded_sha256': digest(data)}


def decode_setup0(raw: bytes) -> tuple[bytes, bytes, dict]:
    """Require exact unencrypted Setup.0 header and two contiguous blocks."""
    if not 117 < len(raw) <= MAX_BLOCK or raw[:64] != SETUP_ID:
        raise ValueError('unexpected setup data header')
    encryption = raw[68:117]
    if encryption[0] != 0 or zlib.crc32(encryption) != struct.unpack_from('<I', raw, 64)[0]:
        raise ValueError('encrypted or corrupted setup data header')
    first, end, a = block(raw, 117)
    second, end, b = block(raw, end)
    if end != len(raw):
        raise ValueError('unexpected setup data trailing bytes')
    return first, second, {'encryption': 'NONE', 'encryption_header_crc': 'PASS',
                           'blocks': [a, b]}


def header_script(raw: bytes) -> dict:
    """Read the scoped 39 Unicode and four ANSI length-prefixed fields."""
    pos, fields = 0, []
    for index in range(43):
        if pos > len(raw) - 4:
            raise ValueError('missing setup header string length')
        length, = struct.unpack_from('<I', raw, pos)
        pos += 4
        if length > MAX_BLOCK or length > len(raw) - pos or (index < 39 and length % 2):
            raise ValueError('invalid setup header string extent')
        field = raw[pos:pos + length]
        fields.append(field.decode('utf-16le') if index < 39 else field)
        pos += length
    if fields[0] != 'AJAZZ Battery Tray' or fields[9] != '0.3.0-beta.61':
        raise ValueError('unexpected setup identity')
    if pos > len(raw) - 68 or struct.unpack_from('<17i', raw, pos) != COUNTS:
        raise ValueError('unexpected setup entry counts')
    script = fields[42]
    if not script.startswith(b'IFPS') or not 28 <= len(script) <= 1024 * 1024:
        raise ValueError('unsupported script header')
    return {'string_fields': 43, 'entry_counts': list(COUNTS),
            'script_bytes': len(script), 'script_sha256': digest(script),
            'script_format': 'IFPS', 'script_semantics': 'NOT_VERIFIED',
            'remaining_header_entries': 'NOT_VERIFIED'}


def locations(raw: bytes, payload: bytes, files: tuple = FILES) -> list[dict]:
    """Match five records to retained app and source icon hashes and solid extent."""
    if len(raw) != LOCATION.size * len(files) or payload[:4] != b'zlb\x1a':
        raise ValueError('unexpected location table or payload marker')
    rows, offset = [], 0
    for i, (name, size, sha) in enumerate(files):
        first, last, start, sub, original, compressed, hashed, _, _, _, flags = LOCATION.unpack_from(
            raw, i * LOCATION.size)
        if ((first, last, start, sub, original, compressed, hashed.hex(), flags)
                != (0, 0, 0, offset, size, len(payload) - 4, sha, 20 if i == 0 else 16)):
            raise ValueError('unexpected file location entry')
        rows.append({'name': name, 'size': size, 'sha256': sha,
                     'solid_offset': sub, 'flags': flags})
        offset += size
    return rows


def verify(raw: bytes) -> dict:
    """Pin the exercised setup and validate framed data without script execution."""
    if digest(raw) != SETUP_SHA:
        raise ValueError('unexpected exercised setup digest')
    _, record = recover(raw)
    first, second, framing = decode_setup0(raw[record['offset0']:record['engine_offset']])
    return {'schema': 1, 'setup_sha256': SETUP_SHA, 'framing': framing,
            'header': header_script(first),
            'locations': locations(second, raw[record['offset1']:record['offset0']]),
            'location_hashes': 'MATCH_RETAINED_INVENTORY',
            'payload_decompression': 'NOT_PERFORMED_BY_THIS_TOOL',
            'compiled_script': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Write scoped evidence for the exact retained artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--setup', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        write_json(args.output, verify(read_local(args.setup)))
    except (OSError, ValueError, KeyError, struct.error, lzma.LZMAError):
        print('FAIL: scoped Setup.0 framing', file=sys.stderr)
        return 2
    print('PASS: Setup.0 framing and location inventory; script semantics not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
