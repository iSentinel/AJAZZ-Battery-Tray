#!/usr/bin/env python3
"""Create or check a local, candidate-bound interactive installer checklist."""

import argparse
from pathlib import Path
import re
import struct
import sys
import zipfile
import zlib

from run_offline_qa import write_json
from validate_scoped_sbom_schema import digest, document, read
from verify_windowsdesktop_provenance import read_local
from verify_inno674_setup_records import ALIGNED_SOURCE
from verify_installer_candidate import verify as verify_installer_archive
from verify_windows_notice_transport import MANIFEST_SHA

CASES = tuple(f'RG{i:02d}' for i in range(1, 7))
STATUSES = ('NOT_RUN', 'NOT_VERIFIED', 'PASS', 'FAIL')


def local_candidate(raw: bytes, row: dict) -> dict:
    """Bind a private local build without claiming hosted qualification."""
    fixed = {'schema': 'local-inno674-build-v1', 'engine_version': '6.7.4',
             'installer_source_sha256': ALIGNED_SOURCE,
             'notice_manifest_sha256': MANIFEST_SHA, 'input_identity': 'MATCH',
             'source_provenance': 'NOT_VERIFIED', 'lifecycle': 'NOT_RUN',
             'distribution_compliance': 'NOT_VERIFIED',
             'release_admission': 'NOT_VERIFIED'}
    fields = ('setup_sha256', 'app_sha256')
    if (set(row) != set(fixed) | set(fields) | {'icons'}
            or any(row[key] != value for key, value in fixed.items())):
        raise ValueError('unexpected local build evidence')
    icons = row['icons']
    if not isinstance(icons, dict) or set(icons) != {
            'AppIcon.ico', 'AppIcon-white.ico', 'AppIcon-black.ico', 'AppIcon-blue.ico'}:
        raise ValueError('unexpected local icon inventory')
    for value in [row[key] for key in fields] + list(icons.values()):
        if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value):
            raise ValueError('invalid local build identity')
    return {**{key: row[key] for key in fields}, 'engine_version': '6.7.4',
            'local_build_evidence_sha256': digest(raw),
            'source_provenance': 'NOT_VERIFIED', 'native_qualification': 'NOT_VERIFIED'}


def candidate(raw: bytes) -> dict:
    """Distinguish a private build from joined native qualification evidence."""
    row = document(raw)
    if row.get('schema') == 'local-inno674-build-v1':
        return local_candidate(raw, row)
    if (row.get('schema') != 'inno-674-migration-evidence-v1'
            or row.get('production_shape') != 'MATCH_SCOPED'
            or row.get('scoped_native_evidence') != 'MATCH'
            or row.get('engine_version') != '6.7.4'
            or row.get('release_admission') != 'NOT_VERIFIED'):
        raise ValueError('unexpected candidate qualification')
    result = {key: row[key] for key in ('source_sha', 'setup_sha256', 'app_sha256')}
    for key, value in result.items():
        size = 40 if key == 'source_sha' else 64
        if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{%d}' % size, value):
            raise ValueError('invalid candidate identity')
    return {**result, 'engine_version': '6.7.4', 'native_evidence_sha256': digest(raw)}


def archive_identity(path: Path, sha: str, source_sha: str) -> dict:
    """Bind the normal hosted installer archive to its exact checkout."""
    report = verify_installer_archive(read_local(path), sha, source_sha)
    row = report['candidate']
    keys = ('source_sha', 'setup_sha256', 'app_sha256')
    return {**{key: row[key] for key in keys}, 'archive_sha256': sha,
            'installer_profile': 'ci-beta61', 'source_provenance': 'CALLER_REVIEW_REQUIRED'}


def bind_binaries(identity: dict, setup: Path | None, app: Path | None,
                  required: bool = False) -> str:
    """Check both local byte hashes without executing or authenticating files."""
    if (setup is None) != (app is None) or (required and setup is None):
        raise ValueError('both candidate binaries are required')
    if setup is None:
        return 'NOT_PROVIDED'
    for path, key in ((setup, 'setup_sha256'), (app, 'app_sha256')):
        data = read_local(path)
        if not data or digest(data) != identity[key]:
            raise ValueError('candidate binary digest differs')
    return 'MATCH'


def binary_binding(raw: bytes, setup: Path | None, app: Path | None) -> str:
    """Require actual local bytes for a build without native qualification."""
    identity = candidate(raw)
    return bind_binaries(identity, setup, app, 'local_build_evidence_sha256' in identity)


def template_identity(identity: dict) -> dict:
    """Create an explicitly untested checklist for the reviewed identity."""
    return {'schema': 'interactive-acceptance-checklist-v1', 'candidate': identity,
            'os_build': '', 'cases': {key: {'status': 'NOT_RUN', 'observation': ''}
                                      for key in CASES}}


def template(raw: bytes) -> dict:
    """Expose checklist creation for the existing evidence formats."""
    return template_identity(candidate(raw))


def check_case(key: str, row: dict) -> str:
    """Require an actual bounded human observation for a recorded result."""
    if not isinstance(row, dict) or set(row) != {'status', 'observation'}:
        raise ValueError('unexpected case fields')
    status, note = row['status'], row['observation']
    if status not in STATUSES or not isinstance(note, str) or len(note) > 500:
        raise ValueError('invalid case result')
    if status == 'NOT_RUN' and note:
        raise ValueError('untested case has an observation')
    if status != 'NOT_RUN' and not note.strip():
        raise ValueError('missing observation')
    return status


def verify_identity(identity: dict, checklist: bytes, binding: str) -> dict:
    """Validate identity and completeness, never authenticate human claims."""
    expected = template_identity(identity)
    data = document(checklist)
    if (set(data) != set(expected) or data['schema'] != expected['schema']
            or data['candidate'] != expected['candidate']
            or not isinstance(data['cases'], dict) or set(data['cases']) != set(CASES)):
        raise ValueError('checklist identity or coverage differs')
    os_build = data['os_build']
    if not isinstance(os_build, str) or (os_build and not re.fullmatch(r'[0-9.]{3,30}', os_build)):
        raise ValueError('invalid OS build')
    results = {key: check_case(key, data['cases'][key]) for key in CASES}
    if not os_build and any(value != 'NOT_RUN' for value in results.values()):
        raise ValueError('record OS build before testing')
    counts = {status: sum(value == status for value in results.values()) for status in STATUSES}
    return {'schema': 'interactive-acceptance-review-v1', 'candidate': expected['candidate'],
            'local_binary_binding': binding,
            'checklist_sha256': digest(checklist), 'case_statuses': results, 'counts': counts,
            'coverage': 'COMPLETE_REPORTED' if counts['PASS'] == len(CASES) else 'INCOMPLETE',
            'human_observations': 'SELF_REPORTED_NOT_AUTHENTICATED',
            'interactive_acceptance': 'NOT_INDEPENDENTLY_VERIFIED',
            'physical_acceptance': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}


def verify(raw: bytes, checklist: bytes,
           setup: Path | None = None, app: Path | None = None) -> dict:
    """Review an existing native or private build checklist."""
    identity = candidate(raw)
    binding = bind_binaries(identity, setup, app, 'local_build_evidence_sha256' in identity)
    return verify_identity(identity, checklist, binding)


def review_request(args: argparse.Namespace) -> dict:
    """Validate the requested evidence format and apply the matching scope."""
    if args.ci_archive is not None:
        if not args.archive_sha256 or not args.source_sha:
            raise ValueError('CI archive requires its digests and checkout identity')
        identity = archive_identity(args.ci_archive, args.archive_sha256, args.source_sha)
        binding = bind_binaries(identity, args.setup, args.app, args.checklist is not None)
        if args.checklist is not None:
            return verify_identity(identity, read(args.checklist), binding)
        return template_identity(identity)
    if args.archive_sha256 is not None or args.source_sha is not None:
        raise ValueError('archive arguments require a CI archive')
    raw = read(args.candidate)
    if args.checklist is not None:
        return verify(raw, read(args.checklist), args.setup, args.app)
    binary_binding(raw, args.setup, args.app)
    return template(raw)


def main(argv: list[str] | None = None) -> int:
    """Emit a private checklist or a scoped review; no network or execution."""
    parser = argparse.ArgumentParser(description=__doc__)
    evidence = parser.add_mutually_exclusive_group(required=True)
    evidence.add_argument('--candidate', type=Path,
                          help='Joined native JSON or private local build evidence JSON')
    evidence.add_argument('--ci-archive', type=Path, help='Normal beta.61 installer CI ZIP')
    parser.add_argument('--archive-sha256', help='Expected SHA-256 of the original CI ZIP')
    parser.add_argument('--source-sha', help='Expected actual native CI checkout SHA')
    parser.add_argument('--checklist', type=Path)
    parser.add_argument('--setup', type=Path, help='Exact candidate setup executable')
    parser.add_argument('--app', type=Path, help='Exact candidate installed application executable')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        write_json(args.output, review_request(args))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            NotImplementedError, struct.error, zipfile.BadZipFile, zlib.error):
        print('FAIL: interactive checklist identity or format', file=sys.stderr)
        return 2
    print('PASS: local checklist format; no independent acceptance or release authorization')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
