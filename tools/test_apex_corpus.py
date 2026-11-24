"""Replay sanitized HID reports against offline and production Apple decoders."""

import csv
import ctypes
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

    def replay(self, decode, platform):
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

    def test_current_windows_replay(self):
        """Use the same numbered reports as the C# unit suite."""
        self.replay(current_percent, "windows")

    @unittest.skipUnless(shutil.which("cc"), "a C compiler is required")
    def test_apple_decoder(self):
        """Call the actual shared header used by both native Mac binaries."""
        wrapper = ('#include "AjazzBatteryReport.h"\n'
                   'int decode(const uint8_t *p, size_t n) {\n'
                   '    return AjazzBatteryPercent(p, n);\n}\n')
        with tempfile.TemporaryDirectory() as temp:
            library = Path(temp) / "decoder.so"
            subprocess.run(["cc", "-std=c11", "-shared", "-fPIC", "-x", "c",
                            "-I", str(ROOT / "macos"), "-", "-o", str(library)],
                           input=wrapper, text=True, check=True)
            decode = ctypes.CDLL(str(library)).decode
            decode.argtypes = (ctypes.c_char_p, ctypes.c_size_t)
            decode.restype = ctypes.c_int

            def apple(data):
                value = decode(data, len(data))
                return None if value < 0 else value

            self.replay(apple, "apple")
