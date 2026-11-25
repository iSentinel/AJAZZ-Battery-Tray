#!/usr/bin/env python3
"""Verify the scoped 6.7.4 product solid stream against exact build inputs."""

import argparse
import lzma
from pathlib import Path
import struct
import sys
import zlib

from compare_inno_loader import digest
from run_offline_qa import write_json
from validate_scoped_sbom_schema import document
from verify_inno_ifps import Reader, check_script
from verify_inno_inner_engine import recover
from verify_inno_setup_data import COUNTS, FILES, LOCATION, decode_setup0
from verify_inno_solid import file_hashes
from verify_windows_notice_transport import tree_files, verify_files
from verify_windowsdesktop_provenance import read_local

NOTICES = (
    'AJAZZ/LICENSE', 'DotNet/core/LICENSE.TXT',
    'DotNet/core/THIRD-PARTY-NOTICES.TXT', 'DotNet/desktop/LICENSE',
    'DotNet/host/LICENSE.TXT', 'DotNet/host/THIRD-PARTY-NOTICES.TXT',
    'Inno/Inno-Setup-LICENSE.txt', 'Inno/LZMA-SDK-7zC.txt',
    'Inno/Pascal-Script-LICENSE.txt', 'manifest.json',
)


def inventory(app: bytes, icons: Path, notices: Path) -> tuple:
    """Pin the app input, four source icons and exact staged notice tree."""
    rows = [(FILES[0][0], len(app), digest(app))]
    if not app:
        raise ValueError('empty application')
    for name, size, sha in FILES[1:]:
        raw = read_local(icons / name)
        if (len(raw), digest(raw)) != (size, sha):
            raise ValueError('icon input differs')
        rows.append(('Icons/' + name, size, sha))
    data = tree_files(notices)
    verify_files(data)
    rows.extend(('Notices/' + name, len(data[name]), digest(data[name]))
                for name in NOTICES)
    return tuple(rows)


def locations(raw: bytes, payload: bytes, files: tuple) -> None:
    """Require every location, contiguous offsets and expected transform flags."""
    if len(raw) != LOCATION.size * len(files) or payload[:4] != b'zlb\x1a':
        raise ValueError('unexpected location table')
    offset = 0
    for i, (_, size, sha) in enumerate(files):
        first, last, start, sub, original, compressed, hashed, _, _, _, flags = (
            LOCATION.unpack_from(raw, i * LOCATION.size))
        if ((first, last, start, sub, original, compressed, hashed.hex(), flags)
                != (0, 0, 0, offset, size, len(payload) - 4, sha, 20 if i == 0 else 16)):
            raise ValueError('unexpected location record')
        offset += size


def script_header(raw: bytes) -> dict:
    """Check identity, counts and scoped IFPS launch predicate."""
    reader = Reader(raw)
    fields = [reader.string().decode('utf-16le') for _ in range(39)]
    if fields[0] != 'AJAZZ Battery Tray' or fields[9] != '0.3.0-beta.61':
        raise ValueError('unexpected setup identity')
    if [reader.string() for _ in range(3)] != [b''] * 3:
        raise ValueError('unexpected license/info fields')
    script = check_script(reader.string())
    counts = list(COUNTS)
    counts[8], counts[9] = 16, 15
    if struct.unpack('<17i', reader.take(68)) != tuple(counts):
        raise ValueError('unexpected setup entry counts')
    return script


def verify(setup: bytes, app: bytes, files: tuple, previous: bytes, bound: bytes) -> dict:
    """Bind the prior resource and product evidence; decode the exact solid stream."""
    resource, product = document(previous), document(bound)
    if (resource.get('schema') != 'inno-674-product-resources-v1'
            or product.get('schema') != 'inno-674-product-binding-v1'
            or resource.get('setup_sha256') != digest(setup)
            or product.get('setup_sha256') != digest(setup)
            or product.get('app_sha256') != digest(app)
            or resource.get('source_sha') != product.get('source_sha')
            or resource.get('resource_payloads') != 'MATCH_SCOPED'
            or product.get('engine_version') != '6.7.4'
            or len(files) != 15 or files[0][1:] != (len(app), digest(app))):
        raise ValueError('candidate identity differs')
    _, offsets = recover(setup)
    if offsets['engine_sha256'] != resource['engine_sha256']:
        raise ValueError('engine differs')
    first, second, framing = decode_setup0(setup[offsets['offset0']:offsets['engine_offset']])
    payload = setup[offsets['offset1']:offsets['offset0']]
    locations(second, payload, files)
    script = script_header(first)
    return {'schema': 'inno-674-solid-payload-v1', 'setup_sha256': digest(setup),
            'app_sha256': digest(app), 'source_sha': product['source_sha'],
            'resource_evidence_sha256': digest(previous), 'product_binding_sha256': digest(bound),
            'framing': framing, 'files': file_hashes(payload, files),
            'solid_stream': 'MATCH', 'script': script,
            'file_destination_records': 'NOT_VERIFIED',
            'remaining_setup_records': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Emit local scoped evidence without executing or extracting payloads."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('setup', 'app', 'icons', 'notices', 'previous', 'binding', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        app = read_local(args.app)
        result = verify(read_local(args.setup), app, inventory(app, args.icons, args.notices),
                        read_local(args.previous), read_local(args.binding))
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, EOFError,
            struct.error, zlib.error, lzma.LZMAError):
        print('FAIL: scoped 6.7.4 solid payload', file=sys.stderr)
        return 2
    print('PASS: exact 15 solid payload files and scoped IFPS; release not admitted')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
