"""Verify the offline case catalog and evidence coverage without hardware."""

import unittest

from export_offline_qa_catalog import catalog, coverage
from run_offline_qa import CLI


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


if __name__ == '__main__':
    unittest.main()
