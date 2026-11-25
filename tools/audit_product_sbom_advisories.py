#!/usr/bin/env python3
"""Bind scoped NuGet advisory observations to the exact product-probe BOM."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

from audit_pinned_nuget_advisories import load_snapshot, scan
from inventory_dotnet_pack_licenses import PACKS
from run_offline_qa import write_json
from validate_scoped_sbom_schema import binding, digest, document, read


def package_set(bom: dict) -> None:
    """Require all four exact source pack identities, hashes and PURLs."""
    expected = {
        'pack:' + kind: (name, version, sha)
        for kind, (name, version, sha) in PACKS.items()
    }
    libraries = [item for item in bom['components'] if item['type'] == 'library']
    if len(libraries) != len(expected):
        raise ValueError('unexpected library count')
    for item in libraries:
        name, version, sha = expected.pop(item['bom-ref'])
        if (item['name'] != name or item['version'] != version
                or item['purl'] != f'pkg:nuget/{name}@{version}'
                or item['hashes'] != [{'alg': 'SHA-256', 'content': sha}]):
            raise ValueError('source pack identity differs')
    if expected:
        raise ValueError('missing source pack')


def audit(raw: bytes, record: dict, schema: dict, snapshot: Path) -> dict:
    """Check exact scoped BOM/schema identity and scan the supplied snapshot."""
    bom = document(raw)
    binding(raw, bom, record)
    if (schema.get('schema') != 'scoped-sbom-schema-v1'
            or schema.get('sbom_sha256') != digest(raw)
            or schema.get('components') != len(bom['components'])
            or schema.get('schema_validation') != 'PASS'
            or schema.get('candidate_binding') != 'MATCH'
            or schema.get('release_admission') != 'NOT_VERIFIED'):
        raise ValueError('schema evidence differs')
    package_set(bom)
    pages, inputs = load_snapshot(snapshot)
    packages = [scan(pages, name, version) for name, version, _ in PACKS.values()]
    return {'schema': 'product-sbom-advisory-v1', 'scope': 'four exact NuGet source packs',
            'sbom_sha256': digest(raw), 'app_sha256': record['app_sha256'],
            'setup_sha256': record['setup_sha256'], 'source_sha': record['source_sha'],
            'evaluated_utc': datetime.now(timezone.utc).isoformat(),
            'inputs': inputs, 'packages': packages,
            'result': 'MATCHES_FOUND' if any(p['matches'] for p in packages) else 'NO_MATCHING_RANGES',
            'snapshot_authentication': 'NOT_VERIFIED', 'freshness_gate': 'NOT_VERIFIED',
            'other_components': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Evaluate local evidence; matching advisories or invalid inputs fail closed."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('sbom', 'binding', 'schema-evidence', 'snapshot', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = audit(read(args.sbom), document(read(args.binding)),
                       document(read(args.schema_evidence)), args.snapshot)
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        print('FAIL: scoped product SBOM advisory audit', file=sys.stderr)
        return 2
    print(result['result'] + ': scoped NuGet snapshot only; release not admitted')
    return 0 if result['result'] == 'NO_MATCHING_RANGES' else 2


if __name__ == '__main__':
    raise SystemExit(main())
