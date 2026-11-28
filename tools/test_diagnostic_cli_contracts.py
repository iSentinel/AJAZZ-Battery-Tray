"""Exercise real diagnostic CLI process exits on synthetic local evidence."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_analyze_aula_sleep import SLEEP, WAKE, summary
from test_analyze_windows_cli_diagnostics import ordinary
from test_compare_get_ids import fixture
from test_compare_ready_clear import report as ready_report
from test_compare_windows_hid_logs import report as hid_report

TOOLS = Path(__file__).resolve().parent


class DiagnosticCliContracts(unittest.TestCase):
    """Use closed stdin and bounded subprocesses, with no device access."""

    def invoke(self, name: str, *args: str) -> subprocess.CompletedProcess:
        """Run only the specified local diagnostic executable entrypoint."""
        return subprocess.run(
            [sys.executable, str(TOOLS / (name + '.py')), *args],
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            encoding='utf-8', timeout=10, check=False)

    def write(self, root: Path, name: str, data: str) -> str:
        """Create a synthetic input and return its command-line path."""
        path = root / name
        path.write_text(data, encoding='utf-8')
        return str(path)

    def expect(self, name: str, code: int, marker: str, *args: str) -> None:
        """Assert process exit and visible outcome without leaking input paths."""
        result = self.invoke(name, *args)
        self.assertEqual(result.returncode, code, name)
        output = result.stdout + result.stderr
        self.assertIn(marker, output)
        self.assertNotIn('Traceback (most recent call last)', output)
        self.assertNotIn('PRIVATE_CANARY', output)

    def test_windows_hid_exit_contract(self) -> None:
        """Separate verified, inconclusive, worker error and invalid input."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            valid = self.write(root, 'awake.txt', hid_report('PASS: verified battery 83%', end=0))
            sleep = self.write(root, 'sleep.txt', hid_report('INCONCLUSIVE: no reply'))
            error = self.write(root, 'error.txt', hid_report('FAIL: worker IOException', end=1))
            for code, marker, path in ((0, 'SUMMARY: PASS', valid),
                                       (2, 'SUMMARY: INCONCLUSIVE', sleep),
                                       (1, 'SUMMARY: FAIL', error),
                                       (1, 'FAIL: invalid Windows HID diagnostic',
                                        str(root / 'PRIVATE_CANARY'))):
                self.expect('compare_windows_hid_logs', code, marker,
                            '--awake', valid, '--after-sleep', path)

    def test_experimental_and_json_exit_contracts(self) -> None:
        """Matrix completeness differs from successful JSON summarization."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            full = self.write(root, 'full.txt', fixture())
            partial = self.write(root, 'partial.txt', fixture(missing=True))
            missing = str(root / 'PRIVATE_CANARY')
            for code, marker, path in ((0, 'Observed pairs: 6/6', full),
                                       (2, 'Observed pairs: 5/6', partial),
                                       (1, 'FAIL: invalid GET-ID diagnostic', missing)):
                self.expect('compare_get_ids', code, marker, '--log', path)
            result = self.invoke('analyze_windows_cli_diagnostics', partial)
            self.assertEqual(result.returncode, 0)
            value = json.loads(result.stdout)
            self.assertEqual(value['outcome'], 'inconclusive')
            self.assertIsNone(value['reported_percent'])
            regular = self.write(root, 'ordinary.txt', ordinary())
            self.expect('analyze_windows_cli_diagnostics', 0, 'UNVERIFIED', regular)
            self.expect('analyze_windows_cli_diagnostics', 2, 'ERROR:', missing)

    def test_aula_exit_contract(self) -> None:
        """Keep complete, partial, failed and invalid observations distinct."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            awake = self.write(root, 'awake.txt', summary())
            sleep = self.write(root, 'sleep.txt', summary(now=SLEEP, percent=None,
                               failures=3, cached=True))
            wake = self.write(root, 'wake.txt', summary(now=WAKE, percent=80,
                              good=80, last_good=WAKE))
            bad = self.write(root, 'bad.txt', summary(now=SLEEP, percent=None,
                             failures=3, cached=False))
            args = ('--asleep', sleep, '--recovered', wake)
            self.expect('analyze_aula_sleep', 0, 'SUMMARY: PASS', '--awake', awake, *args)
            self.expect('analyze_aula_sleep', 2, 'SUMMARY: NOT OBSERVED', *args)
            self.expect('analyze_aula_sleep', 1, 'SUMMARY: FAIL', '--awake', awake,
                        '--asleep', bad, '--recovered', wake)
            self.expect('analyze_aula_sleep', 1, 'FAIL: cannot evaluate AULA summaries',
                        '--asleep', str(root / 'PRIVATE_CANARY'), '--recovered', wake)

    def test_ready_clear_and_apex_exit_contracts(self) -> None:
        """Compare hypotheses without treating a completed report as telemetry."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = self.write(root, 'PRIVATE_CANARY-valid.txt', ready_report())
            second = self.write(root, 'second.txt', ready_report(98, '21:35:12'))
            partial = self.write(root, 'partial.txt', ready_report(time='21:35:12', omit=(30, 65)))
            missing = str(root / 'PRIVATE_CANARY')
            for code, marker, path in ((0, 'SUMMARY: CHANGED FIELD', second),
                                       (2, 'SUMMARY: INCONCLUSIVE', partial),
                                       (1, 'FAIL: invalid ready-clear diagnostic', missing)):
                self.expect('compare_ready_clear', code, marker, '--earlier', first, '--later', path)
            self.expect('compare_apex_reports', 0, 'not validated live battery readings', first)
            self.expect('compare_apex_reports', 1, 'Report #2: ERROR:', first, missing)

    def test_argument_error_contract(self) -> None:
        """Argparse usage errors are separate from operational exit codes."""
        for name in ('compare_windows_hid_logs', 'compare_get_ids',
                     'analyze_windows_cli_diagnostics', 'analyze_aula_sleep',
                     'compare_ready_clear', 'compare_apex_reports'):
            with self.subTest(name=name):
                self.expect(name, 2, 'usage:')
