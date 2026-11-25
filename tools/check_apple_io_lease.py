#!/usr/bin/env python3
"""Check the native Apple vendor gate across processes, without HID."""
import argparse
import fcntl
import os
import stat
import subprocess
from pathlib import Path


def probe(exe: Path) -> int:
    """Run only the lease test mode, never a device command."""
    return subprocess.run(
        [str(exe), "--internal-test-io-lease"], timeout=5,
        check=False,
    ).returncode


def verify(exe: Path) -> None:
    """Hold the same lock from Python and test refusal/recovery."""
    directory = subprocess.check_output(
        ["getconf", "DARWIN_USER_TEMP_DIR"], text=True,
    ).strip()
    if not directory:
        raise RuntimeError("Missing Darwin user temporary directory")
    path = Path(directory) / "ajazz-apex-vendor-io-v1.lock"
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or info.st_nlink != 1 or info.st_mode & 0o077):
            raise RuntimeError("Unsafe lease fixture")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if probe(exe) != 2:
            raise RuntimeError("Contended worker did not refuse")
    finally:
        os.close(fd)
    if probe(exe) != 0:
        raise RuntimeError("Worker did not recover after gate release")
    print("PASS: cross-process Apple I/O exclusion and recovery (no HID)")


def main() -> None:
    """Use a development executable from either Apple edition."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.dry_run:
        print("DRY-RUN: no file, process or HID access")
        return
    verify(args.exe.resolve(strict=True))


if __name__ == "__main__":
    main()
