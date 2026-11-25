#!/usr/bin/env python3
"""Verify the exact scoped notice tree and create a deterministic local ZIP."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import zipfile

from inventory_dotnet_bundle import BundleError
from read_diagnostic_session import unique_object
from run_offline_qa import write_json

MANIFEST_SHA = 'b151b2a7ed4f40ef0859b2f846c87b4211290751b8092eba0aac69bdaac0649c'
MAX_BYTES = 1024 * 1024
NAMES = frozenset({
    'AJAZZ/LICENSE',
    'DotNet/core/LICENSE.TXT', 'DotNet/core/THIRD-PARTY-NOTICES.TXT',
    'DotNet/desktop/LICENSE', 'DotNet/host/LICENSE.TXT',
    'DotNet/host/THIRD-PARTY-NOTICES.TXT',
    'Inno/Inno-Setup-LICENSE.txt', 'Inno/LZMA-SDK-7zC.txt',
    'Inno/Pascal-Script-LICENSE.txt', 'manifest.json',
})


def digest(raw: bytes) -> str:
    """Return the SHA-256 of immutable bytes."""
    return hashlib.sha256(raw).hexdigest()


def safe_stat(path: Path) -> os.stat_result:
    """Reject symlinks and Windows reparse points."""
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
        raise BundleError('Notice tree contains a link or reparse point')
    return info


def tree_files(root: Path) -> dict[str, bytes]:
    """Read exactly the reviewed regular files and no extra directories."""
    if not stat.S_ISDIR(safe_stat(root).st_mode):
        raise BundleError('Expected notice directory')
    allowed_dirs = {str(parent.as_posix()) for name in NAMES
                    for parent in Path(name).parents if parent != Path('.')}
    pending, result, total = [root], {}, 0
    while pending:
        directory = pending.pop()
        for path in directory.iterdir():
            name = path.relative_to(root).as_posix()
            info = safe_stat(path)
            if stat.S_ISDIR(info.st_mode) and name in allowed_dirs:
                pending.append(path)
                continue
            if (not stat.S_ISREG(info.st_mode) or name not in NAMES
                    or not 0 < info.st_size <= MAX_BYTES - total):
                raise BundleError('Unexpected notice tree entry')
            with path.open('rb') as stream:
                data = stream.read(info.st_size + 1)
            if len(data) != info.st_size:
                raise BundleError('Notice file size changed')
            result[name] = data
            total += len(data)
    return result


def verify_files(files: dict[str, bytes]) -> dict:
    """Require pinned manifest and every exact declared notice payload."""
    if set(files) != NAMES or sum(map(len, files.values())) > MAX_BYTES:
        raise BundleError('Unexpected notice member set or size')
    raw = files['manifest.json']
    if digest(raw) != MANIFEST_SHA:
        raise BundleError('Notice manifest differs from reviewed pin')
    manifest = json.loads(raw, object_pairs_hook=unique_object)
    rows = [{'path': name, 'bytes': len(data), 'sha256': digest(data)}
            for name, data in sorted(files.items()) if name != 'manifest.json']
    if rows != manifest['files'] or manifest['release_admission'] != 'NOT_VERIFIED':
        raise BundleError('Notice payload or admission differs')
    return {'manifest_sha256': MANIFEST_SHA, 'files': rows,
            'notice_transport': 'MATCH', 'distribution_compliance': 'NOT_VERIFIED',
            'release_admission': 'NOT_VERIFIED'}


def archive_bytes(files: dict[str, bytes]) -> bytes:
    """Create canonical stored ZIP with fixed timestamp and permissions."""
    verify_files(files)
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, raw in sorted(files.items()):
            item = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            item.create_system = 3
            item.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(item, raw)
    return output.getvalue()


def archive_files(raw: bytes) -> dict[str, bytes]:
    """Reject aliases, symlinks, extra metadata and unreviewed ZIP encodings."""
    if len(raw) > MAX_BYTES:
        raise BundleError('Notice ZIP exceeds limit')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        if len(infos) != len(NAMES) or {x.filename for x in infos} != NAMES:
            raise BundleError('Unexpected notice ZIP member set')
        result = {}
        total = 0
        for item in infos:
            if (item.orig_filename != item.filename or item.flag_bits
                    or item.compress_type != zipfile.ZIP_STORED
                    or item.create_system != 3 or item.external_attr != (stat.S_IFREG | 0o644) << 16
                    or not 0 < item.file_size <= MAX_BYTES - total):
                raise BundleError('Unexpected notice ZIP member metadata')
            data = archive.read(item)
            if len(data) != item.file_size:
                raise BundleError('Notice ZIP size differs')
            result[item.filename] = data
            total += len(data)
    if archive_bytes(result) != raw:
        raise BundleError('Noncanonical notice ZIP')
    return result


def read_zip(path: Path) -> bytes:
    """Read a bounded regular ZIP file."""
    info = safe_stat(path)
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_BYTES:
        raise BundleError('Invalid notice ZIP')
    with path.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) != info.st_size:
        raise BundleError('Notice ZIP size changed')
    return raw


def main(argv: list[str] | None = None) -> int:
    """Verify a staged/installed tree or ZIP; optionally create a local archive."""
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--tree', type=Path)
    inputs.add_argument('--archive', type=Path)
    parser.add_argument('--create-archive', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.archive and args.create_archive:
            raise BundleError('Archive creation requires a tree')
        raw = read_zip(args.archive) if args.archive else None
        files = archive_files(raw) if raw is not None else tree_files(args.tree)
        result = verify_files(files)
        if args.create_archive:
            raw = archive_bytes(files)
            with args.create_archive.open('xb') as stream:
                stream.write(raw)
            archive_files(read_zip(args.create_archive))
        if raw is not None:
            result['archive_sha256'] = digest(raw)
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile):
        print('FAIL: scoped notice transport', file=sys.stderr)
        return 2
    print('PASS: exact reviewed notice transport; distribution compliance not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
