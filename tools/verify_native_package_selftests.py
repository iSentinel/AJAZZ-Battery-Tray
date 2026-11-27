#!/usr/bin/env python3
"""Replay exact retained native package self-test evidence without execution."""

import argparse
from io import BytesIO
from pathlib import Path
import sys
import zipfile

from observe_native_package_selftests import CASES, CORPUS_SHA
from review_beta61_admission import normalized_plan
from review_normalized_package_set import PACKAGES
from run_offline_qa import write_json
from validate_scoped_sbom_schema import digest, document, read
from verify_hardware_acceptance import apple, members, windows
from verify_windowsdesktop_provenance import read_local

RUN_ID = 45914776932
CHECKOUT = '2a0b91f60b8b057290e4cd9815728aa81d9e4b59'
LIMIT = 65536
OBSERVATIONS = {
    'windows': (
        15161214672,
        '82d294e587d8d45c811b672e39dddaa9e859f4c7f8c3b415f5facf9f89915a0f',
        ('windows',),
    ),
    'apple': (
        15161801759,
        '458cfb48e6239468755e53207d82cbc4066bbeac2360c1d960cd073f6eaabd7a',
        ('universal', 'high-sierra'),
    ),
}


def original_executable(raw: bytes, edition: str) -> str:
    """Derive the binary digest from the exact pinned original CI archive."""
    pin = normalized_plan()['assets'][edition]['archive_sha256']
    if digest(raw) != pin:
        raise ValueError('original application archive differs')
    identity = windows(raw) if edition == 'windows' else apple(raw, edition)
    return identity['app_sha256']


def check_observation(raw: bytes, edition: str, exe_sha: str) -> dict:
    """Require exact identity, case order, integer exits and limited scope."""
    row = document(raw)
    expected = {
        'schema': 'native-package-selftests-v1',
        'edition': edition,
        'source_sha': normalized_plan()['source_sha'],
        'package_sha256': PACKAGES[edition][1],
        'executable_sha256': exe_sha,
        'corpus_sha256': CORPUS_SHA,
        'runner_os': row.get('runner_os'),
        'cases': [
            {'mode': mode, 'exit_code': code, 'expected_exit_code': code,
             'result': 'PASS'} for mode, code, _ in CASES[edition]
        ],
        'post_test_inventory': 'MATCH',
        'gui_launch': 'NOT_RUN',
        'physical_acceptance': 'NOT_VERIFIED',
        'release_admission': 'BLOCKED',
    }
    prefix = 'Windows-' if edition == 'windows' else 'macOS-'
    runner = row.get('runner_os')
    if (row != expected or not isinstance(runner, str)
            or not runner.startswith(prefix) or not 0 < len(runner) <= 128
            or not runner.isprintable()):
        raise ValueError('native self-test observation differs')
    if any(type(case[key]) is not int for case in row['cases']
           for key in ('exit_code', 'expected_exit_code')):
        raise ValueError('non-integer exit code')
    return row


def replay(raw: bytes, group: str, binaries: dict[str, str]) -> dict:
    """Replay the exact retained ZIP with no extraction or application launch."""
    artifact, pin, editions = OBSERVATIONS[group]
    if not 0 < len(raw) <= LIMIT or digest(raw) != pin:
        raise ValueError('observation archive digest differs')
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        if sum(item.file_size for item in archive.infolist()) > LIMIT:
            raise ValueError('observation inventory exceeds limit')
    files = members(raw, {edition + '-selftests.json' for edition in editions})
    rows = {}
    for edition in editions:
        data = files[edition + '-selftests.json']
        row = check_observation(data, edition, binaries[edition])
        rows[edition] = {'observation_sha256': digest(data), 'observation': row}
    return {'artifact_id': artifact, 'archive_sha256': pin, 'editions': rows}


def review(observations: dict[str, bytes], originals: dict[str, Path]) -> dict:
    """Bind all three editions and two original evidence archives."""
    if set(originals) != set(CASES) or set(observations) != set(OBSERVATIONS):
        raise ValueError('incomplete evidence set')
    binaries = {edition: original_executable(read_local(path), edition)
                for edition, path in originals.items()}
    groups = {name: replay(raw, name, binaries)
              for name, raw in observations.items()}
    return {'schema': 'native-package-selftest-review-v1',
            'run_id': RUN_ID, 'checkout': CHECKOUT, 'groups': groups,
            'observed_cases': sum(len(cases) for cases in CASES.values()),
            'native_observation': 'MATCH', 'gui_launch': 'NOT_RUN',
            'physical_acceptance': 'NOT_VERIFIED',
            'trusted_signing': 'NOT_VERIFIED', 'release_admission': 'BLOCKED'}


def main(argv: list[str] | None = None) -> int:
    """Write scoped evidence: exit 0 match, exit 2 invalid input."""
    parser = argparse.ArgumentParser(description=__doc__)
    for group in OBSERVATIONS:
        parser.add_argument('--' + group + '-evidence', type=Path, required=True)
    for edition in CASES:
        parser.add_argument('--' + edition + '-archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        observations = {k: read(getattr(args, k + '_evidence')) for k in OBSERVATIONS}
        originals = {k: getattr(args, k.replace('-', '_') + '_archive') for k in CASES}
        write_json(args.output, review(observations, originals))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile):
        print('FAIL: exact native self-test evidence', file=sys.stderr)
        return 2
    print('PASS: 12 scoped native observations; GUI NOT_RUN; release BLOCKED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
