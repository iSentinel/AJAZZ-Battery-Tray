"""Keep candidate hardware acceptance tied to current policy and CI scope."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CandidateAcceptanceTests(unittest.TestCase):
    """Prevent old fallback policy from returning as current acceptance."""

    def test_current_acceptance_replaces_old_fallback(self) -> None:
        """Require explicit consent, cached state, restart and owner annotations."""
        doc = (ROOT / 'docs/CANDIDATE_ACCEPTANCE.md').read_text()
        for item in ('remember on this PC', '120 seconds', '30 minutes',
                     'Link to USB receiver', 'NOT RUN', 'no automatic persistent BLE on Apple',
                     'macOS 13 or later', '10.13.6', 'ReviewedReport'):
            self.assertIn(item, doc)
        old = (ROOT / 'docs/HARDWARE_ACCEPTANCE.md').read_text()
        self.assertNotIn('absent (this session)', old)
        self.assertIn('CANDIDATE_ACCEPTANCE.md', old)

    def test_all_scenario_ids_unique(self) -> None:
        """Each reported physical scenario has one unambiguous identifier."""
        doc = (ROOT / 'docs/CANDIDATE_ACCEPTANCE.md').read_text()
        rows = [line.split('|')[1].strip() for line in doc.splitlines()
                if line.startswith(('| W', '| M'))]
        self.assertEqual(rows, [f'W{i:02d}' for i in range(1, 19)] +
                         [f'M{i:02d}' for i in range(1, 12)])


if __name__ == '__main__':
    unittest.main()
