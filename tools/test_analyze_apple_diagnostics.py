"""Regression coverage for versioned, redacted Apple menu reports."""

import json
from pathlib import Path
import tempfile
import unittest

from analyze_apple_diagnostics import MAX_SIZE, parse, read_report

STAMP = '2026-11-25T05:40:00Z'


def report(legacy: bool = False) -> str:
    """Return a synthetic report in the two native menu layouts."""
    title = ('AJAZZ Battery Tray High Sierra Edition' if legacy
             else 'AJAZZ Battery Tray diagnostic report')
    scope = ('VID:PID: 3151:5007\nUsage: FFFF:0002' if legacy
             else 'VID:PID: 3151:5007; usage FFFF:0002')
    state = ('Battery state: receiver present, no valid battery' if legacy
             else 'Last ordinary status: unavailable')
    return '\n'.join([
        title, 'Report schema: apple-menu-v1', 'Version: test (1)',
        f'UTC: {STAMP}', scope, state + '; battery: unknown',
        'Last verified USB UTC (session): never',
        'Polling active: false; isolated: false',
        'Bluetooth discovery: connected candidates=1',
        'Bluetooth manual 180F/2A19 pending: false',
        'Bluetooth last manual read: not requested',
    ])


class AppleReportTests(unittest.TestCase):
    """Validate evidence boundaries without collecting HID or Bluetooth."""

    def test_both_editions(self) -> None:
        """Normalize either native title and ordinary USB field."""
        for legacy in (False, True):
            result = parse(report(legacy))
            self.assertEqual(result['edition'], 'high-sierra' if legacy else 'universal')
            self.assertEqual(result['usb']['state'], 'unavailable')
            self.assertIsNone(result['usb']['percent'])
            self.assertFalse(result['active_trace_present'])

    def test_independent_gatt_zero(self) -> None:
        """Accept valid GATT zero but preserve independent USB unknown."""
        text = report().replace('read: not requested',
            f'read: outcome=fresh GATT; battery=0%; UTC={STAMP}; elapsed_ms=42')
        result = parse(text)
        self.assertEqual(result['manual_gatt']['percent'], 0)
        self.assertIsNone(result['usb']['percent'])
        self.assertEqual(result['identity_binding'], 'NOT_VERIFIED')

    def test_trace_redaction(self) -> None:
        """Do not return active raw bytes, free text or partial battery claims."""
        text = report() + '\n\nFresh bounded F7/05 trace:\n05.reply.first_bytes=ab cd\nVerified battery: 99%'
        result = parse(text)
        self.assertTrue(result['active_trace_present'])
        self.assertNotIn('ab cd', json.dumps(result))
        self.assertNotIn('99%', json.dumps(result))
        self.assertIsNone(result['usb']['percent'])

    def test_invalid_observations(self) -> None:
        """Reject inconsistent USB/GATT levels and invalid UTC."""
        for text in (
            report().replace('battery: unknown', 'battery: 0%'),
            report().replace('battery: unknown', 'battery: 83%'),
            report().replace(STAMP, '2026-02-30T05:00:00Z'),
            report().replace('read: not requested',
                f'read: outcome=timeout; battery=83%; UTC={STAMP}; elapsed_ms=10'),
        ):
            with self.assertRaises(ValueError):
                parse(text)

    def test_duplicate_and_unknown_schema(self) -> None:
        """Do not silently combine reports or unversioned snapshots."""
        for text in (report() + '\n' + report(True),
                     report() + '\n\nFresh bounded F7/05 trace:\n' + report(),
                     report().replace('apple-menu-v1', 'apple-menu-v2'),
                     report() + '\nUTC: ' + STAMP):
            with self.assertRaises(ValueError):
                parse(text)

    def test_bounded_input(self) -> None:
        """Reject oversized files and accept UTF-8 CRLF reports."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.txt'
            path.write_bytes(report().replace('\n', '\r\n').encode('utf-8-sig'))
            self.assertEqual(parse(read_report(path))['schema'], 'apple-menu-v1')
            path.write_bytes(b'x' * (MAX_SIZE + 1))
            with self.assertRaises(ValueError):
                read_report(path)


if __name__ == '__main__':
    unittest.main()
