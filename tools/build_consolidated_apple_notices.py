#!/usr/bin/env python3
"""Create private notice wrappers without modifying original macOS app archives."""

import argparse
from io import BytesIO
import json
from pathlib import Path
import stat
import sys
import zipfile

from run_offline_qa import write_json
from stage_consolidated_signature_inputs import SOURCE
from verify_hardware_acceptance import APPLE_NAMES, apple, members
from verify_windows_notice_transport import digest
from verify_windowsdesktop_provenance import read_local

PINS = {
    'universal': ('abd8e67afe1da82c3b1930592e4cba7696b327d7626131d0637a711254bc4a0f',
                  'b3e27be66e9927ed8ef4cb143c2a24c11f754567cf7157ac17f62530fabf5d6f'),
    'high-sierra': ('a31f73c49887c3a950352eec57439775656b0bf3b7f1e301fe2cc209bbdb5241',
                    'c1221524f473cc731e1f3ca1bc59d953b205d45ea083626bc97ca6ff1666a02a'),
}
LICENSE_SHA = '9b0d8bab09e6219fb516af7dd95357ef2cb6ebca5bddb94a7eb2f04501f6d336'
LIMIT = 32 * 1024 * 1024


def identity(edition: str) -> bytes:
    """Bind the exact original archive and project license, never release admission."""
    outer, inner = PINS[edition]
    row = {'schema': 'consolidated-apple-notice-wrapper-v1', 'edition': edition,
           'source_sha': SOURCE, 'original_ci_archive_sha256': outer,
           'inner_archive_sha256': inner, 'project_license_sha256': LICENSE_SHA,
           'native_signature_trust': 'NOT_VERIFIED',
           'distribution_compliance': 'NOT_VERIFIED', 'release_admission': 'BLOCKED'}
    return (json.dumps(row, indent=2, sort_keys=True) + '\n').encode()


def package_files(original: bytes, license_bytes: bytes, edition: str) -> dict:
    """Verify original CI envelope and inner app archive before adding a notice."""
    outer, inner = PINS[edition]
    if digest(original) != outer or digest(license_bytes) != LICENSE_SHA:
        raise ValueError('original archive or license differs')
    if apple(original, edition)['inner_archive_sha256'] != inner:
        raise ValueError('inner archive differs')
    base = APPLE_NAMES[edition]
    files = members(original, {base + '.zip', base + '.sha256'})
    return {**files, 'LICENSE': license_bytes, 'package.json': identity(edition)}


def encode(files: dict) -> bytes:
    """Create an external deterministic archive without rewriting inner bytes."""
    stream = BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, raw)
    return stream.getvalue()


def verify_wrapper(raw: bytes, expected: dict, edition: str) -> dict:
    """Check all wrapper bytes and preserve the original archive and checksum."""
    if not 0 < len(raw) <= LIMIT:
        raise ValueError('wrapper size differs')
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        infos = archive.infolist()
        if len(infos) != len(expected) or {x.filename for x in infos} != set(expected):
            raise ValueError('unexpected wrapper inventory')
        for info in infos:
            if (info.orig_filename != info.filename or info.flag_bits or info.create_system != 3
                    or info.external_attr != (stat.S_IFREG | 0o644) << 16
                    or info.compress_type != zipfile.ZIP_STORED
                    or info.file_size != len(expected[info.filename])):
                raise ValueError('invalid wrapper member')
        actual = {x.filename: archive.read(x) for x in infos}
    if actual != expected or encode(actual) != raw:
        raise ValueError('wrapper contents or canonical encoding differ')
    return {'schema': 'consolidated-apple-notice-review-v1', 'edition': edition,
            'source_sha': SOURCE, 'wrapper_sha256': digest(raw),
            'inner_archive_sha256': PINS[edition][1], 'project_license_sha256': LICENSE_SHA,
            'original_inner_bytes': 'MATCH', 'native_signature_trust': 'NOT_VERIFIED',
            'distribution_compliance': 'NOT_VERIFIED', 'release_admission': 'BLOCKED'}


def main(argv: list[str] | None = None) -> int:
    """Create a new private wrapper and reread it; never publish or sign."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--edition', choices=PINS, required=True)
    for name in ('original', 'license', 'archive', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if any(p.exists() or p.is_symlink() for p in (args.archive, args.output)):
            raise ValueError('existing output')
        if args.archive.resolve() == args.output.resolve():
            raise ValueError('output paths must differ')
        files = package_files(read_local(args.original), read_local(args.license), args.edition)
        raw = encode(files)
        verify_wrapper(raw, files, args.edition)
        with args.archive.open('xb') as stream:
            stream.write(raw)
        write_json(args.output, verify_wrapper(read_local(args.archive), files, args.edition))
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile):
        print('FAIL: private Apple notice wrapper', file=sys.stderr)
        return 2
    print('PASS: unchanged original app archive; release BLOCKED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
