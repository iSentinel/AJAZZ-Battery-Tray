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


def boundary_program() -> str:
    """Generate exact-limit native Apple reports with distinct capture times."""
    before, after = report().split(STAMP)
    prefix = json.dumps(before)
    suffix = json.dumps(after + '\n\nFresh bounded F7/05 trace:\n')
    return f"""
#include "AjazzSessionArchive.h"
int main(int argc, char **argv) {{
    if (argc != 2) return 2;
    AjazzDiagnosticSession *s = AjazzSessionCreate();
    if (!s) return 1;
    uint8_t data[AJAZZ_SESSION_REPORT_LIMIT];
    AjazzSessionStart(s);
    bool ok = true;
    char added[28];
    for (unsigned i = 0; i < AJAZZ_SESSION_LIMIT; i++) {{
        int n = snprintf((char *)data, sizeof(data), "%s2026-11-25T05:40:%02uZ%s",
            {prefix}, i, {suffix});
        if (n < 0 || (size_t)n >= sizeof(data)) {{ ok = false; break; }}
        memset(data + n, 'x', sizeof(data) - (size_t)n);
        if (snprintf(added, sizeof(added), "2026-11-25T05:40:%02u.000001Z", i) != 27 ||
            !AjazzSessionAddAt(s, 0, data, sizeof(data), added)) {{ ok = false; break; }}
    }}
    ok = ok && AjazzSessionCount(s) == 32 &&
        !AjazzSessionAddAt(s, 0, data, sizeof(data), "2026-11-25T05:41:00.000001Z") &&
        AjazzSessionSave(s, argv[1]);
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

    def test_native_export_at_count_and_report_limits(self) -> None:
        """Import the real maximum Apple session and preserve every annotation."""
        if os.name == 'nt':
            self.skipTest('POSIX C session writer')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, binary, archive = root / 'limits.c', root / 'limits', root / 'limits.zip'
            source.write_text(boundary_program(), encoding='utf-8')
            subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                            '-I', str(ROOT / 'macos'), str(source), '-o', str(binary)],
                           check=True, timeout=20)
            subprocess.run([str(binary), str(archive)], check=True, timeout=10)
            entries = load_session(archive)
            self.assertEqual(len(entries), 32)
            self.assertEqual(sum(len(t.encode('utf-8')) for t, _ in entries), 2 * 1024 * 1024)
            self.assertTrue(all(len(t.encode('utf-8')) == 65536 for t, _ in entries))
            result = timeline([t for t, _ in entries], [a for _, a in entries])
            self.assertEqual(len(result['transitions']), 31)
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
