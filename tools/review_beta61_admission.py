#!/usr/bin/env python3
"""Bind beta.61 acceptance observations to the exact reviewed release assets."""

import argparse
import json
from pathlib import Path
import struct
import sys
import zipfile
import zlib

from run_offline_qa import write_json
from stage_beta61_release import ASSETS, collect
from validate_scoped_sbom_schema import digest, read
from verify_hardware_acceptance_set import ARCHIVE_PROFILES, review_set
from verify_interactive_acceptance import archive_identity, verify_identity


def release_subject(plan: dict) -> dict:
    """Describe the immutable asset set separately from editable observations."""
    return {
        'beta_tag': 'v0.3.0-beta.61',
        'source_sha': plan['source_sha'],
        'source_tree': plan['source_tree'],
        'assets': {profile: {**row, 'filename': ASSETS[profile][2],
                             'channel': 'high-sierra' if profile == 'high-sierra' else 'beta'}
                   for profile, row in plan['assets'].items()},
    }


def report(plan: dict, hardware: dict, interactive: dict) -> dict:
    """Report coverage and pending release decisions without copying notes."""
    subject = release_subject(plan)
    identity = digest(json.dumps(subject, sort_keys=True, separators=(',', ':')).encode('utf-8'))
    complete = all(x['coverage'] == 'COMPLETE_REPORTED' for x in (hardware, interactive))
    profiles = hardware['profiles']
    return {
        'schema': 'beta61-admission-review-v1',
        'subject': subject,
        'subject_sha256': identity,
        'source_provenance': 'CALLER_REVIEW_REQUIRED',
        'hardware_counts': hardware['counts'],
        'hardware_checklists_sha256': {name: row['checklist_sha256']
                                       for name, row in profiles.items()},
        'interactive_counts': interactive['counts'],
        'interactive_checklist_sha256': interactive['checklist_sha256'],
        'interactive_binary_binding': interactive['local_binary_binding'],
        'reported_coverage': 'COMPLETE_REPORTED' if complete else 'INCOMPLETE',
        'human_observations': 'SELF_REPORTED_NOT_AUTHENTICATED',
        'pending_review': {
            'physical_acceptance': hardware['coverage'],
            'interactive_acceptance': interactive['coverage'],
            'distribution': 'NOT_VERIFIED',
            'signing_disposition': 'NOT_VERIFIED',
            'publication_approval': 'NOT_VERIFIED',
        },
        'release_admission': 'BLOCKED',
    }


def review(raw: bytes, archives: dict[str, Path], checklists: Path) -> dict:
    """Revalidate the pinned assets and original checklists on every review."""
    plan, payload = collect(raw, archives)
    source = plan['source_sha']
    pins = plan['assets']
    hardware = review_set(
        source, {p: (archives[p], pins[p]['archive_sha256']) for p in ARCHIVE_PROFILES},
        checklists)
    identity = archive_identity(archives['installer'], pins['installer']['archive_sha256'], source)
    if (digest(payload['installer']) != identity['setup_sha256']
            or digest(payload['windows']) != identity['app_sha256']):
        raise ValueError('interactive binaries differ from verified release assets')
    interactive = verify_identity(identity, read(checklists / 'interactive-checklist.json'), 'MATCH')
    return report(plan, hardware, interactive)


def main(argv: list[str] | None = None) -> int:
    """Exit 0 for complete reported coverage, 1 for incomplete, or 2 for invalid input."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    for profile in ASSETS:
        parser.add_argument(f'--{profile}-archive', type=Path, required=True)
    parser.add_argument('--checklist-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    archives = {p: getattr(args, p.replace('-', '_') + '_archive') for p in ASSETS}
    try:
        result = review(read(args.manifest), archives, args.checklist_dir)
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            NotImplementedError, zipfile.BadZipFile, struct.error, zlib.error):
        print('FAIL: invalid candidate archive or acceptance evidence', file=sys.stderr)
        return 2
    for name in ('hardware', 'interactive'):
        counts = result[name + '_counts']
        print(f'{name}: ' + ', '.join(f'{status}={value}' for status, value in counts.items()))
    complete = result['reported_coverage'] == 'COMPLETE_REPORTED'
    print(f'{"PASS" if complete else "FAIL"}: reported acceptance coverage')
    print(f'Subject SHA-256: {result["subject_sha256"]}')
    print('Release admission: BLOCKED')
    return 0 if complete else 1


if __name__ == '__main__':
    raise SystemExit(main())
