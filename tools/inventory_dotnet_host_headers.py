#!/usr/bin/env python3
"""Inventory PE header differences against the pinned .NET x64 host."""

import argparse
import hashlib
from pathlib import Path
import struct
import sys
import zipfile

from inventory_dotnet_bundle import BundleError, inventory
from verify_dotnet_host_sections import APPS, sections, template
from verify_windowsdesktop_provenance import read_local
from run_offline_qa import write_json

COFF = ("machine", "section_count", "timestamp", "symbol_table_offset",
        "symbol_count", "optional_size", "characteristics")
OPTIONAL = ("magic", "linker_major", "linker_minor", "size_code",
            "size_initialized", "size_uninitialized", "entry_point",
            "base_code", "image_base", "section_alignment", "file_alignment",
            "os_major", "os_minor", "image_major", "image_minor",
            "subsystem_major", "subsystem_minor", "win32_version",
            "size_image", "size_headers", "checksum", "subsystem",
            "dll_characteristics", "stack_reserve", "stack_commit",
            "heap_reserve", "heap_commit", "loader_flags", "directory_count")
DIRECTORIES = ("export", "import", "resource", "exception", "security",
               "relocation", "debug", "architecture", "global_ptr", "tls",
               "load_config", "bound_import", "iat", "delay_import",
               "clr", "reserved")
STABLE_COFF = ("machine", "section_count", "optional_size", "characteristics")
STABLE_OPTIONAL = ("magic", "entry_point", "base_code", "image_base",
                   "section_alignment", "file_alignment", "dll_characteristics")


def unpack(raw: bytes, offset: int, fmt: str) -> tuple:
    """Reject fields that extend beyond the supplied input."""
    if not 0 <= offset <= len(raw) - struct.calcsize(fmt):
        raise BundleError("Truncated PE header field")
    return struct.unpack_from(fmt, raw, offset)


def digest(raw: bytes) -> dict:
    """Describe opaque header regions without exporting their contents."""
    return {"length": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def parse_core(raw: bytes) -> tuple[int, dict, dict]:
    """Read the exact standard PE32+ COFF and optional fixed headers."""
    if raw[:2] != b"MZ":
        raise BundleError("Invalid DOS signature")
    pe, = unpack(raw, 60, "<I")
    if pe < 64 or raw[pe:pe + 4] != b"PE\0\0":
        raise BundleError("Invalid PE signature")
    coff = dict(zip(COFF, unpack(raw, pe + 4, "<HHIIIHH")))
    if (coff["machine"] != 0x8664 or not 1 <= coff["section_count"] <= 32
            or coff["optional_size"] != 240):
        raise BundleError("Unsupported x64 PE header layout")
    values = unpack(raw, pe + 24, "<HBBIIIIIQIIHHHHHHIIIIHHQQQQII")
    optional = dict(zip(OPTIONAL, values))
    if optional["magic"] != 0x20b or optional["directory_count"] != 16:
        raise BundleError("Unsupported optional header layout")
    return pe, coff, optional


def parse_sections(raw: bytes, table: int, count: int,
                   header_size: int) -> tuple[dict, int]:
    """Read complete section-table records and validate raw-file ranges."""
    if not table + count * 40 <= header_size <= len(raw):
        raise BundleError("Invalid header extent")
    entries, ranges = {}, []
    for pos in range(table, table + count * 40, 40):
        name = raw[pos:pos + 8].rstrip(b"\0").decode("ascii")
        values = unpack(raw, pos + 8, "<IIIIIIHHI")
        keys = ("virtual_size", "virtual_address", "raw_size", "raw_pointer",
                "relocations_pointer", "line_numbers_pointer",
                "relocations_count", "line_numbers_count", "characteristics")
        item = dict(zip(keys, values))
        size, start = item["raw_size"], item["raw_pointer"]
        if not name or name in entries:
            raise BundleError("Invalid section name")
        if size:
            if not header_size <= start <= len(raw) - size:
                raise BundleError("Invalid section raw range")
            ranges.append((start, start + size))
        entries[name] = item
    ranges.sort()
    if any(a[1] > b[0] for a, b in zip(ranges, ranges[1:])):
        raise BundleError("Overlapping section raw ranges")
    return entries, max((end for _, end in ranges), default=header_size)


def certificate_descriptor(directory: dict, raw_end: int, total: int) -> str:
    """Validate the certificate-table file extent, not its signature."""
    offset, size = directory["security"]
    if offset == size == 0:
        return "ABSENT"
    if not size or offset % 8 or not raw_end <= offset <= total - size:
        raise BundleError("Invalid certificate table extent")
    return "PRESENT_NOT_VERIFIED"


def parse_headers(raw: bytes) -> dict:
    """Return complete structural header regions and certificate presence."""
    pe, coff, optional = parse_core(raw)
    directories = {name: list(unpack(raw, pe + 24 + 112 + index * 8, "<II"))
                   for index, name in enumerate(DIRECTORIES)}
    table = pe + 24 + coff["optional_size"]
    header_size = optional["size_headers"]
    entries, raw_end = parse_sections(raw, table, coff["section_count"], header_size)
    end = table + coff["section_count"] * 40
    return {"dos_stub": digest(raw[:pe]), "coff": coff, "optional": optional,
            "directories": directories, "sections": entries,
            "section_order": list(entries), "header_padding": digest(raw[end:header_size]),
            "certificate_table": certificate_descriptor(directories, raw_end, len(raw))}


def changes(host: dict, actual: dict, prefix: str = "") -> list[dict]:
    """Report every differing structural field; do not silently allow changes."""
    result = []
    for key in sorted(host.keys() | actual.keys()):
        path = f"{prefix}.{key}" if prefix else key
        before, after = host.get(key), actual.get(key)
        if isinstance(before, dict) and isinstance(after, dict):
            result.extend(changes(before, after, path))
        elif before != after:
            result.append({"field": path, "host": before, "actual": after})
    return result


def invariants(host: dict, actual: dict, subsystem: int) -> dict:
    """Check only selected immutable fields and the required app subsystem."""
    result = {}
    for group, fields in (("coff", STABLE_COFF), ("optional", STABLE_OPTIONAL)):
        for field in fields:
            result[f"{group}.{field}"] = host[group][field] == actual[group][field]
    result["subsystem"] = host["optional"]["subsystem"] == 3 and (
        actual["optional"]["subsystem"] == subsystem)
    return result


def compare(raw: bytes, host: bytes, kind: str) -> dict:
    """Bind scoped header evidence to the exact bundle and pinned host bytes."""
    bundle = inventory(raw)
    sections(host)
    sections(raw)
    expected, actual = parse_headers(host), parse_headers(raw)
    checks = invariants(expected, actual, APPS[kind][1])
    return {"schema": 1, "scope": "PE header inventory and selected invariants",
            "exe_sha256": bundle["sha256"], "host_sha256": digest(host)["sha256"],
            "application": kind, "invariants": checks,
            "differences": changes(expected, actual),
            "host_certificate_table": expected["certificate_table"],
            "actual_certificate_table": actual["certificate_table"],
            "header_equivalence": "NOT_VERIFIED", "signature": "NOT_VERIFIED",
            "scoped_pass": all(checks.values())}


def main(argv: list[str] | None = None) -> int:
    """Write new local evidence; zero is scoped invariants only, not admission."""
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
        print(f"ERROR: header inventory ({type(error).__name__})", file=sys.stderr)
        return 2
    print("PASS: scoped header invariants; differences require review" if result["scoped_pass"]
          else "FAIL: scoped header invariants")
    return 0 if result["scoped_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
