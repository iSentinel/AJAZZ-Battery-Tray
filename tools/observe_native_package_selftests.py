#!/usr/bin/env python3
"""Run only reviewed synthetic CLI self-tests from exact extracted proposals."""

import argparse
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

from build_consolidated_portable_notices import APP, OUTPUT_NAMES
from inventory_apple_archive import EDITIONS, archive_members
from observe_native_package_extraction import verify_tree
from review_normalized_package_set import PACKAGES, check_package, proposal
from run_offline_qa import write_json
from verify_hardware_acceptance import APPLE_NAMES, members
from verify_windows_notice_transport import digest
from verify_windowsdesktop_provenance import read_local

CORPUS_SHA = 'bd0905806f68054ee0d30e70100aa0cccdbaa79c5ae4ccd910caaaf972f83438'
CASES = {
    'windows': (('--help', 0, 15), ('--self-test-routine-poll-worker', 0, 25),
                ('--self-test-full-hid-watchdog', 124, 15),
                ('--self-test-full-hid-start-gate', 0, 30),
                ('--self-test-full-hid-parent-exit', 0, 30)),
    'universal': (('--help', 0, 15), ('--self-test', 0, 45),
                  ('--self-test-bounded-poll', 0, 45)),
    'high-sierra': (('--help', 0, 15), ('--self-test', 0, 45),
                    ('--self-test-routine-poll', 0, 45),
                    ('--self-test-menu-diagnostic', 0, 45)),
}


def inputs(root: Path, edition: str, original: bytes, license_bytes: bytes) -> tuple:
    """Revalidate the outer package and exact extracted executable inventory."""
    raw = read_local(root / PACKAGES[edition][0])
    check_package(raw, edition, original, license_bytes)
    outer = root / (edition + '-outer')
    if edition == 'windows':
        files = members(raw, OUTPUT_NAMES)
        verify_tree(outer, {name: (data, 0) for name, data in files.items()})
        return outer / APP, digest(files[APP])
    from build_consolidated_apple_notices import package_files
    files = package_files(original, license_bytes, edition)
    verify_tree(outer, {name: (data, 0) for name, data in files.items()})
    inner = archive_members(files[APPLE_NAMES[edition] + '.zip'])
    dest = root / (edition + '-inner')
    verify_tree(dest, inner, executable_modes=True)
    bundle, executable = EDITIONS[edition][:2]
    relative = f'{bundle}/Contents/MacOS/{executable}'
    return dest / relative, digest(inner[relative][0])


def check_result(mode: str, actual: int, expected: int, elapsed: float) -> dict:
    """Require expected status and a genuine bounded watchdog observation."""
    if actual != expected or (expected == 124 and elapsed < 1):
        raise ValueError('synthetic self-test outcome differs')
    return {'mode': mode, 'exit_code': actual, 'expected_exit_code': expected,
            'result': 'PASS'}


def run_case(exe: Path, case: tuple, env: dict) -> dict:
    """Run a fixed synthetic mode with a bounded native process lifetime."""
    mode, expected, timeout = case
    start = time.monotonic()
    if sys.platform == 'win32':
        # Match the reviewed original CI process-tree timeout policy.
        command = ['pwsh', '-NoProfile', '-NonInteractive', '-Command',
                   '$ErrorActionPreference="Stop"; '
                   '$p=Start-Process -FilePath $env:AJAZZ_TEST_EXE '
                   '-ArgumentList $env:AJAZZ_TEST_MODE -PassThru; '
                   'if (!$p.WaitForExit([int]$env:AJAZZ_TEST_TIMEOUT)) '
                   '{ $p.Kill($true); exit 125 }; exit $p.ExitCode']
        env = {**env, 'AJAZZ_TEST_EXE': str(exe), 'AJAZZ_TEST_MODE': mode,
               'AJAZZ_TEST_TIMEOUT': str(timeout * 1000)}
    else:
        command = [str(exe), mode]
    result = subprocess.run(command, cwd=exe.parent, env=env, timeout=timeout + 10,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            check=False)
    print(f'CASE: {mode}; exit={result.returncode}; expected={expected}', flush=True)
    return check_result(mode, result.returncode, expected, time.monotonic() - start)


def observe(root: Path, edition: str, original: bytes, license_bytes: bytes, corpus: Path) -> dict:
    """Execute fixed modes only after exact validation and recheck bytes afterwards."""
    if digest(read_local(corpus)) != CORPUS_SHA:
        raise ValueError('synthetic corpus differs')
    print('PASS: pinned synthetic corpus', flush=True)
    exe, sha = inputs(root, edition, original, license_bytes)
    print('PASS: pre-test package inventory', flush=True)
    env = {**os.environ, 'AJAZZ_TEST_CORPUS': str(corpus.resolve())}
    results = []
    for case in CASES[edition]:
        if digest(read_local(exe)) != sha:
            raise ValueError('self-test executable differs')
        results.append(run_case(exe.resolve(), case, env))
    if inputs(root, edition, original, license_bytes) != (exe, sha):
        raise ValueError('post-test package differs')
    return {'schema': 'native-package-selftests-v1', 'edition': edition,
            'source_sha': proposal()['source_sha'], 'package_sha256': PACKAGES[edition][1],
            'executable_sha256': sha, 'corpus_sha256': CORPUS_SHA,
            'runner_os': platform.platform(), 'cases': results,
            'post_test_inventory': 'MATCH', 'gui_launch': 'NOT_RUN',
            'physical_acceptance': 'NOT_VERIFIED', 'release_admission': 'BLOCKED'}


def main(argv: list[str] | None = None) -> int:
    """Report bounded synthetic self-tests only, never start normal Tray GUI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--edition', choices=CASES, required=True)
    for name in ('root', 'original', 'license', 'corpus', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if (args.edition == 'windows' and sys.platform != 'win32'
                or args.edition != 'windows' and sys.platform != 'darwin'):
            raise ValueError('wrong native host')
        if args.output.exists() or args.output.is_symlink():
            raise ValueError('existing observation')
        row = observe(args.root.resolve(), args.edition, read_local(args.original),
                      read_local(args.license), args.corpus)
        write_json(args.output, row)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'FAIL: native package synthetic self-tests ({type(error).__name__})', file=sys.stderr)
        return 2
    print('PASS: native synthetic self-tests; GUI NOT_RUN; release BLOCKED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
