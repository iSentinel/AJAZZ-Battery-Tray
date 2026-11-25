#!/usr/bin/env python3
"""Review all five hardware profiles against one caller-selected CI generation."""

import argparse
from pathlib import Path
import sys
import zipfile

from run_offline_qa import write_json
from validate_scoped_sbom_schema import read
from verify_hardware_acceptance import PROFILES, candidate, review
from verify_interactive_acceptance import STATUSES
from verify_windowsdesktop_provenance import read_local

ARCHIVE_PROFILES = {
    'windows': ('windows-aj179', 'windows-aj159', 'windows-aula'),
    'universal': ('universal',),
    'high-sierra': ('high-sierra',),
}


def review_set(source: str, archives: dict[str, tuple[Path, str]],
               checklists: Path) -> dict:
    """Revalidate archive bytes and each original checklist; do not trust summaries."""
    if set(archives) != set(ARCHIVE_PROFILES):
        raise ValueError('incomplete archive set')
    if checklists.is_symlink() or not checklists.is_dir():
        raise ValueError('expected local checklist directory')
    results = {}
    for edition, profiles in ARCHIVE_PROFILES.items():
        path, sha = archives[edition]
        identity = candidate(read_local(path), sha, source, profiles[0])
        for profile in profiles:
            record = read(checklists / (profile + '.checklist.json'))
            results[profile] = review(dict(identity, profile=profile), record)
    if set(results) != set(PROFILES):
        raise ValueError('incomplete profile coverage')
    counts = {status: sum(row['counts'][status] for row in results.values())
              for status in STATUSES}
    return {
        'schema': 'hardware-acceptance-set-v1', 'source_sha': source,
        'source_provenance': 'CALLER_REVIEW_REQUIRED', 'profiles': results,
        'counts': counts,
        'coverage': 'COMPLETE_REPORTED' if counts['PASS'] == sum(counts.values())
        else 'INCOMPLETE',
        'human_observations': 'SELF_REPORTED_NOT_AUTHENTICATED',
        'physical_acceptance': 'NOT_INDEPENDENTLY_VERIFIED',
        'release_admission': 'NOT_VERIFIED',
    }


def main(argv: list[str] | None = None) -> int:
    """Emit a new scoped aggregate without network access or device requests."""
    parser = argparse.ArgumentParser(description=__doc__)
    for edition in ARCHIVE_PROFILES:
        parser.add_argument('--' + edition + '-archive', type=Path, required=True)
        parser.add_argument('--' + edition + '-sha256', required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--checklist-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    archives = {}
    for edition in ARCHIVE_PROFILES:
        key = edition.replace('-', '_')
        archives[edition] = (getattr(args, key + '_archive'),
                             getattr(args, key + '_sha256'))
    try:
        result = review_set(args.source_sha, archives, args.checklist_dir)
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile):
        print('FAIL: hardware acceptance set identity or coverage', file=sys.stderr)
        return 2
    print('PASS: five local checklist reviews; no independent acceptance')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
