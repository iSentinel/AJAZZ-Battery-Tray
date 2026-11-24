#!/usr/bin/env python3
"""Compare paired normal/isolated Windows Job Object CPU runs."""
import argparse
import csv
import hashlib
import io
import math
import re
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path

FIELDS = ("utc", "version", "sha256", "mode", "elapsed_seconds",
          "job_cpu_seconds", "total_processes", "active_processes")


def read_run(path, mode):
    """Validate schema, provenance and cumulative counters."""
    with path.open("rb") as source:
        raw = source.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("CSV exceeds 2 MiB")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise ValueError("Unexpected CSV schema")
    rows = list(reader)
    if not 3 <= len(rows) <= 3601:
        raise ValueError("Expected 3–3601 samples")
    hashes, versions = set(), set()
    previous = None
    first = None
    for row in rows:
        if None in row or None in row.values() or row["mode"] != mode:
            raise ValueError("Malformed row or incorrect mode")
        stamp = datetime.fromisoformat(row["utc"].replace("Z", "+00:00"))
        if stamp.utcoffset() != timedelta(0):
            raise ValueError("Expected UTC timestamp")
        hashes.add(row["sha256"])
        versions.add(row["version"])
        sample = (float(row["elapsed_seconds"]), float(row["job_cpu_seconds"]),
                  int(row["total_processes"]), int(row["active_processes"]))
        validate_sample(sample, previous)
        first = first or sample
        previous = sample
    if (len(hashes) != 1 or not re.fullmatch("[0-9a-f]{64}", next(iter(hashes))) or
            len(versions) != 1 or not next(iter(versions)).strip()):
        raise ValueError("Inconsistent executable provenance")
    elapsed = previous[0] - first[0]
    if not 29 <= elapsed <= 3660:
        raise ValueError("Invalid duration")
    cpu = 100 * (previous[1] - first[1]) / elapsed
    if not math.isfinite(cpu):
        raise ValueError("Invalid calculated CPU")
    return (hashes.pop(), versions.pop(), elapsed, cpu,
            previous[2] - first[2], hashlib.sha256(raw).hexdigest())


def validate_sample(sample, previous):
    """Reject inconsistent or impossible cumulative accounting."""
    elapsed, cpu, total, active = sample
    if (not math.isfinite(elapsed) or not math.isfinite(cpu) or
            elapsed < 0 or cpu < 0 or not 1 <= active <= total):
        raise ValueError("Invalid job counters")
    if previous and (elapsed <= previous[0] or cpu < previous[1] or
                     total < previous[2]):
        raise ValueError("Nonmonotonic job counters")


def compare(normal, isolated):
    """Require same executable and comparable run durations."""
    runs = normal + isolated
    if not normal or not isolated:
        raise ValueError("Both modes required")
    if len({r[0:2] for r in runs}) != 1:
        raise ValueError("Different executable SHA256 or version")
    if len({r[5] for r in runs}) != len(runs):
        raise ValueError("Duplicate CSV content")
    durations = [r[2] for r in runs]
    if max(durations) > min(durations) * 1.10:
        raise ValueError("Durations differ by more than 10%")
    return (statistics.median(r[3] for r in normal),
            statistics.median(r[3] for r in isolated))


def main(argv=None):
    """Print a descriptive comparison, never a performance gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--normal", nargs="+", required=True, type=Path)
    parser.add_argument("--isolated", nargs="+", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        paths = [p.resolve() for p in args.normal + args.isolated]
        if len(paths) != len(set(paths)):
            raise ValueError("Duplicate input path")
        normal = [read_run(p, "normal") for p in args.normal]
        isolated = [read_run(p, "isolated") for p in args.isolated]
        old, new = compare(normal, isolated)
    except (OSError, ValueError, OverflowError, csv.Error) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"Normal median one-core CPU:   {old:.4f}%")
    print(f"Isolated median one-core CPU: {new:.4f}%")
    print(f"Difference: {new - old:+.4f} percentage points")
    if old:
        print(f"Relative difference: {(new - old) / old * 100:+.2f}%")
    if min(len(normal), len(isolated)) < 3:
        print("WARNING: fewer than three independent runs per mode")
    print("PASS: input validation only; no performance threshold applied")
    print("Same hardware, settings and workload must be verified separately")
    return 0


if __name__ == "__main__":
    sys.exit(main())
