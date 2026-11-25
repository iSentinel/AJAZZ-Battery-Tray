#!/usr/bin/env python3
"""Compare PE resource payloads with the pinned host and embedded app assembly."""

import argparse
import hashlib
from pathlib import Path
import struct
import sys
import zipfile

from inventory_dotnet_bundle import BundleError, inventory
from verify_dotnet_host_sections import APPS, template
from verify_windowsdesktop_provenance import read_local
from run_offline_qa import write_json

HIGH = 0x80000000
MAX_RESOURCES = 4096


def unpack(raw: bytes, offset: int, fmt: str) -> tuple:
    """Read bounded little-endian fields."""
    size = struct.calcsize(fmt)
    if not 0 <= offset <= len(raw) - size:
        raise BundleError("Truncated resource metadata")
    return struct.unpack_from(fmt, raw, offset)


def resource_area(raw: bytes) -> tuple[bytes, int]:
    """Find the declared resource directory in one raw .rsrc section."""
    if raw[:2] != b"MZ":
        raise BundleError("Invalid DOS header")
    pe, = unpack(raw, 60, "<I")
    if pe < 64 or raw[pe:pe + 4] != b"PE\0\0":
        raise BundleError("Invalid PE header")
    count, = unpack(raw, pe + 6, "<H")
    size, = unpack(raw, pe + 20, "<H")
    optional = pe + 24
    magic, = unpack(raw, optional, "<H")
    directories = {0x10b: 96, 0x20b: 112}.get(magic)
    if directories is None or size < directories + 24 or not 1 <= count <= 32:
        raise BundleError("Unsupported PE layout")
    table = optional + size
    if table + count * 40 > len(raw):
        raise BundleError("Truncated PE sections")
    number, = unpack(raw, optional + directories - 4, "<I")
    if number < 3:
        raise BundleError("Resource directory unavailable")
    rva, length = unpack(raw, optional + directories + 16, "<II")
    matches = []
    for pos in range(table, table + count * 40, 40):
        if raw[pos:pos + 8].rstrip(b"\0") != b".rsrc":
            continue
        virtual, address, extent, ptr = unpack(raw, pos + 8, "<IIII")
        if not (length and address <= rva and rva + length <= address + min(virtual, extent)
                and table + count * 40 <= ptr <= len(raw) - extent):
            raise BundleError("Resource directory outside raw section")
        start = ptr + rva - address
        matches.append((raw[start:start + length], rva))
    if len(matches) != 1:
        raise BundleError("Expected one resource section")
    return matches[0]


class ResourceTree:
    """Bounded three-level type/name/language directory, no resource execution."""

    def __init__(self, raw: bytes, rva: int) -> None:
        """Keep resource area and directory cycle/duplicate guards."""
        self.raw = raw
        self.rva = rva
        self.visited = set()
        self.leaves = {}
        self.entries = 0

    def key(self, value: int, depth: int) -> str:
        """Keep numeric IDs; hash named IDs without exposing arbitrary text."""
        if not value & HIGH:
            if value > 65535:
                raise BundleError("Invalid numeric resource ID")
            return str(value)
        if depth == 2:
            raise BundleError("Named resource language unsupported")
        pos = value & ~HIGH
        size, = unpack(self.raw, pos, "<H")
        start = pos + 2
        if not 1 <= size <= 1024 or start + 2 * size > len(self.raw):
            raise BundleError("Invalid resource name")
        return "name-sha256:" + hashlib.sha256(
            self.raw[start:start + 2 * size]).hexdigest()

    def leaf(self, pos: int, path: tuple) -> None:
        """Hash actual payload bounded by the declared directory span."""
        address, length, _, reserved = unpack(self.raw, pos, "<IIII")
        start = address - self.rva
        if reserved or not 0 <= start <= len(self.raw) - length:
            raise BundleError("Invalid resource data entry")
        if path in self.leaves:
            raise BundleError("Duplicate resource key")
        self.leaves[path] = hashlib.sha256(
            self.raw[start:start + length]).hexdigest()

    def visit(self, pos: int, path: tuple = ()) -> None:
        """Walk exactly three directory levels and reject aliases/cycles."""
        if pos in self.visited or len(path) > 2:
            raise BundleError("Repeated or overdeep resource directory")
        self.visited.add(pos)
        named, ids = unpack(self.raw, pos + 12, "<HH")
        count = named + ids
        self.entries += count
        if not count or self.entries > MAX_RESOURCES:
            raise BundleError("Resource entry budget exceeded")
        seen = set()
        for i in range(count):
            key, target = unpack(self.raw, pos + 16 + i * 8, "<II")
            if bool(key & HIGH) != (i < named):
                raise BundleError("Invalid resource directory ordering")
            name = self.key(key, len(path))
            if name in seen:
                raise BundleError("Duplicate directory key")
            seen.add(name)
            child = path + (name,)
            if len(child) < 3 and target & HIGH:
                self.visit(target & ~HIGH, child)
            elif len(child) == 3 and not target & HIGH:
                self.leaf(target, child)
            else:
                raise BundleError("Invalid resource depth")


def resources(raw: bytes) -> dict:
    """Return resource key to payload hash, not resource metadata provenance."""
    area, rva = resource_area(raw)
    tree = ResourceTree(area, rva)
    tree.visit(0)
    return tree.leaves


def compare_leaves(host: dict, app: dict, actual: dict) -> list[dict]:
    """Apply SDK overlay semantics; expose absent, extra and changed payloads."""
    expected = host | app
    result = []
    for key in sorted(expected.keys() | actual.keys()):
        wanted, found = expected.get(key), actual.get(key)
        status = ("extra" if wanted is None else "missing" if found is None
                  else "match" if wanted == found else "mismatch")
        origin = "app" if key in app else "host" if key in host else "unknown"
        result.append({"key": list(key), "origin": origin,
                       "expected_sha256": wanted, "actual_sha256": found,
                       "status": status})
    return result


def compare(raw: bytes, host: bytes, kind: str) -> dict:
    """Bind the resource comparison to exact bundled app bytes."""
    bundle = inventory(raw)
    app_name = APPS[kind][0]
    hits = [item for item in bundle["files"] if item["path"] == app_name
            and item["type"] == "assembly"]
    if len(hits) != 1:
        raise BundleError("Expected one embedded app assembly")
    item = hits[0]
    app = raw[item["offset"]:item["offset"] + item["size"]]
    entries = compare_leaves(resources(host), resources(app), resources(raw))
    return {"schema": 1, "scope": "PE resource payload overlay only",
            "exe_sha256": bundle["sha256"], "app_sha256": item["sha256"],
            "host_sha256": hashlib.sha256(host).hexdigest(),
            "resources": entries, "metadata": "NOT_VERIFIED",
            "scoped_pass": bool(entries) and all(x["status"] == "match" for x in entries)}


def main(argv: list[str] | None = None) -> int:
    """Produce bounded read-only evidence and fail on unexpected payloads."""
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
        print(f"ERROR: resource comparison ({type(error).__name__})", file=sys.stderr)
        return 2
    print("PASS: scoped resource payload comparison" if result["scoped_pass"]
          else "FAIL: scoped resource payload comparison")
    return 0 if result["scoped_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
