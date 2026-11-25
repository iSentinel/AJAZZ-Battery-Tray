"""Synthetic IFPS instruction and malformed-table regressions."""

import struct
import unittest

from verify_inno_ifps import Reader, check_script, instructions, operand


class IfpsTests(unittest.TestCase):
    """Reject unsupported bytecode and decode scoped operands and branches."""

    def test_operands(self) -> None:
        """Decode signed stack slots and typed literal values."""
        self.assertEqual(operand(Reader(b'\0' + struct.pack('<I', 0x5fffffff))), ('slot', -1))
        self.assertEqual(operand(Reader(b'\1' + struct.pack('<I', 28) + b'\1')), ('bool', 1))

    def test_instructions(self) -> None:
        """Calculate relative branch targets and preserve return instructions."""
        self.assertEqual(instructions(b'\6' + struct.pack('<i', 0) + b'\x09'),
                         [(0, 6, (5,)), (5, 9, ())])

    def test_reject(self) -> None:
        """Reject malformed operands, unknown opcodes and bogus type tables."""
        for raw in (b'\xff', b'\x03', b'\x03\x01' + struct.pack('<I', 28) + b'\x02'):
            with self.assertRaises(ValueError):
                instructions(raw)
        with self.assertRaises(ValueError):
            check_script(struct.pack('<4s6I', b'IFPS', 23, 32, 4, 2, 0, 0) + bytes(616))


if __name__ == '__main__':
    unittest.main()
