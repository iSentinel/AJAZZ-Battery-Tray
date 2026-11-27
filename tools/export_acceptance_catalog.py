#!/usr/bin/env python3
"""Export existing human acceptance definitions without granting any test pass."""

import argparse
from pathlib import Path
import re
import sys

from run_offline_qa import ROOT, read_evidence, write_json
from verify_hardware_acceptance import PROFILES
from verify_interactive_acceptance import CASES

HARDWARE = 'docs/CANDIDATE_ACCEPTANCE.md'
INSTALLER = 'docs/BETA61_WINDOWS_RUNBOOK.md'
GUIDE = 'docs/BETA61_HARDWARE_FIELD_KIT.md'


def rows(raw: bytes, expected: set[str]) -> dict:
    """Read exact case rows and reject missing, duplicate or unknown IDs."""
    result = {}
    for line in raw.decode('utf-8').splitlines():
        if not re.match(r'^\|\s*(?:W|M|RG)[0-9]+\s*\|', line):
            continue
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if (len(cells) != 3 or cells[0] not in expected or cells[0] in result
                or not cells[1] or not cells[2]):
            raise ValueError('invalid or duplicate case row')
        key, action, outcome = cells
        result[key] = {'action': action, 'expected': outcome}
    if set(result) != expected:
        raise ValueError('incomplete case definitions')
    return result


def catalog(hardware: bytes, installer: bytes) -> dict:
    """Keep profile identity separate from shared human case definitions."""
    definitions = rows(hardware, {case for cases in PROFILES.values() for case in cases})
    definitions.update(rows(installer, set(CASES)))
    profiles = {key: {'scope': 'PHYSICAL', 'guide': GUIDE,
                      'cases': list(cases)} for key, cases in PROFILES.items()}
    profiles['interactive'] = {'scope': 'INTERACTIVE_NORMALIZED_SETUP',
                               'guide': INSTALLER, 'cases': list(CASES)}
    return {'schema': 'beta61-acceptance-catalog-v1', 'definitions': definitions,
            'profiles': profiles, 'physical_instances': sum(map(len, PROFILES.values())),
            'interactive_instances': len(CASES), 'observations': 'NOT_COLLECTED',
            'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Export definitions from reviewed repository documents, not user evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New local JSON file')
    args = parser.parse_args(argv)
    try:
        result = catalog(read_evidence(ROOT / HARDWARE), read_evidence(ROOT / INSTALLER))
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        print('FAIL: acceptance catalog', file=sys.stderr)
        return 2
    print('PASS: catalog definitions and coverage; no acceptance results collected')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
