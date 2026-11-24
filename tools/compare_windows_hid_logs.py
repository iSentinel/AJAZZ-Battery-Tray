#!/usr/bin/env python3
"""Compare two or three bounded Windows HID logs without accessing devices."""

import argparse
from dataclasses import dataclass
from pathlib import Path
import re

COUNT = re.compile(r"^STEP: found (\d+) matching MI_02 paths$")
RESULT = re.compile(
    r"^STEP: (SET F7|GET 05) (OK|FAILED) Win32=(\d+) elapsed=(\d+)ms$"
)
PASS = re.compile(r"^PASS: verified battery (\d+)%$")
END = re.compile(r"^END: worker exited (\d+)$")


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


def parse_log(data: str) -> Capture:
    """Parse only stage markers from beta.57+ redacted CLI output."""
    lines = data.splitlines()
    if any(line.startswith("MODE: experimental GET") for line in lines):
        raise ValueError("Use compare_get_ids.py for an experimental GET-ID log")
    if sum(line.startswith("BEGIN: UTC=") for line in lines) != 1:
        raise ValueError("missing or duplicate BEGIN marker")
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
    if path.stat().st_size > 1048576:
        raise ValueError("report exceeds one MiB")
    return parse_log(path.read_text(encoding="utf-8-sig"))


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
