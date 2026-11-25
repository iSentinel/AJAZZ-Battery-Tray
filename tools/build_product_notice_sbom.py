#!/usr/bin/env python3
"""Bind scoped Windows SBOM evidence to the exercised product notice probe."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

from build_scoped_windows_sbom import create
from inventory_dotnet_pack_licenses import PACKS
from read_diagnostic_session import unique_object
from verify_windows_notice_transport import MANIFEST_SHA
from verify_windowsdesktop_provenance import read_local

HEX = re.compile(r'[0-9a-f]{64}')
SHA = re.compile(r'[0-9a-f]{40}')


def digest(raw: bytes) -> str:
    """Hash exact binary or document bytes."""
    return hashlib.sha256(raw).hexdigest()


def lifecycle(raw: bytes) -> dict:
    """Parse bounded JSON without accepting duplicate keys."""
    if not 0 < len(raw) <= 65536:
        raise ValueError('invalid lifecycle extent')
    value = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_object)
    if not isinstance(value, dict):
        raise ValueError('invalid lifecycle document')
    return value


def bind(app: bytes, setup: bytes, clean: dict, upgrade: dict, source: str) -> dict:
    """Require the same actual app/setup/source and passed scoped lifecycle."""
    if not SHA.fullmatch(source):
        raise ValueError('invalid checkout identity')
    identity = {'source_sha': source, 'app_sha256': digest(app),
                'setup_sha256': digest(setup)}
    common = {'tray_launch': 'NOT_OBSERVED', 'physical_acceptance': 'NOT_VERIFIED',
              'release_admission': 'NOT_VERIFIED'}
    expected_clean = {**identity, **common, 'schema': 'product-notice-probe-v1',
                      'installed_notices': 'MATCH', 'uninstalled_notices': 'REMOVED'}
    expected_upgrade = {**identity, **common, 'schema': 'product-notice-upgrade-v1',
                        'baseline_setup_sha256': '555b957b809c2f1bb4228c10a818abadad2df78e455925871713ee7779970672',
                        'baseline_app_sha256': upgrade.get('baseline_app_sha256'),
                        'upgrade_notices': 'MATCH',
                        'reinstall_restores_missing_notice': 'PASS',
                        'uninstall_notices': 'REMOVED', 'synthetic_user_data': 'PRESERVED'}
    old = expected_upgrade['baseline_app_sha256']
    if (clean != expected_clean or upgrade != expected_upgrade
            or not isinstance(old, str) or not HEX.fullmatch(old) or old == identity['app_sha256']):
        raise ValueError('lifecycle evidence differs from candidate')
    return identity


def encode(value: dict) -> bytes:
    """Canonical UTF-8 LF evidence regardless of operating system."""
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf-8')


def qualify(app: bytes, setup: bytes, clean: bytes, upgrade: bytes,
            source: str, packs: dict) -> tuple[bytes, dict]:
    """Rebuild scoped BOM from the same binaries after lifecycle checks."""
    identity = bind(app, setup, lifecycle(clean), lifecycle(upgrade), source)
    bom = create(app, packs, 'tray')
    if bom['metadata']['component']['hashes'] != [
            {'alg': 'SHA-256', 'content': identity['app_sha256']}]:
        raise ValueError('SBOM application identity differs')
    data = encode(bom)
    record = {'schema': 'product-notice-sbom-v1', **identity,
              'clean_lifecycle_sha256': digest(clean),
              'upgrade_lifecycle_sha256': digest(upgrade),
              'notice_manifest_sha256': MANIFEST_SHA,
              'sbom_sha256': digest(data), 'components': len(bom['components']),
              'composition': 'INCOMPLETE', 'schema_validation': 'NOT_VERIFIED',
              'release_admission': 'NOT_VERIFIED'}
    return data, record


def main(argv: list[str] | None = None) -> int:
    """Write new scoped SBOM and binding evidence, without executing binaries."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('app', 'setup', 'clean', 'upgrade', 'sbom', 'output', *PACKS):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--source-sha', required=True)
    args = parser.parse_args(argv)
    try:
        if any(p.exists() or p.is_symlink() for p in (args.sbom, args.output)):
            raise ValueError('output already exists')
        data, record = qualify(read_local(args.app), read_local(args.setup),
                               read_local(args.clean), read_local(args.upgrade), args.source_sha,
                               {k: read_local(getattr(args, k)) for k in PACKS})
        with args.sbom.open('xb') as stream:
            stream.write(data)
        with args.output.open('xb') as stream:
            stream.write(encode(record))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile, ET.ParseError):
        print('FAIL: product notice SBOM binding', file=sys.stderr)
        return 2
    print('PASS: scoped product notice SBOM bound to actual lifecycle; release not admitted')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
