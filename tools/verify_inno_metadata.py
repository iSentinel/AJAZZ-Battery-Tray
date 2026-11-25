"""Reconstruct scoped Inno 6.7.1 manifest and version resource payloads."""

import struct

from compare_inno_loader import digest
from verify_dotnet_host_resources import ResourceTree, resource_area, unpack

VERSION = ('16', '1', '1033')
MANIFEST = ('24', '1', '1033')
ENTRY = b'<file name="comctl32.dll" loadFrom="%SystemRoot%\\system32\\" />\r\n'
MAX_AREA = 8 * 1024 * 1024


class MetadataTree(ResourceTree):
    """Collect only two bounded metadata payloads from the validated tree."""

    def leaf(self, pos: int, path: tuple) -> None:
        """Retain selected local payloads, never export their content."""
        super().leaf(pos, path)
        if path in (VERSION, MANIFEST):
            address, length, _, _ = unpack(self.raw, pos, '<IIII')
            start = address - self.rva
            self.leaves[path] = self.raw[start:start + length]


def metadata(raw: bytes) -> dict:
    """Return the selected payloads in a bounded resource area."""
    area, rva = resource_area(raw)
    if len(area) > MAX_AREA:
        raise ValueError('resource area exceeds limit')
    tree = MetadataTree(area, rva)
    tree.visit(0)
    return {key: tree.leaves[key] for key in (VERSION, MANIFEST)}


def manifest(template: bytes) -> bytes:
    """Replay the compiler's in-place COMCTL32 sideload prevention."""
    start, end, first = b'<dependency>', b'</dependency>', b'<file name="'
    if template.count(start) != 1 or template.count(end) != 1:
        raise ValueError('unexpected dependency count')
    p = template.index(start)
    q = template.index(end) + len(end)
    r = template.find(first)
    if not p < q < r or q - p < len(ENTRY):
        raise ValueError('unexpected manifest structure')
    return (template[:p] + b' ' * (q - p - len(ENTRY))
            + template[q:r] + ENTRY + template[r:])


def set_padded_string(raw: bytearray, key: str, value: str) -> None:
    """Replace only the unique fixed-capacity string's space prefix."""
    token = (key + '\0').encode('utf-16le')
    if raw.count(token) != 1:
        raise ValueError('unexpected version key count')
    pos = raw.index(token)
    if pos < 6:
        raise ValueError('invalid version key')
    size, count, kind = struct.unpack_from('<HHH', raw, pos - 6)
    start = (pos + len(token) + 3) & ~3
    end = start + count * 2
    if (kind != 1 or count < 2 or end != pos - 6 + size or end > len(raw)
            or raw[start:end] != (' ' * (count - 1) + '\0').encode('utf-16le')):
        raise ValueError('unexpected version placeholder')
    replacement = value.encode('utf-16le')
    if len(replacement) > (count - 1) * 2:
        raise ValueError('version value exceeds placeholder')
    raw[start:start + len(replacement)] = replacement


def version(template: bytes, kind: str) -> bytes:
    """Replay reviewed beta.61 string overrides, preserve all other bytes."""
    if kind not in ('loader', 'engine'):
        raise ValueError('unknown version resource kind')
    if len(template) != (1412 if kind == 'loader' else 1300):
        raise ValueError('unexpected version resource extent')
    raw = bytearray(template)
    values = {'CompanyName': 'iSentinel', 'ProductName': 'AJAZZ Battery Tray',
              'ProductVersion': '0.3.0-beta.61'}
    if kind == 'loader':
        values['FileDescription'] = 'AJAZZ Battery Tray Setup'
    for key, value in values.items():
        set_padded_string(raw, key, value)
    return bytes(raw)


def compare_metadata(template: bytes, actual: bytes, kind: str) -> dict:
    """Require exact reconstructed payload bytes, including all padding."""
    before, after = metadata(template), metadata(actual)
    expected_version = version(before[VERSION], kind)
    expected_manifest = manifest(before[MANIFEST]) if kind == 'loader' else before[MANIFEST]
    if after[VERSION] != expected_version or after[MANIFEST] != expected_manifest:
        raise ValueError('version or manifest bytes differ')
    return {'version': 'MATCH', 'version_sha256': digest(expected_version),
            'manifest': 'MATCH', 'manifest_sha256': digest(expected_manifest)}
