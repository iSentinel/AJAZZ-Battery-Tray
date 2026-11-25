"""Source and portable native contracts for the macOS diagnostics menu."""

from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AppleMenuDiagnosticsTests(unittest.TestCase):
    """Check policy boundaries independently of physical AppKit acceptance."""

    def test_passive_snapshots_no_hid(self) -> None:
        """Require passive report builders to use in-memory state."""
        modern = (ROOT / 'macos/main.swift').read_text()
        legacy = (ROOT / 'macos/high-sierra/main.m').read_text()
        snapshot = modern.split('private func diagnosticSnapshot()', 1)[1].split(
            'private func copyReport', 1)[0]
        legacy_snapshot = legacy.split('- (NSString *)diagnostics {', 1)[1].split(
            '- (void)copyReport:', 1)[0]
        for text in (snapshot, legacy_snapshot):
            self.assertNotIn('IOHID', text)
            self.assertNotIn('ReadReceiver', text)
            self.assertNotIn('ApexBattery.read', text)
            self.assertIn('Last verified USB UTC', text)

    def test_explicit_worker_and_single_flight(self) -> None:
        """Keep active capture behind consent and existing polling exclusion."""
        modern = (ROOT / 'macos/main.swift').read_text()
        legacy = (ROOT / 'macos/high-sierra/main.m').read_text()
        self.assertIn('#selector(runHIDDiagnostics)', modern)
        self.assertIn('@selector(runHIDDiagnostics:)', legacy)
        self.assertIn('guard !polling, !diagnosticRunning, !closing', modern)
        self.assertIn('self.polling || self.diagnosticRunning || self.closing', legacy)
        self.assertIn('consent.runModal() == .alertFirstButtonReturn', modern)
        self.assertIn('[consent runModal] != NSAlertFirstButtonReturn', legacy)
        self.assertIn('mode: ApexBoundedWorker.traceMode', modern)
        self.assertIn('CaptureMenuTrace(NO)', legacy)

    def test_trace_worker_no_clock_mode(self) -> None:
        """Keep explicit trace on the existing telemetry path, not RTC."""
        worker = (ROOT / 'macos/ApexBoundedWorker.swift').read_text()
        trace = worker.split('private static func runTrace(', 1)[1].split(
            'static func traceResult(', 1)[0]
        self.assertIn('ApexBattery.read', trace)
        self.assertNotIn('syncClock', trace)
        self.assertIn('count < 16', trace)

    def test_partial_trace_contract(self) -> None:
        """Keep a bounded partial trace without a final battery claim."""
        worker = (ROOT / 'macos/ApexBoundedWorker.swift').read_text()
        parser = worker.split('static func traceResult(', 1)[1].split(
            'static func runChild(', 1)[0]
        self.assertIn('data.count <= 4096', parser)
        self.assertIn('records.dropLast()', parser)
        self.assertIn('!$0.hasPrefix("Verified battery:")', parser)
        self.assertIn('!$0.hasPrefix("Battery status:")', parser)
        self.assertIn('lines.last == "END: trace complete"', parser)
        self.assertIn('read(mode: traceHangMode, timeout: 3)', worker)
        self.assertIn('read(mode: traceFailMode)', worker)
        modern = (ROOT / 'macos/main.swift').read_text()
        self.assertIn('no fresh battery claimed', modern)

    def test_interactive_cancel_preserves_worker_ownership(self) -> None:
        """Cancellation sets a token, never clears the polling exclusion."""
        code = (ROOT / 'macos/main.swift').read_text()
        cancel = code.split('private func cancelHIDDiagnostics()', 1)[1].split(
            'private func appearanceMenu', 1)[0]
        self.assertIn('#selector(cancelHIDDiagnostics)', code)
        self.assertIn('token.cancel()', cancel)
        self.assertNotIn('diagnosticRunning = false', cancel)
        self.assertIn('cancelDiagnosticItem?.isEnabled', code)
        self.assertIn('cancellationRequested', code)
        worker = (ROOT / 'macos/ApexBoundedWorker.swift').read_text()
        self.assertIn('read(mode: traceHangMode, timeout: 4, cancellation: traceCancellation)', worker)
        self.assertIn('stopAndWait(child)', worker)

    def test_export_native_contract(self) -> None:
        """Compile exact shared export helper and check mode/no-clobber/symlink."""
        if os.name == "nt":
            header = (ROOT / "macos/AjazzDiagnosticExport.h").read_text()
            self.assertIn("O_EXCL | O_NOFOLLOW, 0600", header)
            return
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'export.c'
            binary = root / 'export'
            source.write_text(
                '#include "AjazzDiagnosticExport.h"\n'
                'int main(void) { return AjazzDiagnosticExportSelfTest() ? 0 : 1; }\n')
            subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra',
                            '-Werror', '-I', str(ROOT / 'macos'), str(source),
                            '-o', str(binary)], check=True, timeout=20)
            subprocess.run([str(binary)], check=True, timeout=10)


if __name__ == '__main__':
    unittest.main()
