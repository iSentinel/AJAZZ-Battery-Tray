"""Read a bounded local diagnostic session ZIP without extracting any files."""

from datetime import datetime
from io import BytesIO
import json
import os
from pathlib import Path
import stat
import zipfile

from normalize_device_diagnostics import windows_utc

MAX_REPORTS = 32
MAX_REPORT = 1024 * 1024
MAX_TOTAL = 8 * MAX_REPORT
MAX_ARCHIVE = 9 * MAX_REPORT
MAX_MANIFEST = 65536
MARKERS = frozenset(('Baseline', 'UsbSelected', 'BluetoothSelected',
                     'Sleep', 'Wake', 'Other', 'ReviewedReport'))


def read_archive(path: Path) -> bytes:
    """Reject special files and symlinks; bound the complete archive read."""
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_ARCHIVE:
        raise ValueError('invalid archive file')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    with os.fdopen(os.open(path, flags | getattr(os, 'O_BINARY', 0)), 'rb') as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or (
                opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise ValueError('archive identity changed')
        data = stream.read(MAX_ARCHIVE + 1)
    if len(data) > MAX_ARCHIVE:
        raise ValueError('archive size exceeded')
    return data


def unique_object(pairs: list[tuple]) -> dict:
    """Reject duplicate manifest keys rather than silently overriding them."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate manifest key')
        result[key] = value
    return result


def validate_members(archive: zipfile.ZipFile) -> dict:
    """Accept only exact expected names and bounded regular entries."""
    members = archive.infolist()
    if not 3 <= len(members) <= MAX_REPORTS + 1:
        raise ValueError('invalid archive member count')
    expected = {'manifest.json'} | {f'snapshot-{i:02d}.txt'
                                   for i in range(1, len(members))}
    if {info.filename for info in members} != expected:
        raise ValueError('invalid or duplicate member name')
    if sum(info.file_size for info in members if info.filename != 'manifest.json') > MAX_TOTAL:
        raise ValueError('session size exceeded')
    for info in members:
        limit = MAX_MANIFEST if info.filename == 'manifest.json' else MAX_REPORT
        mode = (info.external_attr >> 16) & 0xffff
        if (info.orig_filename != info.filename or info.is_dir() or info.flag_bits & 1
                or stat.S_IFMT(mode) not in (0, stat.S_IFREG)
                or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                or not 0 < info.file_size <= limit):
            raise ValueError('invalid archive member')
    return {info.filename: info for info in members}


def read_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> bytes:
    """Check decompressed length and CRC using a bounded read to EOF."""
    with archive.open(info) as stream:
        data = stream.read(info.file_size + 1)
    if len(data) != info.file_size:
        raise ValueError('member size mismatch')
    return data


def parse_manifest(raw: bytes, members: dict) -> list[dict]:
    """Verify the exact emitter schema and explicit owner annotation semantics."""
    manifest = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
    if not isinstance(manifest, dict) or set(manifest) != {
            'schema', 'identityBinding', 'markers', 'entries'}:
        raise ValueError('invalid session manifest')
    if (manifest['schema'], manifest['identityBinding'], manifest['markers']) != (
            'diagnostic-session-v1', 'NOT_VERIFIED', 'OWNER_ANNOTATED'):
        raise ValueError('unsupported session manifest')
    entries = manifest['entries']
    if not isinstance(entries, list) or len(entries) != len(members) - 1:
        raise ValueError('invalid manifest count')
    previous = None
    result = []
    for i, entry in enumerate(entries, 1):
        name = f'snapshot-{i:02d}.txt'
        if (not isinstance(entry, dict) or set(entry) != {'file', 'marker', 'addedUtc', 'bytes'}
                or entry['file'] != name or not isinstance(entry['marker'], str)
                or entry['marker'] not in MARKERS or type(entry['bytes']) is not int
                or entry['bytes'] != members[name].file_size
                or not isinstance(entry['addedUtc'], str)):
            raise ValueError('invalid manifest entry')
        utc = windows_utc(entry['addedUtc'])
        stamp = datetime.fromisoformat(utc) if utc else None
        if stamp is None or (previous is not None and stamp <= previous):
            raise ValueError('invalid annotation chronology')
        previous = stamp
        result.append({'marker': entry['marker'], 'added_utc': utc})
    return result


def load_session(path: Path) -> list[tuple[str, dict]]:
    """Return report text and validated annotations, without filesystem extraction."""
    with zipfile.ZipFile(BytesIO(read_archive(path))) as archive:
        members = validate_members(archive)
        annotations = parse_manifest(read_member(archive, members['manifest.json']), members)
        return [(read_member(archive, members[f'snapshot-{i:02d}.txt']).decode('utf-8'),
                 entry) for i, entry in enumerate(annotations, 1)]
