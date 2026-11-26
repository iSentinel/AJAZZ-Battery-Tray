#!/usr/bin/env python3
"""Stage only exact previously reviewed CI binaries for read-only signature checks."""

import argparse
from io import BytesIO
from pathlib import Path
import sys
import zipfile

from verify_hardware_acceptance import ICONS, members
from verify_installer_candidate import SETUP, digest
from verify_uninstaller_evidence import EXE, verify_pair
from verify_windowsdesktop_provenance import read_local

SOURCE = 'f939fea7fb422aa588649138d29a750ce62cd22a'
ARCHIVES = {
    'windows': 'e06bda2f95725a37f206cfbaffe6f3b333c735ea0a8e580fe092ccbfed340302',
    'installer': '73de3837a16ac39deeb99ebfb314501203b58a3092e91bb0989df92b2b38c99c',
    'uninstaller': '98177de43879038203f36a1a4bbcf0b0f6d6ab10166813e124517d8d3677d9ce',
}
FILES = {
    'AJAZZBatteryTray.exe': '91f8eea23bd06d926fc2d665d3b69bda64da385cf0051cfeae7a0844a7ff9a6c',
    SETUP: '1cc71e5c2a7119070c80611160b5e263afd2b70155f33b13a88fac848d67542e',
    EXE: '9548d6786c0ae2531a4e4bcd183db9805bd88b7c98571fd033f1b4f05967da65',
}


def collect(raw: dict[str, bytes]) -> dict[str, bytes]:
    """Check all archive pins and identity bindings before extracting bytes."""
    if set(raw) != set(ARCHIVES) or any(digest(raw[k]) != v for k, v in ARCHIVES.items()):
        raise ValueError('original artifact digest differs')
    verify_pair(raw['uninstaller'], ARCHIVES['uninstaller'], raw['installer'],
                ARCHIVES['installer'], SOURCE)
    app = members(raw['windows'], ICONS | {'AJAZZBatteryTray.exe'})['AJAZZBatteryTray.exe']
    with zipfile.ZipFile(BytesIO(raw['installer'])) as archive:
        setup = archive.read(SETUP)
    with zipfile.ZipFile(BytesIO(raw['uninstaller'])) as archive:
        uninstaller = archive.read(EXE)
    files = {'AJAZZBatteryTray.exe': app, SETUP: setup, EXE: uninstaller}
    if any(digest(files[k]) != v for k, v in FILES.items()):
        raise ValueError('candidate binary digest differs')
    return files


def stage(files: dict[str, bytes], root: Path) -> None:
    """Create a fresh output directory; refuse overwriting existing evidence."""
    root.mkdir(mode=0o700, exist_ok=False)
    for name, data in files.items():
        with (root / name).open('xb') as stream:
            stream.write(data)


def main(argv: list[str] | None = None) -> int:
    """Validate and stage local bytes without network access or execution."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ARCHIVES:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        stage(collect({k: read_local(getattr(args, k)) for k in ARCHIVES}), args.output)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile):
        print('FAIL: exact signature input staging', file=sys.stderr)
        return 2
    print('PASS: exact signature inputs staged; trust not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
