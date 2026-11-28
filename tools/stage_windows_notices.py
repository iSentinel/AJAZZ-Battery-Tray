#!/usr/bin/env python3
"""Stage scoped Windows notice files from reviewed sources, without admission."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

from inventory_dotnet_bundle import BundleError
from inventory_dotnet_pack_licenses import PACKS
from stage_dotnet_notices import collect
from verify_windowsdesktop_provenance import read_local

ROOT = Path(__file__).resolve().parents[1]
REPO_PINS = {
    'LICENSE': '9b0d8bab09e6219fb516af7dd95357ef2cb6ebca5bddb94a7eb2f04501f6d336',
    'docs/third-party/inno-6.7.1/Inno-Setup-LICENSE.txt':
        '2e5346868c2a18434489824e11d65c3031620f792fefc415d05f19cd441abf5c',
    'docs/third-party/inno-6.7.1/Pascal-Script-LICENSE.txt':
        'a08799bb2385a3af99a9bbb7c746d0ad9ac7dd07be0fb1473f2f4d1dc3e11bd1',
    'docs/third-party/inno-6.7.1/LZMA-SDK-7zC.txt':
        'e5cc6089348474fc82631365932b1aa09df26a8cfc9f320bbb2509a7b3fc7a0c',
}
PACKAGE_NOTICES = {
    'host': {'license.txt', 'third-party-notices.txt'},
    'core': {'license.txt', 'third-party-notices.txt'},
    'desktop': {'license'},
    'sdk': set(),
}


def repository_notices(root: Path) -> dict[str, bytes]:
    """Read exact reviewed project and Inno notice bytes."""
    result = {}
    for name, sha in REPO_PINS.items():
        data = read_local(root / name)
        if hashlib.sha256(data).hexdigest() != sha:
            raise BundleError('Reviewed repository notice digest differs')
        dest = 'AJAZZ/LICENSE' if name == 'LICENSE' else 'Inno/' + Path(name).name
        result[dest] = data
    return result


def package_notices(packs: dict) -> tuple[dict[str, bytes], list[dict]]:
    """Revalidate all four packs, preserving names in separate directories."""
    if set(packs) != set(PACKS):
        raise BundleError('Expected four reviewed package inputs')
    result, evidence = {}, []
    for kind in PACKS:
        record, files = collect(packs[kind], kind)
        if ({name.casefold() for name in files} != PACKAGE_NOTICES[kind]
                or len(files) != len(PACKAGE_NOTICES[kind])):
            raise BundleError('Unexpected package notice set')
        for name, data in files.items():
            result[f'DotNet/{kind}/{name}'] = data
        evidence.append(record)
    return result, evidence


def stage(packs: dict, output: Path, root: Path = ROOT) -> dict:
    """Stage exact local bytes into a fresh directory only after validation."""
    repo = repository_notices(root)
    package, evidence = package_notices(packs)
    files = repo | package
    if len(files) != 9 or output.exists() or output.is_symlink():
        raise BundleError('Unexpected notice count or existing output')
    output.mkdir(mode=0o700)
    rows = []
    for name, data in sorted(files.items()):
        path = output / name
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
        if path.read_bytes() != data:
            raise BundleError('Staged notice bytes differ')
        rows.append({'path': name, 'bytes': len(data),
                     'sha256': hashlib.sha256(data).hexdigest()})
    result = {'schema': 1, 'scope': 'reviewed Windows notice preparation only',
              'files': rows, 'packages': evidence,
              'distribution_compliance': 'NOT_VERIFIED',
              'sdk_terms': 'REVIEW_REQUIRED', 'windows_single_file_terms': 'REVIEW_REQUIRED',
              'transitive_inno_terms': 'REVIEW_REQUIRED', 'release_admission': 'NOT_VERIFIED'}
    with (output / 'manifest.json').open('xb') as stream:
        stream.write((json.dumps(result, indent=2, sort_keys=True) + '\n').encode('utf-8'))
    return result


def main(argv: list[str] | None = None) -> int:
    """Prepare notices locally; never change or publish an installer."""
    parser = argparse.ArgumentParser(description=__doc__)
    for kind in PACKS:
        parser.add_argument('--' + kind, type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        stage({kind: read_local(getattr(args, kind)) for kind in PACKS}, args.output)
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile, ET.ParseError):
        print('FAIL: scoped Windows notice staging', file=sys.stderr)
        return 2
    print('PASS: nine reviewed notices staged; distribution compliance not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
