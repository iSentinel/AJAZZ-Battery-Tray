"""Regressions for the observed beta.60 extended report field layout."""

import unittest

from analyze_aula_sleep import parse_summary
from normalize_device_diagnostics import BETA60, normalize

STAMP = '2026-11-25T06:34:49.3697656+00:00'
SAMPLE = '2026-11-25T06:34:42.4935390+00:00'


def projected_report() -> str:
    """Use only observed field layout; omit raw buffers and unrelated inventory."""
    return '\n'.join([
        'AJAZZ APEX full comparison report (one capture)',
        f'Version: {BETA60}',
        f'UTC: {STAMP}',
        'Fresh enumeration known=True; receiver count=1; first valid battery=unavailable',
        'unverified mouse field (not telemetry)=93',
        'AJAZZ Battery Tray extended diagnostic report',
        f'App version: {BETA60}',
        f'Report UTC: {STAMP}',
        '[AJAZZ last ordinary poll — not a fresh request]',
        'Completed UTC: 2026-11-25T06:34:42.4766408+00:00',
        'Receiver present: True; presence known: True',
        'Battery: unavailable; status: No valid battery status report',
        'unverified mouse field (not telemetry)=93',
        '[AULA L99 last measurement]',
        f'Auto monitoring: True; interval=30s; UTC: {SAMPLE}',
        'Receiver present: True; presence known: True',
        'Battery: 62; status: Fresh 2.4 GHz battery reply',
        f'Last successful battery: 62; UTC: {SAMPLE}; Consecutive no-reply polls: 0; '
        'Cache lifetime hours: 24; Display cache active: False',
        '[Bluetooth fallback state]',
        'Enabled: False; displayed device: AJAZZ shared receiver (rev. 0002; model unverified); '
        'source: 2.4 GHz; displayed battery: unknown',
        'Opted-in BLE devices: 0; request pending: False',
        '[Fresh APEX protocol matrix — full vendor buffers]',
    ])


class Beta60FieldReportTests(unittest.TestCase):
    """Preserve absent evidence and keep new schemas strict."""

    def test_legacy_missing_inspector(self) -> None:
        """A missing historical section is not proof of a GATT failure."""
        result = normalize(projected_report())
        self.assertEqual(result['manual_gatt']['evidence'], 'NOT_EXPORTED_IN_LEGACY_REPORT')
        self.assertIsNone(result['manual_gatt']['last_direct'])
        self.assertIsNone(result['usb']['percent'])
        self.assertEqual(result['active_capture']['outcome'], 'inconclusive')

    def test_receiver_removed_aula_survives(self) -> None:
        """Use the second field report's independent ordinary and active states."""
        text = projected_report().replace('receiver count=1', 'receiver count=0')
        text = text.replace('unverified mouse field (not telemetry)=93',
                            'unverified mouse field (not telemetry)=unavailable')
        text = text.replace('Receiver present: True; presence known: True',
                            'Receiver present: False; presence known: True', 1)
        text = text.replace('status: No valid battery status report', 'status: Receiver not found')
        text += '\nMatching MI_02 paths: 0'
        result = normalize(text)
        self.assertEqual(result['usb']['state'], 'absent')
        self.assertEqual(result['active_capture']['outcome'], 'receiver_absent')
        self.assertIsNone(result['active_capture']['reported_percent'])
        self.assertEqual(normalize(text.replace('known=True; receiver count=0',
                                               'known=False; receiver count=0'))
                         ['active_capture']['outcome'], 'inconclusive')
        self.assertEqual(normalize(text + '\n[Receiver #1]')['active_capture']['outcome'],
                         'unrecognized')
        self.assertIsNotNone(parse_summary(text))

    def test_new_schema_and_other_build_rejected(self) -> None:
        """Do not silently relax the required section for other reports."""
        text = projected_report()
        for changed in (text.replace('App version: ', 'Report schema: windows-extended-v1\nApp version: '),
                        text.replace(BETA60, '0.3.0-beta.61'),
                        text.replace('[Bluetooth fallback state]', '[Other state]'),
                        text.replace('[Bluetooth fallback state]', '[Bluetooth manual inspection — malformed]\n[Bluetooth fallback state]')):
            with self.assertRaises(ValueError):
                normalize(changed)

    def test_aula_equals_separator(self) -> None:
        """The actual extended emitter uses equals, not colon."""
        actual = parse_summary(projected_report())
        historical = parse_summary(projected_report().replace('interval=30s', 'interval: 30s'))
        self.assertEqual(actual, historical)
        self.assertIsNotNone(actual)


if __name__ == '__main__':
    unittest.main()
