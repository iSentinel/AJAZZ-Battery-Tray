#!/usr/bin/env python3
"""Separate shipped Apple application files from external OS advisory scope."""

import argparse
from pathlib import Path
import sys

from run_offline_qa import write_json
from validate_scoped_sbom_schema import digest, document, read


def properties(item: dict) -> dict:
    """Reject duplicate property names in scoped component evidence."""
    rows = item['properties']
    result = {row['name']: row['value'] for row in rows}
    if len(result) != len(rows):
        raise ValueError('duplicate component properties')
    return result


def classify(bom: dict) -> tuple[list, list]:
    """Require unique shipped files and distinguish external OS install names."""
    shipped, external, seen = [], [], set()
    for item in bom['components']:
        ref, name = item['bom-ref'], item['name']
        props = properties(item)
        if ref in seen:
            raise ValueError('duplicate component')
        seen.add(ref)
        if item['type'] == 'file' and ref == 'file:' + name:
            if props['ajazz:scope'] != 'shipped app member':
                raise ValueError('unexpected file scope')
            shipped.append(ref)
        elif item['type'] == 'library' and ref == 'system:' + name:
            if (props['ajazz:scope'] != 'external OS dependency, not shipped'
                    or props['ajazz:installed_version'] != 'NOT_VERIFIED'
                    or not name.startswith(('/System/Library/', '/usr/lib/'))
                    or item['scope'] != {'required': 'required', 'weak': 'optional'}[
                        props['ajazz:linkage']]):
                raise ValueError('unexpected OS library scope')
            external.append({'path': name, 'linkage': props['ajazz:linkage'],
                             'installed_version': 'NOT_VERIFIED',
                             'advisory_disposition': 'OS_BUILD_REQUIRED'})
        else:
            raise ValueError('unexpected component type')
    if len(shipped) != 7 or not external:
        raise ValueError('unexpected component inventory')
    return shipped, external


def audit(raw: bytes, schema: dict) -> dict:
    """Bind the schema observation and preserve unknown OS patch state."""
    bom = document(raw)
    if (schema.get('schema') != 'scoped-sbom-schema-v1'
            or schema.get('sbom_sha256') != digest(raw)
            or schema.get('schema_validation') != 'PASS'
            or schema.get('components') != len(bom['components'])
            or schema.get('release_admission') != 'NOT_VERIFIED'
            or bom.get('compositions') != [{'aggregate': 'incomplete', 'assemblies': ['application']}]):
        raise ValueError('schema evidence differs')
    root = bom['metadata']['component']
    props = properties(root)
    edition = props['ajazz:edition']
    if edition not in ('universal', 'high-sierra') or props['ajazz:hash_scope'] != 'actual app ZIP':
        raise ValueError('unexpected Apple root')
    shipped, external = classify(bom)
    return {'schema': 'apple-os-dependency-scope-v1', 'sbom_sha256': digest(raw),
            'archive_sha256': root['hashes'][0]['content'], 'edition': edition,
            'shipped_files': len(shipped), 'external_libraries': external,
            'minimum_os': props['ajazz:plist_minimum'],
            'installed_os_build': 'NOT_VERIFIED', 'os_advisories': 'OS_BUILD_REQUIRED',
            'legacy_risk': 'REVIEW_REQUIRED' if edition == 'high-sierra' else 'OS_BUILD_REQUIRED',
            'complete_dependency_graph': 'NOT_VERIFIED',
            'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Emit a scoped dependency classification, never vulnerability clearance."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('sbom', 'schema-evidence', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        write_json(args.output, audit(read(args.sbom), document(read(args.schema_evidence))))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        print('FAIL: Apple OS dependency scope', file=sys.stderr)
        return 2
    print('PASS: Apple dependency scope; installed OS build and advisories remain unverified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
