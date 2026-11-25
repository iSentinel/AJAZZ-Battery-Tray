#!/usr/bin/env python3
"""Compare embedded runtime files with a hash-pinned reviewed NuGet pack."""

import argparse
import hashlib
import io
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

from inventory_dotnet_bundle import LIMIT, BundleError, relative_name
from inventory_dotnet_components import report
from inventory_nuget_assets import VERSION, token
from run_offline_qa import write_json

PACK = "Microsoft.WindowsDesktop.App.Runtime.win-x64"
PREFIX = "runtimes/win-x64/lib/net11.0/"
CORE = "Microsoft.NETCore.App.Runtime.win-x64"
SDK = "Microsoft.Windows.SDK.NET.Ref"
PACK_PREFIXES = {PACK: PREFIX, CORE: PREFIX, SDK: "lib/net9.0/"}
SHA = re.compile(r"[0-9a-f]{64}")
MAX_MEMBER = 32 * 1024 * 1024


def read_local(path: Path) -> bytes:
    """Read an immutable local artifact within the reviewed size budget."""
    if path.is_symlink() or not path.is_file():
        raise BundleError("Expected a regular local artifact")
    with path.open("rb") as stream:
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise BundleError("Artifact exceeds size limit")
    return data


def member_bytes(archive: zipfile.ZipFile, info: zipfile.ZipInfo,
                 limit: int = MAX_MEMBER) -> bytes:
    """Bound uncompressed reads; never extract archive contents."""
    if info.file_size > limit or info.flag_bits & 1:
        raise BundleError("Unsupported archive member")
    with archive.open(info) as stream:
        raw = stream.read(limit + 1)
    if len(raw) != info.file_size or len(raw) > limit:
        raise BundleError("Invalid archive member size")
    return raw


def validate_identity(archive: zipfile.ZipFile, version: str,
                      package: str = PACK) -> None:
    """Require the reviewed package identity and exact declared version."""
    specs = [info for info in archive.infolist()
             if info.filename.lower().endswith(".nuspec")]
    if len(specs) != 1:
        raise BundleError("Expected one package specification")
    raw = member_bytes(archive, specs[0], 65536)
    if b"\x00" in raw or b"<!" in raw:
        raise BundleError("Unsupported package specification")
    metadata = ET.fromstring(raw).find("{*}metadata")
    if metadata is None:
        raise BundleError("Missing package metadata")
    ids = metadata.findall("{*}id")
    versions = metadata.findall("{*}version")
    if (len(ids) != 1 or len(versions) != 1
            or ids[0].text != package or versions[0].text != version):
        raise BundleError("Package identity mismatch")


def package_index(archive: zipfile.ZipFile, prefix: str = PREFIX) -> dict:
    """Index exact package-relative paths and notice hashes, not guessed owners."""
    entries = archive.infolist()
    if len(entries) > 10000 or sum(item.file_size for item in entries) > LIMIT:
        raise BundleError("Archive exceeds budget")
    seen, assets, notices = set(), {}, []
    for info in entries:
        name = info.filename
        if name.casefold() in seen:
            raise BundleError("Duplicate archive path")
        seen.add(name.casefold())
        if info.is_dir():
            continue
        if name.startswith(prefix) and name.endswith(".dll"):
            path = name[len(prefix):]
            assets[relative_name(path)] = hashlib.sha256(
                member_bytes(archive, info)).hexdigest()
        elif name.rsplit("/", 1)[-1].lower() in (
                "license", "license.txt", "thirdpartynotices.txt",
                "third-party-notices.txt", "notice.txt"):
            notices.append({"path": relative_name(name), "sha256":
                            hashlib.sha256(member_bytes(archive, info)).hexdigest()})
    return {"assets": assets, "notices": sorted(notices, key=lambda x: x["path"])}


def compare_files(attribution: dict, component: dict, index: dict,
                  package: str) -> list[dict]:
    """Report both declared and unresolved evidence without ignoring absences."""
    candidates = [(item, "declared") for item in component["files"]]
    if package == PACK:
        candidates += [(item, "unclaimed") for item in attribution["unmatched_files"]
                       if item["path"].endswith(".resources.dll")]
    results = []
    for item, origin in candidates:
        actual = index["assets"].get(item["path"])
        status = ("missing" if actual is None else
                  "match" if actual == item["sha256"] else "mismatch")
        results.append({"path": item["path"], "origin": origin,
                        "embedded_sha256": item["sha256"],
                        "package_sha256": actual, "status": status})
    library = "runtimepack." + package + "/" + component["version"]
    for item in attribution.get("missing_declared_files", []):
        if item["library"] == library:
            results.append({"path": item["path"], "origin": "declared",
                            "embedded_sha256": None,
                            "package_sha256": index["assets"].get(item["path"]),
                            "status": "missing_embedded"})
    return results


def compare(attribution: dict, pack: bytes, expected: str,
            package: str = PACK) -> dict:
    """Compare a reviewed package against its actual embedded payloads."""
    if package not in PACK_PREFIXES:
        raise BundleError("Unreviewed package layout")
    digest = hashlib.sha256(pack).hexdigest()
    if not SHA.fullmatch(expected) or digest != expected:
        raise BundleError("Package SHA-256 mismatch")
    components = [item for item in attribution["components"]
                  if item["id"] == "runtimepack." + package
                  and item["type"] == "runtimepack"]
    if len(components) != 1:
        raise BundleError("Expected one reviewed runtimepack claim")
    component = components[0]
    version = token(component["version"], VERSION)
    with zipfile.ZipFile(io.BytesIO(pack)) as archive:
        validate_identity(archive, version, package)
        index = package_index(archive, PACK_PREFIXES[package])
    results = compare_files(attribution, component, index, package)
    scope = ("WindowsDesktop byte comparison only" if package == PACK
             else "Selected runtimepack byte comparison only")
    return {"schema": 1, "scope": scope,
            "exe_sha256": attribution["exe_sha256"], "package": package,
            "version": version, "package_sha256": digest,
            "notices": index["notices"], "files": results}


def main(argv: list[str] | None = None) -> int:
    """Write evidence even for differences; return 2 unless every file matches."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--package-sha256", required=True)
    parser.add_argument("--pack-id", choices=sorted(PACK_PREFIXES), default=PACK)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = compare(report(read_local(args.exe)), read_local(args.package),
                         args.package_sha256, args.pack_id)
        write_json(args.output, result)
        if not result["files"] or any(x["status"] != "match" for x in result["files"]):
            print("FAIL: runtimepack byte comparison", file=sys.stderr)
            return 2
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            zipfile.BadZipFile, ET.ParseError) as error:
        print(f"ERROR: runtime provenance ({type(error).__name__})",
              file=sys.stderr)
        return 2
    print("PASS: runtimepack byte comparison (not complete SBOM)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
