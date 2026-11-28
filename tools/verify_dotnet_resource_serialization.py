#!/usr/bin/env python3
"""Rebuild the reviewed .NET PE resource overlay from host and app inputs."""

import argparse
import hashlib
from pathlib import Path
import struct
import sys
import zipfile

from inventory_dotnet_bundle import BundleError, inventory
from verify_dotnet_host_resources import HIGH, ResourceTree, resource_area, unpack
from verify_dotnet_host_sections import APPS, template
from verify_dotnet_header_reconstruction import expected_headers
from inventory_dotnet_host_headers import changes, parse_headers
from verify_windowsdesktop_provenance import read_local
from run_offline_qa import write_json

MAX_BYTES = 8 * 1024 * 1024
# Scope named keys to the exact observed host names, not generic .NET collation.
NAMES = frozenset(("CLRDEBUGINFO", "CLRDEBUGINFOWINDOWSAMD64",
                   "MINIDUMP_EMBEDDED_AUXILIARY_PROVIDER"))


class PayloadTree(ResourceTree):
    """Reuse guarded traversal while retaining local-only keys and payload bytes."""

    def key(self, value: int, depth: int) -> int | str:
        """Reject all unreviewed named IDs rather than guessing sort rules."""
        if not value & HIGH:
            if value > 65535:
                raise BundleError("Invalid numeric resource ID")
            return value
        pos = value & ~HIGH
        size, = unpack(self.raw, pos, "<H")
        start = pos + 2
        if depth != 1 or not 1 <= size <= 64 or start + size * 2 > len(self.raw):
            raise BundleError("Unsupported named resource")
        name = self.raw[start:start + 2 * size].decode("utf-16le")
        if name not in NAMES:
            raise BundleError("Unsupported resource name")
        return name

    def leaf(self, pos: int, path: tuple) -> None:
        """Collect bounded payloads; reject alias amplification by total size."""
        address, length, _, reserved = unpack(self.raw, pos, "<IIII")
        start = address - self.rva
        if (reserved or not 0 <= start <= len(self.raw) - length
                or path in self.leaves):
            raise BundleError("Invalid resource payload")
        self.payload_bytes = getattr(self, "payload_bytes", 0) + length
        if self.payload_bytes > MAX_BYTES:
            raise BundleError("Resource payload budget exceeded")
        self.leaves[path] = self.raw[start:start + length]


def payloads(raw: bytes) -> dict:
    """Read a bounded resource tree without exporting resource content."""
    area, rva = resource_area(raw)
    if len(area) > MAX_BYTES:
        raise BundleError("Resource area exceeds budget")
    tree = PayloadTree(area, rva)
    tree.visit(0)
    return tree.leaves


def ordered(keys: dict) -> list:
    """Named keys precede sorted numeric IDs in the supported SDK layout."""
    return sorted(keys, key=lambda k: (not isinstance(k, str), k))


def group(leaves: dict) -> dict:
    """Build the three directory levels from validated payload keys."""
    root = {}
    if not leaves or len(leaves) > 4096:
        raise BundleError("Invalid resource leaf count")
    if sum(map(len, leaves.values())) > MAX_BYTES:
        raise BundleError("Merged resource budget exceeded")
    for (kind, name, lang), data in leaves.items():
        if (not isinstance(kind, int) or not isinstance(lang, int)
                or not 0 <= kind <= 65535 or not 0 <= lang <= 65535
                or not (isinstance(name, int) and 0 <= name <= 65535
                        or isinstance(name, str) and name in NAMES)):
            raise BundleError("Unsupported resource key")
        root.setdefault(kind, {}).setdefault(name, {})[lang] = data
    return root


def directory(out: bytearray, node: dict, names: dict) -> list:
    """Emit one SDK directory and reserve child pointers and named offsets."""
    keys = ordered(node)
    named = sum(isinstance(k, str) for k in keys)
    out.extend(struct.pack("<IIHHHH", 0, 0, 4, 0, named, len(keys) - named))
    children = []
    for key in keys:
        pos = len(out)
        if isinstance(key, str):
            names.setdefault(key, []).append(pos)
        out.extend(struct.pack("<II", 0 if isinstance(key, str) else key, 0))
        children.append((pos + 4, node[key]))
    return children


def pad(out: bytearray, alignment: int) -> None:
    """Fill the next SDK alignment gap with zeros."""
    out.extend(bytes((-len(out)) % alignment))


def serialize(leaves: dict, rva: int) -> bytes:
    """Reproduce SDK breadth-first directories, names, data and leaf entries."""
    out = bytearray()
    names = {}
    pending = directory(out, group(leaves), names)
    for _ in range(2):
        next_level = []
        for position, node in pending:
            struct.pack_into("<I", out, position, len(out) | HIGH)
            next_level.extend(directory(out, node, names))
        pending = next_level
    pad(out, 2)
    for name in sorted(names):
        for position in names[name]:
            struct.pack_into("<I", out, position, len(out) | HIGH)
        out.extend(struct.pack("<H", len(name)) + name.encode("utf-16le"))
    records = []
    for position, data in pending:
        pad(out, 4)
        records.append((position, len(out), len(data)))
        out.extend(data)
    pad(out, 4)
    for position, offset, size in records:
        struct.pack_into("<I", out, position, len(out))
        out.extend(struct.pack("<IIII", rva + offset, size, 1252, 0))
    pad(out, 4)
    if len(out) > MAX_BYTES:
        raise BundleError("Serialized resource budget exceeded")
    return bytes(out)


def compare(raw: bytes, host: bytes, kind: str) -> dict:
    """Build expected bytes from independent host and embedded app resources."""
    bundle = inventory(raw)
    hits = [x for x in bundle["files"] if x["path"] == APPS[kind][0]
            and x["type"] == "assembly"]
    if len(hits) != 1:
        raise BundleError("Expected one embedded app assembly")
    item = hits[0]
    app = raw[item["offset"]:item["offset"] + item["size"]]
    base = parse_headers(host)
    actual_header = parse_headers(raw)
    rva = base["sections"][".rsrc"]["virtual_address"]
    merged = payloads(host) | payloads(app)
    expected = serialize(merged, rva)
    actual, actual_rva = resource_area(raw)
    differences = changes(expected_headers(base, len(expected), APPS[kind][1]),
                          actual_header)
    entry = actual_header["sections"][".rsrc"]
    start = entry["raw_pointer"] + len(expected)
    end = entry["raw_pointer"] + entry["raw_size"]
    tail = start <= end <= len(raw) and not any(raw[start:end])
    match = actual_rva == rva and expected == actual
    return {"schema": 1, "scope": "reviewed resource serialization and header reconstruction",
            "application": kind, "exe_sha256": bundle["sha256"],
            "app_sha256": item["sha256"], "host_sha256": hashlib.sha256(host).hexdigest(),
            "expected_size": len(expected), "actual_size": len(actual),
            "expected_sha256": hashlib.sha256(expected).hexdigest(),
            "actual_sha256": hashlib.sha256(actual).hexdigest(), "resource_match": match,
            "unexpected_header_differences": differences, "resource_tail_zero": tail,
            "signature": "NOT_VERIFIED", "scoped_pass": match and not differences and tail}


def main(argv: list[str] | None = None) -> int:
    """Write no-replace local evidence; zero means only reviewed scope matched."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--application", choices=sorted(APPS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = compare(read_local(args.exe), template(read_local(args.package)),
                         args.application)
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, struct.error, zipfile.BadZipFile) as error:
        print(f"ERROR: resource serialization ({type(error).__name__})", file=sys.stderr)
        return 2
    print("PASS: scoped resource serialization" if result["scoped_pass"]
          else "FAIL: scoped resource serialization")
    return 0 if result["scoped_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
