#!/usr/bin/env python3
"""Verify observed Apple build self-test groups without executing applications."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from run_offline_qa import ROOT, git_value, read_evidence, write_json

REFERENCE = ROOT / 'tests/fixtures/apple-native-groups-v1.json'
PACKAGES = {'universal': 'AJAZZBatteryTray-macOS-universal.zip',
            'high-sierra': 'AJAZZBatteryTray-macOS-HighSierra-Intel.zip'}


def catalog(raw: bytes, edition: str) -> list[str]:
    """Require exact profile inventory and unique printable group labels."""
    row = json.loads(raw)
    profiles = row['profiles']
    if (row['schema'] != 'apple-native-group-catalog-v1'
            or set(profiles) != set(PACKAGES)):
        raise ValueError('invalid Apple catalog')
    profile = profiles[edition]
    names = profile['groups']
    if (profile['package_name'] != PACKAGES[edition]
            or not isinstance(names, list) or not names
            or any(not isinstance(name, str) or not name.strip()
                   or not re.fullmatch(r'[ -~]{1,256}', name) for name in names)
            or len(names) != len(set(names))):
        raise ValueError('invalid Apple group definitions')
    return names


def verify(raw: bytes, names: list[str], package: str) -> dict:
    """Require ordered group labels followed by one exact package marker."""
    actual = []
    finished = False
    for line in raw.decode('utf-8').splitlines():
        if line.startswith(('FAIL:', 'SKIP:')):
            raise ValueError('failed or skipped build test')
        if line.startswith('PASS:'):
            if finished:
                raise ValueError('late or duplicate pass marker')
            if line == 'PASS: ' + package:
                finished = True
            elif line.startswith('PASS: '):
                actual.append(line[6:])
            else:
                raise ValueError('malformed pass marker')
    if actual != names or not finished:
        raise ValueError('Apple group coverage differs')
    return {'schema': 'apple-native-group-review-v1', 'group_count': len(names),
            'coverage': 'MATCH', 'reported_status': 'PASS',
            'scope': 'BUILD_SELF_TEST_GROUPS', 'physical_acceptance': 'NOT_VERIFIED',
            'release_admission': 'BLOCKED'}


def main(argv: list[str] | None = None) -> int:
    """Verify build stdout and retain aggregate scoped evidence only."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--edition', choices=PACKAGES, required=True)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        reference = read_evidence(REFERENCE)
        names = catalog(reference, args.edition)
        package = str(ROOT / 'dist' / PACKAGES[args.edition])
        result = verify(read_evidence(args.capture), names, package)
        result.update(edition=args.edition, checkout=git_value('rev-parse', 'HEAD'),
                      catalog_sha256=hashlib.sha256(reference).hexdigest())
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        print('FAIL: Apple native build group coverage', file=sys.stderr)
        return 2
    print('PASS: exact Apple native build group coverage')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
