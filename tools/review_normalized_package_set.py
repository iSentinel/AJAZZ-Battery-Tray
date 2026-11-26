#!/usr/bin/env python3
"""Review a proposed notice-bearing package set, without selecting or releasing it."""

import argparse
import json
from pathlib import Path
import struct
import sys
import zipfile
import zlib

from build_consolidated_apple_notices import package_files, verify_wrapper
from build_consolidated_portable_notices import verify_zip
from review_beta61_admission import normalized_identity, normalized_plan, release_subject
from run_offline_qa import write_json
from validate_scoped_sbom_schema import digest, read
from verify_windowsdesktop_provenance import read_local

PACKAGES = {
    'windows': ('AJAZZBatteryTray-win-x64-notices.zip',
                'f22c7ed470ac798393ec94b5d61245bb17afea8d78eca3c0d866f3033977cfb3', 'beta'),
    'universal': ('AJAZZBatteryTray-macOS-universal-notices.zip',
                  'a3c837a0d673de8eccac182cf224503e54cf7b64d0bbcf6adb51dce755c025d8', 'beta'),
    'high-sierra': ('AJAZZBatteryTray-macOS-HighSierra-Intel-notices.zip',
                    '7b514bd2a2af310f0803822f8f8bbd80043c0cfca0af38fbb45b1a25f7b39db4', 'high-sierra'),
}


def subject_hash(subject: dict) -> str:
    """Hash canonical identity fields, independent of local availability."""
    return digest(json.dumps(subject, sort_keys=True, separators=(',', ':')).encode())


def proposal() -> dict:
    """Describe only a proposed package set; do not replace original app identities."""
    plan = normalized_plan()
    subject = release_subject(plan)
    assets = {edition: {'filename': name, 'sha256': sha, 'channel': channel,
                        'original_application_sha256': plan['assets'][edition]['release_asset_sha256']}
              for edition, (name, sha, channel) in PACKAGES.items()}
    assets['installer'] = {'filename': subject['assets']['installer']['filename'],
                           'sha256': plan['assets']['installer']['release_asset_sha256'],
                           'channel': 'beta'}
    return {'schema': 'normalized-package-proposal-v1', 'source_sha': plan['source_sha'],
            'source_tree': plan['source_tree'], 'beta_tag': subject['beta_tag'],
            'acceptance_subject_sha256': subject_hash(subject), 'assets': assets}


def check_package(raw: bytes, edition: str, original: bytes, license_bytes: bytes) -> None:
    """Require the exact prototype bytes and original application/notice identity."""
    if digest(raw) != PACKAGES[edition][1]:
        raise ValueError('proposed package digest differs')
    if digest(original) != normalized_plan()['assets'][edition]['archive_sha256']:
        raise ValueError('original application archive differs')
    if edition == 'windows':
        verify_zip(raw)
    else:
        verify_wrapper(raw, package_files(original, license_bytes, edition), edition)


def review(evidence: bytes, packages: dict[str, Path], originals: dict[str, Path],
           license_bytes: bytes, setup: Path | None = None) -> dict:
    """Revalidate the proposal and report availability, not release authorization."""
    normalized_identity(evidence)
    if set(packages) != set(PACKAGES) or set(originals) != set(PACKAGES):
        raise ValueError('incomplete proposed package set')
    for edition in PACKAGES:
        check_package(read_local(packages[edition]), edition,
                      read_local(originals[edition]), license_bytes)
    subject = proposal()
    if setup is not None and digest(read_local(setup)) != subject['assets']['installer']['sha256']:
        raise ValueError('normalized Setup differs')
    return {'schema': 'normalized-package-proposal-review-v1', 'subject': subject,
            'proposal_sha256': subject_hash(subject),
            'local_files': {**{k: 'MATCH' for k in PACKAGES},
                            'installer': 'MATCH' if setup is not None else 'NOT_PROVIDED'},
            'package_selection': 'NOT_VERIFIED', 'package_runtime_acceptance': 'NOT_VERIFIED',
            'distribution_compliance': 'NOT_VERIFIED', 'trusted_signing': 'NOT_VERIFIED',
            'publication_approval': 'NOT_VERIFIED', 'release_admission': 'BLOCKED'}


def main(argv: list[str] | None = None) -> int:
    """Review private files: exit 0 all match, 1 missing Setup, 2 invalid input."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--normalized-evidence', type=Path, required=True)
    for edition in PACKAGES:
        parser.add_argument('--' + edition + '-package', type=Path, required=True)
        parser.add_argument('--' + edition + '-archive', type=Path, required=True)
    parser.add_argument('--license', type=Path, required=True)
    parser.add_argument('--setup', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        packages = {k: getattr(args, k.replace('-', '_') + '_package') for k in PACKAGES}
        originals = {k: getattr(args, k.replace('-', '_') + '_archive') for k in PACKAGES}
        result = review(read(args.normalized_evidence), packages, originals,
                        read(args.license), args.setup)
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            NotImplementedError, zipfile.BadZipFile, struct.error, zlib.error):
        print('FAIL: proposed package identity', file=sys.stderr)
        return 2
    print('PASS: three notice-bearing packages match')
    print('Setup: ' + result['local_files']['installer'])
    print('Proposal SHA-256: ' + result['proposal_sha256'])
    print('Release admission: BLOCKED')
    return 0 if args.setup is not None else 1


if __name__ == '__main__':
    raise SystemExit(main())
