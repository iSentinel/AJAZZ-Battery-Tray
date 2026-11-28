#!/usr/bin/env python3
"""Replay exact retained notice-bearing setup evidence, never release admission."""

import argparse
import base64
from io import BytesIO
from pathlib import Path
import re
import stat
import sys
import zipfile

from build_consolidated_portable_notices import APP, pins
from run_offline_qa import write_json
from stage_consolidated_signature_inputs import FILES, SOURCE
from validate_scoped_sbom_schema import digest, document, read
from verify_inno674_components import VENDOR
from verify_interactive_acceptance import candidate
from verify_windows_notice_transport import MANIFEST_SHA

ARCHIVE_SHA = 'fa752c9e5534aad2b9278d4d94fdf332a57752079ee70db1c90103105c9942f9'
SETUP_SHA = '2512ef432c8acd75622157e16eda04694b41705294f1876547130ccd21b2147b'
UNINSTALLER_SHA = '9f07d326d9136adfa67658ba5719731a17e1a1a3ac7ef66e441d35673e99804e'
LIMIT = 65536
DOCS = {
    'local-build-evidence': '7280eb74913b568b6c84279d69afb608d19700b075597c55f4def8ab39b18937',
    'product-components-before': '8e5ef99b6b7b22a4e5b5c168edae88ba44c293a450d4089e3d659045fdbf5875',
    'product-components-after': '8e5ef99b6b7b22a4e5b5c168edae88ba44c293a450d4089e3d659045fdbf5875',
    'staged-evidence': 'f5581a6502e2a73fc94c54c80485e8268e75b6c0a1f90eae2a2f4e7e0276c8a0',
    'product-installed-evidence': 'f5581a6502e2a73fc94c54c80485e8268e75b6c0a1f90eae2a2f4e7e0276c8a0',
    'product-lifecycle': '97bce7e27da93892b28773f815b5552fd12b18d7f52636d199f36d6bbd3336c3',
    'production-shape': '73e2cd5a1f9b0809940b56ba8974ff1ebe0de297ba009e4486277d05c2822221',
    'exercised-uninstaller': '805bb8c3399ca8da3f0052218dfc1687b42f53beb9a3dcbb9cb5c7fb221f9ce0',
    'authenticode': 'ce21ecc0f60799b87240eb5e3e6cfe5a5f5e51db76dcfacc2338bb78fda4f80d',
    'release-attestation': '3e6c938fa83b2d5095f3c89d0aac3de3b5be5447bce14b0060b2090d5b8a8e0d',
}


def require(ok: bool) -> None:
    """Reject missing or contradictory scoped observations."""
    if not ok:
        raise ValueError('inconsistent exact notice setup evidence')


def paths() -> dict:
    """Return the ten exact original artifact paths."""
    return {('ajazz-inno-674-publisher/' if k in ('authenticode', 'release-attestation')
             else 'ajazz-notice-probe/') + k + '.json': k for k in DOCS}


def unpack(raw: bytes) -> dict:
    """Validate original archive identity, bounded inventory and member digests."""
    require(0 < len(raw) <= LIMIT and digest(raw) == ARCHIVE_SHA)
    names = paths()
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        infos = archive.infolist()
        require(len(infos) == len(names) and {i.filename for i in infos} == set(names))
        require(sum(i.file_size for i in infos) <= LIMIT)
        for info in infos:
            require(info.orig_filename == info.filename and not info.flag_bits & 1
                    and 0 < info.file_size <= LIMIT
                    and stat.S_IFMT(info.external_attr >> 16) in (0, stat.S_IFREG)
                    and info.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED))
        docs = {names[i.filename]: archive.read(i) for i in infos}
    require(all(digest(docs[k]) == v for k, v in DOCS.items()))
    return docs


def check_build(raw: bytes, row: dict) -> None:
    """Reuse the local builder identity check and require the exact original icons."""
    identity = candidate(raw)
    require(identity['setup_sha256'] == SETUP_SHA and identity['app_sha256'] == FILES[APP])
    icons = {Path(name).name: sha for name, (_, sha) in pins().items() if name != APP}
    require(row['icons'] == icons)


def check_lifecycle(rows: dict) -> None:
    """Require the clean silent lifecycle and one immutable setup identity."""
    common = {'source_sha': SOURCE, 'setup_sha256': SETUP_SHA,
              'app_sha256': FILES[APP], 'release_admission': 'NOT_VERIFIED'}
    require(rows['product-lifecycle'] == {
        **common, 'schema': 'product-notice-probe-v1',
        'installed_notices': 'MATCH', 'uninstalled_notices': 'REMOVED',
        'tray_launch': 'NOT_OBSERVED', 'physical_acceptance': 'NOT_VERIFIED'})
    require(rows['production-shape'] == {
        **common, 'schema': 'inno-674-production-shape-v1',
        'output_filename': 'AJAZZBatteryTray-Setup-win-x64.exe',
        'version': '0.3.0-beta.61', 'default_program_files_install': 'MATCH',
        'default_silent_launch': 'NOT_OBSERVED', 'uninstalled': 'REMOVED'})
    require(rows['exercised-uninstaller'] == {
        **common, 'schema': 'inno-674-exercised-uninstaller-v1',
        'uninstaller_sha256': UNINSTALLER_SHA, 'uninstall_result': 'REMOVED'})


def check_inputs(rows: dict) -> None:
    """Check compiler and notices before/after and recorded publisher identity."""
    compiler = rows['product-components-before']
    require(compiler == rows['product-components-after']
            and compiler['vendor_sha256'] == VENDOR
            and compiler['engine_version'] == '6.7.4'
            and compiler['component_identity'] == 'MATCH'
            and compiler['release_admission'] == 'NOT_VERIFIED'
            and len(compiler['files']) == 38)
    notices = rows['staged-evidence']
    require(notices == rows['product-installed-evidence']
            and notices['manifest_sha256'] == MANIFEST_SHA
            and notices['notice_transport'] == 'MATCH'
            and notices['distribution_compliance'] == notices['release_admission'] == 'NOT_VERIFIED'
            and len(notices['files']) == 9)
    sig = rows['authenticode']
    require(sig['asset_sha256'] == VENDOR and sig['status'] == 'Valid'
            and sig['signature_type'] == 'Authenticode' and sig['publisher'] == 'Pyrsys B.V.'
            and sig['release_admission'] == 'NOT_VERIFIED')
    require(all(re.fullmatch('[0-9a-f]{64}', sig[k]) for k in (
        'signer_cert_sha256', 'timestamp_cert_sha256')))


def check_attestation(row: dict) -> None:
    """Inspect the retained attestation subject, not independently verify its signature."""
    envelope = row['attestation']['bundle']['dsseEnvelope']
    statement = document(base64.b64decode(envelope['payload'], validate=True))
    require(statement['predicate']['repository'] == 'jrsoftware/issrc'
            and statement['predicate']['tag'] == 'is-6_7_4')
    subjects = [s for s in statement['subject'] if s.get('name') == 'innosetup-6.7.4.exe']
    require(len(subjects) == 1 and subjects[0]['digest']['sha256'] == VENDOR)


def verify(raw: bytes) -> dict:
    """Replay exact hosted evidence without pretending the new binary was retained."""
    docs = unpack(raw)
    rows = {k: document(v) for k, v in docs.items()}
    check_build(docs['local-build-evidence'], rows['local-build-evidence'])
    check_lifecycle(rows)
    check_inputs(rows)
    check_attestation(rows['release-attestation'])
    require(docs['product-components-before'] == docs['product-components-after']
            and docs['staged-evidence'] == docs['product-installed-evidence'])
    return {'schema': 'consolidated-notice-setup-review-v1', 'source_sha': SOURCE,
            'app_sha256': FILES[APP], 'setup_sha256': SETUP_SHA,
            'uninstaller_sha256': UNINSTALLER_SHA, 'run_id': 45827978336,
            'artifact_id': 15121985132, 'archive_sha256': ARCHIVE_SHA,
            'documents': DOCS, 'hosted_clean_lifecycle': 'MATCH_REPORTED',
            'setup_bytes_retained': False, 'independent_setup_verification': 'NOT_RUN',
            'upgrade_reinstall': 'NOT_RUN', 'native_product_signing': 'NOT_VERIFIED',
            'interactive_acceptance': 'NOT_VERIFIED', 'distribution_compliance': 'NOT_VERIFIED',
            'release_admission': 'BLOCKED'}


def main(argv: list[str] | None = None) -> int:
    """Write a local evidence review without executing or publishing files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        write_json(args.output, verify(read(args.archive)))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile):
        print('FAIL: exact notice setup evidence', file=sys.stderr)
        return 2
    print('PASS: scoped hosted clean lifecycle evidence; release BLOCKED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
