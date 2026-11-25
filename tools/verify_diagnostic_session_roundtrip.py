#!/usr/bin/env python3
"""Verify the synthetic native C# exporter roundtrip; not hardware acceptance."""

import argparse
from pathlib import Path
import sys
import zipfile
import zlib

from compare_diagnostic_timeline import timeline
from read_diagnostic_session import load_session


def verify(path: Path) -> None:
    """Check the exact synthetic marker, state, and source expectations."""
    entries = load_session(path)
    result = timeline([text for text, _ in entries], [entry for _, entry in entries])
    first, second = result['snapshots']
    if (result['identity_binding'] != 'NOT_VERIFIED'
            or first['owner_annotation']['marker'] != 'Baseline'
            or second['owner_annotation']['marker'] != 'BluetoothSelected'
            or first['usb']['state'] != 'unknown' or second['usb']['state'] != 'unavailable'
            or first['aula']['state'] != 'not_checked'
            or second['aula']['fresh_percent'] != 62
            or first['manual_gatt']['last_direct'] is not None
            or second['manual_gatt']['last_direct']['percent'] != 83
            or any(row['usb']['percent'] is not None for row in (first, second))):
        raise ValueError('synthetic fixture expectations differ')


def main(argv: list[str] | None = None) -> int:
    """Fail closed without exposing archive text or path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args(argv)
    try:
        verify(args.archive)
    except (OSError, ValueError, TypeError, KeyError, IndexError,
            zipfile.BadZipFile, zlib.error, RuntimeError, NotImplementedError):
        print('FAIL: diagnostic session roundtrip', file=sys.stderr)
        return 2
    print('PASS: native diagnostic session roundtrip (synthetic)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
