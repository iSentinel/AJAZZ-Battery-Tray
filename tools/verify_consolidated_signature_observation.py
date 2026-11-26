#!/usr/bin/env python3
"""Verify the retained exact Windows signature observation without granting trust."""

import argparse
from io import BytesIO
from pathlib import Path
import stat
import sys
import zipfile

from run_offline_qa import write_json
from stage_consolidated_signature_inputs import FILES, SOURCE
from validate_scoped_sbom_schema import digest, document
from verify_windowsdesktop_provenance import read_local

ARCHIVE_SHA = '89114da68d1e23f3c37be155d33ad0fbb339cb990d06a158bf382f64bda37b3e'
JSON_SHA = '305f453b4d16dc87363bf6f5b179f95cedffd44c261bc0c01f9a3ecbea5ae949'
LIMIT = 65536


def check_observation(raw: bytes) -> dict:
    """Require exact identities, unsigned status and explicit false certificate flags."""
    row = document(raw)
    expected = {'schema': 'consolidated-authenticode-observation-v1',
                'source_sha': SOURCE, 'files': {
                    name: {'sha256': sha, 'status': 'NotSigned',
                           'signature_type': 'None', 'signer_present': False,
                           'timestamp_present': False}
                    for name, sha in FILES.items()},
                'trusted_signing': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}
    if row != expected or any(type(file[key]) is not bool for file in row['files'].values()
                              for key in ('signer_present', 'timestamp_present')):
        raise ValueError('unexpected native observation')
    return row


def verify(raw: bytes) -> dict:
    """Check the pinned original ZIP, its sole bounded member and exact JSON."""
    if not 0 < len(raw) <= LIMIT or digest(raw) != ARCHIVE_SHA:
        raise ValueError('observation archive digest differs')
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        entries = archive.infolist()
        if len(entries) != 1:
            raise ValueError('unexpected observation inventory')
        info = entries[0]
        if (info.filename != 'authenticode.json' or info.orig_filename != info.filename
                or info.flag_bits & 1 or not 0 < info.file_size <= LIMIT
                or stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG)
                or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
            raise ValueError('invalid observation member')
        data = archive.read(info)
    if digest(data) != JSON_SHA:
        raise ValueError('observation JSON digest differs')
    row = check_observation(data)
    return {'schema': 'consolidated-signature-review-v1', 'source_sha': SOURCE,
            'run_id': 45811458861, 'artifact_id': 15113087216,
            'archive_sha256': ARCHIVE_SHA, 'observation_sha256': JSON_SHA,
            'files': row['files'], 'native_unsigned_observation': 'MATCH',
            'trusted_signing': 'NOT_VERIFIED', 'release_admission': 'BLOCKED'}


def main(argv: list[str] | None = None) -> int:
    """Write scoped local evidence; do not sign or authorize any candidate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        write_json(args.output, verify(read_local(args.archive)))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile):
        print('FAIL: exact native signature observation', file=sys.stderr)
        return 2
    print('PASS: three exact unsigned observations; release BLOCKED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
