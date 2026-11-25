"""Replay sanitized HID reports against offline and production Apple decoders."""

import csv
from collections.abc import Callable
import ctypes
from itertools import product
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from compare_apex_reports import current_percent


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests" / "fixtures" / "apex-f7-v1.csv"


class SharedApexCorpusTests(unittest.TestCase):
    """Keep Windows-numbered and Apple-stripped expectations explicit."""

    def replay(self, decode: Callable[[bytes], int | None], platform: str) -> None:
        """Check every corpus row, including its origin and expected result."""
        with CORPUS.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertTrue(rows)
        self.assertEqual(len(rows), len({row["case"] for row in rows}))
        for row in rows:
            with self.subTest(case=row["case"]):
                self.assertIn(row["origin"], ("field-prefix", "synthetic"))
                expected = row[platform]
                self.assertEqual(decode(bytes.fromhex(row["hex"])),
                                 None if expected == "unknown" else int(expected))

    def test_current_windows_replay(self) -> None:
        """Use the same numbered reports as the C# unit suite."""
        self.replay(current_percent, "windows")

    @unittest.skipUnless(shutil.which("cc"), "a C compiler is required")
    def test_apple_decoder(self) -> None:
        """Call the actual shared header used by both native Mac binaries."""
        wrapper = ('#include "AjazzBatteryReport.h"\n'
                   'int decode(const uint8_t *p, size_t n) {\n'
                   '    return AjazzBatteryPercent(p, n);\n}\n')
        with tempfile.TemporaryDirectory() as temp:
            library = Path(temp) / "decoder.so"
            subprocess.run(["cc", "-std=c11", "-shared", "-fPIC", "-x", "c",
                            "-I", str(ROOT / "macos"), "-", "-o", str(library)],
                           input=wrapper, text=True, check=True, timeout=15)
            decode = ctypes.CDLL(str(library)).decode
            decode.argtypes = (ctypes.c_char_p, ctypes.c_size_t)
            decode.restype = ctypes.c_int

            def apple(data: bytes) -> int | None:
                """Translate the shared C decoder's negative result to unavailable."""
                value = decode(data, len(data))
                return None if value < 0 else value

            self.replay(apple, "apple")


    @unittest.skipUnless(shutil.which("cc"), "a C compiler is required")
    def test_apple_typed_observation_parity(self) -> None:
        """Exercise the production C decoder on both IOKit framing forms."""
        wrapper = ('#include "AjazzBatteryReport.h"\n'
                   'int inspect(const uint8_t *p, size_t n, int *out) {\n'
                   '    AjazzF7Observation v = AjazzObserveF7(p, n);\n'
                   '    out[0] = v.reportedField; out[1] = v.verifiedPercent;\n'
                   '    return v.gate;\n}\n'
                   'int decode(const uint8_t *p, size_t n) {\n'
                   '    return AjazzBatteryPercent(p, n);\n}\n')
        with tempfile.TemporaryDirectory() as temp:
            library = Path(temp) / "decoder.so"
            subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                            "-shared", "-fPIC", "-x", "c", "-I", str(ROOT / "macos"),
                            "-", "-o", str(library)], input=wrapper, text=True,
                           check=True, timeout=15)
            native = ctypes.CDLL(str(library))
            native.inspect.argtypes = (ctypes.c_char_p, ctypes.c_size_t,
                                       ctypes.POINTER(ctypes.c_int))
            native.inspect.restype = ctypes.c_int
            native.decode.argtypes = (ctypes.c_char_p, ctypes.c_size_t)
            native.decode.restype = ctypes.c_int
            count = 0
            for flags in product((0, 1, 2), repeat=6):
                slot, ready, keyboard, online, send, boot = flags
                for field in (0, 1, 42, 100, 101, 255):
                    payload = bytes((ready, 0, field, keyboard, online, send, slot + 1, 0, boot))
                    expected = self.expected_gate(slot + 1, ready, keyboard, online, send, boot, field)
                    out = (ctypes.c_int * 2)()
                    self.assertEqual(native.inspect(payload, len(payload), out), expected)
                    self.assertEqual(out[0], field if slot != 0 and 1 <= field <= 100 else -1)
                    accepted = field if expected == 9 else -1
                    self.assertEqual(out[1], accepted)
                    for frame in (payload, b"\x05" + payload):
                        self.assertEqual(native.decode(frame, len(frame)), accepted)
                    count += 1
            self.assertEqual(count, 4374)

    @staticmethod
    def expected_gate(slot: int, ready: int, keyboard: int, online: int,
                      send: int, boot: int, field: int) -> int:
        """Independent oracle for the established ordered F7 policy."""
        reject = (slot == 1, keyboard > 1, ready != 1, online != 0,
                  send != 1, boot != 0, field == 0, field > 100)
        return next((i for i, failed in enumerate(reject, 1) if failed), 9)


    @unittest.skipUnless(shutil.which("cc"), "a C compiler is required")
    def test_apple_trace_gate_names(self) -> None:
        """Exercise the exact diagnostic formatter for both report forms."""
        wrapper = ('#include "AjazzBatteryReport.h"\n'
                   'const char *gate(const uint8_t *p, size_t n) {\n'
                   '    return AjazzF7ReplyGateName(p, n);\n}\n')
        with tempfile.TemporaryDirectory() as temp:
            library = Path(temp) / "gate.so"
            subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                            "-shared", "-fPIC", "-x", "c", "-I", str(ROOT / "macos"),
                            "-", "-o", str(library)], input=wrapper, text=True,
                           check=True, timeout=15)
            gate = ctypes.CDLL(str(library)).gate
            gate.argtypes = (ctypes.c_char_p, ctypes.c_size_t)
            gate.restype = ctypes.c_char_p
            base = bytes((1, 0, 42, 0, 0, 1, 2, 0, 0))
            cases = ((6, 1, "KeyboardOnly"), (3, 2, "InvalidStatus"),
                     (0, 0, "ReadUnavailable"), (4, 1, "Offline"),
                     (5, 0, "CannotSend"), (8, 1, "RadioBoot"),
                     (2, 0, "ZeroField"), (2, 101, "OutOfRange"),
                     (2, 42, "Accepted"), (6, 0, "Unrecognized"))
            for offset, value, expected in cases:
                payload = base[:offset] + bytes((value,)) + base[offset + 1:]
                for frame in (payload, b"\x05" + payload):
                    self.assertEqual(gate(frame, len(frame)), expected.encode())
            for frame in (b"", b"\x05", b"\x05\x00\x00\x2a"):
                self.assertEqual(gate(frame, len(frame)), b"Unrecognized")
            self.assertEqual(gate(None, 10), b"Unrecognized")
