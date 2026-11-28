#!/usr/bin/env python3
"""Summarize one redacted AJAZZ GET-ID experiment; never infer battery."""
import argparse
import re
import sys
from pathlib import Path

from compare_windows_hid_logs import parse_begin
from run_offline_qa import read_evidence

PAIR = re.compile(r"PAIR: delay=(30|100|250)ms length=([0-9]{2,3}) request=(05|00)")
OBSERVED = re.compile(
    r"OBSERVED: request=(05|00) returned=([0-9A-F]{2}) "
    r"length=([0-9]{2,3}) delay=(30|100|250)ms status10=([0-9A-F]{20}); "
    r"existing-parser candidate=(unavailable|[0-9]{1,3}) \(not telemetry\)"
)
MODE = "MODE: experimental GET 05 versus GET 00; no battery claimed"
END = "END: worker exited 2"
OUTCOME = "INCONCLUSIVE: experimental GET ID comparison; no battery claimed"
LIMIT = 1024 * 1024
ProbeKey = tuple[int, int, str]
Observation = tuple[str, str] | None
ProbeEntries = dict[ProbeKey, Observation]


def validate_session(lines: list[str]) -> bool:
    """Validate experimental framing before interpreting probe observations."""
    if not lines or sum(line.startswith("BEGIN:") for line in lines) != 1:
        raise ValueError("Expected one GET-ID diagnostic session")
    parse_begin(lines[0])
    if [line for line in lines if line.startswith("MODE:")] != [MODE]:
        raise ValueError("Missing or ambiguous experimental mode")
    terminal = [line for line in lines if line.startswith(("END:", "TIMEOUT:"))]
    if len(terminal) != 1 or terminal[0] != lines[-1]:
        raise ValueError("Missing or ambiguous experimental terminal marker")
    if any(line.startswith(("PASS:", "FAIL:")) for line in lines):
        raise ValueError("Unexpected success or failure marker")
    outcomes = [line for line in lines if line.startswith("INCONCLUSIVE:")]
    if terminal[0].startswith("TIMEOUT:"):
        if outcomes not in ([], [OUTCOME]):
            raise ValueError("Ambiguous experimental timeout outcome")
        return False
    if terminal[0] != END or outcomes != [OUTCOME] or lines[-2] != OUTCOME:
        raise ValueError("Missing or inconsistent experimental worker outcome")
    if sum(line.startswith("STEP: found ") for line in lines) > 1:
        raise ValueError("Duplicate experimental enumeration")
    return True


def parse(data: str) -> ProbeEntries | None:
    """Read pair markers and observations for exactly one receiver."""
    lines = data.splitlines()
    if not validate_session(lines):
        return None
    if lines.count("STEP: found 1 matching MI_02 paths") != 1 or [
            line for line in lines
            if line.startswith("STEP: experimental receiver #")
    ] != ["STEP: experimental receiver #1"]:
        return None
    validate_probe_scope(lines)
    return parse_pairs(lines)


def validate_probe_scope(lines: list[str]) -> None:
    """Require probes to follow the single enumerated receiver marker."""
    mode = lines.index(MODE)
    count = lines.index("STEP: found 1 matching MI_02 paths")
    receiver = lines.index("STEP: experimental receiver #1")
    if not mode < count < receiver:
        raise ValueError("Invalid experimental receiver order")
    if any(line.startswith(("PAIR:", "OBSERVED:")) for line in lines[:receiver]):
        raise ValueError("Probe precedes experimental receiver")


def validate_matrix_order(entries: ProbeEntries) -> None:
    """Mirror the descriptor-first native matrix, without assuming its length."""
    lengths = list(dict.fromkeys(key[1] for key in entries))
    native = list(dict.fromkeys((lengths[0], 65, 67)))
    expected = [(delay, length, report) for delay in (30, 100, 250)
                for length in native for report in ("05", "00")]
    if list(entries) != expected:
        raise ValueError("Unexpected experimental matrix order")


def parse_pairs(lines: list[str]) -> ProbeEntries | None:
    """Require unique pair keys and consistent observation association."""
    entries = {}
    current = None
    for line in lines:
        if match := PAIR.fullmatch(line):
            current = (int(match[1]), int(match[2]), match[3])
            if current in entries or not 65 <= current[1] <= 256:
                raise ValueError("Duplicate or invalid probe")
            entries[current] = None
        elif match := OBSERVED.fullmatch(line):
            key = (int(match[4]), int(match[3]), match[1])
            prefix, candidate = match[5], match[6]
            if (key != current or key not in entries or
                    entries[key] is not None or prefix[:2] != match[2] or
                    (candidate != "unavailable" and
                     not 1 <= int(candidate) <= 100)):
                raise ValueError("Inconsistent observation")
            entries[key] = (prefix, candidate)
        elif line.startswith(("PAIR:", "OBSERVED:")):
            raise ValueError("Malformed experimental marker")
    lengths = {key[1] for key in entries}
    expected = {(delay, length, report)
                for delay in (30, 100, 250)
                for length in lengths for report in ("05", "00")}
    if not {65, 67} <= lengths or len(lengths) > 3 or set(entries) != expected:
        return None
    validate_matrix_order(entries)
    return entries


def summarize(entries: ProbeEntries) -> list[tuple[int, int, Observation, Observation, str]]:
    """Compare returned status fields without normalizing or decoding IDs."""
    rows = []
    for delay, length in sorted({key[:2] for key in entries}):
        a, b = (entries[(delay, length, report)] for report in ("05", "00"))
        if a is None or b is None:
            state = "INCOMPLETE"
        elif a[0][2:] == b[0][2:]:
            state = "SAME STATUS BYTES"
        else:
            state = "DIFFERENT STATUS BYTES"
        rows.append((delay, length, a, b, state))
    return rows


def main(argv: list[str] | None = None) -> int:
    """Return 0 for complete observations, 2 for incomplete, 1 for invalid."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        entries = parse(read_evidence(args.log, LIMIT).decode("utf-8-sig"))
    except (OSError, ValueError) as error:
        print(f"FAIL: invalid GET-ID diagnostic ({type(error).__name__})", file=sys.stderr)
        return 1
    if entries is None:
        print("INCONCLUSIVE: no complete single-receiver experiment")
        return 2
    complete = 0
    for delay, length, a, b, state in summarize(entries):
        complete += int(a is not None and b is not None)
        print(f"{delay}ms {length}B: 05={a or 'no observation'} "
              f"00={b or 'no observation'} — {state}")
    total = len(entries) // 2
    print(f"Observed pairs: {complete}/{total}; candidates are not telemetry")
    print("Compare separate vendor-display evidence before protocol changes.")
    return 0 if complete == total else 2


if __name__ == "__main__":
    sys.exit(main())
