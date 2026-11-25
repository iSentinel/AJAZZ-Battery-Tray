#!/usr/bin/env python3
"""Produce a bounded, sanitized inventory of one NuGet restore graph."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from run_offline_qa import read_evidence, write_json

NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,159}")
VERSION = re.compile(r"[0-9][A-Za-z0-9.+-]{0,79}")
TARGET = re.compile(r"[A-Za-z0-9][A-Za-z0-9.,=+/_-]{0,159}")
RANGE = re.compile(r"(?:[0-9][A-Za-z0-9.+-]{0,79}|[\[(][0-9A-Za-z., +\-]{1,160}[\])])")


def unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    """Reject duplicate JSON keys rather than silently choosing the last."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON member")
        result[key] = value
    return result


def mapping(value: object) -> dict:
    """Require a JSON object."""
    if not isinstance(value, dict):
        raise ValueError("Expected an object")
    return value


def token(value: object, pattern: re.Pattern) -> str:
    """Return a limited metadata token, never an arbitrary input string."""
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ValueError("Invalid dependency metadata")
    return value


def package_list(entries: dict, libraries: dict) -> list[dict]:
    """Extract package identities for a target; omit path and file metadata."""
    result = []
    seen = set()
    for key, info in sorted(entries.items()):
        library = mapping(libraries[key])
        kind = mapping(info).get("type")
        if kind != library.get("type") or kind not in ("package", "project"):
            raise ValueError("Inconsistent or unsupported library type")
        if kind == "project":
            continue
        name, separator, version = key.partition("/")
        if not separator or name.lower() in seen:
            raise ValueError("Invalid or duplicate package identity")
        seen.add(name.lower())
        result.append({"id": token(name, NAME), "version": token(version, VERSION)})
    return result


def framework_list(frameworks: dict) -> list[dict]:
    """Inventory declared framework references and SDK download requests."""
    result = []
    for name, info in sorted(frameworks.items()):
        details = mapping(info)
        refs = mapping(details.get("frameworkReferences", {}))
        downloads = details.get("downloadDependencies", [])
        if not isinstance(downloads, list):
            raise ValueError("Invalid download dependencies")
        entries = []
        seen = set()
        for item in downloads:
            entry = mapping(item)
            package = token(entry["name"], NAME)
            if package.lower() in seen:
                raise ValueError("Duplicate download dependency")
            seen.add(package.lower())
            entries.append({"id": package, "requested": token(entry["version"], RANGE)})
        result.append({
            "framework": token(name, TARGET),
            "framework_references": sorted(token(ref, NAME) for ref in refs),
            "download_dependencies": sorted(entries, key=lambda item: item["id"]),
        })
    return result


def inventory(raw: bytes) -> dict:
    """Project version-3 assets onto an explicitly limited metadata schema."""
    data = mapping(json.loads(raw, object_pairs_hook=unique_pairs))
    if type(data.get("version")) is not int or data["version"] != 3:
        raise ValueError("Unsupported assets schema")
    targets = mapping(data["targets"])
    libraries = mapping(data["libraries"])
    frameworks = mapping(mapping(data["project"])["frameworks"])
    if not targets or not frameworks:
        raise ValueError("Missing restore targets or frameworks")
    return {
        "schema": 1,
        "scope": "NuGet restore metadata only; not a packaged SBOM",
        "assets_sha256": hashlib.sha256(raw).hexdigest(),
        "targets": [{"target": token(key, TARGET),
                     "packages": package_list(mapping(value), libraries)}
                    for key, value in sorted(targets.items())],
        "frameworks": framework_list(frameworks),
    }


def main(argv: list[str] | None = None) -> int:
    """Return 0 for inventory, 2 for invalid input or existing output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    stage = "input"
    try:
        raw = read_evidence(args.assets)
        stage = "schema"
        result = inventory(raw)
        stage = "output"
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        print(f"ERROR: restore inventory {stage} ({type(error).__name__})",
              file=sys.stderr)
        return 2
    print("PASS: restore metadata inventory (not release admission)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
