#!/usr/bin/env python3
"""Compare local APEX diagnostic reports without communicating with hardware."""

import argparse
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
import re

from run_offline_qa import read_evidence

RX = re.compile(r"^\s*RX buffer\[(\d+)\]=([0-9a-fA-F]+)\s*$")
TX = re.compile(r"^\s*Attempt UTC=.*?delay=(\d+)ms; TX\[(\d+)\]=")
RECEIVER = re.compile(r"^\[Receiver #(\d+)\]$")
SECTION = "[Fresh APEX protocol matrix — full vendor buffers]"
MAX_REPORT_BYTES = 1024 * 1024


def legacy_percent(data: bytes) -> int | None:
    """Decode the historical compact layout used before beta.60."""
    if len(data) >= 4 and data[:3] == b"\x05\x00\x00":
        if 1 <= data[3] <= 100:
            return data[3]
    return None


def current_percent(data: bytes) -> int | None:
    """Replay the current Windows parser on a numbered HID response."""
    if len(data) < 10 or data[0] != 5 or data[7] not in (1, 2, 3):
        return legacy_percent(data)
    if (data[7] == 1 or data[4] > 1 or data[1] != 1
            or data[5] != 0 or data[6] != 1 or data[9] != 0):
        return None
    return data[3] if 1 <= data[3] <= 100 else None


def vendor_candidate(data: bytes) -> tuple[str, int | None]:
    """Hypothetical Windows alignment of GearHub F7 fields, not live parser."""
    if len(data) < 10 or data[0] != 5:
        return "unrecognized", None
    ready, keyboard, mouse, kb_link, mouse_link, send, mask, _, boot = data[1:10]
    if ready not in (0, 1) or send not in (0, 1) or boot not in (0, 1):
        return "unknown-flags", None
    if mask not in (2, 3):
        return "mouse-not-indicated", None
    if boot:
        return "boot-mode", None
    if mouse_link != 0:
        return "mouse-offline-or-unknown", None
    if not 0 <= mouse <= 100:
        return "invalid-percent", None
    return "candidate-only", mouse


def read_attempts(text: str) -> Iterator[tuple[str, int, int, bytes | None]]:
    """Read only fresh capture lines; do not count the prior monitor state."""
    if SECTION not in text:
        raise ValueError("beta.41 fresh matrix section not found")
    receiver, delay, length = "?", None, None
    for line in text.split(SECTION, 1)[1].splitlines():
        match = RECEIVER.fullmatch(line.strip())
        if match:
            receiver, delay, length = match[1], None, None
        match = TX.match(line)
        if match:
            delay, length = map(int, match.groups())
            yield receiver, delay, length, None
        match = RX.fullmatch(line)
        if match:
            data = bytes.fromhex(match[2])
            if len(data) != int(match[1]) or len(data) != length or delay is None:
                raise ValueError("RX buffer length/attempt mismatch")
            yield receiver, delay, length, data


def read_report(path: Path) -> str:
    """Read a bounded identity-checked local report without following links."""
    return read_evidence(path, MAX_REPORT_BYTES).decode("utf-8-sig")


def inspect(path: Path) -> None:
    """Summarize each returned buffer and distinguish no-RX attempts."""
    attempts = Counter()
    received = Counter()
    valid = 0
    for receiver, delay, length, data in read_attempts(read_report(path)):
        key = (receiver, delay, length)
        if data is None:
            attempts[key] += 1
            continue
        received[key] += 1
        current = current_percent(data)
        valid += current is not None
        state, candidate = vendor_candidate(data)
        print(f"receiver={receiver} delay={delay}ms bytes={length} "
              f"current={current if current is not None else 'unknown'} "
              f"legacy={legacy_percent(data)} vendor={candidate} state={state}")
    if not attempts:
        print("No eligible query attempts; inspect descriptor inventory.")
    for (receiver, delay, length), count in (attempts - received).items():
        print(f"receiver={receiver} delay={delay}ms bytes={length} "
              f"no RX ({count} attempts)")
    print(f"Attempts={sum(attempts.values())}; RX={sum(received.values())}; current valid={valid}")


def main() -> int:
    """Command line entry point; return nonzero on malformed input."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    args = parser.parse_args()
    failed = False
    for index, path in enumerate(args.reports, 1):
        print(f"\n=== Report #{index} ===")
        try:
            inspect(path)
        except (OSError, ValueError) as error:
            print(f"Report #{index}: ERROR: {type(error).__name__}")
            failed = True
    print("\nCandidate fields are hypotheses, not validated live battery readings.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
