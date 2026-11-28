#!/usr/bin/env python3
"""Reconstruct scoped unsigned x64 host headers after SDK resource growth."""

import argparse
from copy import deepcopy
from pathlib import Path
import struct
import sys
import zipfile

from inventory_dotnet_bundle import BundleError, inventory
from inventory_dotnet_host_headers import changes, digest, parse_headers
from verify_dotnet_host_sections import APPS, sections, template
from verify_windowsdesktop_provenance import read_local
from run_offline_qa import write_json


def align(value: int, alignment: int) -> int:
    """Apply SDK power-of-two alignment with explicit supported bounds."""
    if not 0 < alignment <= 65536 or alignment & (alignment - 1):
        raise BundleError("Unsupported alignment")
    if not 0 <= value <= 0x7fffffff - alignment:
        raise BundleError("Unsupported size")
    return (value + alignment - 1) & ~(alignment - 1)


def expected_headers(host: dict, resource_size: int, subsystem: int) -> dict:
    """Model ResourceUpdater.Update for an existing growing .rsrc section."""
    result = deepcopy(host)
    optional = result["optional"]
    resources = result["sections"][".rsrc"]
    order = result["section_order"]
    if (host["certificate_table"] != "ABSENT" or optional["subsystem"] != 3
            or subsystem not in (2, 3) or order[-2:] != [".rsrc", ".reloc"]
            or resource_size < resources["virtual_size"]):
        raise BundleError("Unsupported host resource layout")
    raw_alignment = optional["file_alignment"]
    virtual_alignment = optional["section_alignment"]
    raw_size = align(resource_size, raw_alignment)
    delta = raw_size - align(resources["raw_size"], raw_alignment)
    virtual_delta = (align(resource_size, virtual_alignment)
                     - align(resources["virtual_size"], virtual_alignment))
    if delta < 0 or virtual_delta < 0:
        raise BundleError("Unsupported resource shrink")
    optional["subsystem"] = subsystem
    if resource_size != resources["virtual_size"]:
        optional["size_initialized"] += delta
        optional["size_image"] += virtual_delta
        if delta > 0:
            shift_trailing(result, resources, delta, virtual_delta)
        resources["virtual_size"] = resource_size
        resources["raw_size"] = raw_size
        result["directories"]["resource"] = [resources["virtual_address"], resource_size]
    return result


def shift_trailing(header: dict, resources: dict, delta: int,
                   virtual_delta: int) -> None:
    """Shift the single reviewed trailing section and affected directory RVAs."""
    reloc = header["sections"][".reloc"]
    reloc["virtual_address"] += virtual_delta
    reloc["raw_pointer"] += delta
    threshold = resources["virtual_address"] + resources["virtual_size"]
    for directory in header["directories"].values():
        if directory[0] >= threshold:
            directory[0] += virtual_delta


def compare(raw: bytes, host: bytes, kind: str) -> dict:
    """Compare all inventoried header fields conditional on observed resource size."""
    bundle = inventory(raw)
    sections(host)
    sections(raw)
    actual = parse_headers(raw)
    base = parse_headers(host)
    resource = actual["sections"][".rsrc"]
    size = resource["virtual_size"]
    expected = expected_headers(base, size, APPS[kind][1])
    differences = changes(expected, actual)
    start = resource["raw_pointer"] + size
    end = resource["raw_pointer"] + resource["raw_size"]
    padding_zero = start <= end <= len(raw) and not any(raw[start:end])
    return {"schema": 1, "scope": "conditional SDK header reconstruction",
            "application": kind, "exe_sha256": bundle["sha256"],
            "host_sha256": digest(host)["sha256"], "observed_resource_size": size,
            "resource_size_origin": "OBSERVED_NOT_INDEPENDENTLY_REBUILT",
            "unexpected_header_differences": differences,
            "resource_tail_padding_zero": padding_zero,
            "signature": "NOT_VERIFIED", "scoped_pass": not differences and padding_zero}


def main(argv: list[str] | None = None) -> int:
    """Write no-replace evidence; zero means scoped match, not release admission."""
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
        print(f"ERROR: header reconstruction ({type(error).__name__})", file=sys.stderr)
        return 2
    print("PASS: conditional header reconstruction" if result["scoped_pass"]
          else "FAIL: conditional header reconstruction")
    return 0 if result["scoped_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
