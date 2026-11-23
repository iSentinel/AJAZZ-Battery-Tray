#!/usr/bin/env python3
"""Compare measured Windows tray resource CSVs without extra dependencies."""

import argparse
import csv
import math
import statistics
import sys
from pathlib import Path

FIELDS = (
    "utc", "version", "elapsed_seconds", "cpu_seconds",
    "cpu_one_core_percent", "working_set_bytes", "private_bytes",
    "handles", "threads",
)
METRICS = (
    "cpu_one_core_percent", "working_set_mib", "private_mib",
    "handles", "threads",
)


def number(row, key):
    """Read a finite nonnegative numeric field."""
    value = float(row[key])
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"invalid {key}")
    return value


def read_run(path):
    """Validate and summarize one bounded sampler export."""
    if path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError(f"{path}: CSV exceeds 2 MiB")
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f"{path}: unexpected CSV header")
        rows = list(reader)
    if not 3 <= len(rows) <= 3601:
        raise ValueError(f"{path}: expected 3–3601 samples")
    versions = {row["version"] for row in rows}
    if len(versions) != 1 or not next(iter(versions)):
        raise ValueError(f"{path}: inconsistent version")
    elapsed = [number(row, "elapsed_seconds") for row in rows]
    cpu = [number(row, "cpu_seconds") for row in rows]
    duration = elapsed[-1] - elapsed[0]
    if duration < 29 or duration > 3660:
        raise ValueError(f"{path}: invalid sample duration")
    if any(b <= a for a, b in zip(elapsed, elapsed[1:])):
        raise ValueError(f"{path}: non-increasing elapsed time")
    if any(b < a for a, b in zip(cpu, cpu[1:])):
        raise ValueError(f"{path}: decreasing CPU counter")
    result = {"version": versions.pop(), "duration": duration}
    result["cpu_one_core_percent"] = 100 * (cpu[-1] - cpu[0]) / duration
    for key in ("working_set_bytes", "private_bytes", "handles", "threads"):
        values = [number(row, key) for row in rows]
        target = key.replace("_bytes", "_mib")
        result[target] = statistics.median(values) / (
            1048576 if key.endswith("_bytes") else 1
        )
    return result


def compare(baseline, candidate):
    """Compare medians of independent, similarly timed runs."""
    if not baseline or not candidate:
        raise ValueError("both groups require at least one run")
    for group in (baseline, candidate):
        if len({run["version"] for run in group}) != 1:
            raise ValueError("each group must contain a single version")
    durations = [run["duration"] for run in baseline + candidate]
    if max(durations) > min(durations) * 1.10:
        raise ValueError("run durations differ by more than 10%")
    output = []
    for key in METRICS:
        old = statistics.median(run[key] for run in baseline)
        new = statistics.median(run[key] for run in candidate)
        delta = (new - old) / old * 100 if old else None
        output.append((key, old, new, delta))
    return output


def main(argv=None):
    """Run the comparison; PASS denotes valid inputs, not a performance gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", nargs="+", type=Path, required=True)
    parser.add_argument("--candidate", nargs="+", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        paths = [p.resolve() for p in args.baseline + args.candidate]
        if len(set(paths)) != len(paths):
            raise ValueError("duplicate input path")
        baseline = [read_run(p) for p in args.baseline]
        candidate = [read_run(p) for p in args.candidate]
        result = compare(baseline, candidate)
    except (OSError, ValueError, TypeError, csv.Error) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"Baseline: {baseline[0]['version']} ({len(baseline)} runs)")
    print(f"Candidate: {candidate[0]['version']} ({len(candidate)} runs)")
    print(f"{'Metric':26} {'Baseline':>12} {'Candidate':>12} {'Delta %':>12}")
    for name, old, new, delta in result:
        change = "N/A" if delta is None else f"{delta:+.2f}"
        print(f"{name:26} {old:12.4f} {new:12.4f} {change:>12}")
    if min(len(baseline), len(candidate)) < 3:
        print("WARNING: fewer than three independent runs per version.")
    print("PASS: inputs valid; no performance threshold applied.")
    print("Comparability of hardware, settings and workload is manual.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
