#!/usr/bin/env python3
"""Emit a scoped CycloneDX 1.6 BOM for one reviewed Windows single-file EXE."""

import argparse
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

from inventory_dotnet_bundle import BundleError
from inventory_dotnet_components import report
from inventory_dotnet_pack_licenses import PACKS, inspect
from verify_windowsdesktop_provenance import compare as pack_compare, read_local
from verify_dotnet_host_sections import APPS, template, compare as host_compare
from verify_dotnet_resource_serialization import compare as resource_compare
from run_offline_qa import write_json


def properties(**values: str) -> list[dict]:
    """Emit explicitly namespaced evidence properties."""
    return [{"name": "ajazz:" + name, "value": value} for name, value in values.items()]


def hash_value(value: str) -> list[dict]:
    """Represent a SHA-256 digest in CycloneDX syntax."""
    return [{"alg": "SHA-256", "content": value}]


def pack_component(kind: str, evidence: dict, count: int) -> dict:
    """Identify pinned source package, not an installed standalone package."""
    name, version, sha = PACKS[kind]
    result = {"type": "library", "bom-ref": "pack:" + kind,
              "name": name, "version": version,
              "purl": f"pkg:nuget/{name}@{version}", "hashes": hash_value(sha),
              "properties": properties(hash_scope="source NuGet archive",
                                         embedded_files=str(count),
                                         redistribution="REVIEW_REQUIRED")}
    if evidence["license"]["expression"]:
        result["licenses"] = [{"license": {"id": evidence["license"]["expression"]}}]
    else:
        result["licenses"] = [{"license": {"name": "Microsoft Windows SDK license",
                                           "url": evidence["license"]["url"]}}]
    return result


def file_component(item: dict, owner: str) -> dict:
    """Bind a file hash and size to its validated owner and bundle identity."""
    return {"type": "file", "bom-ref": "file:" + item["path"], "name": item["path"],
            "hashes": hash_value(item["sha256"]),
            "properties": properties(owner=owner, embedded_bytes=str(item["size"]),
                                     scope="embedded payload")}


def pack_files(attribution: dict, packs: dict, kind: str) -> tuple[list, set]:
    """Match all embedded third-party claims against exact pinned package bytes."""
    package = PACKS[kind][0]
    claims = [x for x in attribution["components"] if x["id"] == "runtimepack." + package]
    if not claims:
        return [], set()
    result = pack_compare(attribution, packs[kind], PACKS[kind][2], package)
    if not result["files"] or any(x["status"] != "match" for x in result["files"]):
        raise BundleError("Unverified embedded package files")
    names = {x["path"] for x in result["files"]}
    available = claims[0]["files"] + attribution["unmatched_files"]
    files = [file_component(x, "pack:" + kind) for x in available if x["path"] in names]
    if len(files) != len(names):
        raise BundleError("Ambiguous package coverage")
    return files, names


def validate_coverage(attribution: dict, files: list) -> None:
    """Require every embedded file exactly once, including configuration."""
    expected = [x["path"] for c in attribution["components"] for x in c["files"]]
    expected += [x["path"] for x in attribution["unmatched_files"] + attribution["configuration_files"]]
    actual = [x["name"] for x in files]
    if (attribution["missing_declared_files"] or len(actual) != len(set(actual))
            or sorted(expected) != sorted(actual)):
        raise BundleError("Incomplete or duplicate bundle coverage")


def create(raw: bytes, packs: dict, application: str) -> dict:
    """Compose verified scoped evidence, refusing unsupported native host content."""
    if set(packs) != set(PACKS):
        raise BundleError("Expected all four reviewed packages")
    evidence = {kind: inspect(value, kind) for kind, value in packs.items()}
    host = template(packs["host"])
    if not (host_compare(raw, host, application)["scoped_pass"] and
            resource_compare(raw, host, application)["scoped_pass"]):
        raise BundleError("Unverified host scope")
    attribution = report(raw)
    projects = [c for c in attribution["components"] if c["type"] == "project"]
    if len(projects) != 1 or [x["path"] for x in projects[0]["files"]] != [APPS[application][0]]:
        raise BundleError("Unexpected application identity")
    project = projects[0]
    files = [file_component(x, "application") for x in project["files"] + attribution["configuration_files"]]
    components = [pack_component("host", evidence["host"], 0)]
    for kind in ("core", "desktop", "sdk"):
        items, names = pack_files(attribution, packs, kind)
        if names:
            components.append(pack_component(kind, evidence[kind], len(names)))
            files.extend(items)
    validate_coverage(attribution, files)
    return document(attribution, project, components, files)


def document(attribution: dict, project: dict, packs: list, files: list) -> dict:
    """Build CycloneDX inventory without asserting a complete dependency graph."""
    root = {"type": "application", "bom-ref": "application", "name": project["id"],
            "version": project["version"], "hashes": hash_value(attribution["exe_sha256"]),
            "properties": properties(hash_scope="actual EXE", coverage="scoped Windows single-file",
                                     release_admission="NOT_VERIFIED", advisories="NOT_RUN",
                                     signatures="NOT_VERIFIED", dependency_graph="NOT_VERIFIED")}
    return {"bomFormat": "CycloneDX", "specVersion": "1.6", "version": 1,
            "metadata": {"component": root}, "components": packs + files,
            "compositions": [{"aggregate": "incomplete", "assemblies": ["application"]}]}


def main(argv: list[str] | None = None) -> int:
    """Write no-replace BOM; zero means only the reviewed input scope matched."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--application", choices=sorted(APPS), required=True)
    for kind in PACKS:
        parser.add_argument("--" + kind, type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        packs = {kind: read_local(getattr(args, kind)) for kind in PACKS}
        write_json(args.output, create(read_local(args.exe), packs, args.application))
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile, ET.ParseError) as error:
        print(f"ERROR: scoped SBOM ({type(error).__name__})", file=sys.stderr)
        return 2
    print("PASS: scoped Windows SBOM; complete product coverage not verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
