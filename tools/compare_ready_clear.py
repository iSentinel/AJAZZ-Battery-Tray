#!/usr/bin/env python3
"""Compare two complete single-receiver F7 matrices, not battery telemetry."""

import argparse
from datetime import datetime
from pathlib import Path
import re

from compare_apex_reports import SECTION, read_attempts, current_percent

LIMIT = 1024 * 1024
EXPECTED = {(delay, length) for delay in (30, 100, 250)
            for length in (65, 67)}
MARKER = re.compile(r"^UTC: (.+)$", re.MULTILINE)


def ready_clear(data):
    """Mirror the narrow Windows display-only field predicate."""
    if (len(data) >= 10 and data[0] == 5 and data[7] == 2
            and data[1] == 0 and data[4] <= 1 and data[5] == 0
            and data[6] == 1 and data[9] == 0 and 1 <= data[3] <= 100):
        return data[3]
    return None


def parse_matrix(text):
    """Require a completed, consistent, rev 0002, 65-byte descriptor matrix."""
    if text.count(SECTION) != 1:
        raise ValueError("Expected one fresh full matrix")
    before, section = text.split(SECTION, 1)
    stamps = MARKER.findall(before)
    if len(stamps) != 1:
        raise ValueError("Expected one capture UTC marker")
    stamp = datetime.fromisoformat(stamps[0].strip())
    if stamp.utcoffset() is None:
        raise ValueError("Capture timestamp needs timezone")
    lines = [line.strip() for line in section.splitlines()]
    identity = ["Matching MI_02 paths: 1", "[Receiver #1]",
                "Interface: 3151:5007 MI_02 COL--",
                "USB revision: 0x0002", "Feature report size: 65",
                "Usage: FFFF:0002; input=0; output=0"]
    if any(lines.count(marker) != 1 for marker in identity):
        return stamp, None
    if sum(line.startswith("[Receiver #") for line in lines) != 1:
        return stamp, None
    entries = collect_attempts(text)
    if set(entries) != EXPECTED or any(v is None for v in entries.values()):
        return stamp, None
    if lines.count("Matrix result: 0/6 valid replies; first valid=unavailable") != 1:
        return stamp, None
    levels = {ready_clear(value) for value in entries.values()}
    if len(levels) != 1 or None in levels:
        return stamp, None
    if any(current_percent(value) is not None for value in entries.values()):
        return stamp, None
    return stamp, levels.pop()


def collect_attempts(text):
    """Reject repeated attempts, orphan responses and duplicate responses."""
    entries = {}
    active = None
    for receiver, delay, length, data in read_attempts(text):
        key = (delay, length)
        if receiver != "1" or key not in EXPECTED:
            raise ValueError("Unexpected receiver or matrix key")
        if data is None:
            if key in entries:
                raise ValueError("Duplicate attempt")
            entries[key] = None
            active = key
        else:
            if active != key or entries[key] is not None:
                raise ValueError("Duplicate or orphan response")
            entries[key] = data
    return entries


def read_report(path):
    """Read bounded local data only."""
    with path.open("rb") as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError("Report exceeds one MiB")
    return parse_matrix(raw.decode("utf-8-sig"))


def compare(first, second):
    """A change in the field is an observation, never a validated percentage."""
    if first[0] >= second[0]:
        raise ValueError("Reports must have distinct chronological timestamps")
    if first[1] is None or second[1] is None:
        return "INCONCLUSIVE"
    return "CHANGED FIELD" if first[1] != second[1] else "UNCHANGED FIELD"


def main(argv=None):
    """0 = complete comparison, 2 = inconclusive, 1 = invalid input."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--earlier", type=Path, required=True)
    parser.add_argument("--later", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        first, second = read_report(args.earlier), read_report(args.later)
        result = compare(first, second)
    except (OSError, ValueError) as error:
        print(f"FAIL: {error}")
        return 1
    for label, (stamp, field) in (("Earlier", first), ("Later", second)):
        value = field if field is not None else "unavailable"
        print(f"{label}: {stamp.isoformat()} unverified field={value}")
    print(f"SUMMARY: {result}")
    print("Not telemetry. Same physical device and vendor gauge require owner evidence.")
    return 2 if result == "INCONCLUSIVE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
