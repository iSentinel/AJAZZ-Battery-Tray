#!/usr/bin/env python3
"""Inventory declared licenses and notices in four hash-pinned NuGet packs."""

import argparse
import hashlib
import io
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

from inventory_dotnet_bundle import BundleError, LIMIT
from verify_windowsdesktop_provenance import member_bytes, read_local, validate_identity
from run_offline_qa import write_json

PACKS = {
    "host": ("Microsoft.NETCore.App.Host.win-x64", "11.0.0",
             "5d89e190bda6185fb17f7b2a264b57406fac9a03fdcd079673b853c0f2b49334"),
    "core": ("Microsoft.NETCore.App.Runtime.win-x64", "11.0.0",
             "1acb5da59cd994d3d50c9c52a9701bc8342948a1d8e4165f49bedf267c286b36"),
    "desktop": ("Microsoft.WindowsDesktop.App.Runtime.win-x64", "11.0.0",
                "1a5954e7945ecb3788cb88c66847e4c62d89e6739156355831029eb7d16d0c05"),
    "sdk": ("Microsoft.Windows.SDK.NET.Ref", "10.0.19041.87",
            "a40057b09a13efede843b5189839e73e04d013d5c6420f45b6009abc8ddba220"),
}
NOTICE_NAMES = {"license", "license.txt", "third-party-notices.txt",
                "thirdpartynotices.txt", "notice.txt"}


def metadata_field(metadata: ET.Element, name: str) -> ET.Element | None:
    """Read at most one exact metadata field; reject ambiguous declarations."""
    values = metadata.findall("{*}" + name)
    if len(values) > 1:
        raise BundleError("Duplicate package license metadata")
    return values[0] if values else None


def declared_license(metadata: ET.Element, kind: str) -> dict:
    """Accept only observed declarations; do not infer redistribution rights."""
    license_node = metadata_field(metadata, "license")
    url_node = metadata_field(metadata, "licenseUrl")
    accept_node = metadata_field(metadata, "requireLicenseAcceptance")
    url = url_node.text if url_node is not None else None
    acceptance = accept_node.text if accept_node is not None else None
    if kind == "sdk":
        if (license_node is not None or url != "https://aka.ms/WinSDKLicenseURL"
                or acceptance != "true"):
            raise BundleError("Unexpected Windows SDK license declaration")
        return {"expression": None, "url": url, "requires_acceptance": True,
                "disposition": "TERMS_REVIEW_REQUIRED"}
    if (license_node is None or license_node.attrib != {"type": "expression"}
            or license_node.text != "MIT" or url != "https://licenses.nuget.org/MIT"
            or acceptance not in (None, "false")):
        raise BundleError("Unexpected .NET license declaration")
    return {"expression": "MIT", "url": url, "requires_acceptance": False,
            "disposition": "NOTICE_DISTRIBUTION_REVIEW_REQUIRED"}


def notice_inventory(archive: zipfile.ZipFile) -> tuple[list, bool]:
    """Hash exact root notices and identify signature member without trusting it."""
    infos = archive.infolist()
    if len(infos) > 10000 or sum(x.file_size for x in infos) > LIMIT:
        raise BundleError("Archive exceeds budget")
    seen, notices = set(), []
    for info in infos:
        name = info.filename.casefold()
        if name in seen:
            raise BundleError("Duplicate archive member")
        seen.add(name)
        if name in NOTICE_NAMES:
            raw = member_bytes(archive, info, 2 * 1024 * 1024)
            if not raw or info.is_dir():
                raise BundleError("Invalid notice file")
            notices.append({"path": info.filename, "size": len(raw),
                            "sha256": hashlib.sha256(raw).hexdigest()})
    return sorted(notices, key=lambda x: x["path"]), ".signature.p7s" in seen


def inspect(pack: bytes, kind: str) -> dict:
    """Verify exact input identity, then return a scoped license observation."""
    package, version, expected = PACKS[kind]
    if hashlib.sha256(pack).hexdigest() != expected:
        raise BundleError("Pinned package digest mismatch")
    with zipfile.ZipFile(io.BytesIO(pack)) as archive:
        validate_identity(archive, version, package)
        spec = next(x for x in archive.infolist() if x.filename.lower().endswith(".nuspec"))
        metadata = ET.fromstring(member_bytes(archive, spec, 65536)).find("{*}metadata")
        if metadata is None:
            raise BundleError("Missing metadata")
        license_info = declared_license(metadata, kind)
        notices, signed = notice_inventory(archive)
    required = {"license.txt", "third-party-notices.txt"} if kind in ("host", "core") else (
        {"license"} if kind == "desktop" else set())
    if {x["path"].casefold() for x in notices} != required or not signed:
        raise BundleError("Unexpected reviewed notice or signature member inventory")
    return {"package": package, "version": version, "package_sha256": expected,
            "license": license_info, "notices": notices,
            "signature_member": "PRESENT_NOT_VERIFIED", "compliance": "NOT_VERIFIED"}


def main(argv: list[str] | None = None) -> int:
    """Write no-replace evidence for the exact four reviewed package inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    for kind in PACKS:
        parser.add_argument("--" + kind, type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        entries = [inspect(read_local(getattr(args, kind)), kind) for kind in PACKS]
        write_json(args.output, {"schema": 1, "scope": "pinned package license inventory",
                                 "packages": entries, "release_admission": "NOT_VERIFIED"})
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile, ET.ParseError) as error:
        print(f"ERROR: license inventory ({type(error).__name__})", file=sys.stderr)
        return 2
    print("PASS: pinned license inventory; redistribution review remains required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
