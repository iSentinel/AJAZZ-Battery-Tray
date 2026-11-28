#!/usr/bin/env python3
"""Validate a scoped CycloneDX 1.6 BOM with exact local schemas, offline."""

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys

from read_diagnostic_session import unique_object
from run_offline_qa import write_json

PINS = {
    'bom-1.6.schema.json': '3e92dddbc30cf7f6a02b80f0942b1a4cfd4fb1c26f1dfc4310afa9d613cafb93',
    'jsf-0.82.schema.json': '8bae002c25e723db7ee1f26afde680ae1a2b1a8f6b4b4b0fd65dc3becb090aae',
    'spdx.schema.json': 'baa9d3bd1ed57b6751b0887edead6b5063ff53ff7429cf85d476c6c94af0166e',
}
ROOT_SCHEMA = 'bom-1.6.schema.json'
LIMIT = 2 * 1024 * 1024


def digest(raw: bytes) -> str:
    """Return SHA-256 of the original input bytes."""
    return hashlib.sha256(raw).hexdigest()


def read(path: Path) -> bytes:
    """Read bounded regular local files, refusing symlinks."""
    if path.is_symlink() or not path.is_file():
        raise ValueError('expected regular local document')
    with path.open('rb') as stream:
        raw = stream.read(LIMIT + 1)
    if not 0 < len(raw) <= LIMIT:
        raise ValueError('document extent exceeds limit')
    return raw


def document(raw: bytes) -> dict:
    """Reject duplicate JSON keys and non-object documents."""
    data = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_object)
    if not isinstance(data, dict):
        raise ValueError('expected JSON object')
    return data


def schemas(root: Path) -> dict[str, dict]:
    """Load only the exact reviewed schema files and identities."""
    result = {}
    for name, pin in PINS.items():
        raw = read(root / name)
        if digest(raw) != pin:
            raise ValueError('schema digest differs')
        schema = document(raw)
        if schema.get('$id') != 'http://cyclonedx.org/schema/' + name:
            raise ValueError('schema identity differs')
        result[name] = schema
    return result


def binding(raw: bytes, bom: dict, record: dict) -> None:
    """Optionally verify the exact BOM hash and candidate root identity."""
    if (record.get('schema') != 'product-notice-sbom-v1'
            or record.get('sbom_sha256') != digest(raw)
            or record.get('components') != len(bom['components'])
            or record.get('composition') != 'INCOMPLETE'
            or record.get('release_admission') != 'NOT_VERIFIED'
            or bom['metadata']['component']['hashes'] != [
                {'alg': 'SHA-256', 'content': record.get('app_sha256')}]):
        raise ValueError('SBOM binding differs')


def validate(raw: bytes, local: dict, record: dict | None = None) -> dict:
    """Use the pinned validator and an offline-only local schema registry."""
    from jsonschema import Draft7Validator
    from referencing import Registry, Resource

    if version('jsonschema') != '4.23.0':
        raise ValueError('unreviewed validator version')
    bom = document(raw)
    registry = Registry().with_resources(
        (value['$id'], Resource.from_contents(value)) for value in local.values())
    root = local[ROOT_SCHEMA]
    Draft7Validator.check_schema(root)
    validator = Draft7Validator(root, registry=registry)
    if not validator.is_valid(bom):
        raise ValueError('CycloneDX schema validation failed')
    if bom.get('compositions') != [{'aggregate': 'incomplete', 'assemblies': ['application']}]:
        raise ValueError('unexpected scoped composition')
    if record is not None:
        binding(raw, bom, record)
    return {'schema': 'scoped-sbom-schema-v1', 'sbom_sha256': digest(raw),
            'components': len(bom['components']), 'schema_sha256': PINS,
            'validator': 'jsonschema 4.23.0 Draft7', 'schema_validation': 'PASS',
            'candidate_binding': 'MATCH' if record is not None else 'NOT_PROVIDED',
            'composition': 'INCOMPLETE', 'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Emit new schema evidence; schema validity is not release admission."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sbom', type=Path, required=True)
    parser.add_argument('--schema-dir', type=Path, required=True)
    parser.add_argument('--binding', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        record = document(read(args.binding)) if args.binding else None
        result = validate(read(args.sbom), schemas(args.schema_dir), record)
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, ImportError):
        print('FAIL: scoped offline CycloneDX validation', file=sys.stderr)
        return 2
    print('PASS: scoped CycloneDX schema; release not admitted')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
