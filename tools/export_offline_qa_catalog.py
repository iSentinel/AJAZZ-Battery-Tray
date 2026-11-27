#!/usr/bin/env python3
"""List offline QA cases and compare exact-checkout evidence coverage."""

import argparse
import json
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as ET

from run_offline_qa import CLI, ROOT, junit_counts, read_evidence, source_context
from run_offline_qa import verify_manifest, write_json


def case_ids(suite: unittest.TestSuite) -> list[str]:
    """Flatten discovered test identities without running test bodies."""
    names = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            names.extend(case_ids(item))
        else:
            names.append(item.id())
    return names


def catalog() -> dict:
    """Use the runner's actual discovery pattern and CLI registry."""
    loader = unittest.TestLoader()
    names = case_ids(loader.discover(str(ROOT / 'tools'), pattern='test_*.py'))
    if (loader.errors or not names or len(set(names)) != len(names)
            or any(not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]{1,255}', name)
                   for name in names) or len(set(CLI)) != len(CLI)):
        raise ValueError('invalid offline discovery')
    commands = [['python', 'tools/code_audit.py', '--baseline',
                 'config/code-audit-baseline.json']]
    commands.extend(['python', f'tools/{name}.py', '--help'] for name in CLI)
    commands.append(['python', 'tools/qa_unittest.py', '--output', 'python-results.xml'])
    return {'schema': 'offline-qa-catalog-v1', 'scope': 'OFFLINE_PYTHON',
            'unittest_ids': sorted(names), 'commands': commands,
            'observations': 'NOT_COLLECTED', 'hardware': 'NOT_RUN'}


def coverage(expected: dict, summary: dict, xml: bytes) -> None:
    """Reject missing, extra or duplicate reported case and command identities."""
    root = ET.fromstring(xml)
    names = [case.get('name') for case in root.findall('testcase')]
    if (root.tag != 'testsuite' or len(set(names)) != len(names)
            or set(names) != set(expected['unittest_ids'])):
        raise ValueError('test coverage differs')
    commands = [step['command'] for step in summary['steps']]
    if commands != expected['commands']:
        raise ValueError('command coverage differs')


def verify_run(directory: Path, expected: dict) -> dict:
    """Bind coverage to the current clean source and verified local inventory."""
    verify_manifest(directory)
    source = json.loads(read_evidence(directory / 'source-toolchain.json'))
    summary = json.loads(read_evidence(directory / 'summary.json'))
    current = source_context()
    if (current['dirty'] or source['dirty'] is not False
            or any(source[key] != current[key] or summary[key] != current[key]
                   for key in ('commit', 'tree'))):
        raise ValueError('source identity differs')
    coverage(expected, summary, read_evidence(directory / 'python-results.xml'))
    if summary['tests'] != junit_counts(directory / 'python-results.xml'):
        raise ValueError('test counts differ')
    verify_manifest(directory)
    return {'schema': 'offline-qa-coverage-v1', 'commit': current['commit'],
            'tree': current['tree'], 'test_count': len(expected['unittest_ids']),
            'command_count': len(expected['commands']), 'coverage': 'MATCH',
            'reported_status': summary['status'], 'authentication': 'NOT_VERIFIED',
            'hardware': 'NOT_RUN', 'release_admission': 'NOT_VERIFIED'}


def main(argv: list[str] | None = None) -> int:
    """Export the catalog or check existing local evidence; never run test bodies."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verify-run', type=Path, help='Existing exact-checkout QA run')
    args = parser.parse_args(argv)
    try:
        expected = catalog()
        result = verify_run(args.verify_run, expected) if args.verify_run else expected
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, ET.ParseError):
        print('FAIL: offline QA catalog or coverage', file=sys.stderr)
        return 2
    print('PASS: offline QA catalog or coverage; no acceptance inferred')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
