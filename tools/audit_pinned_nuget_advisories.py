#!/usr/bin/env python3
"""Evaluate stable pinned package versions against a local NuGet feed snapshot."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

from inventory_dotnet_bundle import BundleError
from inventory_dotnet_pack_licenses import PACKS
from inventory_nuget_assets import unique_pairs
from run_offline_qa import write_json

VERSION = re.compile(r"([0-9]{1,10}(?:\.[0-9]{1,10}){1,3})(?:-([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*))?")
PAGE = re.compile(r"https://api\.nuget\.org/v3-vulnerabilities/[0-9.]+(?:/[0-9.]+)?/vulnerability\.(base|update)\.json")
URL = re.compile(r"https://github\.com/advisories/GHSA-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}")
LIMIT = 16 * 1024 * 1024


def version_key(value: str) -> tuple:
    """Parse only reviewed numeric versions and optional prerelease identifiers."""
    match = VERSION.fullmatch(value)
    if not match:
        raise BundleError("Unsupported advisory version")
    parts = tuple(int(x) for x in match[1].split('.'))
    if any(x > 2147483647 for x in parts):
        raise BundleError("Version component exceeds range")
    prerelease = tuple((0, int(x)) if x.isdigit() else (1, x.lower())
                       for x in match[2].split('.')) if match[2] else ()
    return parts + (0,) * (4 - len(parts)), not bool(prerelease), prerelease


def affected(version: str, interval: str) -> bool:
    """Compare reviewed NuGet interval syntax; refuse unknown or malformed bounds."""
    current = version_key(version)
    if not current[1] or not isinstance(interval, str) or len(interval) > 256:
        raise BundleError("Unsupported audit target or interval")
    if len(interval) < 3 or interval[0] not in '[(' or interval[-1] not in '])':
        raise BundleError("Unsupported advisory interval")
    fields = [x.strip() for x in interval[1:-1].split(',')]
    if len(fields) == 1 and interval[0] == '[' and interval[-1] == ']':
        return current == version_key(fields[0])
    if len(fields) != 2 or not any(fields):
        raise BundleError("Invalid advisory interval")
    low, high = (version_key(x) if x else None for x in fields)
    if ((low is None and interval[0] != '(') or (high is None and interval[-1] != ')')
            or (low is not None and high is not None and low > high)):
        raise BundleError("Invalid advisory bounds")
    return (low is None or current > low or current == low and interval[0] == '[') and (
        high is None or current < high or current == high and interval[-1] == ']')


def read_json(path: Path) -> tuple[object, str]:
    """Read bounded immutable local evidence; reject duplicate JSON keys."""
    if path.is_symlink() or not path.is_file():
        raise BundleError("Expected regular snapshot file")
    with path.open('rb') as stream:
        raw = stream.read(LIMIT + 1)
    if not raw or len(raw) > LIMIT:
        raise BundleError("Snapshot exceeds budget")
    return json.loads(raw, object_pairs_hook=unique_pairs), hashlib.sha256(raw).hexdigest()


def load_snapshot(root: Path) -> tuple[list, list]:
    """Require both observed feed partitions and record input hashes and timestamps."""
    index, digest = read_json(root / 'index.json')
    if not isinstance(index, list) or len(index) != 2:
        raise BundleError("Unexpected vulnerability index")
    pages, evidence, seen = [], [], set()
    for row in index:
        name, url, updated = row['@name'], row['@id'], row['@updated']
        match = PAGE.fullmatch(url)
        if not match or name != match[1] or name in seen:
            raise BundleError("Unexpected vulnerability page identity")
        parsed = datetime.fromisoformat(updated.replace('Z', '+00:00'))
        if parsed.tzinfo is None or parsed > datetime.now(timezone.utc):
            raise BundleError("Invalid vulnerability page timestamp")
        seen.add(name)
        page, sha = read_json(root / (name + '.json'))
        if not isinstance(page, dict) or (name == 'base' and not page):
            raise BundleError("Invalid vulnerability page")
        pages.append(page)
        evidence.append({'name': name, 'url': url, 'updated': updated, 'sha256': sha})
    if seen != {'base', 'update'}:
        raise BundleError("Incomplete vulnerability snapshot")
    return pages, [{'name': 'index', 'sha256': digest}] + evidence


def scan(pages: list, package: str, version: str) -> dict:
    """Evaluate every matching package range in both partitions."""
    matches, count = set(), 0
    for page in pages:
        records = page.get(package.lower(), [])
        if not isinstance(records, list):
            raise BundleError("Invalid advisory list")
        for row in records:
            url, severity, interval = row['url'], row['severity'], row['versions']
            if not URL.fullmatch(url) or type(severity) is not int or severity not in range(4):
                raise BundleError("Unsupported advisory record")
            count += 1
            if affected(version, interval):
                matches.add((url, severity, interval))
    return {'package': package, 'version': version, 'ranges_examined': count,
            'matches': [{'url': u, 'severity': s, 'range': v} for u, s, v in sorted(matches)]}


def main(argv: list[str] | None = None) -> int:
    """Exit 0 for no matching ranges, 2 for matches or incomplete evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        pages, evidence = load_snapshot(args.snapshot)
        entries = [scan(pages, name, version) for name, version, _ in PACKS.values()]
        matched = any(x['matches'] for x in entries)
        write_json(args.output, {'schema': 1, 'scope': 'four pinned NuGet package versions',
                                 'source': 'NuGet VulnerabilityInfo local snapshot',
                                 'evaluated_utc': datetime.now(timezone.utc).isoformat(),
                                 'inputs': evidence, 'packages': entries,
                                 'snapshot_authentication': 'NOT_VERIFIED',
                                 'freshness_gate': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'})
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        print(f'ERROR: advisory audit ({type(error).__name__})', file=sys.stderr)
        return 2
    print('FAIL: matching advisory ranges' if matched else 'PASS: no matching ranges in supplied snapshot; not release admission')
    return 2 if matched else 0


if __name__ == '__main__':
    raise SystemExit(main())
