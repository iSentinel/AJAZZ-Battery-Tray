#!/usr/bin/env python3
"""Qualify scoped 6.7.4 product resources and English uninstaller messages."""

import argparse
import lzma
from pathlib import Path
import struct
import sys
import zlib

from compare_inno_loader import compare, digest
from run_offline_qa import write_json
from validate_scoped_sbom_schema import document
from verify_dotnet_host_resources import resources
from verify_inno674_product_binary import ENGINE, LOADER
from verify_inno_inner_engine import recover
from verify_inno_messages import verify_messages
from verify_inno_metadata import compare_metadata
from verify_inno_resources import ICON_SHA, compare_resources, icon_resources
from verify_inno_serialization import verify_serialization
from verify_inno_uninstaller import attribute
from verify_windowsdesktop_provenance import read_local

BODY = '31b34a6d0f6d21f25e92c7ef6fcb03067654b5dd16df3416374f2d12ed4b3dbd'
OPTIONS = '20818b0695dca2c6bd625d633b29e98f012f3db4e0d16c2c05f447bacb563e0a'


def check_messages(raw: bytes) -> dict:
    """Require exact unchanged English source serialization and language options."""
    result = verify_messages(raw)
    if (result['body_sha256'], result['language_options_sha256']) != (BODY, OPTIONS):
        raise ValueError('English message or language option bytes differ')
    return {**result, 'message_semantics': 'MATCH_PINNED_ENGLISH_TEXT',
            'language_options_semantics': 'MATCH_REVIEWED_DEFAULTS'}


def check_resources(template: bytes, actual: bytes, icons: dict, kind: str) -> dict:
    """Reconstruct the scoped resource changes and observed directory layout."""
    result = compare_resources(resources(template), resources(actual), icons, kind)
    result['metadata_payloads'] = compare_metadata(template, actual, kind)
    result['layout'] = verify_serialization(actual)
    result['directory_metadata'] = 'MATCH_OBSERVED_LAYOUT'
    result['resource_serialization'] = 'MATCH_OBSERVED_LAYOUT'
    result['unqualified'] = []
    return result


def verify(setup: bytes, exe: bytes, loader: bytes, template: bytes,
           icon: bytes, previous: bytes) -> dict:
    """Bind prior scoped attribution and validate exact new resource bytes."""
    record = document(previous)
    if (record.get('schema') != 'inno-674-product-binary-v1'
            or record.get('setup_sha256') != digest(setup)
            or record.get('uninstaller', {}).get('uninstaller_sha256') != digest(exe)
            or record.get('release_admission') != 'NOT_VERIFIED'
            or (digest(loader), digest(template), digest(icon)) != (LOADER, ENGINE, ICON_SHA)):
        raise ValueError('attribution or template identity differs')
    compare(loader, setup)
    engine, frame = recover(setup)
    compare(template, engine, overlay_expected=False)
    if record.get('engine_frame') != frame:
        raise ValueError('engine frame identity differs')
    uninstaller = attribute(engine, exe)
    if record['uninstaller'] != uninstaller:
        raise ValueError('uninstaller attribution differs')
    icons = icon_resources(icon)
    return {'schema': 'inno-674-product-resources-v1', 'source_sha': record['source_sha'],
            'setup_sha256': digest(setup), 'binary_attribution_sha256': digest(previous),
            'engine_sha256': frame['engine_sha256'], 'uninstaller_sha256': digest(exe),
            'loader': check_resources(loader, setup, icons, 'loader'),
            'engine': check_resources(template, engine, icons, 'engine'),
            'messages': check_messages(exe[uninstaller['message_offset']:-12]),
            'resource_payloads': 'MATCH_SCOPED', 'solid_payload_attribution': 'NOT_VERIFIED',
            'compiled_script': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Read exact local inputs without executing them; emit new JSON evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    names = ('setup', 'uninstaller', 'loader', 'engine', 'icon', 'previous')
    for name in (*names, 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        write_json(args.output, verify(*(read_local(getattr(args, n)) for n in names)))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, struct.error,
            zlib.error, lzma.LZMAError, RecursionError):
        print('FAIL: scoped Inno 6.7.4 resource attribution', file=sys.stderr)
        return 2
    print('PASS: scoped resources and English messages; release not admitted')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
