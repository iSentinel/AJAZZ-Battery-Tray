#!/usr/bin/env python3
"""Compare two complete single-receiver F7 matrices, not battery telemetry."""

import argparse
from datetime import datetime
from pathlib import Path
import re

from compare_apex_reports import SECTION, current_percent

LIMIT = 1024 * 1024
Matrix = tuple[datetime, int | None]
Report = tuple[Matrix, int | None, bool]
ProbeEntries = dict[tuple[int, int], bytes | None]
EXPECTED = {(delay, length) for delay in (30, 100, 250)
            for length in (65, 67)}
MARKER = re.compile(r"^UTC: (.+)$", re.MULTILINE)
TX = re.compile(r"Attempt UTC=(.+); delay=(30|100|250)ms; TX\[(65|67)\]=([0-9A-F]+)")
GET = re.compile(r"GET request buffer\[(65|67)\]=([0-9A-F]+)")
RX = re.compile(r"RX buffer\[(65|67)\]=([0-9A-F]+)")
SUCCESS = re.compile(r"SET F7 / GET 05 \((65|67) bytes\): OK; header=([0-9A-F]{8}); no valid battery")


def ready_clear(data: bytes | bytearray) -> int | None:
    """Mirror the narrow Windows display-only field predicate."""
    if (len(data) >= 10 and data[0] == 5 and data[7] == 2
            and data[1] == 0 and data[4] <= 1 and data[5] == 0
            and data[6] == 1 and data[9] == 0 and 1 <= data[3] <= 100):
        return data[3]
    return None


def parse_matrix(text: str) -> Matrix:
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


def parse_probe(lines: list[str], length: int) -> bytes | None:
    """Require the exact GET buffer, successful chain and response in order."""
    relevant = [line for line in lines if line.startswith(
        ("GET request buffer", "SET F7 / GET", "RX buffer"))]
    if len(relevant) < 3:
        return None
    if len(relevant) != 3:
        raise ValueError("Duplicate probe evidence")
    request = GET.fullmatch(relevant[0])
    success = SUCCESS.fullmatch(relevant[1])
    response = RX.fullmatch(relevant[2])
    if not request or not success or not response:
        return None
    if any(int(marker[1]) != length for marker in (request, success, response)):
        raise ValueError("Probe length mismatch")
    if bytes.fromhex(request[2]) != bytes([5]).ljust(length, bytes(1)):
        raise ValueError("Unexpected GET request buffer")
    data = bytes.fromhex(response[2])
    if len(data) != length or data[:4].hex().upper() != success[2]:
        raise ValueError("Response length/header mismatch")
    return data


def collect_attempts(text: str) -> ProbeEntries:
    """Reject orphan evidence, duplicate probes and non-F7 requests."""
    entries = {}
    active = None
    block = []
    for line in text.split(SECTION, 1)[1].splitlines():
        line = line.strip()
        if line.startswith("Attempt UTC="):
            if active is not None:
                entries[active] = parse_probe(block, active[1])
            match = TX.fullmatch(line)
            if not match:
                raise ValueError("Malformed attempt marker")
            timestamp = datetime.fromisoformat(match[1])
            if timestamp.utcoffset() is None:
                raise ValueError("Attempt timestamp needs timezone")
            active = (int(match[2]), int(match[3]))
            if active not in EXPECTED or active in entries:
                raise ValueError("Duplicate or invalid attempt")
            if bytes.fromhex(match[4]) != bytes([0, 247]).ljust(active[1], bytes(1)):
                raise ValueError("Unexpected SET request buffer")
            entries[active] = None
            block = []
        elif active is not None:
            block.append(line)
        elif line.startswith(("GET request buffer", "SET F7 / GET", "RX buffer")):
            raise ValueError("Orphan probe evidence")
    if active is not None:
        entries[active] = parse_probe(block, active[1])
    return entries


def ordinary_field(text: str) -> int | None:
    """Read only the ordinary summary; never treat its field as fresh capture."""
    heading = "[AJAZZ last ordinary poll — not a fresh request]"
    end = "[Independent AJAZZ receivers]"
    if text.count(heading) != 1 or text.count(end) != 1:
        return None
    block = text.split(heading, 1)[1].split(end, 1)[0]
    lines = [line.strip() for line in block.splitlines()]
    if any(lines.count(marker) != 1 for marker in (
            "Receiver present: True; presence known: True",
            "Matching MI_02 paths: 1", "USB revision: 0x0002",
            "Interface: 3151:5007 MI_02 COL--", "Feature report size: 65")):
        return None
    if not any(line.startswith("Battery: unavailable;") for line in lines):
        return None
    values = [line.rsplit("=", 1)[1] for line in lines
              if line.startswith("unverified mouse field (not telemetry)=")]
    if len(values) != 1 or not values[0].isdigit():
        return None
    value = int(values[0])
    if not 1 <= value <= 100:
        return None
    headers = [SUCCESS.fullmatch(line) for line in lines
               if line.startswith("SET F7 / GET")]
    if (len(headers) != 2 or any(match is None for match in headers)
            or {int(match[1]) for match in headers} != {65, 67}
            or any(match[2] != f"050000{value:02X}" for match in headers)):
        return None
    return value


def disagreement(text: str, matrix: Matrix) -> tuple[int | None, bool]:
    """Keep ordinary and full-capture observations independent."""
    ordinary = ordinary_field(text)
    return ordinary, matrix[1] is not None and ordinary is not None and ordinary != matrix[1]


def read_report(path: Path) -> Report:
    """Read bounded local data only."""
    with path.open("rb") as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError("Report exceeds one MiB")
    text = raw.decode("utf-8-sig")
    matrix = parse_matrix(text)
    ordinary, conflict = disagreement(text, matrix)
    return matrix, ordinary, conflict


def compare(first: Matrix, second: Matrix) -> str:
    """A change in the field is an observation, never a validated percentage."""
    if first[0] >= second[0]:
        raise ValueError("Reports must have distinct chronological timestamps")
    if first[1] is None or second[1] is None:
        return "INCONCLUSIVE"
    return "CHANGED FIELD" if first[1] != second[1] else "UNCHANGED FIELD"


def main(argv: list[str] | None = None) -> int:
    """0 = complete comparison, 2 = inconclusive, 1 = invalid input."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--earlier", type=Path, required=True)
    parser.add_argument("--later", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        first, ordinary_a, conflict_a = read_report(args.earlier)
        second, ordinary_b, conflict_b = read_report(args.later)
        result = compare(first, second)
    except (OSError, ValueError) as error:
        print(f"FAIL: {error}")
        return 1
    for label, (stamp, field) in (("Earlier", first), ("Later", second)):
        value = field if field is not None else "unavailable"
        print(f"{label}: {stamp.isoformat()} unverified field={value}")
    for label, ordinary, conflict in (("Earlier", ordinary_a, conflict_a),
                                      ("Later", ordinary_b, conflict_b)):
        if ordinary is not None:
            print(f"{label} prior ordinary field={ordinary} (not telemetry)")
        if conflict:
            print(f"WARNING: {label} ordinary/full field disagreement")
    if conflict_a or conflict_b:
        print(f"Full matrix comparison: {result}")
        result = "INCONCLUSIVE"
    print(f"SUMMARY: {result}")
    print("Not telemetry. Same physical device and vendor gauge require owner evidence.")
    return 2 if result == "INCONCLUSIVE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
