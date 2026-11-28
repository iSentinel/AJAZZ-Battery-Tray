"""Native catalog regression tests; no executable launch or device access."""

import unittest
from unittest.mock import patch

from export_native_package_catalog import catalog
from observe_native_package_selftests import CASES


class NativeCatalogTests(unittest.TestCase):
    """Check exact scoped definitions, not hardware or GUI outcomes."""

    def test_registry(self) -> None:
        """Keep the actual three-edition case registry and watchdog exit."""
        row = catalog()
        self.assertEqual(row['case_count'], 12)
        expected = {edition + ':' + mode for edition, cases in CASES.items()
                    for mode, _, _ in cases}
        self.assertEqual(set(row['cases']), expected)
        self.assertEqual(row['cases']['windows:--self-test-full-hid-watchdog']
                         ['expected_exit_code'], 124)
        self.assertEqual(row['observations'], 'NOT_COLLECTED')
        self.assertEqual(row['gui_launch'], 'NOT_RUN')
        self.assertEqual(row['release_admission'], 'BLOCKED')

    def test_invalid_registry(self) -> None:
        """Reject duplicate cases, boolean exits and nonpositive timeouts."""
        for cases in ((('--help', 0, 15), ('--help', 0, 15)),
                      (('--help', False, 15),), (('--help', 0, 0),)):
            with self.subTest(cases=cases), patch(
                    'export_native_package_catalog.CASES', {'windows': cases}):
                with self.assertRaises(ValueError):
                    catalog()


if __name__ == '__main__':
    unittest.main()
