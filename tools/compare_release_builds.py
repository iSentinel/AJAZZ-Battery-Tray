#!/usr/bin/env python3
"""Compare the shipped bytes from two reviewed native CI build runs."""

import argparse
from pathlib import Path
import re
import struct
import sys
import zipfile
import zlib

from run_offline_qa import write_json
from verify_hardware_acceptance import apple, digest, windows
from verify_installer_candidate import verify
from verify_windowsdesktop_provenance import read_local

PROFILES = ('windows', 'installer', 'universal', 'high-sierra')


def inspect(path: Path, expected: str, source: str, profile: str) -> dict:
    """Validate the downloaded archive against the reviewed digest and layout."""
    raw = read_local(path)
    if not re.fullmatch(r'[0-9a-f]{64}', expected) or digest(raw) != expected:
        raise ValueError('archive SHA-256 differs')
    if profile == 'installer':
        candidate = verify(raw, expected, source)['candidate']
        return {'asset_sha256': candidate['setup_sha256'],
                'app_sha256': candidate['app_sha256']}
    if profile == 'windows':
        data = windows(raw)
        return {'asset_sha256': data['app_sha256'],
                'payload_sha256': data['payload_sha256']}
    data = apple(raw, profile)
    return {'asset_sha256': data['inner_archive_sha256'],
            'payload_sha256': data['payload_sha256']}


def compare(left: dict, right: dict) -> dict:
    """Classify exact asset equality separately from component differences."""
    a = left.get('payload_sha256', {})
    b = right.get('payload_sha256', {})
    changed = sorted(name for name in a.keys() | b.keys() if a.get(name) != b.get(name))
    if left['asset_sha256'] == right['asset_sha256']:
        status = 'MATCH'
    elif a and b and not changed:
        status = 'PACKAGING_DIFFERS'
    else:
        status = 'ASSET_DIFFERS'
    return {'result': status, 'changed_members': changed}


def run(args: argparse.Namespace) -> dict:
    """Bind the comparison to a caller-reviewed checkout and two CI runs."""
    if not re.fullmatch(r'[0-9a-f]{40}', args.source_sha):
        raise ValueError('invalid source SHA')
    if min(args.run_ids) <= 0 or len(set(args.run_ids)) != 2:
        raise ValueError('two distinct run IDs are required')
    left = inspect(args.first, args.first_sha256, args.source_sha, args.profile)
    right = inspect(args.second, args.second_sha256, args.source_sha, args.profile)
    return {'schema': 'release-build-comparison-v1', 'profile': args.profile,
            'source_sha': args.source_sha, 'source_provenance': 'CALLER_REVIEW_REQUIRED',
            'run_ids': args.run_ids, 'archive_sha256': [args.first_sha256, args.second_sha256],
            'assets': [left, right], **compare(left, right)}


def main(argv: list[str] | None = None) -> int:
    """Return 0 for exact release asset equality, 1 for differences, 2 for errors."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=PROFILES, required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--run-ids', nargs=2, type=int, required=True)
    parser.add_argument('--first', type=Path, required=True)
    parser.add_argument('--first-sha256', required=True)
    parser.add_argument('--second', type=Path, required=True)
    parser.add_argument('--second-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = run(args)
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            NotImplementedError, zipfile.BadZipFile, struct.error, zlib.error):
        print('ERROR: invalid or unavailable build comparison input', file=sys.stderr)
        return 2
    matched = result['result'] == 'MATCH'
    print(f"{'PASS' if matched else 'FAIL'}: {args.profile} {result['result']}")
    return 0 if matched else 1


if __name__ == '__main__':
    raise SystemExit(main())
