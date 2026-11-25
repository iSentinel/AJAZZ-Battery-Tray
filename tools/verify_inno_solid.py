#!/usr/bin/env python3
"""Independently decode the scoped Inno solid LZMA2 payload and hash files."""

import argparse
import hashlib
import lzma
from pathlib import Path
import sys

from compare_inno_loader import digest
from run_offline_qa import write_json
from verify_inno_inner_engine import recover, reverse_calls
from verify_inno_setup_data import FILES, SETUP_SHA, decode_setup0, locations
from verify_windowsdesktop_provenance import read_local

CHUNK = 65536
MAX_DICT = 64 * 1024 * 1024


def decoder_for(raw: bytes) -> lzma.LZMADecompressor:
    """Validate the documented LZMA2 dictionary property and chunk marker."""
    if len(raw) < 6 or raw[:4] != b'zlb\x1a' or raw[4] >= 40:
        raise ValueError('invalid LZMA2 header')
    prop = raw[4]
    dictionary = (2 | (prop & 1)) << (prop // 2 + 11)
    if dictionary > MAX_DICT:
        raise ValueError('LZMA2 dictionary exceeds budget')
    return lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[
        {'id': lzma.FILTER_LZMA2, 'dict_size': dictionary}])


def file_hashes(raw: bytes, files: tuple) -> list[dict]:
    """Hash bounded decoded file chunks; reverse call optimization for first file."""
    decoder = decoder_for(raw)
    pending = raw[5:]
    results = []
    for index, (name, size, expected) in enumerate(files):
        hashed, offset = hashlib.sha256(), 0
        while offset < size:
            count = min(CHUNK, size - offset)
            if decoder.eof:
                raise ValueError('premature end of solid stream')
            data = decoder.decompress(pending, max_length=count)
            pending = b''
            if len(data) != count:
                raise ValueError('short solid stream block')
            if index == 0:
                data = reverse_calls(data, offset)
            hashed.update(data)
            offset += count
        if hashed.hexdigest() != expected:
            raise ValueError('decoded file hash differs')
        results.append({'name': name, 'bytes': size, 'sha256': expected,
                        'call_transform': index == 0})
    if not decoder.eof and decoder.decompress(b'', max_length=1):
        raise ValueError('unexpected decoded solid stream suffix')
    if not decoder.eof or decoder.unused_data:
        raise ValueError('unexpected solid stream terminal state')
    return results


def verify(raw: bytes) -> dict:
    """Bind exact setup and location table before independent decoding."""
    if digest(raw) != SETUP_SHA:
        raise ValueError('unexpected setup digest')
    _, record = recover(raw)
    _, second, _ = decode_setup0(raw[record['offset0']:record['engine_offset']])
    payload = raw[record['offset1']:record['offset0']]
    locations(second, payload)
    return {'schema': 1, 'setup_sha256': SETUP_SHA, 'compressed_bytes': len(payload) - 4,
            'files': file_hashes(payload, FILES), 'solid_stream': 'MATCH',
            'compiled_script': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Verify bounded local bytes without extracting or executing payload files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--setup', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        write_json(args.output, verify(read_local(args.setup)))
    except (OSError, ValueError, EOFError, lzma.LZMAError):
        print('FAIL: scoped solid stream verification', file=sys.stderr)
        return 2
    print('PASS: independent solid stream and five decoded file hashes')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
