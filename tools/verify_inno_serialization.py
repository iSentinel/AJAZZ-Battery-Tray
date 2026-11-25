"""Reconstruct the observed Inno Windows resource serialization after payload verification."""

import struct

from compare_inno_loader import digest, layout
from verify_dotnet_host_resources import HIGH, ResourceTree, resource_area, unpack
from verify_dotnet_resource_serialization import directory

MAX_AREA = 8 * 1024 * 1024
NAMES = frozenset(('DVCLAL', 'PACKAGEINFO', 'MAINICON', 'HELPER_EXE_AMD64',
                   'MSG_ERROR', 'MSG_INFO', 'MSG_WARNING', 'TNEWDISKFORM',
                   'TSELECTFOLDERFORM', 'TSELECTLANGUAGEFORM',
                   'TUNINSTALLPROGRESSFORM', 'TUNINSTALLSHAREDFILEFORM',
                   'TWIZARDFORM', 'Z_GROUPICON'))


class InnoTree(ResourceTree):
    """Read bounded payloads and only reviewed numeric or named keys."""

    def key(self, value: int, depth: int) -> int | str:
        """Decode reviewed names after standard bounds and depth checks."""
        super().key(value, depth)
        if not value & HIGH:
            return value
        pos = value & ~HIGH
        size, = unpack(self.raw, pos, '<H')
        name = self.raw[pos + 2:pos + 2 + size * 2].decode('utf-16le')
        if depth != 1 or name not in NAMES:
            raise ValueError('unsupported Inno resource name')
        return name

    def leaf(self, pos: int, path: tuple) -> None:
        """Collect validated payloads under a cumulative size budget."""
        address, length, _, _ = unpack(self.raw, pos, '<IIII')
        self.payload_bytes = getattr(self, 'payload_bytes', 0) + length
        if self.payload_bytes > MAX_AREA:
            raise ValueError('resource payload budget exceeded')
        super().leaf(pos, path)
        start = address - self.rva
        self.leaves[path] = self.raw[start:start + length]


def tree_group(leaves: dict) -> dict:
    """Build the three-level observed tree with strictly scoped identifiers."""
    if not leaves or len(leaves) > 4096 or sum(map(len, leaves.values())) > MAX_AREA:
        raise ValueError('resource tree budget exceeded')
    root = {}
    for (kind, name, lang), data in leaves.items():
        if (type(kind) is not int or not 0 <= kind <= 65535 or lang not in (0, 1033)
                or not (type(name) is int and 0 <= name <= 65535
                        or isinstance(name, str) and name in NAMES)):
            raise ValueError('unsupported resource key')
        root.setdefault(kind, {}).setdefault(name, {})[lang] = data
    return root


def serialize(leaves: dict, rva: int) -> bytes:
    """Rebuild observed directories, leaf records, names and padded payloads."""
    out = bytearray()
    names = {}
    pending = directory(out, tree_group(leaves), names)
    for _ in range(2):
        next_level = []
        for position, node in pending:
            struct.pack_into('<I', out, position, len(out) | HIGH)
            next_level.extend(directory(out, node, names))
        pending = next_level
    records = []
    for position, data in pending:
        struct.pack_into('<I', out, position, len(out))
        records.append((len(out), data))
        out.extend(bytes(16))
    for name, positions in names.items():
        for position in positions:
            struct.pack_into('<I', out, position, len(out) | HIGH)
        out.extend(struct.pack('<H', len(name)) + name.encode('utf-16le'))
    out.extend(bytes((-len(out)) % 4))
    for position, data in records:
        struct.pack_into('<IIII', out, position, rva + len(out), len(data), 1252, 0)
        out.extend(data)
        out.extend(b'PAD'[:(-len(out)) % 4])
    if len(out) > MAX_AREA:
        raise ValueError('serialized resource budget exceeded')
    return bytes(out)


def check_area(raw: bytes, rva: int) -> dict:
    """Require byte equality including metadata, ordering and alignment."""
    if len(raw) > MAX_AREA:
        raise ValueError('resource area exceeds limit')
    tree = InnoTree(raw, rva)
    tree.visit(0)
    if serialize(tree.leaves, rva) != raw:
        raise ValueError('resource serialization differs')
    return {'directory_count': len(tree.visited), 'leaf_count': len(tree.leaves),
            'area_bytes': len(raw), 'area_sha256': digest(raw),
            'directory_metadata': 'MATCH_OBSERVED_LAYOUT'}


def check_tail(tail: bytes) -> None:
    """Require the exact observed Windows section padding pattern."""
    pattern = b'PADDINGXXPADDING'
    if len(tail) >= 512 or tail != (pattern * 35)[:len(tail)]:
        raise ValueError('resource section tail differs')


def verify_serialization(exe: bytes) -> dict:
    """Check serialization after independently qualifying leaf payloads."""
    raw, rva = resource_area(exe)
    result = check_area(raw, rva)
    section = layout(exe)['sections']['.rsrc']
    start, end = section['raw_pointer'] + len(raw), section['raw_pointer'] + section['raw_size']
    if not start <= end <= len(exe):
        raise ValueError('invalid resource section extent')
    tail = exe[start:end]
    check_tail(tail)
    return {**result, 'tail_bytes': len(tail), 'tail_sha256': digest(tail),
            'serialization': 'MATCH_OBSERVED_LAYOUT', 'tail': 'MATCH_OBSERVED_PATTERN'}
