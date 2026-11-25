"""Guard the explicit local-only diagnostic session entry points."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'src/AjazzBatteryTray'


class DiagnosticSessionTests(unittest.TestCase):
    """No implicit device I/O or upload from session annotation."""

    def test_passive_menu_and_explicit_review(self) -> None:
        """A marker captures existing monitoring data, not a new HID request."""
        code = (ROOT / 'TrayAppContext.cs').read_text()
        menu = code.split('private ToolStripMenuItem BuildDiagnosticSessionMenu()', 1)[1]
        menu = menu.split('private void AddSessionSnapshot', 1)[0]
        self.assertIn('BuildExtendedReport("HID inventory not requested (session snapshot).")', menu)
        self.assertNotIn('FullHidCapture', menu)
        self.assertIn('DiagnosticMarker.ReviewedReport, report', code)
        self.assertIn('_diagnosticSession.Clear();', code)
        review = (ROOT / 'DiagnosticReportForm.cs').read_text()
        self.assertIn('addToSession();', review)

    def test_bounded_local_export(self) -> None:
        """Use a bounded ZIP with fixed names and explicit owner annotations."""
        code = (ROOT / 'DiagnosticSession.cs').read_text()
        self.assertIn('MaximumReports = 32', code)
        self.assertIn('MaximumTotalBytes = 8 * MaximumReportBytes', code)
        self.assertIn('OWNER_ANNOTATED', code)
        self.assertIn('NOT_VERIFIED', code)
        self.assertNotIn('HttpClient', code)
        tray = (ROOT / 'TrayAppContext.cs').read_text()
        self.assertIn('FileMode.CreateNew, FileAccess.Write, FileShare.None', tray)


if __name__ == '__main__':
    unittest.main()
