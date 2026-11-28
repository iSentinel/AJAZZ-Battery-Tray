#!/usr/bin/env python3
"""Bind experimental USB display acceptance to a separate Windows candidate."""

import argparse
from pathlib import Path
import re
import sys
import zipfile

from run_offline_qa import write_json
from validate_scoped_sbom_schema import digest, document, read
from verify_hardware_acceptance import candidate
from verify_interactive_acceptance import STATUSES, check_case
from verify_windowsdesktop_provenance import read_local

CASES = tuple(f'UD{i:02d}' for i in range(1, 9))
PROFILES = ('windows-aj179', 'windows-aj159')


# Reviewed CI metadata, not a claim derived from an operator's diagnostic.
PINNED_SOURCE = 'd75e92fdba1c20226105291d0c6fe8eebeb6fe58'
PINNED_CHECKOUT = '6fadeac262c84252a21298cce57d418e48b9ad0a'
PINNED_TREE = '0eb9b029609eee033e34653116b23420bbacf426'
PINNED_ARCHIVE = 'eda76563161e4ece990435a7d8e89d577363c596a178439241c644aa810b7b81'
PINNED_APP = '482542de35b4d2e089ff41eaf34debba1dacd67015fb45d467ef4b587a7cb894'


def reviewed_runtime(identity: dict) -> str:
    """Require the reviewed successor artifact, not merely a beta.61 version."""
    if (identity.get('source_sha') != PINNED_SOURCE
            or identity.get('archive_sha256') != PINNED_ARCHIVE
            or identity.get('app_sha256') != PINNED_APP):
        raise ValueError('not the reviewed experimental display candidate')
    return '0.3.0-beta.61+' + PINNED_CHECKOUT


def template(identity: dict) -> dict:
    """Keep successor observations separate from ordinary release checklists."""
    if identity['profile'] not in PROFILES:
        raise ValueError('expected APEX Windows profile')
    version = reviewed_runtime(identity)
    return {'schema': 'unverified-display-acceptance-v2', 'candidate': identity,
            'expected_version': version, 'observed_version': '',
            'os_build': '', 'cases': {key: {'status': 'NOT_RUN', 'observation': ''}
                                      for key in CASES}}


def review(identity: dict, raw: bytes) -> dict:
    """Validate complete local coverage without authenticating observations."""
    expected, row = template(identity), document(raw)
    if (set(row) != set(expected) or row['schema'] != expected['schema']
            or row['candidate'] != identity or row['expected_version'] != expected['expected_version']
            or not isinstance(row['cases'], dict)
            or set(row['cases']) != set(CASES)):
        raise ValueError('checklist identity or coverage differs')
    os_build = row['os_build']
    if not isinstance(os_build, str) or (os_build and not re.fullmatch(r'[0-9.]{3,30}', os_build)):
        raise ValueError('invalid OS build')
    results = {key: check_case(key, row['cases'][key]) for key in CASES}
    recorded = any(value != 'NOT_RUN' for value in results.values())
    observed = row['observed_version']
    if not isinstance(observed, str) or observed not in ('', expected['expected_version']):
        raise ValueError('reported runtime version differs')
    if recorded and (not os_build or not observed):
        raise ValueError('record OS build and exact runtime version before testing')
    counts = {status: sum(value == status for value in results.values()) for status in STATUSES}
    return {'schema': 'unverified-display-review-v2', 'candidate': identity,
            'checkout_sha': PINNED_CHECKOUT, 'source_tree': PINNED_TREE,
            'runtime_version_binding': 'MATCH_REPORTED' if observed else 'NOT_REPORTED',
            'checklist_sha256': digest(raw), 'case_statuses': results, 'counts': counts,
            'coverage': 'COMPLETE_REPORTED' if counts['PASS'] == len(CASES) else 'INCOMPLETE',
            'human_observations': 'SELF_REPORTED_NOT_AUTHENTICATED',
            'physical_acceptance': 'NOT_INDEPENDENTLY_VERIFIED',
            'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Create or review local evidence; no device requests or release actions."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--archive-sha256', required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--profile', choices=PROFILES, required=True)
    parser.add_argument('--checklist', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        identity = candidate(read_local(args.archive), args.archive_sha256,
                             args.source_sha, args.profile)
        result = review(identity, read(args.checklist)) if args.checklist else template(identity)
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile):
        print('FAIL: invalid experimental display evidence', file=sys.stderr)
        return 2
    print('PASS: local checklist format; no independent acceptance or release admission')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
