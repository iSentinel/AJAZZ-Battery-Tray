#!/usr/bin/env python3
"""Compare two or three bounded Windows HID logs without accessing devices."""

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re

from run_offline_qa import read_evidence

BEGIN = re.compile(
    r"BEGIN: UTC=([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,7})?(?:Z|\+00:00)) timeout=([0-9]{1,2})s"
)
COUNT = re.compile(r"^STEP: found ([0-9]{1,10}) matching MI_02 paths$")
RESULT = re.compile(
    r"^STEP: (SET F7|GET 05) (OK|FAILED) Win32=(-?[0-9]{1,10}) elapsed=([0-9]{1,19})ms$"
)
PASS = re.compile(r"^PASS: verified battery ([0-9]{1,3})%$")
END = re.compile(r"^END: worker exited ([0-9]{1,10})$")


@dataclass(frozen=True)
class Capture:
    """Safe result of one opt-in F7/05 diagnostic invocation."""

    candidates: int | None
    open_ok: int
    open_failed: int
    set_ok: int
    set_failed: int
    get_ok: int
    get_failed: int
    battery: int | None
    timed_out: bool
    ended: int | None
    inconclusive: bool


def parse_begin(line: str) -> tuple[datetime, int]:
    """Parse the native UTC start marker and bounded diagnostic deadline."""
    match = BEGIN.fullmatch(line)
    if not match or not 3 <= int(match[2]) <= 90:
        raise ValueError("invalid diagnostic start or deadline")
    return datetime.fromisoformat(match[1].replace("Z", "+00:00")), int(match[2])


def validate_timeout(line: str, deadline: int) -> None:
    """Require the supervisor timeout marker to match its declared deadline."""
    expected = f"TIMEOUT: HID worker exceeded {deadline}s; no level claimed"
    if line != expected:
        raise ValueError("invalid diagnostic timeout marker")


def validate_numeric_fields(lines: list[str]) -> None:
    """Check native UTC framing and integral transport field bounds."""
    _, deadline = parse_begin(next((line for line in lines if line.strip()), ""))
    for line in lines:
        if line.startswith("TIMEOUT:"):
            validate_timeout(line, deadline)
        if count := COUNT.fullmatch(line):
            if int(count[1]) > 2**31 - 1:
                raise ValueError("receiver count exceeds native integer range")
        if result := RESULT.fullmatch(line):
            if not -(2**31) <= int(result[3]) <= 2**31 - 1:
                raise ValueError("Win32 result exceeds native integer range")
            if int(result[4]) > 2**63 - 1:
                raise ValueError("elapsed time exceeds native integer range")
        elif line.startswith(("STEP: SET F7 ", "STEP: GET 05 ")):
            if not re.fullmatch(r"STEP: (SET F7|GET 05) begin length=[0-9]{1,10}", line):
                raise ValueError("malformed HID transfer marker")


def validate_markers(lines: list[str]) -> None:
    """Require unambiguous parent and worker outcome markers."""
    singletons = ("BEGIN:", "STEP: found ", "PASS:", "INCONCLUSIVE:",
                  "FAIL:", "END:", "TIMEOUT:")
    counts = {prefix: 0 for prefix in singletons}
    nonempty = [line for line in lines if line.strip()]
    if not nonempty or not nonempty[0].startswith("BEGIN: UTC="):
        raise ValueError("missing initial BEGIN marker")
    for line in nonempty:
        for prefix in singletons:
            if line.startswith(prefix):
                counts[prefix] += 1
                if counts[prefix] > 1:
                    raise ValueError("duplicate HID diagnostic marker")
        for prefix, pattern in (("STEP: found ", COUNT), ("PASS:", PASS),
                                ("END:", END)):
            if line.startswith(prefix) and not pattern.fullmatch(line):
                raise ValueError("malformed HID diagnostic marker")
    if counts["END:"] + counts["TIMEOUT:"] != 1 or not nonempty[-1].startswith(
            ("END:", "TIMEOUT:")):
        raise ValueError("missing or misplaced terminal marker")
    if counts["PASS:"] + counts["INCONCLUSIVE:"] + counts["FAIL:"] > 1:
        raise ValueError("conflicting worker outcome markers")
    if counts["FAIL:"] and nonempty[-1] != "END: worker exited 1":
        raise ValueError("worker failure contradicts terminal marker")
    if counts["INCONCLUSIVE:"] and nonempty[-1].startswith("END:") and (
            nonempty[-1] != "END: worker exited 2"):
        raise ValueError("inconclusive outcome contradicts worker exit")


def validate_verified_order(lines: list[str]) -> None:
    """Require an ordered, same-open F7/05 chain before verified output."""
    enumerated = opened = pending_set = complete = outcome = False
    for line in lines:
        match = RESULT.fullmatch(line)
        is_open = line in ("STEP: HID open succeeded", "STEP: HID open failed")
        if outcome and line.startswith("STEP:"):
            raise ValueError("HID operation follows verified outcome")
        if count := COUNT.fullmatch(line):
            enumerated = int(count[1]) > 0
        elif is_open:
            if not enumerated:
                raise ValueError("HID open precedes positive enumeration")
            opened = line == "STEP: HID open succeeded"
            pending_set = False
        elif match:
            if not opened:
                raise ValueError("HID transfer lacks successful open")
            operation, status, error, _ = match.groups()
            if status == "OK" and int(error) != 0:
                raise ValueError("successful HID transfer has Win32 error")
            if operation == "SET F7":
                pending_set = status == "OK"
            else:
                if not pending_set:
                    raise ValueError("GET 05 lacks preceding successful SET F7")
                complete |= status == "OK"
                pending_set = False
        elif PASS.fullmatch(line):
            if not complete:
                raise ValueError("verified result precedes complete HID chain")
            outcome = True


def parse_log(data: str) -> Capture:
    """Parse only stage markers from beta.57+ redacted CLI output."""
    lines = data.splitlines()
    if any(line.startswith("MODE: experimental GET") for line in lines):
        raise ValueError("Use compare_get_ids.py for an experimental GET-ID log")
    validate_markers(lines)
    validate_numeric_fields(lines)
    if any(PASS.fullmatch(line) for line in lines):
        validate_verified_order(lines)
    values = {"open_ok": 0, "open_failed": 0, "set_ok": 0,
              "set_failed": 0, "get_ok": 0, "get_failed": 0}
    candidates, level, ended = None, None, None
    timeout, inconclusive = False, False
    for line in lines:
        if match := COUNT.fullmatch(line):
            candidates = int(match[1])
        if line == "STEP: HID open succeeded":
            values["open_ok"] += 1
        if line == "STEP: HID open failed":
            values["open_failed"] += 1
        if match := RESULT.fullmatch(line):
            key = ("set" if match[1] == "SET F7" else "get") + (
                "_ok" if match[2] == "OK" else "_failed")
            values[key] += 1
        if match := PASS.fullmatch(line):
            level = int(match[1])
        if match := END.fullmatch(line):
            ended = int(match[1])
        if line.startswith("INCONCLUSIVE:"):
            inconclusive = True
        if line.startswith("TIMEOUT:"):
            timeout = True
    return validate_capture(Capture(candidates, **values, battery=level,
                                    timed_out=timeout, ended=ended,
                                    inconclusive=inconclusive))


def validate_capture(value: Capture) -> Capture:
    """Reject partial successes and contradictory worker exit markers."""
    if value.timed_out:
        if value.ended is not None or value.battery is not None:
            raise ValueError("timeout contradicts worker completion")
        return value
    if value.ended not in (0, 1, 2):
        raise ValueError("missing or invalid worker exit code")
    if value.battery is not None:
        if not 1 <= value.battery <= 100 or value.ended != 0:
            raise ValueError("battery and exit code are inconsistent")
        if (not value.candidates or not value.open_ok or
                not value.set_ok or not value.get_ok):
            raise ValueError("verified level lacks full F7/05 operation chain")
    elif value.ended == 0:
        raise ValueError("successful exit without verified battery")
    return value


def classify(value: Capture) -> tuple[str, str]:
    """Describe the furthest documented HID stage without guessing."""
    if value.timed_out:
        return "TIMEOUT", "worker reached deadline; battery unverified"
    if value.battery is not None:
        return "VERIFIED", f"battery={value.battery}% (from validated parser)"
    if value.ended == 1:
        return "ERROR", "worker failed without verified telemetry"
    if value.candidates == 0:
        return "NO RECEIVER", "no matching MI_02 interface was enumerated"
    if value.open_failed and value.open_ok == 0:
        return "OPEN FAILED", "matching HID collection did not open"
    if value.set_failed and value.set_ok == 0:
        return "SET FAILED", "F7 feature request did not succeed"
    if value.get_failed and value.get_ok == 0:
        return "GET FAILED", "05 feature report could not be read"
    return "UNVERIFIED", "no battery recognized by the parser"


def read_capture(path: Path) -> Capture:
    """Read one bounded local text report, never querying attached HID."""
    return parse_log(read_evidence(path, 1048576).decode("utf-8-sig"))


def compare(items: list[tuple[str, Capture]]) -> tuple[str, list[str]]:
    """Mark non-verified cases inconclusive, never as zero battery."""
    rows = []
    for label, capture in items:
        status, message = classify(capture)
        rows.append(f"{label}: {status} — {message}")
    if all(item.battery is not None for _, item in items):
        result = "PASS"
    elif any(item.ended == 1 for _, item in items):
        result = "FAIL"
    else:
        result = "INCONCLUSIVE"
    return result, rows


def main() -> int:
    """Exit 0 for verified results, 2 for uncertainty, 1 for bad logs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--awake", required=True, type=Path)
    parser.add_argument("--after-sleep", required=True, type=Path)
    parser.add_argument("--reconnect", type=Path)
    args = parser.parse_args()
    paths = [("AWAKE", args.awake), ("AFTER SLEEP", args.after_sleep)]
    if args.reconnect is not None:
        paths.append(("RECONNECT", args.reconnect))
    try:
        result, rows = compare([(label, read_capture(path))
                                for label, path in paths])
    except (OSError, UnicodeError, ValueError) as error:
        print(f"FAIL: invalid Windows HID diagnostic: {type(error).__name__}")
        return 1
    for row in rows:
        print(row)
    print(f"SUMMARY: {result}")
    print("Reports cannot prove the same physical receiver or correct HID framing.")
    return {"PASS": 0, "INCONCLUSIVE": 2, "FAIL": 1}[result]


if __name__ == "__main__":
    raise SystemExit(main())
