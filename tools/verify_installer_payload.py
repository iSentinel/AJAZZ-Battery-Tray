#!/usr/bin/env python3
"""Compare independently extracted installer files to reviewed local evidence."""

import argparse
import hashlib
import os
from pathlib import Path
import stat
import sys
import zipfile
import zlib
import struct

from run_offline_qa import write_json
from verify_installer_candidate import verify, MAX_SETUP
from verify_windowsdesktop_provenance import read_local

APP = 'app/AJAZZBatteryTray.exe'
ICONS = ('AppIcon.ico', 'AppIcon-black.ico', 'AppIcon-blue.ico', 'AppIcon-white.ico')
MAX_ICON = 1024 * 1024


def file_digest(path: Path, limit: int) -> str:
    """Hash a bounded regular file, refusing final-component symlinks."""
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= limit:
        raise ValueError('invalid payload file')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    with os.fdopen(os.open(path, flags | getattr(os, 'O_BINARY', 0)), 'rb') as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or (
                opened.st_dev, opened.st_ino, opened.st_size) != (
                    before.st_dev, before.st_ino, before.st_size):
            raise ValueError('payload file changed')
        digest = hashlib.sha256()
        size = 0
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            if size > limit:
                raise ValueError('payload file too large')
            digest.update(chunk)
        after = os.fstat(stream.fileno())
        if size != before.st_size or after.st_mtime_ns != opened.st_mtime_ns:
            raise ValueError('payload file changed during read')
    return digest.hexdigest()


def exact_directory(root: Path, names: set[str]) -> None:
    """Require only the expected direct children of a regular directory."""
    if not stat.S_ISDIR(root.lstat().st_mode):
        raise ValueError('invalid payload directory')
    with os.scandir(root) as entries:
        seen = set()
        for entry in entries:
            if entry.name not in names or entry.name in seen:
                raise ValueError('unexpected payload entry')
            seen.add(entry.name)
    if seen != names:
        raise ValueError('missing payload entry')


def payload(root: Path, icons: Path, expected_app: str) -> dict:
    """Verify exact extracted tree against manifest app and local icon bytes."""
    exact_directory(root, {'app'})
    exact_directory(root / 'app', {'AJAZZBatteryTray.exe', 'Icons'})
    exact_directory(root / 'app/Icons', set(ICONS))
    if not stat.S_ISDIR(icons.lstat().st_mode):
        raise ValueError('invalid reference icon directory')
    app = file_digest(root / APP, MAX_SETUP)
    if app != expected_app:
        raise ValueError('extracted application differs')
    result = {APP: app}
    for name in ICONS:
        path = f'app/Icons/{name}'
        actual = file_digest(root / path, MAX_ICON)
        if actual != file_digest(icons / name, MAX_ICON):
            raise ValueError('extracted icon differs')
        result[path] = actual
    return result


def main(argv: list[str] | None = None) -> int:
    """Verify trusted immutable local inputs; no extraction or execution."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--payload-dir', type=Path, required=True)
    parser.add_argument('--source-icons', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        evidence = verify(read_local(args.archive), args.sha256, args.source_sha)
        files = payload(args.payload_dir, args.source_icons,
                        evidence['candidate']['app_sha256'])
        write_json(args.output, {'schema': 1, 'archive_sha256': args.sha256,
                   'source_sha': args.source_sha, 'files': files,
                   'scope': 'independently extracted declared application files',
                   'extractor_trust': 'NOT_VERIFIED', 'installer_engine': 'NOT_VERIFIED',
                   'source_icon_provenance': 'CALLER_REVIEW_REQUIRED',
                   'release_admission': 'NOT_VERIFIED'})
    except (OSError, ValueError, TypeError, KeyError, RuntimeError,
            NotImplementedError, zipfile.BadZipFile, zlib.error, struct.error):
        print('FAIL: installer payload verification', file=sys.stderr)
        return 2
    print('PASS: extracted application and icons; engine and trust not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
