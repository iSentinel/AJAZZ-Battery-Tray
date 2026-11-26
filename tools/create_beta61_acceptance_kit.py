#!/usr/bin/env python3
"""Create six blank normalized beta.61 acceptance forms from exact artifacts."""

import argparse
from pathlib import Path
import struct
import sys
import zipfile
import zlib

from review_beta61_admission import normalized_identity, normalized_plan
from run_offline_qa import write_json
from validate_scoped_sbom_schema import read
from verify_hardware_acceptance import candidate, template
from verify_hardware_acceptance_set import ARCHIVE_PROFILES
from verify_interactive_acceptance import template_identity
from verify_windowsdesktop_provenance import read_local


def forms(raw: bytes, archives: dict[str, Path]) -> dict:
    """Verify all four original artifacts before creating any blank form."""
    if set(archives) != set(ARCHIVE_PROFILES):
        raise ValueError('incomplete application archive set')
    interactive = normalized_identity(raw)
    plan = normalized_plan()
    result = {'interactive-checklist.json': template_identity(interactive)}
    for edition, profiles in ARCHIVE_PROFILES.items():
        asset = plan['assets'][edition]
        identity = candidate(read_local(archives[edition]), asset['archive_sha256'],
                             plan['source_sha'], profiles[0])
        key = 'app_sha256' if edition == 'windows' else 'inner_archive_sha256'
        if identity[key] != asset['release_asset_sha256']:
            raise ValueError('application identity differs')
        for profile in profiles:
            result[profile + '.checklist.json'] = template(dict(identity, profile=profile))
    return result


def stage(records: dict, output: Path) -> None:
    """Write only into a fresh directory, never overwrite an existing kit."""
    output.mkdir(mode=0o700, exist_ok=False)
    for name, record in sorted(records.items()):
        write_json(output / name, record)


def main(argv: list[str] | None = None) -> int:
    """Generate blank forms offline; no binary extraction, execution or approval."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--normalized-evidence', required=True, type=Path)
    for edition in ARCHIVE_PROFILES:
        parser.add_argument('--' + edition + '-archive', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.output_dir.exists() or args.output_dir.is_symlink():
            raise ValueError('output directory already exists')
        archives = {edition: getattr(args, edition.replace('-', '_') + '_archive')
                    for edition in ARCHIVE_PROFILES}
        stage(forms(read(args.normalized_evidence), archives), args.output_dir)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            NotImplementedError, zipfile.BadZipFile, struct.error, zlib.error):
        print('FAIL: exact blank acceptance kit', file=sys.stderr)
        return 2
    print('PASS: six blank forms, 57 hardware and six interactive cases NOT_RUN')
    print('Release admission: BLOCKED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
