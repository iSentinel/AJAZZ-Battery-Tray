"""Synthetic regressions for redacted CLI diagnostic summaries."""

import json
import os
from pathlib import Path
import tempfile
import unittest

from analyze_windows_cli_diagnostics import LIMIT, analyze, read_local
from test_compare_get_ids import fixture


def ordinary(gate: str = 'ReadUnavailable') -> str:
    """Build a synthetic ordinary CLI capture with a policy label."""
    return '\n'.join((
        'BEGIN: UTC=2026-01-01T00:00:00Z timeout=40s',
        'STEP: found 1 matching MI_02 paths',
        'STEP: HID open succeeded',
        'STEP: SET F7 OK Win32=0 elapsed=0ms',
        'STEP: GET 05 OK Win32=0 elapsed=1ms',
        '[Receiver #1]', 'Interface: synthetic',
        'SET F7 / GET 05 (65 bytes): OK; header=omitted',
        'F7 policy gate: ' + gate,
        'INCONCLUSIVE: no verified battery report', 'END: worker exited 2',
    ))


class WindowsCliAnalysisTests(unittest.TestCase):
    """Check local analysis without hardware or private report data."""

    def test_ordinary(self) -> None:
        """Separate transport success from a missing accepted level."""
        row = analyze(ordinary())
        self.assertEqual(row['outcome'], 'UNVERIFIED')
        self.assertIsNone(row['reported_percent'])
        self.assertEqual(row['transport']['get_ok'], 1)
        self.assertEqual(row['policy_sequences']['reported_gate_counts'],
                         {'ReadUnavailable': 1})
        self.assertNotIn('omitted', json.dumps(row))

    def test_experiment(self) -> None:
        """Count equal and unequal pairs without promoting either to charge."""
        for changed in (False, True):
            row = analyze(fixture(changed=changed))
            self.assertEqual(row['outcome'], 'complete')
            self.assertEqual(row['pair_counts'], {
                'DIFFERENT STATUS BYTES' if changed else 'SAME STATUS BYTES': 6})
            self.assertIsNone(row['reported_percent'])
            self.assertNotIn('status10', json.dumps(row))

    def test_incomplete(self) -> None:
        """Preserve partial pair coverage and hide timed-out gate evidence."""
        row = analyze(fixture(missing=True))
        self.assertEqual(row['outcome'], 'inconclusive')
        self.assertEqual(row['pair_counts']['INCOMPLETE'], 1)
        text = ordinary().replace('END: worker exited 2',
                                  'TIMEOUT: HID worker exceeded 40s')
        row = analyze(text)
        self.assertEqual(row['outcome'], 'TIMEOUT')
        self.assertEqual(row['policy_sequences']['reported_gate_counts'], {})

    def test_conflicting_markers(self) -> None:
        """Reject duplicate terminal markers and excess classifications."""
        text = ordinary()
        for bad in (text.replace('END: worker exited 2',
                                 'END: worker exited 2\nEND: worker exited 2'),
                    text.replace('STEP: GET 05 OK Win32=0 elapsed=1ms\n', '')):
            with self.assertRaises(ValueError):
                analyze(bad)

    def test_completed_outcomes(self) -> None:
        """Reject contradictory successful, inconclusive and transport evidence."""
        base = ordinary()
        success = base.replace('INCONCLUSIVE: no verified battery report',
                               'PASS: verified battery 42%').replace(
                                   'END: worker exited 2', 'END: worker exited 0')
        for bad in (ordinary('Accepted'), success,
                    base.replace('INCONCLUSIVE:', 'FAIL:'),
                    base.replace('STEP: SET F7 OK Win32=0 elapsed=0ms\n', ''),
                    base.replace('STEP: found 1 matching MI_02 paths',
                                 'STEP: found 1 matching MI_02 paths\n'
                                 'STEP: found 0 matching MI_02 paths')):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                analyze(bad)
        for gate in ('Accepted', 'Unrecognized'):
            row = analyze(success.replace('ReadUnavailable', gate))
            self.assertEqual(row['reported_percent'], 42)
        legacy = success.replace('F7 policy gate: ReadUnavailable\n', '')
        self.assertEqual(analyze(legacy)['reported_percent'], 42)

    def test_experimental_terminal(self) -> None:
        """A mixed timeout and worker exit cannot describe one experiment."""
        text = fixture()
        for bad in (text + '\nTIMEOUT: worker exceeded deadline',
                    text.replace('END: worker exited 2',
                                 'END: worker exited 2\nEND: worker exited 2')):
            with self.assertRaises(ValueError):
                analyze(bad)

    def test_shared_utc_framing_for_both_modes(self) -> None:
        """Use the same native start validation in ordinary and experimental logs."""
        for text in (ordinary(), fixture()):
            header = text.splitlines()[0]
            valid = 'BEGIN: UTC=2026-01-01T00:00:00.1234567+00:00 timeout=90s'
            self.assertEqual(analyze(text.replace(header, valid))['capture_utc'],
                             '2026-01-01T00:00:00.123456+00:00')
            for bad in (valid.replace('+00:00', '+02:00'),
                        valid.replace('90s', '91s'), valid.replace('90s', '９０s'),
                        valid.replace('01-01', '02-30')):
                with self.subTest(header=bad), self.assertRaises(ValueError):
                    analyze(text.replace(header, bad))

    def test_shared_bounded_reader(self) -> None:
        """Preserve BOM, cap, and rejection of linked/nonregular input."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'capture.txt'
            raw = ordinary().encode('utf-8-sig')
            path.write_bytes(raw + b'\n' * (LIMIT - len(raw)))
            self.assertEqual(analyze(read_local(path))['outcome'], 'UNVERIFIED')
            with self.assertRaises(ValueError):
                read_local(root)
            alias = root / 'alias.txt'
            os.link(path, alias)
            for linked in (path, alias):
                with self.assertRaises(ValueError):
                    read_local(linked)
            alias.unlink()
            path.write_bytes(raw + b'\n' * (LIMIT + 1 - len(raw)))
            with self.assertRaises(ValueError):
                read_local(path)
            try:
                alias.symlink_to(path)
            except OSError:
                return
            with self.assertRaises(ValueError):
                read_local(alias)

    def test_invalid(self) -> None:
        """Reject displaced markers, missing timezone and invented labels."""
        for text in ('prefix\n' + ordinary(), ordinary().replace('00Z', '00'),
                     ordinary('invented'), ordinary() + '\ntrailing'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                analyze(text)


if __name__ == '__main__':
    unittest.main()
