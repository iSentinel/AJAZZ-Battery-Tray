#!/usr/bin/env python3
"""Attribute reviewed Setup.0 wizard images to the pinned compiler resources."""

import argparse
from pathlib import Path
import struct
import sys

from compare_inno_loader import digest
from run_offline_qa import write_json
from verify_dotnet_host_resources import resources
from verify_inno_setup_records import verify as verify_records
from verify_windowsdesktop_provenance import read_local

COMPILER_SHA = '1a6ff68241e7f3b18543bb875283788913abbdd7b9d7403ac094598d044def7a'
WIZARD_NAMES = ('WIZARDIMAGE150', 'WIZARDSMALLIMAGE250')
WIZARD_SIZES = (5767, 10005)


def key(name: str) -> tuple[str, str, str]:
    """Build the guarded PE walker's exact RCDATA resource identity."""
    return ('10', 'name-sha256:' + digest(name.encode('utf-16le')), '1033')


def compare(images: list[dict], leaves: dict) -> list[dict]:
    """Require exact light-mode resource identities, lengths and payload hashes."""
    if len(images) != len(WIZARD_NAMES):
        raise ValueError('unexpected wizard image count')
    rows = []
    for index, (image, name, size) in enumerate(zip(images, WIZARD_NAMES, WIZARD_SIZES)):
        sha = leaves.get(key(name))
        if not sha or image != {'index': index, 'bytes': size, 'sha256': sha}:
            raise ValueError('wizard resource differs')
        rows.append({**image, 'resource': name, 'match': 'MATCH'})
    return rows


def verify(setup: bytes, source: bytes, isl: bytes, ids: bytes, compiler: bytes) -> dict:
    """Pin reviewed compiler bytes, then qualify both actual image payloads."""
    if digest(compiler) != COMPILER_SHA:
        raise ValueError('compiler digest differs')
    result = verify_records(setup, source, isl, ids)
    result['wizard_images'] = compare(result['wizard_images'], resources(compiler))
    result['wizard_image_provenance'] = 'MATCH_PINNED_COMPILER_RCDATA'
    result['compiler_sha256'] = COMPILER_SHA
    result['publisher_trust'] = 'NOT_VERIFIED'
    return result


def main(argv: list[str] | None = None) -> int:
    """Write scoped evidence without executing the compiler or installer."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('setup', 'installer-script', 'default-isl', 'message-ids', 'compiler', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        write_json(args.output, verify(read_local(args.setup), read_local(args.installer_script),
                                      read_local(args.default_isl), read_local(args.message_ids),
                                      read_local(args.compiler)))
    except (OSError, ValueError, KeyError, struct.error):
        print('FAIL: scoped wizard resource provenance', file=sys.stderr)
        return 2
    print('PASS: both wizard image hashes match pinned compiler resources')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
