#!/usr/bin/env python3
"""Reproduce and extract exact proposed packages using native OS archive tools."""

import argparse
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys

from build_consolidated_apple_notices import encode, package_files
from build_consolidated_portable_notices import build, OUTPUT_NAMES
from inventory_apple_archive import archive_members, EDITIONS
from review_normalized_package_set import PACKAGES, check_package, proposal
from run_offline_qa import write_json
from verify_hardware_acceptance import APPLE_NAMES, members
from verify_windows_notice_transport import digest, safe_stat, tree_files
from verify_windowsdesktop_provenance import read_local


def verify_tree(root: Path, expected: dict, executable_modes: bool = False) -> None:
    """Check exact extracted inventory, bytes and optional executable bits."""
    if not stat.S_ISDIR(safe_stat(root).st_mode):
        raise ValueError('expected extracted directory')
    pending, found = [root], set()
    directories = {parent.as_posix() for name in expected for parent in Path(name).parents
                   if parent != Path('.')}
    while pending:
        for path in pending.pop().iterdir():
            name = path.relative_to(root).as_posix()
            info = safe_stat(path)
            if stat.S_ISDIR(info.st_mode) and name in directories:
                pending.append(path)
                continue
            if not stat.S_ISREG(info.st_mode) or name not in expected:
                raise ValueError('unexpected extracted entry')
            raw, mode = expected[name]
            if info.st_size != len(raw) or read_local(path) != raw:
                raise ValueError('extracted file bytes differ')
            if executable_modes and info.st_mode & 0o111 != mode & 0o111:
                raise ValueError('executable mode differs')
            found.add(name)
    if found != set(expected):
        raise ValueError('incomplete extracted inventory')


def extract(archive: Path, dest: Path) -> None:
    """Extract validated archive into a new directory using native tooling."""
    dest.mkdir(mode=0o700, exist_ok=False)
    if sys.platform == 'win32':
        command = ['pwsh', '-NoProfile', '-NonInteractive', '-Command',
                   '$ErrorActionPreference="Stop"; Expand-Archive '
                   '-LiteralPath $env:AJAZZ_EXTRACT_ARCHIVE -DestinationPath $env:AJAZZ_EXTRACT_DEST']
    elif sys.platform == 'darwin':
        command = ['/usr/bin/ditto', '-x', '-k', str(archive), str(dest)]
    else:
        raise ValueError('native extraction requires Windows or macOS')
    env = {**os.environ, 'AJAZZ_EXTRACT_ARCHIVE': str(archive.resolve()),
           'AJAZZ_EXTRACT_DEST': str(dest.resolve())}
    subprocess.run(command, check=True, timeout=120, env=env)


def observe(edition: str, original: bytes, license_bytes: bytes,
            notices: Path | None, root: Path) -> dict:
    """Bind reproduced package bytes and verify native extraction without launch."""
    if edition == 'windows':
        if notices is None:
            raise ValueError('Windows notice tree required')
        raw = build(original, tree_files(notices))
        expected = members(raw, OUTPUT_NAMES)
    else:
        expected = package_files(original, license_bytes, edition)
        raw = encode(expected)
    check_package(raw, edition, original, license_bytes)
    path = root / PACKAGES[edition][0]
    with path.open('xb') as output:
        output.write(raw)
    outer = root / (edition + '-outer')
    extract(path, outer)
    verify_tree(outer, {name: (data, 0) for name, data in expected.items()})
    row = {'edition': edition, 'package_sha256': digest(raw), 'outer_files': len(expected),
           'source_sha': proposal()['source_sha'], 'runner_os': platform.platform(),
           'outer_extraction': 'MATCH', 'application_launch': 'NOT_RUN',
           'release_admission': 'BLOCKED'}
    if edition != 'windows':
        inner = outer / (APPLE_NAMES[edition] + '.zip')
        dest = root / (edition + '-inner')
        extract(inner, dest)
        files = archive_members(expected[inner.name])
        verify_tree(dest, files, executable_modes=True)
        subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict',
                        '--all-architectures', str(dest / EDITIONS[edition][0])],
                       check=True, timeout=90)
        row.update(inner_files=len(files), inner_extraction='MATCH',
                   executable_modes='MATCH', codesign_integrity='PASS')
    return row


def main(argv: list[str] | None = None) -> int:
    """Observe one native package, retain only a JSON report, never launch it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--edition', choices=PACKAGES, required=True)
    for name in ('original', 'license', 'root', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--notices', type=Path)
    args = parser.parse_args(argv)
    try:
        if (args.edition == 'windows' and sys.platform != 'win32'
                or args.edition != 'windows' and sys.platform != 'darwin'):
            raise ValueError('wrong native host')
        args.root.mkdir(mode=0o700, exist_ok=False)
        row = observe(args.edition, read_local(args.original), read_local(args.license),
                      args.notices, args.root)
        write_json(args.output, {'schema': 'native-package-extraction-v1', **row})
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError):
        print('FAIL: native package extraction', file=sys.stderr)
        return 2
    print('PASS: exact package extraction; application launch NOT_RUN; release BLOCKED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
