"""Exercise the exact Apple C session writer and common Python ZIP importer."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from compare_diagnostic_timeline import timeline
from read_diagnostic_session import load_session
from test_analyze_apple_diagnostics import report, STAMP

ROOT = Path(__file__).resolve().parents[1]


def c_program() -> str:
    """Create a synthetic no-HID fixture using both Apple report layouts."""
    a = json.dumps(report(), ensure_ascii=False)
    b = json.dumps(report(True).replace(STAMP, '2026-11-25T05:41:00Z'), ensure_ascii=False)
    return f"""
#include "AjazzSessionArchive.h"
int main(int argc, char **argv) {{
    if (argc != 2) return 2;
    AjazzDiagnosticSession *s = AjazzSessionCreate();
    const char *a = {a}, *b = {b};
    const char *t1 = "2026-11-25T05:40:01.000000Z", *t2 = "2026-11-25T05:41:01.000000Z";
    bool ok = !AjazzSessionAddAt(s, 0, (const uint8_t*)a, strlen(a), t1);
    AjazzSessionStart(s);
    ok = ok && AjazzSessionAddAt(s, 0, (const uint8_t*)a, strlen(a), t1) &&
        !AjazzSessionAddAt(s, 2, (const uint8_t*)a, strlen(a), t2) &&
        !AjazzSessionAddAt(s, 99, (const uint8_t*)b, strlen(b), t2) &&
        !AjazzSessionAddAt(s, 2, (const uint8_t*)b, strlen(b), t1) &&
        !AjazzSessionAddAt(s, 2, (const uint8_t*)b, AJAZZ_SESSION_REPORT_LIMIT+1, t2) &&
        !AjazzSessionSave(s, argv[1]) &&
        AjazzSessionAddAt(s, 2, (const uint8_t*)b, strlen(b), t2) &&
        AjazzSessionSave(s, argv[1]) && !AjazzSessionSave(s, argv[1]);
    AjazzSessionClear(s);
    ok = ok && !AjazzSessionActive(s) && AjazzSessionCount(s) == 0;
    AjazzSessionDestroy(s);
    return !ok;
}}
"""


class AppleSessionArchiveTests(unittest.TestCase):
    """Keep both GUI editions connected to the bounded local session writer."""

    def test_portable_native_zip_roundtrip(self) -> None:
        """Compile C with strict warnings and import real emitted ZIP bytes."""
        if os.name == 'nt':
            self.skipTest('POSIX C session writer')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, binary, archive = root / 'test.c', root / 'test', root / 'test.zip'
            source.write_text(c_program(), encoding='utf-8')
            subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                            '-I', str(ROOT / 'macos'), str(source), '-o', str(binary)],
                           check=True, timeout=20)
            subprocess.run([str(binary), str(archive)], check=True, timeout=10)
            self.assertEqual(archive.stat().st_mode & 0o777, 0o600)
            entries = load_session(archive)
            result = timeline([t for t, _ in entries], [a for _, a in entries])
            self.assertEqual([r['edition'] for r in result['snapshots']],
                             ['universal', 'high-sierra'])
            self.assertEqual(result['snapshots'][1]['owner_annotation']['marker'],
                             'BluetoothSelected')
            self.assertEqual(result['identity_binding'], 'NOT_VERIFIED')

    def test_both_menu_paths_passive(self) -> None:
        """The annotation path must not start an active HID worker."""
        swift = (ROOT / 'macos/main.swift').read_text()
        legacy = (ROOT / 'macos/high-sierra/main.m').read_text()
        self.assertIn('addSessionReport(diagnosticSnapshot(), marker:', swift)
        self.assertIn('[self addSessionReport:[self diagnostics] marker:', legacy)
        for code in (swift, legacy):
            for name in ('AjazzSessionCreate', 'AjazzSessionAdd', 'AjazzSessionSave',
                         'AjazzSessionClear', 'AjazzSessionDestroy'):
                self.assertIn(name, code)
            self.assertIn('Add report to diagnostic session', code)


if __name__ == '__main__':
    unittest.main()
