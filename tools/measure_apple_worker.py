#!/usr/bin/env python3
"""Measure synthetic Apple worker startup, not USB or CPU performance."""
import argparse
import csv
import json
import math
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

EXPECTED = {"kind": "synthetic", "percent": None, "presence": "unknown"}


def measure(executable, timeout):
    """Run one fixed synthetic sample with a bounded deadline."""
    started = time.monotonic()
    result = subprocess.run(
        [str(executable), "--internal-poll-sample"],
        capture_output=True, check=True, timeout=timeout,
    )
    elapsed = (time.monotonic() - started) * 1000
    if json.loads(result.stdout) != EXPECTED or result.stderr:
        raise ValueError("Unexpected synthetic worker response")
    return elapsed, len(result.stdout)


def quantile(values, fraction):
    """Return the nearest-rank quantile."""
    return sorted(values)[math.ceil(len(values) * fraction) - 1]


def collect(executable, output, iterations, timeout):
    """Store measurements incrementally and never overwrite existing CSV."""
    values = []
    with output.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["iteration", "utc", "elapsed_ms", "stdout_bytes"])
        handle.flush()
        for index in range(1, iterations + 1):
            elapsed, count = measure(executable, timeout)
            writer.writerow([
                index, datetime.now(timezone.utc).isoformat(),
                f"{elapsed:.3f}", count,
            ])
            handle.flush()
            values.append(elapsed)
    return values


def main(argv=None):
    """Validate options, support a side-effect-free dry run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if not 5 <= args.iterations <= 50 or not 1 <= args.timeout <= 30:
        parser.error("iterations must be 5..50; timeout 1..30 seconds")
    if args.dry_run:
        print(f"DRY-RUN: {args.iterations} synthetic launches; no HID or files")
        return 0
    if args.exe is None or args.output is None:
        parser.error("--exe and --output are required")
    try:
        values = collect(
            args.exe.resolve(strict=True), args.output,
            args.iterations, args.timeout,
        )
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"FAIL: {type(error).__name__}", file=sys.stderr)
        return 1
    print(
        f"PASS: n={len(values)} p50={quantile(values, .50):.3f} ms "
        f"p95={quantile(values, .95):.3f} ms max={max(values):.3f} ms"
    )
    print("No HID, radio, CPU or owner-hardware performance measured.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
