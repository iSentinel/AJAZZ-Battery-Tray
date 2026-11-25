"""Regression coverage for the common redacted diagnostic envelope."""

import json
import unittest

from normalize_device_diagnostics import normalize
from test_analyze_apple_diagnostics import report

STAMP = '2026-11-25T05:40:00.1234567+00:00'
TITLE = 'AJAZZ Battery Tray extended diagnostic report'
FULL = 'AJAZZ APEX full comparison report (one capture)'
MATRIX = '[Fresh APEX protocol matrix — full vendor buffers]'


def windows_report(versioned: bool = True) -> str:
    """Represent the actual extended report's fixed snapshot fields."""
    lines = [TITLE]
    if versioned:
        lines.append('Report schema: windows-extended-v1')
    lines.extend([
        'App version: test',
        f'Report UTC: {STAMP}',
        '[AJAZZ last ordinary poll — not a fresh request]',
        f'Completed UTC: {STAMP}',
        'Receiver present: True; presence known: True',
        'Battery: unavailable; status: No valid battery status report',
        'unverified mouse field (not telemetry)=95',
        '[AULA L99 last measurement]',
        'Battery: 66; status: cached',
        '[Bluetooth manual inspection — historical, not a fresh request]',
        'Manual operation pending: False',
        'Last manual result: paired endpoint (name omitted); transport=Classic; '
        f'battery=95; source=WindowsCached; completed UTC={STAMP}; historical=true',
        'Last direct GATT result: AJ179 APEX; transport=BLE; '
        f'battery=83; source=DirectGatt; completed UTC={STAMP}; historical=true',
    ])
    return '\n'.join(lines)


class NormalizeDiagnosticsTests(unittest.TestCase):
    """Check source separation without hardware or platform dependencies."""

    def test_windows_sources_independent(self) -> None:
        """Do not convert unverified F7, cached or unrelated AULA to USB."""
        result = normalize(windows_report())
        self.assertIsNone(result['usb']['percent'])
        self.assertEqual(result['usb']['state'], 'unavailable')
        self.assertEqual(result['manual_gatt']['last_manual']['source'], 'WindowsCached')
        self.assertEqual(result['manual_gatt']['last_direct']['percent'], 83)
        self.assertEqual(result['snapshot_utc'], '2026-11-25T05:40:00.123456+00:00')
        self.assertNotIn('AJ179 APEX', json.dumps(result))
        self.assertEqual(result['identity_binding'], 'NOT_VERIFIED')

    def test_legacy_and_full(self) -> None:
        """Label legacy and full capture without exporting matrix content."""
        result = normalize(FULL + '\n' + windows_report(False) +
                           '\n' + MATRIX + '\nRX buffer[2]=dead')
        self.assertEqual(result['schema'], 'windows-extended-legacy')
        self.assertTrue(result['active_trace_present'])
        self.assertNotIn('dead', json.dumps(result))

    def test_apple_envelope(self) -> None:
        """Wrap both Apple layouts without changing their existing parser."""
        for legacy in (False, True):
            result = normalize(report(legacy))
            self.assertEqual(result['format'], 'device-diagnostics-summary-v1')
            self.assertEqual(result['schema'], 'apple-menu-v1')
            self.assertIsNone(result['usb']['percent'])

    def test_presence_unknown(self) -> None:
        """Unknown receiver presence must not become confirmed absence."""
        result = normalize(windows_report().replace(
            'Receiver present: True; presence known: True',
            'Receiver present: False; presence known: False'))
        self.assertIsNone(result['usb']['receiver_present'])
        self.assertEqual(result['usb']['state'], 'unknown')

    def test_not_open_and_timeout(self) -> None:
        """Absent manual inspector and failed fresh capture remain unknown."""
        text = windows_report().split('[Bluetooth manual inspection', 1)[0]
        text += '[Bluetooth manual inspection — historical] Not opened this session.\n'
        text += '[Fresh APEX protocol matrix] NOT_RUN: worker timed out.'
        result = normalize(text)
        self.assertIsNone(result['manual_gatt']['last_direct'])
        self.assertFalse(result['active_trace_present'])

    def test_universal_active_outcome(self) -> None:
        """Keep active reported value distinct from the ordinary snapshot."""
        trace = "\n\nFresh bounded F7/05 trace:\n"
        result = normalize(report() + trace +
                           "Battery status: battery\nVerified battery: 83%\nElapsed ms: 12")
        self.assertEqual(result["active_capture"]["outcome"], "reported_valid")
        self.assertEqual(result["active_capture"]["reported_percent"], 83)
        self.assertIsNone(result["usb"]["percent"])
        self.assertEqual(result["active_capture"]["independent_verification"], "NOT_VERIFIED")

    def test_incomplete_overrides_terminal_claim(self) -> None:
        """Timeout or cancellation must never import a terminal percentage."""
        for reason in ("cancelled", "timeout", "worker failed"):
            text = report() + "\n\nFresh bounded F7/05 trace:\n"
            text += f"INCOMPLETE: {reason}; no fresh battery claimed\n"
            text += "Battery status: battery\nVerified battery: 83%\nElapsed ms: 12"
            result = normalize(text)["active_capture"]
            self.assertEqual(result["outcome"], reason if reason != "worker failed" else "incomplete")
            self.assertIsNone(result["reported_percent"])
        legacy = report(True) + "\n\nFresh bounded F7/05 trace:\n"
        legacy += "PASS: battery=83%\n[Output truncated]\nDiagnostic exit: 0\nElapsed ms: 12"
        self.assertEqual(normalize(legacy)["active_capture"]["outcome"], "incomplete")
        self.assertIsNone(normalize(legacy)["active_capture"]["reported_percent"])

    def test_legacy_active_exit(self) -> None:
        """Interpret only coherent legacy exit status and final percentage."""
        prefix = report(True) + "\n\nFresh bounded F7/05 trace:\n"
        for code, outcome, value in ((0, "reported_valid", 83), (2, "inconclusive", None),
                                      (124, "timeout", None), (125, "cancelled", None)):
            detail = "PASS: battery=83%\n" if code == 0 else ""
            result = normalize(prefix + detail + f"Diagnostic exit: {code}\nElapsed ms: 12")
            self.assertEqual(result["active_capture"]["outcome"], outcome)
            self.assertEqual(result["active_capture"]["reported_percent"], value)

    def test_windows_active_summary(self) -> None:
        """Use only the typed summary preceding the extended snapshot."""
        prefix = FULL + "\nFresh enumeration known=True; receiver count=1; first valid battery=83\n"
        result = normalize(prefix + windows_report() + "\n" + MATRIX + "\nRX buffer[2]=dead")
        self.assertEqual(result["active_capture"]["reported_percent"], 83)
        self.assertIsNone(result["usb"]["percent"])
        self.assertNotIn("dead", json.dumps(result))
        text = windows_report() + "\n[Fresh APEX protocol matrix] NOT_RUN: worker timed out."
        self.assertEqual(normalize(text)["active_capture"]["outcome"], "timeout")

    def test_unrecognized_terminal_fields(self) -> None:
        """Missing or duplicate terminal fields do not imply success."""
        prefix = report() + "\n\nFresh bounded F7/05 trace:\n"
        for detail in ("Verified battery: 83%", "Battery status: battery\nVerified battery: 83%",
                       "Battery status: battery\nBattery status: battery\nVerified battery: 83%\nElapsed ms: 1"):
            self.assertEqual(normalize(prefix + detail)["active_capture"]["outcome"], "unrecognized")

    def test_invalid_sources_and_framing(self) -> None:
        """Reject duplicate fields, contradictory levels and wrong sources."""
        base = windows_report()
        for text in (
            base + '\n' + base,
            base.replace('windows-extended-v1', 'windows-extended-v2'),
            base.replace('Battery: unavailable; status:', 'Battery: 0; status:'),
            base.replace('source=DirectGatt', 'source=WindowsCached'),
            base.replace('transport=BLE', 'transport=Classic'),
            base.replace('completed UTC=' + STAMP, 'completed UTC=never'),
            FULL + '\n' + base,
            base + '\n' + MATRIX,
        ):
            with self.subTest(case=text[:60]), self.assertRaises(ValueError):
                normalize(text)


if __name__ == '__main__':
    unittest.main()
