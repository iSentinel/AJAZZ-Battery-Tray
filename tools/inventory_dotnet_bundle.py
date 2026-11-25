#!/usr/bin/env python3
"""Inventory uncompressed .NET single-file bundle v6.0 without execution."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

from run_offline_qa import write_json

MARKER = bytes.fromhex(
    "8b1202b96a612038727b930214d7a03213f5b9e6efae3318ee3b2dce24b36aae")
LIMIT = 256 * 1024 * 1024
TYPES = ("unknown", "assembly", "native", "deps", "runtimeconfig", "symbols")
SEGMENT = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.+ -]{0,199}")


class BundleError(ValueError):
    """Fixed diagnostic without source path or input values."""


class Reader:
    """Bounded cursor over manifest bytes."""

    def __init__(self, data: bytes, position: int) -> None:
        """Initialize a cursor at a validated offset."""
        self.data = data
        self.position = position

    def take(self, count: int) -> bytes:
        """Read exactly count bytes or reject truncation."""
        end = self.position + count
        if count < 0 or not 0 <= self.position <= end <= len(self.data):
            raise BundleError("Truncated manifest")
        result = self.data[self.position:end]
        self.position = end
        return result

    def numbers(self, fmt: str) -> tuple:
        """Read fixed-width little-endian fields."""
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))

    def string(self) -> str:
        """Decode a bounded .NET BinaryWriter UTF-8 string."""
        length = 0
        for shift in range(0, 14, 7):
            value = self.take(1)[0]
            length |= (value & 127) << shift
            if not value & 128:
                if not 0 < length <= 1024 or (shift and value == 0):
                    raise BundleError("Invalid manifest string length")
                return self.take(length).decode("utf-8")
        raise BundleError("Oversized manifest string")


def relative_name(name: str) -> str:
    """Allow only safe relative bundle paths, never extract them."""
    if any(not SEGMENT.fullmatch(part) or part.endswith((".", " "))
           for part in name.split("/")):
        raise BundleError("Invalid bundle path")
    return name


def header(data: bytes) -> tuple[Reader, int, int, tuple]:
    """Locate one marker and require the reviewed v6.0 manifest layout."""
    marker = data.find(MARKER)
    if (data[:2] != b"MZ" or marker < 8
            or data.find(MARKER, marker + 1) != -1):
        raise BundleError("Invalid or ambiguous PE bundle marker")
    offset, = struct.unpack_from("<q", data, marker - 8)
    if not marker + len(MARKER) <= offset < len(data):
        raise BundleError("Invalid manifest offset")
    reader = Reader(data, offset)
    major, minor, count = reader.numbers("<IIi")
    if (major, minor) != (6, 0) or not 1 <= count <= 4096:
        raise BundleError("Unsupported bundle layout")
    if not re.fullmatch(r"[A-Za-z0-9_-]{12}", reader.string()):
        raise BundleError("Invalid bundle identifier")
    metadata = reader.numbers("<qqqqQ")
    if metadata[-1] not in (0, 1):
        raise BundleError("Unknown bundle flags")
    return reader, offset, count, metadata


def entry(reader: Reader, boundary: int) -> dict:
    """Validate one manifest entry and hash actual embedded bytes."""
    offset, size, compressed = reader.numbers("<qqq")
    kind = reader.take(1)[0]
    name = relative_name(reader.string())
    if kind >= len(TYPES) or compressed != 0:
        raise BundleError("Unsupported type or compression")
    if not 0 <= size <= boundary or not 0 < offset <= boundary - size:
        raise BundleError("Embedded bytes out of range")
    return {"path": name, "type": TYPES[kind], "offset": offset,
            "size": size, "sha256": hashlib.sha256(
                memoryview(reader.data)[offset:offset + size]).hexdigest()}


def validate_entries(entries: list[dict], metadata: tuple) -> None:
    """Reject collisions, overlapping payloads and inconsistent JSON pointers."""
    seen = set()
    end = 0
    for item in sorted(entries, key=lambda item: (item["offset"], item["size"])):
        name = item["path"].casefold()
        if name in seen or item["offset"] < end:
            raise BundleError("Duplicate or overlapping bundle entry")
        seen.add(name)
        end = item["offset"] + item["size"]
    for kind, pointer in (("deps", metadata[:2]), ("runtimeconfig", metadata[2:4])):
        found = [(item["offset"], item["size"]) for item in entries
                 if item["type"] == kind]
        if found != [pointer] or not pointer[1]:
            raise BundleError("Missing or inconsistent configuration entry")


def inventory(data: bytes) -> dict:
    """Return exact embedded file identities, not a complete product SBOM."""
    if len(data) > LIMIT:
        raise BundleError("Bundle exceeds size limit")
    reader, boundary, count, metadata = header(data)
    entries = [entry(reader, boundary) for _ in range(count)]
    validate_entries(entries, metadata)
    return {"schema": 1, "bundle_version": "6.0", "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "scope": "embedded uncompressed manifest entries only",
            "files": sorted(entries, key=lambda item: item["path"])}


def main(argv: list[str] | None = None) -> int:
    """Read a bounded regular executable and create a new inventory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.exe.is_symlink() or not args.exe.is_file():
            raise BundleError("Expected a regular executable")
        with args.exe.open("rb") as stream:
            data = stream.read(LIMIT + 1)
        write_json(args.output, inventory(data))
    except (OSError, ValueError, struct.error) as error:
        detail = str(error) if isinstance(error, BundleError) else type(error).__name__
        print(f"ERROR: bundle inventory: {detail}", file=sys.stderr)
        return 2
    print("PASS: embedded bundle inventory (not release admission)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
