#!/usr/bin/env python3
"""Attribute the exact 6.7.4 product probe and exercised uninstaller."""

import argparse
import lzma
from pathlib import Path
import re
import struct
import sys
import zlib

from compare_inno_loader import compare, digest
from run_offline_qa import write_json
from validate_scoped_sbom_schema import document
from verify_inno_inner_engine import recover
from verify_inno_messages import verify_messages
from verify_inno_uninstaller import attribute
from verify_windowsdesktop_provenance import read_local

LOADER = '998c58046b0808e75a030859962e1fe1ea600e8a5cf4646b09aadce77342c1a9'
ENGINE = '0c94d43e2c0f4d8371a2e1813b5446f3bc85ece3211dc4a6676159b534bbc483'
HEX = re.compile(r'[0-9a-f]{64}')


def identity(setup: bytes, exe: bytes, bound: dict, exercised: dict) -> None:
    """Require the exact lifecycle-bound setup and executed uninstaller."""
    if (bound.get('schema') != 'inno-674-product-binding-v1'
            or bound.get('engine_version') != '6.7.4'
            or bound.get('setup_sha256') != digest(setup)
            or bound.get('release_admission') != 'NOT_VERIFIED'
            or not re.fullmatch(r'[0-9a-f]{40}', bound.get('source_sha', ''))
            or not HEX.fullmatch(bound.get('app_sha256', ''))):
        raise ValueError('product binding differs')
    expected = {'schema': 'inno-674-exercised-uninstaller-v1',
                'source_sha': bound['source_sha'], 'setup_sha256': digest(setup),
                'app_sha256': bound['app_sha256'], 'uninstaller_sha256': digest(exe),
                'uninstall_result': 'REMOVED', 'release_admission': 'NOT_VERIFIED'}
    if exercised != expected:
        raise ValueError('exercised uninstaller binding differs')


def inspect_binary(setup: bytes, exe: bytes, loader: bytes, engine: bytes) -> dict:
    """Check pinned templates, framed engine, PE prefix and message structure."""
    if digest(loader) != LOADER or digest(engine) != ENGINE:
        raise ValueError('6.7.4 template identity differs')
    outer = compare(loader, setup)
    recovered, frame = recover(setup)
    inner = compare(engine, recovered, overlay_expected=False)
    uninstall = attribute(recovered, exe)
    messages = verify_messages(exe[uninstall['message_offset']:-12])
    return {'loader': outer, 'engine_frame': frame, 'engine_sections': inner['sections'],
            'uninstaller': uninstall, 'messages': messages,
            'loader_non_resource': 'MATCH', 'engine_non_resource': 'MATCH',
            'resource_provenance': 'NOT_VERIFIED', 'compiled_script': 'NOT_VERIFIED',
            'solid_payload_attribution': 'NOT_VERIFIED'}


def qualify(setup: bytes, exe: bytes, loader: bytes, engine: bytes,
            binding_raw: bytes, exercised_raw: bytes) -> dict:
    """Bind the scoped attribution to exact native product observations."""
    bound = document(binding_raw)
    identity(setup, exe, bound, document(exercised_raw))
    return {'schema': 'inno-674-product-binary-v1', 'source_sha': bound['source_sha'],
            'setup_sha256': digest(setup), 'app_sha256': bound['app_sha256'],
            'binding_sha256': digest(binding_raw), 'exercised_sha256': digest(exercised_raw),
            **inspect_binary(setup, exe, loader, engine),
            'interactive_acceptance': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Verify scoped local bytes without executing or extracting binaries."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('setup', 'uninstaller', 'loader', 'engine', 'binding', 'exercised', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = qualify(*(read_local(getattr(args, name)) for name in
                           ('setup', 'uninstaller', 'loader', 'engine', 'binding', 'exercised')))
        write_json(args.output, result)
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, struct.error,
            zlib.error, lzma.LZMAError, RecursionError):
        print('FAIL: scoped Inno 6.7.4 product binary attribution', file=sys.stderr)
        return 2
    print('PASS: scoped loader/engine/uninstaller attribution; release not admitted')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
