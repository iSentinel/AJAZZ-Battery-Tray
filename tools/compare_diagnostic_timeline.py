#!/usr/bin/env python3
"""Compare local diagnostic snapshots without merging device identities."""

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

from analyze_aula_sleep import parse_summary
from compare_apex_reports import read_report
from compare_ready_clear import disagreement, parse_matrix
from normalize_device_diagnostics import FULL, normalize

MAX_REPORTS = 32


def aula_observation(text: str, stamp: datetime) -> dict | None:
    """Separate the last successful reading from a current verified reply."""
    if '[AULA L99 last measurement]' not in text.splitlines():
        return None
    sample = parse_summary(text)
    for time in (sample.last_read, sample.last_good_at):
        if time is not None and time > stamp:
            raise ValueError('future AULA observation')
    if sample.percent is not None and (
            not sample.known or not sample.present or sample.cache_active
            or sample.last_read is None or sample.last_good != sample.percent
            or sample.last_good_at != sample.last_read or sample.failures):
        raise ValueError('inconsistent fresh AULA measurement')
    if (sample.last_good is None) != (sample.last_good_at is None):
        raise ValueError('inconsistent AULA last-good sample')
    if sample.last_read and sample.last_good_at and sample.last_good_at > sample.last_read:
        raise ValueError('future AULA last-good sample')
    if sample.cache_active and (
            not sample.known or not sample.present or sample.percent is not None
            or sample.last_good is None or sample.last_good_at is None
            or sample.last_read is None or not sample.failures
            or not 0 < sample.cache_lifetime <= 24
            or not 0 <= (sample.last_read - sample.last_good_at).total_seconds()
            < sample.cache_lifetime * 3600):
        raise ValueError('inconsistent AULA cache')
    return {'state': 'fresh' if sample.percent is not None else
            'cached' if sample.cache_active else 'unavailable',
            'fresh_percent': sample.percent, 'last_good_percent': sample.last_good,
            'last_good_utc': sample.last_good_at.isoformat() if sample.last_good_at else None,
            'failures': sample.failures, 'receiver_present': sample.present if sample.known else None}


def ready_observation(text: str, normalized: dict) -> dict | None:
    """Require the existing narrow full-matrix validation, not a summary label."""
    if text.splitlines()[0] != FULL:
        return None
    if normalized['active_capture']['outcome'] == 'receiver_absent':
        return {'matrix_field': None, 'ordinary_field': None, 'conflict': False}
    matrix = parse_matrix(text)
    if matrix[0] > datetime.fromisoformat(normalized['snapshot_utc']):
        raise ValueError('matrix timestamp after snapshot')
    ordinary, conflict = disagreement(text, matrix)
    return {'matrix_field': matrix[1], 'ordinary_field': ordinary, 'conflict': conflict}


def snapshot(text: str) -> dict:
    """Project one report without paths, raw bytes, names or inferred identity."""
    text = text.replace('\r\n', '\n').rstrip('\n')
    row = normalize(text)
    stamp = datetime.fromisoformat(row['snapshot_utc'])
    if row['edition'] == 'windows':
        row['aula'] = aula_observation(text, stamp)
        row['ready_clear_unverified'] = ready_observation(text, row)
    else:
        row['aula'] = None
        row['ready_clear_unverified'] = None
    return row


def change(before: dict, after: dict) -> dict:
    """Describe observable states only, never infer physical connection mode."""
    first, second = before['usb']['state'], after['usb']['state']
    a = before['ready_clear_unverified']
    b = after['ready_clear_unverified']
    field = 'NOT_COMPARABLE'
    if a and b and not a['conflict'] and not b['conflict']:
        if a['matrix_field'] is not None and b['matrix_field'] is not None:
            field = 'UNCHANGED' if a['matrix_field'] == b['matrix_field'] else 'CHANGED'
    old_aula, new_aula = before['aula'], after['aula']
    return {'from_utc': before['snapshot_utc'], 'to_utc': after['snapshot_utc'],
            'usb_state_before': first, 'usb_state_after': second,
            'unverified_field_change': field, 'identity_binding': 'NOT_VERIFIED',
            'same_edition': before['edition'] == after['edition'],
            'aula_state_before': old_aula['state'] if old_aula else None,
            'aula_state_after': new_aula['state'] if new_aula else None,
            'active_outcome_before': before['active_capture']['outcome'],
            'active_outcome_after': after['active_capture']['outcome']}


def timeline(reports: list[str]) -> dict:
    """Order distinct capture times and describe adjacent observations."""
    if not 2 <= len(reports) <= MAX_REPORTS:
        raise ValueError('expected two to 32 reports')
    rows = sorted((snapshot(text) for text in reports),
                  key=lambda row: datetime.fromisoformat(row['snapshot_utc']))
    stamps = [datetime.fromisoformat(row['snapshot_utc']) for row in rows]
    if len(set(stamps)) != len(stamps):
        raise ValueError('duplicate capture timestamp')
    return {'format': 'device-diagnostic-timeline-v1',
            'identity_binding': 'NOT_VERIFIED', 'snapshots': rows,
            'transitions': [change(a, b) for a, b in zip(rows, rows[1:])]}


def main(argv: list[str] | None = None) -> int:
    """Print bounded redacted JSON; fail closed without echoing input."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reports', nargs='+', type=Path)
    args = parser.parse_args(argv)
    try:
        if not 2 <= len(args.reports) <= MAX_REPORTS:
            raise ValueError('invalid report count')
        result = timeline([read_report(path) for path in args.reports])
    except (OSError, ValueError, OverflowError, IndexError, TypeError):
        print('ERROR: invalid or unsupported diagnostic timeline', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
