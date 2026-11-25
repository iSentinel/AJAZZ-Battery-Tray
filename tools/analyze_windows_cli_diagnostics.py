#!/usr/bin/env python3
"""Summarize bounded Windows CLI diagnostic logs locally without raw payloads."""

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import re
import sys

from compare_diagnostic_timeline import gate_sequences
from compare_get_ids import MODE, parse, summarize
from compare_windows_hid_logs import classify, parse_log

LIMIT = 1024 * 1024
BEGIN = re.compile(r'BEGIN: UTC=(\S+) timeout=(\d+)s')


def read_local(path: Path) -> str:
    """Read bounded UTF-8 text from a local regular file."""
    if path.is_symlink() or not path.is_file():
        raise ValueError('expected local regular file')
    with path.open('rb') as stream:
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError('log exceeds size limit')
    return data.decode('utf-8-sig')


def framing(text: str) -> tuple[list[str], str]:
    """Require a single first capture marker and timezone-aware timestamp."""
    text = text.replace('\r\n', '\n').rstrip('\n')
    if '\r' in text or '\x00' in text or len(text.encode()) > LIMIT:
        raise ValueError('invalid log framing')
    lines = text.splitlines()
    if not lines or sum(line.startswith('BEGIN:') for line in lines) != 1:
        raise ValueError('missing or duplicate begin')
    match = BEGIN.fullmatch(lines[0])
    if not match or not 3 <= int(match[2]) <= 90:
        raise ValueError('invalid begin')
    stamp = datetime.fromisoformat(match[1])
    if stamp.utcoffset() is None:
        raise ValueError('missing timezone')
    return lines, stamp.isoformat()


def experiment(lines: list[str]) -> dict:
    """Compare only paired status prefixes without returning raw bytes."""
    entries = parse('\n'.join(lines))
    rows = summarize(entries) if entries is not None else []
    counts = Counter(row[-1] for row in rows)
    return {'mode': 'experimental_get_ids',
            'outcome': 'complete' if rows and not counts['INCOMPLETE']
            else 'inconclusive', 'pair_counts': dict(sorted(counts.items())),
            'reported_percent': None}


def ordinary(lines: list[str]) -> dict:
    """Preserve ordinary worker outcome and exclude gates from failed captures."""
    terminal = [line for line in lines if line.startswith(('END:', 'TIMEOUT:'))]
    if len(terminal) != 1 or lines[-1] != terminal[0]:
        raise ValueError('missing, duplicate or displaced terminal marker')
    if sum(line.startswith('PASS:') for line in lines) > 1:
        raise ValueError('duplicate success marker')
    capture = parse_log('\n'.join(lines))
    status, _ = classify(capture)
    completed = capture.ended in (0, 2) and not capture.timed_out
    if completed and lines[-1] != f'END: worker exited {capture.ended}':
        raise ValueError('invalid terminal marker')
    gates = gate_sequences('\n'.join(lines) if completed else '', False)
    if sum(gates['reported_gate_counts'].values()) > capture.get_ok:
        raise ValueError('more classifications than successful GET operations')
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
