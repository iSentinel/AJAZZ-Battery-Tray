#!/usr/bin/env python3
"""Verify local OSV querybatch observations against exact scoped BOM identity."""

import argparse
from pathlib import Path
import re
import sys

from audit_product_sbom_advisories import package_set
from inventory_dotnet_pack_licenses import PACKS
from run_offline_qa import write_json
from validate_scoped_sbom_schema import binding, digest, document, read

ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,199}')


def crosscheck(bom_raw: bytes, bound: dict, query_raw: bytes, response_raw: bytes) -> dict:
    """Require exact ordered requests, all results and no pending page."""
    bom = document(bom_raw)
    binding(bom_raw, bom, bound)
    package_set(bom)
    expected = [{'package': {'ecosystem': 'NuGet', 'name': name}, 'version': version}
                for name, version, _ in PACKS.values()]
    if document(query_raw) != {'queries': expected}:
        raise ValueError('unexpected OSV query')
    response = document(response_raw)
    results = response.get('results')
    if set(response) != {'results'} or not isinstance(results, list) or len(results) != len(expected):
        raise ValueError('unexpected OSV result count')
    packages = []
    for query, result in zip(expected, results):
        if not isinstance(result, dict) or set(result) - {'vulns'}:
            raise ValueError('unexpected or paginated OSV result')
        vulns = result.get('vulns', [])
        if not isinstance(vulns, list):
            raise ValueError('invalid OSV vulnerability list')
        ids = []
        for vuln in vulns:
            identifier = vuln['id']
            if not isinstance(identifier, str) or not ID.fullmatch(identifier):
                raise ValueError('invalid OSV identifier')
            ids.append(identifier)
        packages.append({'package': query['package']['name'], 'version': query['version'],
                         'ids': sorted(set(ids))})
    return {'schema': 'product-sbom-osv-v1', 'sbom_sha256': digest(bom_raw),
            'app_sha256': bound['app_sha256'], 'request_sha256': digest(query_raw),
            'response_sha256': digest(response_raw), 'packages': packages,
            'result': 'MATCHES_FOUND' if any(p['ids'] for p in packages) else 'NO_IDS_RETURNED',
            'scope': 'four exact NuGet source pack versions; local OSV response',
            'response_authentication': 'NOT_VERIFIED', 'freshness_gate': 'NOT_VERIFIED',
            'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Reject malformed observations and report positive matches as failure."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('sbom', 'binding', 'query', 'response', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = crosscheck(read(args.sbom), document(read(args.binding)),
                            read(args.query), read(args.response))
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        print('FAIL: scoped OSV crosscheck', file=sys.stderr)
        return 2
    print(result['result'] + ': scoped response only; release not admitted')
    return 0 if result['result'] == 'NO_IDS_RETURNED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
