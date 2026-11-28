"""Test fixed synthetic mode selection and fail-closed result interpretation."""

from pathlib import Path
import unittest
from unittest.mock import patch

from observe_native_package_selftests import CASES, check_result, observe


class NativeSelftestTests(unittest.TestCase):
    """Do not mistake a watchdog timeout or invalid input for acceptance."""

    def test_watchdog_expected_status(self) -> None:
        """A bounded 124 is valid only for its reviewed watchdog mode."""
        self.assertEqual(check_result('watchdog', 124, 124, 1.1)['result'], 'PASS')
        for actual, expected, elapsed in ((0, 124, 2), (124, 0, 2), (124, 124, 0.1)):
            with self.assertRaises(ValueError):
                check_result('fixture', actual, expected, elapsed)

    def test_only_fixed_modes(self) -> None:
        """No normal GUI or real HID diagnostic mode is in the reviewed set."""
        self.assertEqual([len(CASES[k]) for k in ('windows', 'universal', 'high-sierra')],
                         [5, 3, 4])
        for cases in CASES.values():
            for mode, expected, timeout in cases:
                self.assertTrue(mode == '--help' or mode.startswith('--self-test'))
                self.assertIn(expected, (0, 124))
                self.assertGreater(timeout, 0)

    def test_invalid_corpus_before_execution(self) -> None:
        """Reject changed synthetic fixtures before reading or launching a package."""
        with patch('observe_native_package_selftests.read_local', return_value=b'changed'), patch(
                'observe_native_package_selftests.inputs') as inputs, patch(
                'observe_native_package_selftests.run_case') as run:
            with self.assertRaises(ValueError):
                observe(Path('root'), 'windows', b'original', b'license', Path('corpus'))
            inputs.assert_not_called()
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
