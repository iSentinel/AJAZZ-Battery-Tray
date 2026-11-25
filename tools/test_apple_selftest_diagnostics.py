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

    def test_corpus_failure_and_fractional_history(self) -> None:
        """Pin all original corpus predicates and deterministic boundary replay."""
        raw = (ROOT / 'macos/main.swift').read_text()
        corpus = raw.split('private func corpusFailure(', 1)[1].split(
            'if CommandLine.arguments.contains', 1)[0]
        for stage in ('fixture-read', 'fixture-count', 'fixture-layout',
                      'fixture-hex', 'decoder', 'history-read', 'history-row',
                      'history-observation', 'alerts'):
            self.assertIn(f'corpusFailure("{stage}"', corpus)
        self.assertIn('[0.001, 0.499, 0.9999].enumerated()', corpus)
        self.assertIn('sample.timestamp <= now', corpus)
        self.assertIn('sample.percent == percent', corpus)
        self.assertIn('writer.record(status, at: now)', corpus)
        writer = (ROOT / 'macos/BatteryHistory.swift').read_text()
        self.assertIn('floor(time.timeIntervalSince1970)', writer)
        self.assertIn('observation.timestamp <= now', writer)


if __name__ == '__main__':
    unittest.main()
