#!/usr/bin/env python3
"""Stage an exact local CI portable payload for private installer preflight."""

import argparse
from pathlib import Path
import stat
import subprocess
import sys
import zipfile

from run_offline_qa import ROOT
from verify_hardware_acceptance import ICONS, candidate, members
from verify_windows_notice_transport import safe_stat
from verify_windowsdesktop_provenance import read_local

EXE = 'AJAZZBatteryTray.exe'


def checkout(source: Path, sha: str) -> None:
    """Check the actual clean tracked checkout, not the archive's provenance."""
    def git(*args: str) -> str:
        """Read local Git metadata without a shell or network."""
        return subprocess.check_output(['git', *args], cwd=source, text=True,
                                       stderr=subprocess.DEVNULL, timeout=15).strip()

    if (Path(git('rev-parse', '--show-toplevel')).resolve() != source.resolve()
            or git('rev-parse', 'HEAD') != sha
            or git('status', '--porcelain', '--untracked-files=no')):
        raise ValueError('source checkout differs or has tracked changes')


def directory(path: Path) -> None:
    """Require a real directory rather than a symlink or reparse point."""
    if not stat.S_ISDIR(safe_stat(path).st_mode):
        raise ValueError('expected local directory')


def stage(raw: bytes, sha: str, source_sha: str, source: Path) -> dict:
    """Check exact archive and source icon bytes before creating a new payload."""
    directory(source)
    checkout(source, source_sha)
    identity = candidate(raw, sha, source_sha, 'windows-aj179')
    files = members(raw, ICONS | {EXE})
    assets = source / 'src/AjazzBatteryTray/Assets'
    for parent in (source / 'src', assets.parent, assets):
        directory(parent)
    for name in ICONS:
        path = assets / Path(name).name
        safe_stat(path)
        if read_local(path) != files[name]:
            raise ValueError('portable icon differs from source')
    dist = source / 'dist'
    if not dist.exists() and not dist.is_symlink():
        dist.mkdir()
    directory(dist)
    target = dist / 'app'
    target.mkdir(exist_ok=False)
    with (target / EXE).open('xb') as stream:
        stream.write(files[EXE])
    return identity


def main(argv: list[str] | None = None) -> int:
    """Stage a new local payload; never compile, install or publish anything."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--archive-sha256', required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--source', type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        safe_stat(args.source)
        safe_stat(args.archive)
        identity = stage(read_local(args.archive), args.archive_sha256,
                         args.source_sha, args.source.resolve())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            zipfile.BadZipFile, subprocess.SubprocessError):
        print('FAIL: local portable payload staging', file=sys.stderr)
        return 2
    print('PASS: staged private portable app; source provenance caller-reviewed')
    print('Application SHA-256:', identity['app_sha256'])
    print('No compiler executed; release admission not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
