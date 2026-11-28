#!/usr/bin/env python3
"""Preflight or compile a local unpublished Windows candidate; never install it."""

import argparse
from collections.abc import Iterator
from contextlib import contextmanager, nullcontext
import os
from pathlib import Path
import subprocess
import sys

from inventory_dotnet_components import report
from run_offline_qa import ROOT, write_json
from verify_windowsdesktop_provenance import read_local
from validate_scoped_sbom_schema import digest, document, read
from verify_inno674_components import PIN, verify as verify_components
from verify_inno674_setup_records import ALIGNED_SOURCE
from verify_installer_payload import file_digest
from verify_windows_notice_transport import NAMES, safe_stat, tree_files, verify_files

SETUP = 'AJAZZBatteryTray-Setup-win-x64.exe'
LIMIT = 256 * 1024 * 1024
FIXED_STAMP_NS = 946684800 * 10**9  # 2000-01-01T00:00:00Z
ICONS = ('AppIcon.ico', 'AppIcon-white.ico', 'AppIcon-black.ico', 'AppIcon-blue.ico')
OUTPUTS = (SETUP, 'product-components-before.json',
           'product-components-after.json', 'local-build-evidence.json')


def fresh(root: Path) -> None:
    """Reject existing outputs and unsafe output directories."""
    if not root.is_dir():
        raise ValueError('expected existing output directory')
    safe_stat(root)
    if any((root / name).exists() or (root / name).is_symlink() for name in OUTPUTS):
        raise ValueError('output already exists')


def snapshot(compiler: Path, notices: Path, source: Path = ROOT) -> dict:
    """Check reviewed source, compiler, notices and exact local payload hashes."""
    script = source / 'installer/AJAZZBatteryTray.iss'
    safe_stat(script)
    if digest(read(script).replace(b'\r\n', b'\n')) != ALIGNED_SOURCE:
        raise ValueError('installer source differs')
    app = source / 'dist/app/AJAZZBatteryTray.exe'
    safe_stat(app)
    bundle = report(read_local(app))
    projects = [c for c in bundle['components'] if c['type'] == 'project']
    if len(projects) != 1 or (projects[0]['id'], projects[0]['version']) != (
            'AJAZZBatteryTray', '0.3.0-beta.61'):
        raise ValueError('unexpected application version or identity')
    icons = source / 'src/AjazzBatteryTray/Assets'
    for name in ICONS:
        safe_stat(icons / name)
    return {'installer_source_sha256': ALIGNED_SOURCE,
            'app_sha256': bundle['exe_sha256'],
            'icons': {name: file_digest(icons / name, LIMIT) for name in ICONS},
            'compiler': verify_components(compiler, document(read(PIN))),
            'notices': verify_files(tree_files(notices))}


@contextmanager
def normalized_timestamps(source: Path, notices: Path) -> Iterator[None]:
    """Apply the fixed UTC stamp to the exact payload and restore its metadata."""
    assets = source / 'src/AjazzBatteryTray/Assets'
    paths = [source / 'dist/app/AJAZZBatteryTray.exe']
    paths.extend(assets / name for name in ICONS)
    paths.extend(notices / name for name in sorted(NAMES))
    original = {path: safe_stat(path) for path in paths}
    try:
        for path, stamp in original.items():
            os.utime(path, ns=(stamp.st_atime_ns, FIXED_STAMP_NS))
        yield
    finally:
        for path, stamp in original.items():
            os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))


def arguments(compiler: Path, notices: Path, output: Path, source: Path = ROOT) -> list[str]:
    """Construct explicit compiler arguments; never use a shell or PATH lookup."""
    return [str(compiler / 'ISCC.exe'), '/DProductNoticeProbe=1',
            '/DProductionNoticeCandidate=1', f'/DNoticeRoot={notices}',
            f'/O{output}', str(source / 'installer/AJAZZBatteryTray.iss')]


def compile_candidate(compiler: Path, notices: Path, output: Path, before: dict,
                      source: Path = ROOT) -> None:
    """Compile only on Windows; bind post-build observations to the output."""
    if os.name != 'nt':
        raise ValueError('compilation requires Windows')
    write_json(output / OUTPUTS[1], before['compiler'])
    result = subprocess.run(arguments(compiler, notices, output, source), cwd=source,
                            check=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300)
    banner = b'Compiler engine version: Inno Setup 6.7.4'
    if sum(line.strip() == banner for line in result.stdout.splitlines()) != 1:
        raise ValueError('unexpected compiler banner')
    after = snapshot(compiler, notices, source)
    if before != after:
        raise ValueError('build input identity changed')
    safe_stat(output / SETUP)
    write_json(output / OUTPUTS[2], after['compiler'])
    write_json(output / OUTPUTS[3], {'schema': 'local-inno674-build-v1',
               'setup_sha256': file_digest(output / SETUP, LIMIT),
               'app_sha256': after['app_sha256'], 'icons': after['icons'],
               'installer_source_sha256': ALIGNED_SOURCE,
               'notice_manifest_sha256': after['notices']['manifest_sha256'],
               'engine_version': '6.7.4', 'input_identity': 'MATCH',
               'source_provenance': 'NOT_VERIFIED', 'lifecycle': 'NOT_RUN',
               'distribution_compliance': 'NOT_VERIFIED',
               'release_admission': 'NOT_VERIFIED'})


def main(argv: list[str] | None = None) -> int:
    """Default to non-executing preflight; require explicit compilation."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('compiler', 'notices', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--source', type=Path, default=ROOT, help='Prepared installer checkout')
    parser.add_argument('--reproducible', action='store_true',
                        help='Use the hosted fixed UTC payload timestamps during compilation')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--compile', action='store_true')
    args = parser.parse_args(argv)
    try:
        for path in (args.compiler, args.notices, args.output, args.source):
            safe_stat(path)
        compiler, notices, output = (p.resolve() for p in
                                     (args.compiler, args.notices, args.output))
        fresh(output)
        source = args.source.resolve()
        before = snapshot(compiler, notices, source)
        if args.compile:
            if args.reproducible and os.name != 'nt':
                raise ValueError('compilation requires Windows')
            stamp_policy = normalized_timestamps(source, notices) if args.reproducible else nullcontext()
            with stamp_policy:
                compile_candidate(compiler, notices, output, before, source)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError):
        print('FAIL: local candidate build or preflight', file=sys.stderr)
        return 2
    print('PASS: local build' if args.compile else 'PASS: dry-run; no compiler executed')
    print('Release admission and distribution compliance not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
