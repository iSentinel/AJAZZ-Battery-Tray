#!/usr/bin/env python3
"""Compare the observed PE32 Inno loader to its pinned official template."""

import argparse
import hashlib
from pathlib import Path
import struct
import sys

from inventory_dotnet_host_headers import parse_sections, unpack
from run_offline_qa import write_json
from verify_windowsdesktop_provenance import read_local

TEMPLATE_SHA = 'eb95b6ea1abb86dfb53023c2c8ce3c2e8d51cfc52f7a8efa61cc33e198feff23'
ORDER = ('.text', '.itext', '.data', '.bss', '.idata', '.didata',
         '.edata', '.tls', '.rdata', '.reloc', '.rsrc')


def digest(raw: bytes) -> str:
    """Hash an exact byte region."""
    return hashlib.sha256(raw).hexdigest()


def aligned(value: int, alignment: int) -> int:
    """Round a nonnegative extent to a power-of-two alignment."""
    if alignment <= 0 or alignment & (alignment - 1):
        raise ValueError('invalid alignment')
    return (value + alignment - 1) & ~(alignment - 1)


def layout(raw: bytes) -> dict:
    """Validate this narrow unsigned PE32 loader layout and resource extent."""
    if raw[:2] != b'MZ':
        raise ValueError('invalid DOS signature')
    pe, = unpack(raw, 60, '<I')
    if pe < 64 or raw[pe:pe + 4] != b'PE\0\0':
        raise ValueError('invalid PE signature')
    machine, count, _, _, _, optional, flags = unpack(raw, pe + 4, '<HHIIIHH')
    o = pe + 24
    if (machine, count, optional, flags) != (0x14c, len(ORDER), 224, 0x102):
        raise ValueError('unsupported loader COFF layout')
    if unpack(raw, o, '<H')[0] != 0x10b or unpack(raw, o + 92, '<I')[0] != 16:
        raise ValueError('unsupported PE32 optional header')
    if unpack(raw, o + 128, '<II') != (0, 0):
        raise ValueError('signed loader variant is outside scope')
    header, = unpack(raw, o + 60, '<I')
    table = o + optional
    sections, end = parse_sections(raw, table, count, header)
    resource = sections.get('.rsrc', {})
    va, size = unpack(raw, o + 112, '<II')
    sa, fa = unpack(raw, o + 32, '<II')
    if (tuple(sections) != ORDER or not size or resource['virtual_address'] != va
            or resource['virtual_size'] != size
            or resource['raw_size'] != aligned(size, fa)
            or resource['raw_pointer'] + resource['raw_size'] != end
            or unpack(raw, o + 56, '<I')[0] != aligned(va + size, sa)):
        raise ValueError('unsupported resource section layout')
    return {'optional': o, 'table': table, 'header': header,
            'sections': sections, 'end': end}


def normalized_header(raw: bytes, info: dict) -> bytes:
    """Mask only the five observed resource-growth fields."""
    o, t = info['optional'], info['table'] + 40 * (len(ORDER) - 1)
    data = bytearray(raw[:info['header']])
    for pos in (o + 8, o + 56, o + 116, t + 8, t + 16):
        data[pos:pos + 4] = bytes(4)
    return bytes(data)


def compare(template: bytes, actual: bytes, *, overlay_expected: bool = True) -> dict:
    """Require exact non-resource bytes and header invariants, not engine trust."""
    a, b = layout(template), layout(actual)
    if (a['end'] != len(template) or
            (b['end'] < len(actual)) != overlay_expected):
        raise ValueError('unexpected template or installer overlay')
    ar, br = a['sections']['.rsrc'], b['sections']['.rsrc']
    if normalized_header(template, a) != normalized_header(actual, b):
        raise ValueError('header differs beyond resource-growth fields')
    delta = br['raw_size'] - ar['raw_size']
    if (unpack(actual, b['optional'] + 8, '<I')[0]
            - unpack(template, a['optional'] + 8, '<I')[0] != delta):
        raise ValueError('initialized data growth differs')
    if template[a['header']:ar['raw_pointer']] != actual[b['header']:br['raw_pointer']]:
        raise ValueError('non-resource loader bytes differ')
    rows = []
    for name in ORDER:
        x, y = a['sections'][name], b['sections'][name]
        first = template[x['raw_pointer']:x['raw_pointer'] + x['raw_size']]
        second = actual[y['raw_pointer']:y['raw_pointer'] + y['raw_size']]
        if name != '.rsrc' and (x != y or first != second):
            raise ValueError('non-resource section differs')
        rows.append({'section': name, 'template_sha256': digest(first),
                     'actual_sha256': digest(second),
                     'state': 'RESOURCE_NOT_QUALIFIED' if name == '.rsrc' else 'MATCH'})
    return {'schema': 1, 'template_sha256': digest(template), 'setup_sha256': digest(actual),
            'sections': rows, 'non_resource_bytes': 'MATCH',
            'resource_section': 'NOT_QUALIFIED', 'overlay_bytes': len(actual) - b['end'],
            'overlay_sha256': digest(actual[b['end']:]),
            'embedded_engine': 'NOT_VERIFIED', 'uninstaller': 'NOT_VERIFIED',
            'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Bind actual input bytes to the expected setup digest and pinned loader."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', type=Path, required=True)
    parser.add_argument('--setup', type=Path, required=True)
    parser.add_argument('--setup-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        template, actual = read_local(args.template), read_local(args.setup)
        if digest(template) != TEMPLATE_SHA or digest(actual) != args.setup_sha256:
            raise ValueError('input digest differs')
        write_json(args.output, compare(template, actual))
    except (OSError, ValueError, TypeError, KeyError, struct.error):
        print('FAIL: scoped Inno loader comparison', file=sys.stderr)
        return 2
    print('PASS: non-resource loader bytes; resources and embedded engine not qualified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
