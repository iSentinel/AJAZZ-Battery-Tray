#!/usr/bin/env python3
"""Bind unsigned native Authenticode observations to an exact candidate."""

import argparse
from pathlib import Path
import re
import sys

from run_offline_qa import write_json
from validate_scoped_sbom_schema import digest, document, read


def verify(raw: bytes, migration: bytes, exercised: bytes) -> dict:
    """Require exact identities; never grant trust to an unsigned candidate."""
    observed, joined, removed = map(document, (raw, migration, exercised))
    keys = ('source_sha', 'setup_sha256', 'app_sha256')
    identity = {key: joined[key] for key in keys}
    if (joined['schema'] != 'inno-674-migration-evidence-v1'
            or joined['production_shape'] != 'MATCH_SCOPED'
            or joined['scoped_native_evidence'] != 'MATCH'
            or joined['release_admission'] != 'NOT_VERIFIED'
            or removed['schema'] != 'inno-674-exercised-uninstaller-v1'
            or removed['uninstall_result'] != 'REMOVED'
            or removed['release_admission'] != 'NOT_VERIFIED'
            or joined['documents']['exercised-uninstaller'] != digest(exercised)
            or any(removed[k] != v for k, v in identity.items())):
        raise ValueError('candidate evidence differs')
    expected = {**identity, 'uninstaller_sha256': removed['uninstaller_sha256']}
    if any(not re.fullmatch(r'[0-9a-f]{40}' if k == 'source_sha' else
                            r'[0-9a-f]{64}', v) for k, v in expected.items()):
        raise ValueError('invalid candidate identity')
    files = {role: {'sha256': expected[key], 'status': 'NotSigned',
                    'signature_type': 'None', 'signer_present': False,
                    'timestamp_present': False}
             for role, key in (('setup', 'setup_sha256'), ('app', 'app_sha256'),
                               ('uninstaller', 'uninstaller_sha256'))}
    if observed != {'schema': 'candidate-authenticode-observation-v1',
                    'source_sha': identity['source_sha'], 'files': files,
                    'release_admission': 'NOT_VERIFIED'}:
        raise ValueError('unexpected Authenticode observation')
    return {'schema': 'candidate-signature-evidence-v1', **expected,
            'observation_sha256': digest(raw), 'migration_sha256': digest(migration),
            'exercised_sha256': digest(exercised), 'native_unsigned_observation': 'MATCH',
            'trusted_signing': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Verify native JSON observations without executing or signing binaries."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('observation', 'migration', 'exercised', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        write_json(args.output, verify(read(args.observation), read(args.migration),
                                       read(args.exercised)))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        print('FAIL: candidate signature evidence', file=sys.stderr)
        return 2
    print('PASS: unsigned observation bound; trusted signing remains unverified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
