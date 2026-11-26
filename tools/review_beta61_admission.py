#!/usr/bin/env python3
"""Bind beta.61 acceptance observations to the exact reviewed release assets."""

import argparse
from io import BytesIO
import json
from pathlib import Path
import struct
import sys
import zipfile
import zlib

from build_consolidated_apple_notices import PINS as APPLE_PINS
from run_offline_qa import write_json
from stage_consolidated_signature_inputs import ARCHIVES as ORIGINAL_ARCHIVES, FILES, SOURCE
from stage_beta61_release import ASSETS, collect
from validate_scoped_sbom_schema import digest, document, read
from verify_consolidated_notice_setup import APP, paths as notice_evidence_paths
from verify_hardware_acceptance_set import ARCHIVE_PROFILES, review_set
from verify_interactive_acceptance import (
    CASES, archive_identity, candidate as interactive_candidate, template_identity, verify_identity,
)
from verify_windowsdesktop_provenance import read_local


SOURCE_TREE = 'cd90b485b8e45d4702ec31cd4a09154a4e417226'
NORMALIZED_SETUP_SHA = 'e7195b3817e919eeff47606c036089a2e9fabc44b2238eae466918b992da90a8'
NORMALIZED_EVIDENCE_SHA = 'b4e314e5d3c1479be1fae8fcf9ef797dd3f3c93cb5fb4ff4142d00425f0f3b98'
ARTIFACTS = {'windows': 15110510075, 'universal': 15108849028, 'high-sierra': 15109082825}


def normalized_plan() -> dict:
    """Describe the original apps and the normalized Setup qualification."""
    pins = {'windows': (ORIGINAL_ARCHIVES['windows'], FILES[APP]), **APPLE_PINS}
    assets = {edition: {'artifact': ARTIFACTS[edition], 'archive_sha256': outer,
                        'release_asset_sha256': inner}
              for edition, (outer, inner) in pins.items()}
    assets['installer'] = {'evidence_artifact': 15139373707,
                           'evidence_archive_sha256': NORMALIZED_EVIDENCE_SHA,
                           'release_asset_sha256': NORMALIZED_SETUP_SHA}
    return {'source_sha': SOURCE, 'source_tree': SOURCE_TREE, 'assets': assets,
            'scope': 'NORMALIZED_SETUP_AND_ORIGINAL_APPLICATIONS'}


def normalized_identity(raw: bytes) -> dict:
    """Bind the exact hosted payload replay and interactive template."""
    if digest(raw) != NORMALIZED_EVIDENCE_SHA:
        raise ValueError('normalized evidence archive differs')
    names = {'ajazz-notice-probe/' + name + '.json' for name in (
        'setup-repeat-observation', 'product-upgrade-lifecycle', 'product-upgrade-notices',
        'product-reinstall-notices', 'candidate-payload-replay', 'interactive-checklist',
    )} | set(notice_evidence_paths())
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        infos = archive.infolist()
        if (len(infos) != len(names) or set(archive.namelist()) != names
                or sum(info.file_size for info in infos) > 65536):
            raise ValueError('unexpected normalized evidence inventory')
        root = 'ajazz-notice-probe/'
        identity = interactive_candidate(archive.read(root + 'local-build-evidence.json'))
        payload = document(archive.read(root + 'candidate-payload-replay.json'))
        form = document(archive.read(root + 'interactive-checklist.json'))
    if (identity['setup_sha256'] != NORMALIZED_SETUP_SHA or identity['app_sha256'] != FILES[APP]
            or payload['setup_sha256'] != identity['setup_sha256']
            or payload['app_sha256'] != identity['app_sha256']
            or payload['source_sha'] != SOURCE or payload['private_build_match'] is not True
            or payload['release_admission'] != 'NOT_VERIFIED'
            or form != template_identity(identity)):
        raise ValueError('normalized Setup qualification differs')
    return identity


def normalized_form(identity: dict, raw: bytes, setup: Path | None) -> dict:
    """Review a blank form, or require the matching Setup for actual results."""
    binding = 'NOT_PROVIDED'
    if setup is not None:
        if digest(read_local(setup)) != identity['setup_sha256']:
            raise ValueError('local Setup differs from normalized evidence')
        binding = 'MATCH'
    result = verify_identity(identity, raw, binding)
    if setup is None and result['counts']['NOT_RUN'] != len(CASES):
        raise ValueError('observed interactive cases require the exact local Setup')
    return result


def review_normalized(raw: bytes, archives: dict[str, Path], checklists: Path,
                      setup: Path | None = None) -> dict:
    """Review exact applications and normalized Setup evidence without publication."""
    identity = normalized_identity(raw)
    plan = normalized_plan()
    hardware = review_set(SOURCE, {edition: (archives[edition], plan['assets'][edition]['archive_sha256'])
                                   for edition in ARCHIVE_PROFILES}, checklists)
    if hardware['profiles']['windows-aj179']['candidate']['app_sha256'] != identity['app_sha256']:
        raise ValueError('original portable app differs from normalized evidence')
    for edition in APPLE_PINS:
        app = hardware['profiles'][edition]['candidate']
        if app['inner_archive_sha256'] != plan['assets'][edition]['release_asset_sha256']:
            raise ValueError('original Apple app archive differs')
    interactive = normalized_form(identity, read(checklists / 'interactive-checklist.json'), setup)
    result = report(plan, hardware, interactive)
    result['pending_review']['release_asset_selection'] = 'NOT_VERIFIED'
    return result


def release_subject(plan: dict) -> dict:
    """Describe the immutable asset set separately from editable observations."""
    subject = {
        'beta_tag': 'v0.3.0-beta.61',
        'source_sha': plan['source_sha'],
        'source_tree': plan['source_tree'],
        'assets': {profile: {**row, 'filename': ASSETS[profile][2],
                             'channel': 'high-sierra' if profile == 'high-sierra' else 'beta'}
                   for profile, row in plan['assets'].items()},
    }
    if 'scope' in plan:
        subject['scope'] = plan['scope']
    return subject


def report(plan: dict, hardware: dict, interactive: dict) -> dict:
    """Report coverage and pending release decisions without copying notes."""
    subject = release_subject(plan)
    identity = digest(json.dumps(subject, sort_keys=True, separators=(',', ':')).encode('utf-8'))
    complete = all(x['coverage'] == 'COMPLETE_REPORTED' for x in (hardware, interactive))
    profiles = hardware['profiles']
    return {
        'schema': 'beta61-admission-review-v1',
        'subject': subject,
        'subject_sha256': identity,
        'source_provenance': 'CALLER_REVIEW_REQUIRED',
        'hardware_counts': hardware['counts'],
        'hardware_checklists_sha256': {name: row['checklist_sha256']
                                       for name, row in profiles.items()},
        'interactive_counts': interactive['counts'],
        'interactive_checklist_sha256': interactive['checklist_sha256'],
        'interactive_binary_binding': interactive['local_binary_binding'],
        'reported_coverage': 'COMPLETE_REPORTED' if complete else 'INCOMPLETE',
        'human_observations': 'SELF_REPORTED_NOT_AUTHENTICATED',
        'pending_review': {
            'physical_acceptance': hardware['coverage'],
            'interactive_acceptance': interactive['coverage'],
            'distribution': 'NOT_VERIFIED',
            'signing_disposition': 'NOT_VERIFIED',
            'publication_approval': 'NOT_VERIFIED',
        },
        'release_admission': 'BLOCKED',
    }


def review(raw: bytes, archives: dict[str, Path], checklists: Path) -> dict:
    """Revalidate the pinned assets and original checklists on every review."""
    plan, payload = collect(raw, archives)
    source = plan['source_sha']
    pins = plan['assets']
    hardware = review_set(
        source, {p: (archives[p], pins[p]['archive_sha256']) for p in ARCHIVE_PROFILES},
        checklists)
    identity = archive_identity(archives['installer'], pins['installer']['archive_sha256'], source)
    if (digest(payload['installer']) != identity['setup_sha256']
            or digest(payload['windows']) != identity['app_sha256']):
        raise ValueError('interactive binaries differ from verified release assets')
    interactive = verify_identity(identity, read(checklists / 'interactive-checklist.json'), 'MATCH')
    return report(plan, hardware, interactive)


def review_request(args: argparse.Namespace, archives: dict[str, Path]) -> dict:
    """Dispatch to the selected reviewed candidate without mixing scopes."""
    if args.manifest is not None:
        if args.installer_archive is None or args.setup is not None:
            raise ValueError('original manifest mode requires only the Setup archive')
        return review(read(args.manifest), {**archives, 'installer': args.installer_archive},
                      args.checklist_dir)
    if args.installer_archive is not None:
        raise ValueError('normalized mode takes the actual Setup executable')
    return review_normalized(read(args.normalized_evidence), archives, args.checklist_dir, args.setup)


def main(argv: list[str] | None = None) -> int:
    """Exit 0 for complete reported coverage, 1 for incomplete, or 2 for invalid input."""
    parser = argparse.ArgumentParser(description=__doc__)
    origin = parser.add_mutually_exclusive_group(required=True)
    origin.add_argument('--manifest', type=Path, help='Original four-archive candidate')
    origin.add_argument('--normalized-evidence', type=Path, help='Exact native Windows evidence ZIP')
    for profile in ARCHIVE_PROFILES:
        parser.add_argument(f'--{profile}-archive', type=Path, required=True)
    parser.add_argument('--installer-archive', type=Path, help='Original CI Setup ZIP for --manifest')
    parser.add_argument('--setup', type=Path, help='Exact local Setup EXE for --normalized-evidence')
    parser.add_argument('--checklist-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    archives = {p: getattr(args, p.replace('-', '_') + '_archive') for p in ARCHIVE_PROFILES}
    try:
        result = review_request(args, archives)
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            NotImplementedError, zipfile.BadZipFile, struct.error, zlib.error):
        print('FAIL: invalid candidate archive or acceptance evidence', file=sys.stderr)
        return 2
    for name in ('hardware', 'interactive'):
        counts = result[name + '_counts']
        print(f'{name}: ' + ', '.join(f'{status}={value}' for status, value in counts.items()))
    complete = result['reported_coverage'] == 'COMPLETE_REPORTED'
    print(f'{"PASS" if complete else "FAIL"}: reported acceptance coverage')
    print(f'Subject SHA-256: {result["subject_sha256"]}')
    print('Release admission: BLOCKED')
    return 0 if complete else 1


if __name__ == '__main__':
    raise SystemExit(main())
