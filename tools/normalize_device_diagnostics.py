#!/usr/bin/env python3
"""Normalize local Apple and Windows diagnostic snapshots without raw data."""

import argparse
import json
from pathlib import Path
import re
import sys

from analyze_apple_diagnostics import HEADERS, MAX_SIZE, field, level, parse, utc
from compare_apex_reports import read_report

WINDOWS = 'AJAZZ Battery Tray extended diagnostic report'
FULL = 'AJAZZ APEX full comparison report (one capture)'
ORDINARY = '[AJAZZ last ordinary poll — not a fresh request]'
MANUAL = '[Bluetooth manual inspection — historical, not a fresh request]'
NOT_OPEN = '[Bluetooth manual inspection — historical] Not opened this session.'
MATRIX = '[Fresh APEX protocol matrix — full vendor buffers]'


def windows_utc(value: str) -> str | None:
    """Accept .NET UTC precision, truncating the seventh fractional digit."""
    if value == 'never':
        return None
    value = re.sub(r'(\.\d{6})\d(?=Z$|\+00:00$)', r'\1', value)
    return utc(value)


def windows_level(value: str, minimum: int) -> int | None:
    """Decode only an explicit percentage, not the unverified vendor field."""
    return level('unknown' if value == 'unavailable' else value + '%', minimum)


def windows_usb(lines: list[str]) -> dict:
    """Read the three fixed ordinary-poll fields, never the fresh matrix."""
    if lines.count(ORDINARY) != 1:
        raise ValueError('missing or duplicate ordinary poll')
    offset = lines.index(ORDINARY)
    block = lines[offset + 1:offset + 4]
    if len(block) != 3 or not block[0].startswith('Completed UTC: '):
        raise ValueError('invalid ordinary poll layout')
    presence = re.fullmatch(r'Receiver present: (True|False|unknown); presence known: (True|False|unknown)', block[1])
    battery = re.fullmatch(r'Battery: (unavailable|\d+); status: .+', block[2])
    if not presence or not battery:
        raise ValueError('invalid ordinary poll fields')
    stamp = windows_utc(block[0].removeprefix('Completed UTC: '))
    percent = windows_level(battery[1], 1)
    known = presence[2] == 'True'
    present = presence[1] == 'True' if known else None
    if (known and presence[1] == 'unknown') or (
            percent is not None and (present is not True or stamp is None)):
        raise ValueError('inconsistent ordinary poll')
    state = ('valid' if percent is not None else 'unavailable' if present is True
             else 'absent' if present is False else 'unknown')
    return {'state': state, 'percent': percent, 'completed_utc': stamp,
            'receiver_present': present}


def manual_observation(value: str) -> dict | None:
    """Keep historical typed source separate from the last direct GATT."""
    if value == 'never':
        return None
    match = re.fullmatch(r'[^;]+; transport=(BLE|Classic); battery=(unavailable|\d+); source=(Unavailable|DirectGatt|WindowsCached); completed UTC=([^;]+); historical=true', value)
    if not match:
        raise ValueError('invalid manual observation')
    transport, battery, source, stamp = match.groups()
    percent = windows_level(battery, 0)
    completed = windows_utc(stamp)
    if (completed is None or (source == 'Unavailable') != (percent is None)
            or (source == 'DirectGatt' and transport != 'BLE')):
        raise ValueError('inconsistent manual observation')
    return {'transport': transport, 'source': source, 'percent': percent,
            'completed_utc': completed}


def windows_gatt(lines: list[str]) -> dict:
    """Parse one historical inspector section or explicit not-open state."""
    if lines.count(NOT_OPEN) == 1 and MANUAL not in lines:
        return {'pending': None, 'last_manual': None, 'last_direct': None}
    if lines.count(MANUAL) != 1 or NOT_OPEN in lines:
        raise ValueError('missing or duplicate manual inspector')
    block = lines[lines.index(MANUAL) + 1:]
    pending = field(block, 'Manual operation pending: ')
    if pending not in ('True', 'False'):
        raise ValueError('invalid manual pending')
    manual = manual_observation(field(block, 'Last manual result: '))
    direct = manual_observation(field(block, 'Last direct GATT result: '))
    if direct is not None and direct['source'] != 'DirectGatt':
        raise ValueError('direct GATT section has non-direct source')
    return {'pending': pending == 'True', 'last_manual': manual,
            'last_direct': direct}


def parse_windows(text: str) -> dict:
    """Accept one known extended or full Windows report, never raw buffers."""
    lines = text.splitlines()
    if (lines[0] not in (WINDOWS, FULL) or lines.count(WINDOWS) != 1
            or lines.count(FULL) != int(lines[0] == FULL)
            or any(line in HEADERS for line in lines) or lines.count(MATRIX) > 1):
        raise ValueError('invalid Windows report framing')
    start = lines.index(WINDOWS)
    stop = lines.index(MATRIX) if MATRIX in lines else len(lines)
    if not start < stop or (lines[0] == FULL) != (MATRIX in lines):
        raise ValueError('inconsistent full capture framing')
    block = lines[start:stop]
    schema = [line for line in block if line.startswith('Report schema: ')]
    if schema not in ([], ['Report schema: windows-extended-v1']):
        raise ValueError('unsupported Windows schema')
    stamp = windows_utc(field(block, 'Report UTC: '))
    if stamp is None:
        raise ValueError('missing report UTC')
    return {'schema': 'windows-extended-v1' if schema else 'windows-extended-legacy',
            'edition': 'windows', 'snapshot_utc': stamp, 'usb': windows_usb(block),
            'manual_gatt': windows_gatt(block), 'active_trace_present': MATRIX in lines,
            'identity_binding': 'NOT_VERIFIED', 'simultaneous': 'NOT_VERIFIED'}


def normalize(text: str) -> dict:
    """Dispatch by exact report title and emit a common evidence envelope."""
    text = text.replace('\r\n', '\n').rstrip('\n')
    if not text or '\r' in text or '\x00' in text:
        raise ValueError('invalid report framing')
    title = text.split('\n', 1)[0]
    if title in HEADERS:
        if len(text.encode('utf-8')) > MAX_SIZE:
            raise ValueError('Apple report exceeds size budget')
        result = parse(text)
    else:
        result = parse_windows(text)
    return {'format': 'device-diagnostics-summary-v1', **result}


def main(argv: list[str] | None = None) -> int:
    """Normalize one local file without publishing identifiers or raw trace."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    args = parser.parse_args(argv)
    try:
        result = normalize(read_report(args.report))
    except (OSError, ValueError, OverflowError, IndexError):
        print('ERROR: invalid or unsupported diagnostic report', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
