#!/usr/bin/env python3
"""Check Windows console assertion coverage against a reviewed reference."""

import argparse
import json
from pathlib import Path
import re
import sys

from run_offline_qa import ROOT, read_evidence, write_json

REFERENCE = ROOT / 'tests/fixtures/windows-native-assertions-v1.json'


def catalog(raw: bytes) -> list[str]:
    """Require unique exact assertion labels, including intentional spaces."""
    row = json.loads(raw)
    names = row['assertions']
    if (row['schema'] != 'windows-native-assertion-catalog-v1'
            or not isinstance(names, list) or not names
            or any(not isinstance(name, str) or not name.strip()
                   or not re.fullmatch(r'[ -~]{1,256}', name) for name in names)
            or len(names) != len(set(names))):
        raise ValueError('invalid assertion catalog')
    return names


def verify(raw: bytes, names: list[str]) -> dict:
    """Require the exact ordered assertions and one matching successful summary."""
    actual = []
    summary = None
    for line in raw.decode('utf-8-sig').splitlines():
        if line.startswith(('PASS ', 'FAIL ')):
            if summary is not None or not line.startswith('PASS '):
                raise ValueError('failed or late assertion')
            actual.append(line[5:])
        elif line.startswith('Summary:'):
            if summary is not None:
                raise ValueError('duplicate summary')
            summary = re.fullmatch(r'Summary: PASS=([0-9]+), FAIL=0', line)
            if summary is None:
                raise ValueError('invalid assertion summary')
    if actual != names or summary is None or int(summary[1]) != len(names):
        raise ValueError('assertion coverage differs')
    return {'schema': 'windows-native-assertion-review-v1',
            'assertion_count': len(names), 'coverage': 'MATCH',
            'reported_status': 'PASS', 'scope': 'SYNTHETIC_CONSOLE_ASSERTIONS',
            'physical_acceptance': 'NOT_VERIFIED', 'release_admission': 'BLOCKED'}


def main(argv: list[str] | None = None) -> int:
    """Verify a local console capture; export only aggregate scoped evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = verify(read_evidence(args.capture), catalog(read_evidence(REFERENCE)))
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        print('FAIL: Windows native assertion coverage', file=sys.stderr)
        return 2
    print('PASS: exact Windows assertion coverage')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
