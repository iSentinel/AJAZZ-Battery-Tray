#!/usr/bin/env python3
"""Verify ordered Windows Dashboard smoke-test groups from a local capture."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from run_offline_qa import ROOT, git_value, read_evidence, write_json

REFERENCE = ROOT / 'tests/fixtures/windows-dashboard-groups-v1.json'


def catalog(raw: bytes) -> list[str]:
    """Require the reviewed catalog format and distinct printable group labels."""
    row = json.loads(raw)
    groups = row['groups']
    if (row['schema'] != 'windows-dashboard-group-catalog-v1'
            or not isinstance(groups, list) or not groups
            or any(not isinstance(name, str) or not name.strip()
                   or not re.fullmatch(r'[ -~]{1,256}', name) for name in groups)
            or len(set(groups)) != len(groups)):
        raise ValueError('invalid dashboard catalog')
    return groups


def verify(raw: bytes, groups: list[str]) -> dict:
    """Match all ordered PASS labels; do not treat synthetic scale as real DPI."""
    observed = []
    for line in raw.decode('utf-8-sig').splitlines():
        if line.startswith(('FAIL:', 'SKIP:')):
            raise ValueError('failed or skipped dashboard group')
        if line.startswith('PASS:'):
            if not line.startswith('PASS: '):
                raise ValueError('malformed dashboard pass marker')
            observed.append(line[6:])
    if observed != groups:
        raise ValueError('dashboard group coverage differs')
    return {'schema': 'windows-dashboard-group-review-v1',
            'group_count': len(groups), 'coverage': 'MATCH',
            'reported_status': 'PASS', 'scope': 'SYNTHETIC_DASHBOARD_SMOKE',
            'real_dpi': 'NOT_VERIFIED', 'physical_acceptance': 'NOT_VERIFIED',
            'release_admission': 'BLOCKED'}


def main(argv: list[str] | None = None) -> int:
    """Check existing stdout; CI must independently require native exit zero."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        reference = read_evidence(REFERENCE)
        result = verify(read_evidence(args.capture), catalog(reference))
        result['catalog_sha256'] = hashlib.sha256(reference).hexdigest()
        result['checkout'] = git_value('rev-parse', 'HEAD')
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        print('FAIL: Windows Dashboard group coverage', file=sys.stderr)
        return 2
    print('PASS: exact Dashboard smoke group coverage; real DPI NOT_VERIFIED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
