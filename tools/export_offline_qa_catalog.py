#!/usr/bin/env python3
"""List offline QA cases and compare exact-checkout evidence coverage."""

import argparse
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as ET

from run_offline_qa import CLI, ROOT, check_directory, evidence_snapshot
from run_offline_qa import junit_counts_bytes, parse_evidence_json, read_verified_inventory
from run_offline_qa import source_context, write_json


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


def step_passed(step: dict) -> bool:
    """Require each reported process status to agree with its exit code."""
    status, code = step['status'], step['exit_code']
    if status == 'PASS' and type(code) is int and code == 0:
        return True
    if status == 'FAIL' and type(code) is int and code != 0:
        return False
    if status in ('ERROR', 'TIMEOUT') and code is None:
        return False
    raise ValueError('contradictory command status or exit code')


def verify_status(summary: dict, counts: dict, audit: dict) -> None:
    """Refuse a reported PASS contradicted by commands, JUnit or audit."""
    reported = summary['status']
    if reported not in ('PASS', 'FAIL'):
        raise ValueError('invalid reported status')
    tests = summary['tests']
    if (not isinstance(tests, dict) or tests != counts
            or any(type(value) is not int for value in tests.values())):
        raise ValueError('test counts differ')
    outcomes = [step_passed(step) for step in summary['steps']]
    if audit['status'] not in ('PASS', 'FAIL'):
        raise ValueError('invalid audit status')
    if audit['status'] == 'PASS' and any(audit[key] != [] for key in
                                         ('findings', 'new', 'resolved')):
        raise ValueError('contradictory zero-debt audit')
    if reported == 'PASS' and (not all(outcomes) or not counts['tests']
            or any(counts[key] for key in ('failures', 'errors', 'skipped'))
            or audit['status'] != 'PASS'):
        raise ValueError('contradictory reported PASS')


def verify_run(directory: Path, expected: dict) -> dict:
    """Bind coverage to the current clean source and verified local inventory."""
    initial = evidence_snapshot(directory)
    verified = read_verified_inventory(directory)
    source = parse_evidence_json(verified['source-toolchain.json'])
    summary = parse_evidence_json(verified['summary.json'])
    xml = verified['python-results.xml']
    current = source_context()
    if (current['dirty'] or source['dirty'] is not False
            or any(source[key] != current[key] or summary[key] != current[key]
                   for key in ('commit', 'tree'))):
        raise ValueError('source identity differs')
    coverage(expected, summary, xml)
    verify_status(summary, junit_counts_bytes(xml),
                  parse_evidence_json(verified['code-audit.json']))
    check_directory(directory)
    if evidence_snapshot(directory) != initial:
        raise ValueError('evidence changed during coverage review')
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
