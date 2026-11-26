"""Synthetic tests of scoped installation record parsing."""

import struct
import unittest
from unittest.mock import patch

from verify_inno_ifps import Reader
from verify_inno_setup_records import (
    CANDIDATES, MIN_VERSION, check_task, custom_messages, verify, wizard_data,
)


def field(text: str) -> bytes:
    """Serialize one Unicode field."""
    raw = text.encode('utf-16le')
    return struct.pack('<I', len(raw)) + raw


class SetupRecordTests(unittest.TestCase):
    """Check exact policy strings, flags and complete wizard framing."""

    def test_candidate_rejects_mixed_source_and_setup(self) -> None:
        """Reject an exact setup paired with the other reviewed source before decoding."""
        reference_setup, reference_source = CANDIDATES['reference']
        current_setup, current_source = CANDIDATES['b2c5ce9']
        with patch('verify_inno_setup_records.recover') as recover:
            with patch('verify_inno_setup_records.digest', side_effect=[current_setup, reference_source]):
                with self.assertRaisesRegex(ValueError, 'installer source digest'):
                    verify(b'', b'', b'', b'', candidate='b2c5ce9')
            with patch('verify_inno_setup_records.digest', side_effect=[reference_setup, current_source]):
                with self.assertRaisesRegex(ValueError, 'installer source digest'):
                    verify(b'', b'', b'', b'')
            recover.assert_not_called()

    def test_task(self) -> None:
        """Reject a default-checked task or altered task name."""
        raw = b''.join(map(field, ['desktopicon', 'Create a desktop shortcut',
                                  'Additional shortcuts:', '', '', '']))
        raw += b'\0\1' + MIN_VERSION + b'\2'
        check_task(Reader(raw))
        for changed in (raw[:-1] + b'\0', raw.replace(b'd\0e\0', b'x\0e\0', 1)):
            with self.assertRaises(ValueError):
                check_task(Reader(changed))

    def test_custom_messages(self) -> None:
        """Expand newline tokens and reject duplicate source keys."""
        self.assertEqual(custom_messages(b'[CustomMessages]\nA=x%nB\n'), [['A', 'x\r\nB']])
        with self.assertRaises(ValueError):
            custom_messages(b'[CustomMessages]\nA=x\nA=y\n')

    def test_wizard_framing(self) -> None:
        """Reject trailing bytes, wrong counts and invalid image signatures."""
        images = [b'\x89PNG\r\n\x1a\n' + bytes(n - 8) for n in (5767, 10005)]
        raw = b''.join(struct.pack('<II', 1, len(x)) + x for x in images) + bytes(16)
        self.assertEqual(len(wizard_data(Reader(raw))), 2)
        for changed in (raw + b'x', raw[:-1], bytes(4) + raw[4:]):
            with self.assertRaises(ValueError):
                wizard_data(Reader(changed))


if __name__ == '__main__':
    unittest.main()
