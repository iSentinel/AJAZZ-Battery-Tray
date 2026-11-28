#!/usr/bin/env python3
"""Summarize bounded Windows CLI diagnostic logs locally without raw payloads."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from compare_diagnostic_timeline import gate_sequences
from compare_get_ids import MODE, parse, summarize
from compare_windows_hid_logs import Capture, classify, parse_begin, parse_log
from run_offline_qa import read_evidence

LIMIT = 1024 * 1024


def read_local(path: Path) -> str:
    """Read bounded UTF-8 text from a local regular file."""
    return read_evidence(path, LIMIT).decode('utf-8-sig')


def framing(text: str) -> tuple[list[str], str]:
    """Require a single first capture marker and timezone-aware timestamp."""
    text = text.replace('\r\n', '\n').rstrip('\n')
    if '\r' in text or '\x00' in text or len(text.encode()) > LIMIT:
        raise ValueError('invalid log framing')
    lines = text.splitlines()
    if not lines or sum(line.startswith('BEGIN:') for line in lines) != 1:
        raise ValueError('missing or duplicate begin')
    stamp, _ = parse_begin(lines[0])
    return lines, stamp.isoformat()


def terminal_marker(lines: list[str]) -> str:
    """Require one terminal marker and exclude contradictory worker outcomes."""
    terminal = [line for line in lines if line.startswith(('END:', 'TIMEOUT:'))]
    if len(terminal) != 1 or lines[-1] != terminal[0]:
        raise ValueError('missing, duplicate or displaced terminal marker')
    if terminal[0].startswith('TIMEOUT:'):
        if any(line.startswith('PASS:') for line in lines):
            raise ValueError('timeout contradicts success')
    return terminal[0]


def experiment(lines: list[str]) -> dict:
    """Compare only paired status prefixes without returning raw bytes."""
    terminal_marker(lines)
    entries = parse('\n'.join(lines))
    rows = summarize(entries) if entries is not None else []
    counts = Counter(row[-1] for row in rows)
    return {'mode': 'experimental_get_ids',
            'outcome': 'complete' if rows and not counts['INCOMPLETE']
            else 'inconclusive', 'pair_counts': dict(sorted(counts.items())),
            'reported_percent': None}


def validate_completed(lines: list[str], capture: Capture) -> None:
    """Require the emitted terminal summary to agree with the worker result."""
    outcomes = [line for line in lines
                if line.startswith(('PASS:', 'INCONCLUSIVE:', 'FAIL:'))]
    expected = (f'PASS: verified battery {capture.battery}%'
                if capture.ended == 0 else 'INCONCLUSIVE: no verified battery report')
    if outcomes != [expected] or lines[-2] != expected:
        raise ValueError('contradictory or displaced worker outcome')
    if capture.get_ok + capture.get_failed > capture.set_ok:
        raise ValueError('GET count exceeds successful SET count')


def validate_gates(gates: dict, capture: Capture) -> None:
    """Check reported labels without promoting them to independent telemetry."""
    counts = gates['reported_gate_counts']
    total = sum(counts.values())
    if total > capture.get_ok:
        raise ValueError('more classifications than successful GET operations')
    if counts.get('Accepted', 0) and capture.battery is None:
        raise ValueError('accepted classification contradicts missing battery')
    if (capture.battery is not None and total == capture.get_ok
            and not (counts.get('Accepted') or counts.get('Unrecognized'))):
        raise ValueError('reported battery contradicts complete rejection labels')


def ordinary(lines: list[str]) -> dict:
    """Preserve ordinary worker outcome and exclude gates from failed captures."""
    terminal_marker(lines)
    capture = parse_log('\n'.join(lines))
    status, _ = classify(capture)
    completed = capture.ended in (0, 2) and not capture.timed_out
    if completed:
        validate_completed(lines, capture)
    gates = gate_sequences('\n'.join(lines) if completed else '', False)
    validate_gates(gates, capture)
    return {'mode': 'ordinary_f7', 'outcome': status,
            'reported_percent': capture.battery,
            'transport': {'set_ok': capture.set_ok, 'set_failed': capture.set_failed,
                          'get_ok': capture.get_ok, 'get_failed': capture.get_failed},
            'policy_sequences': gates}


def analyze(text: str) -> dict:
    """Return a redacted evidence envelope without physical identity claims."""
    lines, stamp = framing(text)
    result = experiment(lines) if MODE in lines else ordinary(lines)
    return {'format': 'windows-cli-diagnostic-summary-v1', 'capture_utc': stamp,
            'identity_binding': 'NOT_VERIFIED',
            'independent_verification': 'NOT_VERIFIED', **result}


def main(argv: list[str] | None = None) -> int:
    """Emit JSON for supported evidence, or a generic error without input echo."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    args = parser.parse_args(argv)
    try:
        result = analyze(read_local(args.log))
    except (OSError, ValueError, OverflowError):
        print('ERROR: invalid or unsupported CLI diagnostic', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
