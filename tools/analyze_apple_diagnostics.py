#!/usr/bin/env python3
"""Normalize redacted macOS menu snapshots without exporting vendor trace bytes."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

from run_offline_qa import read_evidence

MAX_SIZE = 65536
TRACE = '\n\nFresh bounded F7/05 trace:\n'
SCHEMA = 'Report schema: apple-menu-v1'
HEADERS = {
    'AJAZZ Battery Tray diagnostic report': 'universal',
    'AJAZZ Battery Tray High Sierra Edition': 'high-sierra',
}
STATES = {
    'battery': 'valid', 'valid': 'valid', 'absent': 'absent',
    'not connected': 'absent', 'unavailable': 'unavailable',
    'receiver present, no valid battery': 'unavailable',
    'unknown': 'unknown', 'access error': 'unknown',
    'timeout': 'timeout', 'HID read stalled': 'timeout',
    'unsupported': 'unsupported', 'HID usage mismatch': 'unsupported',
    'not checked yet': 'not_checked',
}
GATT_FAILURES = {
    'timeout', 'connection failed', 'service unavailable',
    'characteristic unavailable', 'invalid reply', 'disconnected',
    'access unavailable', 'service discovery failed',
    'characteristic discovery failed',
}


def field(lines: list[str], prefix: str) -> str:
    """Require one unambiguous field in the passive section."""
    matches = [line[len(prefix):] for line in lines if line.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError('missing or duplicate snapshot field')
    return matches[0]


def utc(value: str) -> str:
    """Require an ISO-8601 UTC timestamp, not a local or relative time."""
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)', value):
        raise ValueError('invalid UTC timestamp')
    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return stamp.astimezone(timezone.utc).isoformat()


def level(value: str, minimum: int) -> int | None:
    """Preserve unknown and distinguish USB and Bluetooth valid ranges."""
    if value == 'unknown':
        return None
    if not re.fullmatch(r'(?:0|[1-9]\d{0,2})%', value):
        raise ValueError('invalid battery field')
    number = int(value[:-1])
    if not minimum <= number <= 100:
        raise ValueError('battery out of range')
    return number


def reported_age(percent: int | None, measured: str | None, snapshot: str) -> dict:
    """Classify reported age at capture time, never at import time."""
    if percent is None:
        status = 'NO_REPORTED_PERCENT'
    elif measured is None:
        status = 'MISSING_TIMESTAMP'
    else:
        seconds = (datetime.fromisoformat(snapshot) -
                   datetime.fromisoformat(measured)).total_seconds()
        if seconds < 0:
            status = 'FUTURE_TIMESTAMP'
        elif seconds > 300:
            status = 'EXPIRED'
        elif seconds == 300:
            # Native exports truncate timestamps to seconds. The exact
            # five-minute boundary cannot be reconstructed from them.
            status = 'BOUNDARY_UNCERTAIN'
        else:
            status = 'WITHIN_REPORTED_WINDOW'
    return {'freshness_at_snapshot': status,
            'reported_age_eligible_percent': (
                percent if status == 'WITHIN_REPORTED_WINDOW' else None)}


def usb(lines: list[str], edition: str, snapshot: str) -> dict:
    """Normalize ordinary session observation, never the active trace."""
    prefix = 'Last ordinary status: ' if edition == 'universal' else 'Battery state: '
    status, sep, value = field(lines, prefix).partition('; battery: ')
    if not sep or status not in STATES:
        raise ValueError('invalid USB state')
    normalized = STATES[status]
    percent = level(value, 1)
    if (normalized == 'valid') != (percent is not None):
        raise ValueError('inconsistent USB observation')
    last = field(lines, 'Last verified USB UTC (session): ')
    measured = None if last == 'never' else utc(last)
    return {'state': normalized, 'percent': percent,
            'last_verified_utc': measured,
            **reported_age(percent, measured, snapshot)}


def gatt(lines: list[str]) -> dict:
    """Normalize historical manual GATT observation without identity."""
    pending = field(lines, 'Bluetooth manual 180F/2A19 pending: ').lower()
    if pending not in ('true', 'false'):
        raise ValueError('invalid GATT pending flag')
    reading = field(lines, 'Bluetooth last manual read: ')
    result = {'pending': pending == 'true', 'outcome': 'not requested',
              'percent': None, 'utc': None, 'elapsed_ms': None}
    if reading == 'not requested':
        return result
    match = re.fullmatch(r'outcome=([^;]+); battery=([^;]+); UTC=([^;]+); elapsed_ms=(\d{1,10})', reading)
    if not match:
        raise ValueError('malformed manual GATT observation')
    outcome, value, stamp, duration = match.groups()
    percent = level(value, 0)
    if outcome not in GATT_FAILURES | {'fresh GATT'} or (
            (outcome == 'fresh GATT') != (percent is not None)):
        raise ValueError('inconsistent manual GATT observation')
    result.update(outcome=outcome, percent=percent, utc=utc(stamp),
                  elapsed_ms=int(duration))
    return result


def parse(text: str) -> dict:
    """Accept one versioned report; never return the raw active trace."""
    text = text.replace('\r\n', '\n').rstrip('\n')
    if '\r' in text or '\x00' in text or text.count(TRACE) > 1:
        raise ValueError('invalid report framing')
    snapshot, marker, _ = text.partition(TRACE)
    lines = snapshot.splitlines()
    if not lines or len(lines) > 32 or lines[0] not in HEADERS:
        raise ValueError('unsupported report title')
    if field(lines, 'Report schema: ') != SCHEMA.removeprefix('Report schema: '):
        raise ValueError('unsupported schema')
    if sum(line in HEADERS for line in text.splitlines()) != 1:
        raise ValueError('multiple report titles')
    edition = HEADERS[lines[0]]
    expected = ('VID:PID: 3151:5007; usage FFFF:0002' if edition == 'universal'
                else 'VID:PID: 3151:5007')
    if lines.count(expected) != 1 or (
            edition == 'high-sierra' and lines.count('Usage: FFFF:0002') != 1):
        raise ValueError('unexpected HID scope')
    stamp = utc(field(lines, 'UTC: '))
    return {'schema': 'apple-menu-v1', 'edition': edition,
            'snapshot_utc': stamp, 'usb': usb(lines, edition, stamp),
            'manual_gatt': gatt(lines), 'active_trace_present': bool(marker),
            'identity_binding': 'NOT_VERIFIED', 'simultaneous': 'NOT_VERIFIED'}


def read_report(path: Path) -> str:
    """Read bounded, identity-checked local input without following links."""
    return read_evidence(path, MAX_SIZE).decode('utf-8-sig')


def main(argv: list[str] | None = None) -> int:
    """Print only normalized, allowlisted fields or a generic error."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    args = parser.parse_args(argv)
    try:
        result = parse(read_report(args.report))
    except (OSError, ValueError, OverflowError):
        print('ERROR: invalid or unsupported Apple menu report', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
