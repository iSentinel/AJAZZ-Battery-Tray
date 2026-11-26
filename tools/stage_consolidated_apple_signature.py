#!/usr/bin/env python3
"""Stage original Apple archives for native signature observation, without execution."""

import argparse
from pathlib import Path
import sys
import zipfile

from build_consolidated_apple_notices import PINS
from verify_apple_resource_seal import report
from verify_hardware_acceptance import APPLE_NAMES, apple, members
from verify_windows_notice_transport import digest
from verify_windowsdesktop_provenance import read_local


def collect(raw: bytes, edition: str) -> bytes:
    """Bind the original CI envelope, app archive and ad-hoc integrity."""
    outer, inner = PINS[edition]
    if digest(raw) != outer:
        raise ValueError('original Apple CI archive differs')
    if apple(raw, edition)['inner_archive_sha256'] != inner:
        raise ValueError('original inner archive differs')
    base = APPLE_NAMES[edition]
    payload = members(raw, {base + '.zip', base + '.sha256'})[base + '.zip']
    if digest(payload) != inner:
        raise ValueError('extracted inner archive differs')
    report(payload, edition)
    return payload


def main(argv: list[str] | None = None) -> int:
    """Write only a fresh verified app ZIP; never extract or execute it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--edition', choices=PINS, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        raw = collect(read_local(args.archive), args.edition)
        with args.output.open('xb') as stream:
            stream.write(raw)
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile):
        print('FAIL: exact Apple signature input', file=sys.stderr)
        return 2
    print('PASS: original Apple archive staged; native trust not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
