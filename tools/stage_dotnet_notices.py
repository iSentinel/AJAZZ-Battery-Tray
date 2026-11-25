#!/usr/bin/env python3
"""Stage reviewed upstream notice bytes locally, without release admission."""

import argparse
import hashlib
import io
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

from inventory_dotnet_bundle import BundleError
from inventory_dotnet_pack_licenses import PACKS, inspect
from verify_windowsdesktop_provenance import member_bytes, read_local
from run_offline_qa import write_json


def collect(pack: bytes, kind: str) -> tuple[dict, dict]:
    """Recheck pinned identity and preserve exact upstream notice bytes."""
    evidence = inspect(pack, kind)
    files = {}
    with zipfile.ZipFile(io.BytesIO(pack)) as archive:
        for entry in evidence["notices"]:
            raw = member_bytes(archive, archive.getinfo(entry["path"]), 2 * 1024 * 1024)
            if len(raw) != entry["size"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
                raise BundleError("Notice bytes changed")
            files[entry["path"]] = raw
    return evidence, files


def stage(packs: dict, output: Path) -> dict:
    """Validate all inputs before creating a fresh, unpublished directory."""
    if set(packs) != set(PACKS):
        raise BundleError("Expected all four reviewed packages")
    collected = {kind: collect(raw, kind) for kind, raw in packs.items()}
    if output.exists() or output.is_symlink():
        raise BundleError("Output directory already exists")
    output.mkdir(mode=0o700)
    entries = []
    for kind, (evidence, files) in collected.items():
        directory = output / kind
        directory.mkdir(mode=0o700)
        for name, raw in files.items():
            with (directory / name).open("xb") as stream:
                stream.write(raw)
        entries.append(evidence)
    result = {"schema": 1, "scope": "upstream notice staging only",
              "packages": entries, "release_admission": "NOT_VERIFIED",
              "sdk_terms": "REVIEW_REQUIRED", "windows_single_file_terms": "REVIEW_REQUIRED"}
    write_json(output / "manifest.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    """Stage local notice files; never publish or approve a release."""
    parser = argparse.ArgumentParser(description=__doc__)
    for kind in PACKS:
        parser.add_argument("--" + kind, type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        stage({kind: read_local(getattr(args, kind)) for kind in PACKS}, args.output)
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile, ET.ParseError) as error:
        print(f"ERROR: notice staging ({type(error).__name__})", file=sys.stderr)
        return 2
    print("PASS: exact notices staged; release compliance remains unverified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
