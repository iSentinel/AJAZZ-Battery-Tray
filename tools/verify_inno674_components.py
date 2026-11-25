#!/usr/bin/env python3
"""Check exact proposed Inno 6.7.4 compiler inputs; no binary execution."""

import argparse
import json
from pathlib import Path
import stat
import sys

from compare_inno_compiler import NAMES, compare
from read_diagnostic_session import unique_object
from run_offline_qa import write_json

PIN = Path(__file__).resolve().parents[1] / 'config/inno-674-component-pins.json'
VENDOR = 'a549929319f9120716677c685535ca4671e4b937b5fdc87e2585f32d8eb30e8c'


def verify(root: Path, pins: dict) -> dict:
    """Require the exact known input set and reject Windows reparse points."""
    if (set(pins) != {'schema', 'vendor_sha256', 'engine_version', 'files'}
            or pins['schema'] != 'inno-674-component-pins-v1'
            or pins['vendor_sha256'] != VENDOR or pins['engine_version'] != '6.7.4'):
        raise ValueError('unexpected compiler pin schema')
    if len(pins['files']) != len(NAMES):
        raise ValueError('unexpected compiler input count')
    paths = [root]
    for item in pins['files']:
        if set(item) != {'name', 'bytes', 'sha256'} or item['name'] not in NAMES:
            raise ValueError('unexpected compiler input')
        paths.append(root / item['name'])
    for path in paths:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('compiler input is a link or reparse point')
    rows = compare([dict(item, state='PRESENT') for item in pins['files']], root)
    return {'schema': 'inno-674-component-evidence-v1', 'engine_version': '6.7.4',
            'vendor_sha256': VENDOR, 'files': rows, 'component_identity': 'MATCH',
            'scope': 'reviewed top-level compiler inputs, not loaded component trace',
            'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Write fresh exact component evidence from a local compiler directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        pins = json.loads(PIN.read_bytes(), object_pairs_hook=unique_object)
        write_json(args.output, verify(args.root, pins))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        print('FAIL: Inno 6.7.4 component identity', file=sys.stderr)
        return 2
    print('PASS: exact 38 compiler inputs; release not admitted')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
