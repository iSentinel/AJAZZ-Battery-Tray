#!/usr/bin/env python3
"""Build a private notice-bearing ZIP from the exact consolidated portable artifact."""

import argparse
from io import BytesIO
import json
from pathlib import Path
import stat
import sys
import zipfile

from run_offline_qa import write_json
from stage_consolidated_signature_inputs import ARCHIVES, FILES, SOURCE
from verify_hardware_acceptance import ICONS, members
from verify_inno_solid import CANDIDATES
from verify_windows_notice_transport import MANIFEST_SHA, NAMES, digest, tree_files, verify_files
from verify_windowsdesktop_provenance import read_local

APP = 'AJAZZBatteryTray.exe'
PAYLOAD = ICONS | {APP}
OUTPUT_NAMES = PAYLOAD | {'portable.json'} | {'Notices/' + name for name in NAMES}
MAX_ZIP = 160 * 1024 * 1024


def pins() -> dict:
    """Return the exact app and icon identities independently verified from Setup."""
    rows = CANDIDATES['f939fea'][1]
    result = {APP: (rows[0][1], FILES[APP])}
    result.update({'Icons/' + name: (size, sha) for name, size, sha in rows[1:]})
    return result


def identity() -> bytes:
    """Bind original source, archive, payload and notice manifest without approval."""
    row = {'schema': 'consolidated-portable-notices-v1', 'source_sha': SOURCE,
           'original_archive_sha256': ARCHIVES['windows'], 'payload': {
               name: {'bytes': size, 'sha256': sha} for name, (size, sha) in pins().items()},
           'notice_manifest_sha256': MANIFEST_SHA, 'distribution_compliance': 'NOT_VERIFIED',
           'physical_acceptance': 'NOT_VERIFIED', 'release_admission': 'BLOCKED'}
    return (json.dumps(row, indent=2, sort_keys=True) + '\n').encode()


def verify_payload(files: dict) -> None:
    """Require the complete exact original five-file payload."""
    if set(files) != PAYLOAD or any((len(files[k]), digest(files[k])) != v for k, v in pins().items()):
        raise ValueError('portable payload differs')


def build(original: bytes, notices: dict) -> bytes:
    """Validate inputs then create a canonical stored ZIP without altering any file."""
    if digest(original) != ARCHIVES['windows']:
        raise ValueError('original portable archive differs')
    payload = members(original, PAYLOAD)
    verify_payload(payload)
    verify_files(notices)
    files = {**payload, 'portable.json': identity(),
             **{'Notices/' + name: raw for name, raw in notices.items()}}
    stream = BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, raw)
    return stream.getvalue()


def verify_zip(raw: bytes) -> dict:
    """Revalidate the bounded local package, exact files and notice bytes."""
    if not 0 < len(raw) <= MAX_ZIP:
        raise ValueError('portable ZIP exceeds limit')
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        infos = archive.infolist()
        if len(infos) != len(OUTPUT_NAMES) or {x.filename for x in infos} != OUTPUT_NAMES:
            raise ValueError('unexpected package inventory')
        for info in infos:
            limit = pins().get(info.filename, (1024 * 1024, ''))[0]
            if (info.orig_filename != info.filename or info.flag_bits or info.create_system != 3
                    or info.external_attr != (stat.S_IFREG | 0o644) << 16
                    or info.compress_type != zipfile.ZIP_STORED
                    or not 0 < info.file_size <= limit):
                raise ValueError('invalid package member')
        if sum(x.file_size for x in infos) > MAX_ZIP:
            raise ValueError('package member budget exceeded')
        files = {x.filename: archive.read(x) for x in infos}
    verify_payload({k: files[k] for k in PAYLOAD})
    if files['portable.json'] != identity():
        raise ValueError('package identity differs')
    notice = verify_files({k: files['Notices/' + k] for k in NAMES})
    return {'schema': 'consolidated-portable-notices-review-v1', 'source_sha': SOURCE,
            'archive_sha256': digest(raw), 'original_archive_sha256': ARCHIVES['windows'],
            'app_sha256': FILES[APP], 'notice_transport': notice,
            'runtime_execution': 'NOT_PERFORMED', 'release_admission': 'BLOCKED'}


def main(argv: list[str] | None = None) -> int:
    """Create and reread a private package; never publish or overwrite files."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('original', 'notices', 'archive', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if any(p.exists() or p.is_symlink() for p in (args.archive, args.output)):
            raise ValueError('existing output')
        if args.archive.resolve() == args.output.resolve():
            raise ValueError('output paths must differ')
        raw = build(read_local(args.original), tree_files(args.notices))
        verify_zip(raw)
        with args.archive.open('xb') as stream:
            stream.write(raw)
        write_json(args.output, verify_zip(read_local(args.archive)))
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile):
        print('FAIL: consolidated portable notice prototype', file=sys.stderr)
        return 2
    print('PASS: private portable notice transport; release BLOCKED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
