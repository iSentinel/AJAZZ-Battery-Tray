#!/usr/bin/env python3
"""Export fixed synthetic native package cases, not physical acceptance results."""

import argparse
from pathlib import Path
import sys

from observe_native_package_selftests import CASES, CORPUS_SHA
from review_beta61_admission import normalized_plan
from review_normalized_package_set import PACKAGES
from run_offline_qa import write_json


def catalog() -> dict:
    """Derive stable edition-qualified IDs from the actual execution registry."""
    definitions = {}
    for edition, cases in CASES.items():
        rows = {}
        for mode, code, timeout in cases:
            key = edition + ':' + mode
            if (key in definitions or key in rows or not mode.startswith('--')
                    or type(code) is not int or type(timeout) is not int or timeout <= 0):
                raise ValueError('invalid native case registry')
            rows[key] = {'edition': edition, 'argument': mode,
                         'expected_exit_code': code, 'timeout_seconds': timeout,
                         'package_sha256': PACKAGES[edition][1]}
        definitions.update(rows)
    return {'schema': 'native-package-case-catalog-v1',
            'source_sha': normalized_plan()['source_sha'], 'corpus_sha256': CORPUS_SHA,
            'cases': definitions, 'case_count': len(definitions),
            'scope': 'SYNTHETIC_NATIVE_PACKAGE_CLI', 'observations': 'NOT_COLLECTED',
            'gui_launch': 'NOT_RUN', 'physical_acceptance': 'NOT_VERIFIED',
            'release_admission': 'BLOCKED'}


def main(argv: list[str] | None = None) -> int:
    """Write a new catalog file without launching any application."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        write_json(args.output, catalog())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        print('FAIL: native package case catalog', file=sys.stderr)
        return 2
    print('PASS: synthetic native CLI catalog; no observations collected')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
