#!/usr/bin/env python3
"""Build a local-only portable prototype from the exact historical candidate."""

import argparse
import io
import json
import lzma
from pathlib import Path
import stat
import struct
import sys
import zipfile

from run_offline_qa import write_json
from verify_inno_inner_engine import recover
from verify_inno_setup_data import FILES, SETUP_SHA, decode_setup0, locations
from verify_inno_solid import file_hashes
from verify_installer_candidate import SETUP, members, read_member, verify
from verify_windows_notice_transport import (
    MANIFEST_SHA, NAMES, digest, tree_files, verify_files,
)
from verify_windowsdesktop_provenance import read_local

SOURCE = '3dd4d8477f440691476752cbc124ca3e32a1d8ca'
CANDIDATE_SHA = '7c0739db76e39b01d55585ef9001a1eba144bd82ea61c4419abe2fdd1d45f557'
APP = 'AJAZZBatteryTray-win-x64.exe'
MAX_ZIP = 160 * 1024 * 1024


def recover_app(candidate: bytes) -> bytes:
    """Bind exact candidate archive and decode all solid file hashes."""
    record = verify(candidate, CANDIDATE_SHA, SOURCE)['candidate']
    if record['setup_sha256'] != SETUP_SHA or record['app_sha256'] != FILES[0][2]:
        raise ValueError('historical candidate identity differs')
    with zipfile.ZipFile(io.BytesIO(candidate)) as archive:
        setup = read_member(archive, members(archive)[SETUP])
    _, offsets = recover(setup)
    _, table, _ = decode_setup0(setup[offsets['offset0']:offsets['engine_offset']])
    payload = setup[offsets['offset1']:offsets['offset0']]
    locations(table, payload)
    stream = io.BytesIO()
    file_hashes(payload, FILES, app_sink=stream)
    return stream.getvalue()


def manifest() -> bytes:
    """Bind prototype to reviewed candidate and notice manifest, never admission."""
    data = {'schema': 1, 'scope': 'local historical portable prototype',
            'source_sha': SOURCE, 'candidate_archive_sha256': CANDIDATE_SHA,
            'setup_sha256': SETUP_SHA, 'app_sha256': FILES[0][2],
            'notice_manifest_sha256': MANIFEST_SHA,
            'physical_acceptance': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}
    return (json.dumps(data, indent=2, sort_keys=True) + '\n').encode()


def verify_members(files: dict[str, bytes]) -> dict:
    """Require exact application, notices and candidate-bound manifest."""
    if set(files) != {APP, 'portable.json'} | {'Notices/' + name for name in NAMES}:
        raise ValueError('unexpected portable members')
    if len(files[APP]) != FILES[0][1] or digest(files[APP]) != FILES[0][2]:
        raise ValueError('portable app differs')
    if files['portable.json'] != manifest():
        raise ValueError('portable identity differs')
    notice = verify_files({name: files['Notices/' + name] for name in NAMES})
    return {'schema': 1, 'source_sha': SOURCE, 'app_sha256': FILES[0][2],
            'candidate_archive_sha256': CANDIDATE_SHA, 'notice_transport': notice,
            'runtime_execution': 'NOT_PERFORMED', 'release_admission': 'NOT_VERIFIED'}


def build(app: bytes, notices: dict[str, bytes]) -> bytes:
    """Write a deterministic stored ZIP after verification of all member bytes."""
    files = {APP: app, 'portable.json': manifest(),
             **{'Notices/' + name: raw for name, raw in notices.items()}}
    verify_members(files)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, raw)
    return stream.getvalue()


def verify_zip(raw: bytes) -> dict:
    """Bound member reads and verify exact application/notice provenance."""
    if len(raw) > MAX_ZIP:
        raise ValueError('portable ZIP exceeds size budget')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        names = {APP, 'portable.json'} | {'Notices/' + name for name in NAMES}
        if len(infos) != len(names) or {x.filename for x in infos} != names:
            raise ValueError('unexpected portable ZIP inventory')
        files, total = {}, 0
        for info in infos:
            limit = FILES[0][1] if info.filename == APP else 1024 * 1024
            if (info.orig_filename != info.filename or info.flag_bits
                    or info.compress_type != zipfile.ZIP_STORED
                    or info.external_attr != (stat.S_IFREG | 0o644) << 16
                    or not 0 < info.file_size <= min(limit, MAX_ZIP - total)):
                raise ValueError('invalid portable member')
            data = read_member(archive, info)
            files[info.filename] = data
            total += len(data)
    result = verify_members(files)
    result['portable_zip_sha256'] = digest(raw)
    return result


def main(argv: list[str] | None = None) -> int:
    """Create a new local prototype, reread it, and emit scoped evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--notices', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if any(path.exists() or path.is_symlink() for path in (args.archive, args.output)):
            raise ValueError('existing output')
        notices = tree_files(args.notices)
        verify_files(notices)
        raw = build(recover_app(read_local(args.candidate)), notices)
        with args.archive.open('xb') as stream:
            stream.write(raw)
        result = verify_zip(read_local(args.archive))
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, RuntimeError, EOFError, struct.error,
            lzma.LZMAError, zipfile.BadZipFile):
        print('FAIL: local portable notice prototype', file=sys.stderr)
        return 2
    print('PASS: historical portable prototype; no release admission')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
