#!/usr/bin/env python3
"""Attribute actual .NET bundle files to explicitly declared deps libraries."""

import argparse
import json
from pathlib import Path
import re
import sys

from inventory_dotnet_bundle import LIMIT, inventory, BundleError, relative_name
from inventory_nuget_assets import unique_pairs, mapping, token, NAME, VERSION
from run_offline_qa import write_json

TARGET = re.compile(r"\.NETCoreApp,Version=v[0-9]+\.[0-9]+/win-x64")


def deps_document(data: bytes, files: list[dict]) -> dict:
    """Read only the previously validated embedded dependency record."""
    item, = [item for item in files if item["type"] == "deps"]
    if item["size"] > 2 * 1024 * 1024:
        raise BundleError("Embedded deps exceeds limit")
    raw = data[item["offset"]:item["offset"] + item["size"]]
    return mapping(json.loads(raw, object_pairs_hook=unique_pairs))


def identity(key: str, value: object) -> dict:
    """Keep project/runtimepack/package identities distinct."""
    name, separator, version = key.partition("/")
    kind = mapping(value).get("type")
    if not separator or kind not in ("project", "runtimepack", "package"):
        raise BundleError("Unknown library identity")
    return {"id": token(name, NAME), "version": token(version, VERSION),
            "type": kind}


def claims(component: dict) -> list[str]:
    """Accept explicit flat runtime paths and localized resource paths only."""
    result = []
    for section in ("runtime", "native", "resources"):
        for path, value in mapping(component.get(section, {})).items():
            mapping(value)
            result.append(relative_name(path))
    if component.get("runtimeTargets"):
        raise BundleError("Unreviewed runtimeTargets layout")
    if len(set(path.casefold() for path in result)) != len(result):
        raise BundleError("Duplicate declared asset")
    return sorted(result)


def correlate(deps: dict, files: list[dict]) -> dict:
    """Match exact paths; preserve missing, ambiguous and unclaimed evidence."""
    runtime = token(mapping(deps["runtimeTarget"])["name"], TARGET)
    libraries = mapping(deps["libraries"])
    targets = mapping(deps["targets"])
    selected = mapping(targets[runtime])
    if not libraries or set(selected) != set(libraries):
        raise BundleError("Inconsistent selected library inventory")
    components, owners, absent = [], {}, []
    payload = {item["path"]: item for item in files
               if item["type"] not in ("deps", "runtimeconfig")}
    for key, value in sorted(selected.items()):
        component = identity(key, libraries[key])
        paths = claims(mapping(value))
        component["files"] = []
        for path in paths:
            if path.casefold() in owners:
                raise BundleError("Ambiguous asset ownership")
            owners[path.casefold()] = key
            if path in payload:
                component["files"].append(payload[path])
            else:
                absent.append({"library": key, "path": path})
        components.append(component)
    unmatched = [item for path, item in sorted(payload.items())
                 if path not in {file["path"] for component in components
                                 for file in component["files"]}]
    return {"runtime_target": runtime, "components": components,
            "unmatched_files": unmatched, "missing_declared_files": absent}


def report(data: bytes) -> dict:
    """Bind attribution to the hash of the actual executable."""
    bundle = inventory(data)
    result = correlate(deps_document(data, bundle["files"]), bundle["files"])
    return {"schema": 1, "exe_sha256": bundle["sha256"],
            "scope": "embedded deps claims; incomplete SBOM",
            "configuration_files": [item for item in bundle["files"]
                                    if item["type"] in ("deps", "runtimeconfig")],
            **result}


def main(argv: list[str] | None = None) -> int:
    """Produce read-only attribution evidence; never overwrite an output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.exe.is_symlink() or not args.exe.is_file():
            raise BundleError("Expected a regular executable")
        with args.exe.open("rb") as stream:
            data = stream.read(LIMIT + 1)
        write_json(args.output, report(data))
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        print(f"ERROR: dependency attribution ({type(error).__name__})",
              file=sys.stderr)
        return 2
    print("PASS: scoped dependency attribution (not release admission)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
