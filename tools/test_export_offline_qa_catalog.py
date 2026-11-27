"""Verify the offline case catalog and evidence coverage without hardware."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from export_offline_qa_catalog import catalog, coverage, verify_run
from run_offline_qa import CLI, read_evidence, verify_inventory, write_json


class OfflineCatalogTests(unittest.TestCase):
    """Exercise current discovery and explicit coverage rejection."""

    def test_discovery(self) -> None:
        """Use the actual loader and command registry, not duplicated counts."""
        row = catalog()
        self.assertIn(self.id(), row['unittest_ids'])
        self.assertEqual(len(row['commands']), len(CLI) + 2)
        self.assertEqual(row['observations'], 'NOT_COLLECTED')
        self.assertEqual(row['hardware'], 'NOT_RUN')

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


    def test_verified_bytes_and_late_mutation(self) -> None:
        """Consume the verified bytes once and reject later evidence mutation."""
        expected = {'unittest_ids': ['a.A.test_x'], 'commands': [['python', 'one']]}
        current = {'commit': 'synthetic-commit', 'tree': 'synthetic-tree', 'dirty': False}
        summary = dict(current, status='PASS', steps=[{'command': ['python', 'one']}],
                       tests={'tests': 1, 'failures': 0, 'errors': 0, 'skipped': 0})
        xml = (b'<testsuite tests="1" failures="0" errors="0" skipped="0">'
               b'<testcase name="a.A.test_x"/></testsuite>')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / 'source-toolchain.json', current)
            write_json(root / 'summary.json', summary)
            write_json(root / 'code-audit.json', {'status': 'PASS'})
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
