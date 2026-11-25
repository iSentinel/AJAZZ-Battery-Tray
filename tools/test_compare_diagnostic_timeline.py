"""Synthetic timeline regressions based on the observed field layout."""

import json
import unittest

from compare_diagnostic_timeline import gate_sequences, timeline
from compare_ready_clear import parse_matrix
from test_beta60_field_report_import import projected_report
from test_compare_ready_clear import report
from normalize_device_diagnostics import MATRIX


def field_report(field: int, time: str) -> str:
    """Join redacted extended projection and synthetic six-probe matrix."""
    prefix = projected_report().split(MATRIX)[0]
    prefix = prefix.replace('2026-11-25T06:34:49.3697656', f'2026-11-25T{time}')
    matrix = report(field).split(MATRIX, 1)[1]
    matrix = matrix.replace('2026-11-24T21:22:33', f'2026-11-25T{time}')
    return prefix + MATRIX + matrix


class DiagnosticTimelineTests(unittest.TestCase):
    """Never equate repeated raw observations with a validated battery."""

    def test_gate_sequences_scoped(self) -> None:
        """Keep transitions within one observed collection and completed exchange."""
        def pair(gate: str) -> str:
            """Build a synthetic successful Apple GET and its classification."""
            return ('05.get.result=0x00000000 length=65\n'
                    '05.reply.first_bytes=omitted\nF7 policy gate: ' + gate)
        text = '\n'.join(('STEP: collection.open', pair('ReadUnavailable'),
                          pair('Accepted'), 'STEP: collection.open',
                          pair('Offline'), '05.get.result=0x00000001 length=0',
                          pair('Accepted')))
        result = gate_sequences(text, True)
        self.assertEqual(result['reported_gate_counts'],
                         {'Accepted': 2, 'Offline': 1, 'ReadUnavailable': 1})
        self.assertEqual(result['reported_transitions'],
                         [{'from': 'ReadUnavailable', 'to': 'Accepted', 'count': 1}])
        self.assertNotIn('omitted', json.dumps(result))

    def test_gate_sequences_reject_orphan_and_duplicate(self) -> None:
        """Do not accept labels outside a successful in-scope transfer."""
        get = 'Interface: synthetic\nSET F7 / GET 05 (65 bytes): OK; header=omitted'
        for text in ('F7 policy gate: Accepted', get + '\nF7 policy gate: invented',
                     get + '\nunrelated section\nF7 policy gate: Accepted',
                     get + '\nF7 policy gate: Accepted\nF7 policy gate: Offline'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                gate_sequences(text, False)

    def test_gate_sequence_missing_label_breaks_transition(self) -> None:
        """Missing classifications never bridge two observations."""
        get = 'SET F7 / GET 05 (65 bytes): OK; header=omitted'
        text = '\n'.join(('Interface: synthetic', get, 'F7 policy gate: Offline',
                          get, get, 'F7 policy gate: Accepted'))
        result = gate_sequences(text, False)
        self.assertEqual(result['reported_transitions'], [])
        self.assertEqual(sum(result['reported_gate_counts'].values()), 2)

    def test_order_and_unchanged_unverified(self) -> None:
        """Sort by actual capture time and keep the F7 value unverified."""
        first = field_report(93, '07:03:42')
        second = field_report(93, '07:04:42')
        result = timeline([second, first])
        self.assertEqual(result['transitions'][0]['unverified_field_change'], 'UNCHANGED')
        self.assertIsNone(result['snapshots'][0]['usb']['percent'])
        self.assertEqual(result['snapshots'][0]['ready_clear_unverified']['matrix_field'], 93)
        self.assertNotIn('RX buffer', json.dumps(result))
        self.assertEqual(result['identity_binding'], 'NOT_VERIFIED')

    def test_cache_and_fresh_separate(self) -> None:
        """Preserve last-good AULA while explicitly marking a missing reply."""
        first = field_report(93, '07:03:42')
        second = field_report(93, '07:04:42').replace(
            'Battery: 62; status: Fresh 2.4 GHz battery reply',
            'Battery: unavailable; status: Receiver present; keyboard asleep or no valid reply')
        second = second.replace('Consecutive no-reply polls: 0', 'Consecutive no-reply polls: 5')
        second = second.replace('Display cache active: False', 'Display cache active: True')
        second = second.replace('interval=30s; UTC: 2026-11-25T06:34:42.4935390',
                                'interval=30s; UTC: 2026-11-25T07:04:23')
        result = timeline([first, second])
        self.assertEqual(result['transitions'][0]['aula_state_before'], 'fresh')
        self.assertEqual(result['transitions'][0]['aula_state_after'], 'cached')
        rows = result['snapshots']
        self.assertEqual(rows[0]['aula']['state'], 'fresh')
        self.assertEqual(rows[1]['aula']['state'], 'cached')
        self.assertIsNone(rows[1]['aula']['fresh_percent'])
        self.assertEqual(rows[1]['aula']['last_good_percent'], 62)

    def test_duplicate_and_missing_matrix(self) -> None:
        """Do not invent a change when evidence is incomplete."""
        first = field_report(93, '07:03:42')
        with self.assertRaises(ValueError):
            timeline([first, first])
        second = field_report(93, '07:04:42')
        lines = second.splitlines()
        lines.pop(next(i for i, line in enumerate(lines) if line.startswith('RX buffer')))
        self.assertIsNone(parse_matrix('\n'.join(lines))[1])
        self.assertEqual(timeline([first, '\n'.join(lines)])['transitions'][0]
                         ['unverified_field_change'], 'NOT_COMPARABLE')

    def test_absent_receiver_then_return(self) -> None:
        """Confirmed absence is not a zero battery or a comparable field."""
        first = field_report(93, '07:03:42')
        absent = field_report(93, '07:04:42').split(MATRIX)[0] + MATRIX
        absent += '\nMatching MI_02 paths: 0'
        absent = absent.replace('receiver count=1', 'receiver count=0')
        absent = absent.replace('Receiver present: True; presence known: True',
                                'Receiver present: False; presence known: True', 1)
        last = field_report(93, '07:05:42')
        result = timeline([first, absent, last])
        self.assertEqual(result['snapshots'][1]['active_capture']['outcome'], 'receiver_absent')
        self.assertEqual(result['transitions'][1]['usb_state_before'], 'absent')
        self.assertEqual(result['transitions'][1]['usb_state_after'], 'unavailable')
        self.assertEqual(result['transitions'][1]['unverified_field_change'], 'NOT_COMPARABLE')

    def test_inconsistent_aula_rejected(self) -> None:
        """A cache cannot be fresh or come from a future observation."""
        first = field_report(93, '07:03:42')
        second = field_report(93, '07:04:42')
        with self.assertRaises(ValueError):
            timeline([first, second.replace('Display cache active: False',
                                           'Display cache active: True')])
        with self.assertRaises(ValueError):
            timeline([first, second.replace('06:34:42.4935390', '08:34:42.4935390')])


if __name__ == '__main__':
    unittest.main()
