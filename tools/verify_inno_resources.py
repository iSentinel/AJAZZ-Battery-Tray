#!/usr/bin/env python3
"""Verify scoped Inno resource payloads and exact custom icon attribution."""

import argparse
import lzma
from pathlib import Path
import struct
import sys
import zlib

from compare_inno_loader import TEMPLATE_SHA, compare, digest
from run_offline_qa import write_json
from verify_dotnet_host_resources import resources
from verify_inno_inner_engine import ENGINE_SHA, recover
from verify_windowsdesktop_provenance import read_local

ICON_SHA = 'be6d9849acd8c768725d73a4b1a70a4aba9284770dff72bbb5d355694bef3b16'
MAX_ICON = 1024 * 1024
LANG = '1033'


def named_group(name: str) -> tuple[str, str, str]:
    """Return the resource walker's hashed name key."""
    return ('14', 'name-sha256:' + digest(name.encode('utf-16le')), LANG)


def icon_resources(raw: bytes) -> dict:
    """Parse exact seven-image ICO and reconstruct group using IDs 100..106."""
    if not 118 < len(raw) <= MAX_ICON or struct.unpack_from('<HHH', raw) != (0, 1, 7):
        raise ValueError('unexpected ICO header')
    group = bytearray(raw[:6])
    pos, result = 118, {}
    for i, width in enumerate((16, 24, 32, 48, 64, 128, 0)):
        start = 6 + i * 16
        w, h, colors, reserved, planes, depth, size, offset = struct.unpack_from(
            '<BBBBHHII', raw, start)
        if ((w, h, colors, reserved, planes, depth) != (width, width, 0, 0, 0, 32)
                or offset != pos or not 0 < size <= len(raw) - pos):
            raise ValueError('unexpected ICO image extent or metadata')
        result[('3', str(100 + i), LANG)] = digest(raw[pos:pos + size])
        group.extend(raw[start:start + 12] + struct.pack('<H', 100 + i))
        pos += size
    if pos != len(raw):
        raise ValueError('unexpected ICO trailing bytes')
    result[named_group('MAINICON')] = digest(group)
    return result


def expected_leaves(template: dict, ico: dict, kind: str) -> tuple[dict, set]:
    """Model only reviewed loader/engine icon replacement and removed groups."""
    if kind == 'loader':
        removed = set(range(1, 27))
        obsolete = named_group('MAINICON_DARK')
        unresolved = {('10', '11111', LANG), ('16', '1', LANG), ('24', '1', LANG)}
    elif kind == 'engine':
        removed = set(range(1, 14)) | {17, 18, 19}
        obsolete = named_group('Z_UNINSTALLICON')
        unresolved = {('16', '1', LANG)}
    else:
        raise ValueError('unknown PE kind')
    dropped = {('3', str(i), LANG) for i in removed} | {obsolete}
    if not (dropped | unresolved | {named_group('MAINICON')}) <= template.keys():
        raise ValueError('unexpected template resource layout')
    expected = {k: v for k, v in template.items() if k not in dropped}
    if (ico.keys() - {named_group('MAINICON')}) & expected.keys():
        raise ValueError('replacement icon ID already exists')
    return expected | ico, unresolved


def compare_resources(template: dict, actual: dict, ico: dict, kind: str) -> dict:
    """Require exact key set and qualified payloads; report unqualified leaves."""
    expected, unresolved = expected_leaves(template, ico, kind)
    if expected.keys() != actual.keys():
        raise ValueError('unexpected resource keys')
    if any(actual[k] != v for k, v in expected.items() if k not in unresolved):
        raise ValueError('resource payload differs outside unresolved scope')
    return {'kind': kind, 'template_count': len(template), 'actual_count': len(actual),
            'unchanged_template_count': sum(template.get(k) == v for k, v in actual.items()),
            'icon_images': 7, 'icon_group': 'MATCH',
            'removed_count': len(template.keys() - actual.keys()),
            'unqualified': [{'key': list(k), 'actual_sha256': actual[k],
                             'template_sha256': template[k]} for k in sorted(unresolved)],
            'directory_metadata': 'NOT_VERIFIED', 'resource_serialization': 'NOT_VERIFIED'}


def verify(setup: bytes, loader: bytes, template: bytes, ico: bytes, sha: str) -> dict:
    """Pin all inputs, recover the inner PE and compare scoped leaf payloads."""
    if [digest(x) for x in (setup, loader, template, ico)] != [sha, TEMPLATE_SHA, ENGINE_SHA, ICON_SHA]:
        raise ValueError('input digest differs')
    compare(loader, setup)
    engine, record = recover(setup)
    compare(template, engine, overlay_expected=False)
    icons = icon_resources(ico)
    return {'schema': 1, 'setup_sha256': sha, 'icon_sha256': ICON_SHA,
            'engine_sha256': record['engine_sha256'],
            'loader': compare_resources(resources(loader), resources(setup), icons, 'loader'),
            'engine': compare_resources(resources(template), resources(engine), icons, 'engine'),
            'offset_table': 'CRC_AND_BOUNDS_VERIFIED',
            'version_manifest_provenance': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Produce a new local scoped report without executing any input."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('setup', 'loader-template', 'engine-template', 'icon', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--setup-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        result = verify(read_local(args.setup), read_local(args.loader_template),
                        read_local(args.engine_template), read_local(args.icon), args.setup_sha256)
        write_json(args.output, result)
    except (OSError, ValueError, TypeError, KeyError, struct.error, zlib.error, lzma.LZMAError):
        print('FAIL: scoped Inno resource attribution', file=sys.stderr)
        return 2
    print('PASS: scoped icon and unchanged resource payload attribution')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
