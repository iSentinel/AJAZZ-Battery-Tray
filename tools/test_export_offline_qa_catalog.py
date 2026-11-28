"""Verify the offline case catalog and evidence coverage without hardware."""

import ast
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from export_offline_qa_catalog import catalog, coverage, verify_run, verify_status
from run_offline_qa import CLI, ROOT, read_evidence, verify_inventory, write_json


class OfflineCatalogTests(unittest.TestCase):
    """Exercise current discovery and explicit coverage rejection."""

    def test_discovery(self) -> None:
        """Use the actual loader and command registry, not duplicated counts."""
        row = catalog()
        self.assertIn(self.id(), row['unittest_ids'])
        self.assertEqual(len(row['commands']), 2 * len(CLI) + 2)
        for name in CLI:
            for flag in ('--help', '-h'):
                self.assertIn(['python', f'tools/{name}.py', flag], row['commands'])
        self.assertEqual(row['observations'], 'NOT_COLLECTED')
        self.assertEqual(row['hardware'], 'NOT_RUN')

    def test_cli_registry_matches_source_entrypoints(self) -> None:
        """Discover root Python entrypoints independently of the QA registry."""
        names = set()
        for path in sorted((ROOT / 'tools').glob('*.py')):
            if path.name.startswith('test_'):
                continue
            tree = ast.parse(path.read_text(encoding='utf-8'))
            if any(isinstance(node, ast.If) and '__main__' in ast.unparse(node.test)
                   for node in tree.body):
                names.add(path.stem)
        self.assertTrue(names)
        self.assertEqual(set(CLI), names)
        self.assertEqual(len(CLI), len(names))

    def test_coverage(self) -> None:
        """Reject missing, extra and duplicate identities and reordered steps."""
        expected = {'unittest_ids': ['a.A.test_x', 'b.B.test_y'],
                    'commands': [['python', 'one'], ['python', 'two']]}
        summary = {'steps': [{'command': cmd} for cmd in expected['commands']]}
        good = b'<testsuite><testcase name="a.A.test_x"/><testcase name="b.B.test_y"/></testsuite>'
        coverage(expected, summary, good)
        for raw in (good.replace(b'<testcase name="b.B.test_y"/>', b''),
                    good.replace(b'b.B.test_y', b'a.A.test_x'),
                    good.replace(b'b.B.test_y', b'c.C.test_z')):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                coverage(expected, summary, raw)
        with self.assertRaises(ValueError):
            coverage(expected, {'steps': list(reversed(summary['steps']))}, good)


    def test_reported_status_consistency(self) -> None:
        """Reject forged PASS semantics even when inventory hashes match."""
        counts = {'tests': 1, 'failures': 0, 'errors': 0, 'skipped': 0}
        audit = {'status': 'PASS', 'findings': [], 'new': [], 'resolved': []}
        good = {'status': 'PASS', 'tests': counts,
                'steps': [{'status': 'PASS', 'exit_code': 0}]}
        verify_status(good, counts, audit)
        for step in ({'status': 'PASS', 'exit_code': True},
                     {'status': 'PASS', 'exit_code': 1},
                     {'status': 'FAIL', 'exit_code': 0},
                     {'status': 'FAIL', 'exit_code': 1},
                     {'status': 'TIMEOUT', 'exit_code': None},
                     {'status': 'ERROR', 'exit_code': None}):
            with self.subTest(step=step), self.assertRaises(ValueError):
                verify_status(dict(good, steps=[step]), counts, audit)
        for key in ('failures', 'errors', 'skipped'):
            bad_counts = dict(counts, **{key: 1})
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_status(dict(good, tests=bad_counts), bad_counts, audit)
        with self.assertRaises(ValueError):
            verify_status(dict(good, tests=dict(counts, tests=True)), counts, audit)
        for bad_audit in (dict(audit, status='FAIL'), dict(audit, new=[['drift']]),
                          dict(audit, status='INVENTORY_ONLY')):
            with self.subTest(audit=bad_audit), self.assertRaises(ValueError):
                verify_status(good, counts, bad_audit)
        # A complete but honestly failed run can still match coverage.
        failed = dict(good, status='FAIL', steps=[{'status': 'FAIL', 'exit_code': 1}])
        verify_status(failed, counts, audit)
        with self.assertRaises(ValueError):
            verify_status(dict(good, status='UNKNOWN'), counts, audit)

    def test_ambiguous_json_with_matching_manifest(self) -> None:
        """Reject ambiguous source, summary and audit even with valid hashes."""
        current = {'commit': 'synthetic', 'tree': 'tree', 'dirty': False}
        expected = {'unittest_ids': ['a.A.test_x'], 'commands': [['python', 'one']]}
        summary = dict(current, status='PASS', steps=[
            {'command': ['python', 'one'], 'status': 'PASS', 'exit_code': 0}],
            tests={'tests': 1, 'failures': 0, 'errors': 0, 'skipped': 0})
        audit = {'status': 'PASS', 'findings': [], 'new': [], 'resolved': []}
        documents = {'source-toolchain.json': current, 'summary.json': summary,
                     'code-audit.json': audit}
        xml = (b'<testsuite tests="1" failures="0" errors="0" skipped="0">'
               b'<testcase name="a.A.test_x"/></testsuite>')
        for name, key in (('source-toolchain.json', 'dirty'),
                          ('summary.json', 'status'), ('code-audit.json', 'status')):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                for filename, data in documents.items():
                    raw = json.dumps(data).encode('utf-8')
                    if filename == name:
                        prefix = json.dumps({key: 'invalid'}).encode('utf-8')
                        raw = prefix[:-1] + b',' + raw[1:]
                    (root / filename).write_bytes(raw)
                (root / 'python-results.xml').write_bytes(xml)
                write_json(root / 'manifest.json', verify_inventory(root))
                with patch('export_offline_qa_catalog.source_context', return_value=current):
                    with self.assertRaisesRegex(ValueError, 'Duplicate evidence JSON key'):
                        verify_run(root, expected)

    def test_verified_bytes_and_late_mutation(self) -> None:
        """Consume the verified bytes once and reject later evidence mutation."""
        expected = {'unittest_ids': ['a.A.test_x'], 'commands': [['python', 'one']]}
        current = {'commit': 'synthetic-commit', 'tree': 'synthetic-tree', 'dirty': False}
        summary = dict(current, status='PASS', steps=[{'command': ['python', 'one'], 'status': 'PASS', 'exit_code': 0}],
                       tests={'tests': 1, 'failures': 0, 'errors': 0, 'skipped': 0})
        xml = (b'<testsuite tests="1" failures="0" errors="0" skipped="0">'
               b'<testcase name="a.A.test_x"/></testsuite>')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / 'source-toolchain.json', current)
            write_json(root / 'summary.json', summary)
            write_json(root / 'code-audit.json', {'status': 'PASS', 'findings': [],
                                                  'new': [], 'resolved': []})
            (root / 'python-results.xml').write_bytes(xml)
            write_json(root / 'manifest.json', verify_inventory(root))
            with patch('export_offline_qa_catalog.source_context', return_value=current):
                with patch('run_offline_qa.read_evidence', wraps=read_evidence) as read:
                    result = verify_run(root, expected)
                self.assertEqual(read.call_count, 5)
                self.assertEqual(result['coverage'], 'MATCH')
                self.assertEqual(result['reported_status'], 'PASS')

            def mutate() -> dict:
                """Change the summary after the manifest-verified bytes were read."""
                (root / 'summary.json').write_text('{}', encoding='utf-8')
                return current

            with patch('export_offline_qa_catalog.source_context', side_effect=mutate):
                with self.assertRaisesRegex(ValueError, 'changed during coverage'):
                    verify_run(root, expected)


if __name__ == '__main__':
    unittest.main()
