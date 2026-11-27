#!/usr/bin/env python3
"""Prepare and verify a private Windows profile backup before a tray upgrade."""

import argparse
import hashlib
import os
from pathlib import Path
import re
import stat
import sys

from run_offline_qa import write_json
from validate_scoped_sbom_schema import document
from verify_windows_notice_transport import safe_stat

LIMIT = 8 * 1024 * 1024
TOTAL = 64 * 1024 * 1024
COUNT = 128
ENTRY_LIMIT = 4096
MANIFEST = 'backup.json'
FIXED = {'settings.json', 'battery-history.csv', 'aula-l99-history.csv'}


def allowed(name: str) -> bool:
    """Limit the copy to reviewed settings and history filenames."""
    return name in FIXED or re.fullmatch(r'ajazz-[0-9A-F]{64}-history\.csv', name) is not None


def fingerprint(info: os.stat_result) -> tuple:
    """Identify the observed file and detect ordinary concurrent changes."""
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_ctime_ns, info.st_nlink)


def cross_fingerprint(info: os.stat_result) -> tuple:
    """Compare path and descriptor using compatible timestamp semantics."""
    # Windows path stat may expose creation time as ctime while fstat
    # exposes change time (CPython #157671). Compare birthtime there.
    stamp = getattr(info, 'st_birthtime_ns', None) if os.name == 'nt' else info.st_ctime_ns
    if stamp is None:
        raise ValueError('missing compatible file timestamp')
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            stamp, info.st_nlink)


def read_file(path: Path) -> bytes:
    """Read a bounded single-link regular file and detect observed mutation."""
    before = safe_stat(path)
    if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
            or not 0 <= before.st_size <= LIMIT):
        raise ValueError('unsupported profile file')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        if (not stat.S_ISREG(opened.st_mode)
                or cross_fingerprint(opened) != cross_fingerprint(before)):
            raise ValueError('profile path and descriptor differ')
        data = stream.read(LIMIT + 1)
        if fingerprint(os.fstat(stream.fileno())) != fingerprint(opened):
            raise ValueError('profile file changed')
    if len(data) != before.st_size or fingerprint(safe_stat(path)) != fingerprint(before):
        raise ValueError('profile file changed')
    return data


def inventory(root: Path, strict: bool = False) -> list[str]:
    """Collect only approved names; never traverse subdirectories or logs."""
    if not stat.S_ISDIR(safe_stat(root).st_mode):
        raise ValueError('expected profile directory')
    names = []
    # scandir streams entries; Path.iterdir can materialize the entire directory.
    with os.scandir(root) as entries:
        for index, entry in enumerate(entries, 1):
            if index > ENTRY_LIMIT:
                raise ValueError('profile directory entry limit exceeded')
            if allowed(entry.name):
                names.append(entry.name)
                if len(names) > COUNT:
                    raise ValueError('profile count exceeds limit')
            elif strict and entry.name != MANIFEST:
                raise ValueError('unexpected backup entry')
    return sorted(names)


def collect(root: Path, strict: bool = False) -> dict[str, bytes]:
    """Read the exact selected file set twice to detect ordinary changes."""
    names = inventory(root, strict)
    files, total = {}, 0
    for name in names:
        raw = read_file(root / name)
        total += len(raw)
        if total > TOTAL:
            raise ValueError('profile byte budget exceeded')
        files[name] = raw
    if not files or inventory(root, strict) != names:
        raise ValueError('empty or changing profile inventory')
    if any(read_file(root / name) != raw for name, raw in files.items()):
        raise ValueError('profile bytes changed')
    return files


def manifest(files: dict[str, bytes]) -> dict:
    """Build a local-only byte identity record, not portable preferences."""
    return {'schema': 'windows-profile-backup-v1', 'files': [
        {'name': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        for name, raw in sorted(files.items())],
        'scope': 'SAME_USER_LOCAL_ONLY', 'restore': 'NOT_RUN'}


def verify(root: Path) -> dict:
    """Require the exact backup inventory and the original recorded bytes."""
    files = collect(root, strict=True)
    expected = manifest(files)
    row = document(read_file(root / MANIFEST))
    if row != expected or any(type(item['bytes']) is not int for item in row['files']):
        raise ValueError('backup identity differs')
    return expected


def backup(source: Path, output: Path) -> dict:
    """Copy approved files to a fresh local directory; never alter the profile."""
    if not stat.S_ISDIR(safe_stat(output.parent).st_mode):
        raise ValueError('expected output parent')
    if source.resolve() in (output.resolve(), *output.resolve().parents):
        raise ValueError('output must be outside the source')
    files = collect(source)
    output.mkdir(mode=0o700, exist_ok=False)
    for name, raw in files.items():
        with (output / name).open('xb') as stream:
            stream.write(raw)
    write_json(output / MANIFEST, manifest(files))
    return verify(output)


def rehearse(source: Path, output: Path) -> dict:
    """Restore exact verified bytes into a new isolated directory only."""
    if not stat.S_ISDIR(safe_stat(output.parent).st_mode):
        raise ValueError('expected output parent')
    # Restrict rehearsal to a sibling of the backup, not the live profile.
    if output.parent.resolve() != source.parent.resolve():
        raise ValueError('rehearsal must be a sibling of the backup')
    if not re.fullmatch(r'AJAZZ-rehearsal-[A-Za-z0-9-]{1,64}', output.name):
        raise ValueError('expected dedicated rehearsal directory name')
    if source.resolve() == output.resolve():
        raise ValueError('rehearsal must differ from backup')
    expected = verify(source)
    files = collect(source, strict=True)
    if manifest(files) != expected or verify(source) != expected:
        raise ValueError('backup changed')
    output.mkdir(mode=0o700, exist_ok=False)
    for name, raw in files.items():
        with (output / name).open('xb') as stream:
            stream.write(raw)
    if collect(output, strict=True) != files or verify(source) != expected:
        raise ValueError('rehearsal bytes differ')
    return expected


def main(argv: list[str] | None = None) -> int:
    """Exit 0 for matched scope, 2 for invalid inputs; no live restore."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, help='Closed tray user profile')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--dry-run', action='store_true')
    action.add_argument('--backup', type=Path, help='Fresh private directory')
    action.add_argument('--verify', type=Path, help='Existing private backup')
    action.add_argument('--rehearse', type=Path, help='New sibling rehearsal directory')
    args = parser.parse_args(argv)
    try:
        if args.verify is not None:
            if args.source is not None:
                raise ValueError('verification needs only the backup')
            row = verify(args.verify)
        else:
            if args.source is None:
                raise ValueError('source required')
            if args.rehearse is not None:
                row = rehearse(args.source, args.rehearse)
            else:
                row = (manifest(collect(args.source)) if args.dry_run
                       else backup(args.source, args.backup))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        print('FAIL: local profile backup or verification', file=sys.stderr)
        return 2
    if args.rehearse is not None:
        print(f"PASS: {len(row['files'])} rehearsal files; live restore NOT_RUN")
    else:
        print(f"PASS: {len(row['files'])} profile files; restore NOT_RUN")
    print('Local private data: do not upload or share')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
