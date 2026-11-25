#!/usr/bin/env python3
"""Compare selected x64 PE sections with the pinned .NET 11 single-file host."""

import argparse
import hashlib
import io
from pathlib import Path
import struct
import sys
import zipfile

from inventory_dotnet_bundle import BundleError, MARKER, inventory
from verify_windowsdesktop_provenance import read_local, member_bytes
from run_offline_qa import write_json

PACK_SHA = "5d89e190bda6185fb17f7b2a264b57406fac9a03fdcd079673b853c0f2b49334"
HOST_SHA = "5a668b88d76442f4013866ffd9912fdd79d116cbc4fdd6cc555ad979bf40d7d9"
APP_MARKER = b"c3ab8ff13720e8ad9047dd39466b3c8974e592c2fa383d4a3960714caef0c4f2"
APPS = {"tray": ("AJAZZBatteryTray.dll", 2), "ha": ("AjazzHaPreview.dll", 3)}
EXACT = (".text", ".CLR_UEF", ".rdata", ".pdata", "Section", ".reloc")
SECTION_NAMES = set(EXACT) | {".data", ".rsrc"}


def sections(raw: bytes) -> tuple[dict, int]:
    """Read bounded x64 PE32+ raw sections and subsystem; no execution."""
    if len(raw) < 64 or raw[:2] != b"MZ":
        raise BundleError("Invalid DOS header")
    off, = struct.unpack_from("<I", raw, 60)
    if not 64 <= off <= len(raw) - 24 or raw[off:off+4] != b"PE\0\0":
        raise BundleError("Invalid PE header")
    machine, count = struct.unpack_from("<HH", raw, off + 4)
    size, = struct.unpack_from("<H", raw, off + 20)
    table = off + 24 + size
    if (machine != 0x8664 or count != 8 or size < 70
            or table + count * 40 > len(raw)
            or struct.unpack_from("<H", raw, off + 24)[0] != 0x20b):
        raise BundleError("Unsupported PE layout")
    result, ranges = {}, []
    for pos in range(table, table + count * 40, 40):
        name = raw[pos:pos+8].rstrip(b"\0").decode("ascii")
        length, ptr = struct.unpack_from("<II", raw, pos + 16)
        if (name not in SECTION_NAMES or name in result or not length
                or ptr < table + count * 40 or ptr + length > len(raw)):
            raise BundleError("Invalid raw section")
        result[name] = (ptr, raw[ptr:ptr+length])
        ranges.append((ptr, ptr + length))
    ranges.sort()
    if any(a[1] > b[0] for a, b in zip(ranges, ranges[1:])):
        raise BundleError("Overlapping raw sections")
    return result, struct.unpack_from("<H", raw, off + 24 + 68)[0]


def unique_position(raw: bytes, marker: bytes) -> int:
    """Reject missing and ambiguous SDK placeholders."""
    pos = raw.find(marker)
    if pos < 0 or raw.find(marker, pos + 1) != -1:
        raise BundleError("Missing or ambiguous SDK placeholder")
    return pos


def data_patch(original: bytes, actual: bytes, app: str,
               header_offset: int) -> dict:
    """Reconstruct exactly the two reviewed SDK patches; compare every byte."""
    marker = unique_position(original, MARKER)
    name = unique_position(original, APP_MARKER)
    encoded = app.encode("ascii")
    if (marker < 8 or original[marker-8:marker] != bytes(8)
            or len(encoded) >= len(APP_MARKER) or header_offset <= 0
            or not (name + len(APP_MARKER) <= marker - 8
                    or marker + len(MARKER) <= name)):
        raise BundleError("Unexpected SDK patch layout")
    expected = bytearray(original)
    expected[marker-8:marker] = struct.pack("<q", header_offset)
    expected[name:name+len(APP_MARKER)] = encoded.ljust(len(APP_MARKER), b"\0")
    return {"match": bytes(expected) == actual,
            "expected_changed_bytes": sum(x != y for x, y in zip(original, expected)),
            "unexpected_bytes": sum(x != y for x, y in zip(expected, actual))
            + abs(len(expected) - len(actual))}


def template(pack: bytes) -> bytes:
    """Use only the exact previously observed upstream package and host bytes."""
    if hashlib.sha256(pack).hexdigest() != PACK_SHA:
        raise BundleError("Host package digest mismatch")
    with zipfile.ZipFile(io.BytesIO(pack)) as archive:
        hits = [x for x in archive.infolist()
                if x.filename == "runtimes/win-x64/native/singlefilehost.exe"]
        if len(hits) != 1:
            raise BundleError("Expected one host template")
        raw = member_bytes(archive, hits[0])
    if hashlib.sha256(raw).hexdigest() != HOST_SHA:
        raise BundleError("Host template digest mismatch")
    return raw


def compare(raw: bytes, host: bytes, kind: str) -> dict:
    """Verify scoped sections and exact patch; resources remain unresolved."""
    app, subsystem = APPS[kind]
    bundle = inventory(raw)
    original, host_sub = sections(host)
    actual, actual_sub = sections(raw)
    marker = unique_position(raw, MARKER)
    header, = struct.unpack_from("<q", raw, marker - 8)
    data_ptr, data = actual[".data"]
    if (marker < 8 or not data_ptr + 8 <= marker
            < data_ptr + len(data) - len(MARKER) + 1
            or not max(ptr + len(val) for ptr, val in actual.values()) <= header):
        raise BundleError("Bundle marker or header outside reviewed layout")
    exact = {name: original[name][1] == actual[name][1] for name in EXACT}
    patch = data_patch(original[".data"][1], data, app, header)
    subsystem_ok = host_sub == 3 and actual_sub == subsystem
    return {"schema": 1, "scope": "selected PE sections and SDK data patch",
            "exe_sha256": bundle["sha256"], "host_sha256": HOST_SHA,
            "package_sha256": PACK_SHA, "application": kind,
            "exact_sections": exact, "data_patch": patch,
            "subsystem_match": subsystem_ok, "resources": "UNRESOLVED",
            "headers": "PARTIAL", "signature": "NOT_VERIFIED",
            "scoped_pass": all(exact.values()) and patch["match"] and subsystem_ok}


def main(argv: list[str] | None = None) -> int:
    """Produce local evidence; nonzero for a failed scoped comparison."""
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
        print(f"ERROR: host comparison ({type(error).__name__})", file=sys.stderr)
        return 2
    print("PASS: scoped host comparison; resources unresolved" if result["scoped_pass"]
          else "FAIL: scoped host comparison")
    return 0 if result["scoped_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
