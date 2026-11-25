"""Source contract for fixed synthetic Apple self-test diagnostics."""

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AppleSelftestDiagnosticsTests(unittest.TestCase):
    """Keep all original validation groups and aggregate failure semantics."""

    def test_all_groups_required(self) -> None:
        """Require each original group exactly once without short-circuit omission."""
        raw = (ROOT / 'macos/main.swift').read_text()
        block = raw.split('let checks: [(String, Bool)] = [', 1)[1].split('for (name, passed)', 1)[0]
        groups = re.findall(r'\("[a-z-]+", (\w+)\)', block)
        self.assertCountEqual(groups, ['corpusValid', 'provenanceValid', 'sharedFrameValid',
                                      'presenceValid', 'localizationValid', 'bluetoothValid',
                                      'alertTests', 'timeoutValid', 'selectedTests', 'jumpTests',
                                      'chartValid', 'historyValid', 'clockValid', 'guardValid',
                                      'legacyParserValid'])
        self.assertIn('let valid = checks.allSatisfy { $0.1 }', raw)
        self.assertIn('if !valid { exit(1) }', raw)


if __name__ == '__main__':
    unittest.main()
