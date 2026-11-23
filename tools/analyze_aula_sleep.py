#!/usr/bin/env python3
"""Compare three existing AULA L99 clipboard summaries without USB access."""

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re

CACHE_FIELDS = re.compile(
    r"^Last successful battery: (?P<level>unavailable|\d+); "
    r"UTC: (?P<time>[^;]+); "
    r"Consecutive no-reply polls: (?P<failures>\d+); "
    r"Cache lifetime hours: (?P<lifetime>\d+(?:\.\d+)?); "
    r"Display cache active: (?P<active>True|False)$"
)


@dataclass(frozen=True)
class Summary:
    """Fields copied by the AULA L99 diagnostic menu."""

    version: str
    automatic: bool
    present: bool
    known: bool
    percent: int | None
    last_read: datetime | None
    last_good: int | None
    last_good_at: datetime | None
    failures: int
    cache_active: bool
    cache_lifetime: float


def parse_bool(value: str) -> bool:
    """Require a confirmed boolean rather than a missing device state."""
    if value not in {"True", "False"}:
        raise ValueError("expected True or False")
    return value == "True"


def parse_level(value: str) -> int | None:
    """Validate a battery value without interpreting zero as a reading."""
    if value == "unavailable":
        return None
    if not value.isdecimal() or not 1 <= int(value) <= 100:
        raise ValueError("battery outside verified 1..100 range")
    return int(value)


def parse_time(value: str) -> datetime | None:
    """Reject ambiguous timestamps and normalize for safe comparisons."""
    if value == "never":
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("invalid ISO timestamp") from error
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamp missing UTC offset")
    return result


def parse_summary(data: str) -> Summary:
    """Parse only known exported fields, never paths or serial numbers."""
    lines = data.strip().splitlines()
    if not lines or lines[0] != "AULA L99 2.4 GHz experimental battery check":
        raise ValueError("not an AULA L99 clipboard summary")
    fields = dict(line.split(": ", 1) for line in lines[1:]
                  if ": " in line and not line.startswith("Last successful"))
    cache = next((CACHE_FIELDS.fullmatch(line) for line in lines
                  if line.startswith("Last successful battery: ")), None)
    if cache is None:
        raise ValueError("AULA cache/status fields are missing")
    required = ("Version", "Automatic monitoring enabled", "Receiver present",
                "Presence known", "Battery percentage", "Last read UTC")
    if any(name not in fields for name in required):
        raise ValueError("required AULA summary field is missing")
    return Summary(
        version=fields["Version"],
        automatic=parse_bool(fields["Automatic monitoring enabled"]),
        present=parse_bool(fields["Receiver present"]),
        known=parse_bool(fields["Presence known"]),
        percent=parse_level(fields["Battery percentage"]),
        last_read=parse_time(fields["Last read UTC"]),
        last_good=parse_level(cache["level"]),
        last_good_at=parse_time(cache["time"]),
        failures=int(cache["failures"]),
        cache_active=parse_bool(cache["active"]),
        cache_lifetime=float(cache["lifetime"]),
    )


def check_awake(value: Summary) -> tuple[str, str]:
    """Require a confirmed fresh reading before evaluating standby."""
    if not value.automatic:
        return "NOT OBSERVED", "automatic monitoring was disabled"
    if not value.known or not value.present:
        return "NOT OBSERVED", "receiver presence was not confirmed"
    if value.percent is None or value.last_read is None:
        return "NOT OBSERVED", "initial fresh battery reply is unavailable"
    if value.last_good != value.percent or value.last_good_at is None:
        return "FAIL", "fresh battery and last-good cache disagree"
    if value.last_good_at > value.last_read or value.cache_active:
        return "FAIL", "inconsistent fresh measurement timestamps/state"
    return "PASS", "initial fresh reading and timestamp confirmed"


def check_sleep(awake: Summary, value: Summary) -> tuple[str, str]:
    """Never claim standby was observed when the receiver still replies."""
    if value.last_read is None or awake.last_read is None:
        return "NOT OBSERVED", "sleep checkpoint has no poll time"
    if value.last_read < awake.last_read:
        return "FAIL", "sleep checkpoint predates the initial reading"
    if value.percent is not None:
        return "NOT OBSERVED", "keyboard still returned a fresh battery reply"
    if value.last_good != awake.last_good or (
            value.last_good_at != awake.last_good_at):
        return "FAIL", "last verified sample was lost or replaced"
    if not value.known:
        if value.cache_active:
            return "FAIL", "cached value exposed with unknown receiver presence"
        return "NOT OBSERVED", "USB presence unknown; hidden cache retained"
    if not value.present:
        return "NOT OBSERVED", "receiver was confirmed disconnected"
    if value.failures == 0:
        return "FAIL", "no reply recorded without increasing failure counter"
    age = value.last_read - value.last_good_at
    if age.total_seconds() < 0:
        return "FAIL", "sleep cache timestamp is in the future"
    if age.total_seconds() >= value.cache_lifetime * 3600:
        if value.cache_active:
            return "FAIL", "expired battery cache is still displayed"
        return "NOT OBSERVED", "sleep exceeded cache lifetime"
    if not value.cache_active:
        return "FAIL", "verified receiver with valid cache did not display it"
    return "PASS", "sleep shows timestamped cached sample, not fresh charge"


def check_recovery(sleep: Summary, value: Summary) -> tuple[str, str]:
    """Only a new verified measurement counts as recovery."""
    if not value.known or not value.present or value.percent is None:
        return "FAIL", "no fresh reply after the keyboard was awakened"
    if value.last_read is None or value.last_good_at is None:
        return "FAIL", "recovered reading has no measurement timestamp"
    if sleep.last_read is not None and value.last_read < sleep.last_read:
        return "FAIL", "recovery timestamp predates sleep checkpoint"
    if value.last_good_at > value.last_read or (
            value.last_good != value.percent):
        return "FAIL", "recovery last-good sample mismatches the fresh reply"
    if value.cache_active or value.failures != 0:
        return "FAIL", "recovery retained cached flag or failure counter"
    return "PASS", "a new verified reading and zero failures are visible"


def analyze(awake: Summary, sleep: Summary,
            recovered: Summary) -> tuple[str, list[tuple[str, str, str]]]:
    """Evaluate fresh, sleep and wake states without claiming HID proof."""
    checks = [
        ("AWAKE", *check_awake(awake)),
        ("SLEEP", *check_sleep(awake, sleep)),
        ("RECOVERED", *check_recovery(sleep, recovered)),
    ]
    result = ("FAIL" if any(item[1] == "FAIL" for item in checks) else
              "NOT OBSERVED" if any(item[1] == "NOT OBSERVED" for item in checks)
              else "PASS")
    if awake.last_good_at and recovered.last_good_at and (
            recovered.last_good_at <= awake.last_good_at):
        checks.append(("TIMELINE", "FAIL", "recovery has no newer good sample"))
        result = "FAIL"
    return result, checks


def read_file(path: Path) -> Summary:
    """Read a bounded, local-only clipboard export as UTF-8."""
    if path.stat().st_size > 65536:
        raise ValueError("summary exceeds 64 KiB limit")
    return parse_summary(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    """Return PASS=0, FAIL=1, NOT OBSERVED=2, invalid input=1."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--awake", type=Path, required=True)
    parser.add_argument("--asleep", type=Path, required=True)
    parser.add_argument("--recovered", type=Path, required=True)
    args = parser.parse_args()
    try:
        result, checks = analyze(*(read_file(path) for path in
                                   (args.awake, args.asleep, args.recovered)))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"FAIL: cannot evaluate AULA summaries: {type(error).__name__}")
        return 1
    for name, status, message in checks:
        print(f"{name}: {status} — {message}")
    print(f"SUMMARY: {result}")
    print("Receiver identity and HID bytes cannot be proven from clipboard summaries.")
    return {"PASS": 0, "FAIL": 1, "NOT OBSERVED": 2}[result]


if __name__ == "__main__":
    raise SystemExit(main())
