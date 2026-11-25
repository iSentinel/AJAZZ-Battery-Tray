"""Exercise Windows session ZIP layout and fail-closed importer boundaries."""

from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile

from compare_diagnostic_timeline import main, timeline
from read_diagnostic_session import load_session, MAX_REPORT
from test_compare_diagnostic_timeline import field_report


def fixture() -> tuple[dict, dict]:
    """Mirror the exporter with synthetic full reports and owner markers."""
    texts = {f'snapshot-{i:02d}.txt': field_report(93, f'07:0{i + 2}:42')
             for i in (1, 2)}
    entries = [{'file': name, 'marker': marker,
                'addedUtc': f'2026-11-25T07:0{i + 2}:43.1234567+00:00',
                'bytes': len(text.encode('utf-8'))}
               for i, ((name, text), marker) in enumerate(
                   zip(texts.items(), ('Baseline', 'BluetoothSelected')), 1)]
    manifest = {'schema': 'diagnostic-session-v1', 'identityBinding': 'NOT_VERIFIED',
                'markers': 'OWNER_ANNOTATED', 'entries': entries}
    return texts, manifest


def write_zip(path: Path, texts: dict, manifest: dict | str) -> None:
    """Write a local fixture, not a hardware report."""
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in texts.items():
            archive.writestr(name, data)
        archive.writestr('manifest.json', manifest if isinstance(manifest, str)
                         else json.dumps(manifest))


class SessionImportTests(unittest.TestCase):
    """Test strict manifest, names, times, sizes and no extraction."""

    def test_valid_archive_cli_and_owner_annotations(self) -> None:
        """Preserve owner marker provenance without claiming transport state."""
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'test.zip'
            write_zip(path, *fixture())
            out = StringIO()
            with redirect_stdout(out):
                self.assertEqual(main(['--session', str(path)]), 0)
            result = json.loads(out.getvalue())
            self.assertEqual(result['snapshots'][1]['owner_annotation']['marker'],
                             'BluetoothSelected')
            self.assertEqual(result['identity_binding'], 'NOT_VERIFIED')
            self.assertEqual(result['snapshots'][1]['usb']['state'], 'unavailable')
            self.assertEqual(list(Path(root).iterdir()), [path])
            self.assertNotIn('RX buffer', out.getvalue())

    def test_initial_passive_snapshot_without_aula_poll(self) -> None:
        """Handle the actual unchecked AULA emitter state without assuming absence."""
        texts, _ = fixture()
        first, second = texts.values()
        first = first.replace('interval=30s; UTC: 2026-11-25T06:34:42.4935390+00:00',
                              'interval=30s; UTC: never')
        start = first.index('[AULA L99 last measurement]')
        first = first[:start] + first[start:].replace(
            'Receiver present: True; presence known: True',
            'Receiver present: unknown; presence known: unknown', 1)
        first = first.replace('Battery: 62; status: Fresh 2.4 GHz battery reply',
                              'Battery: unavailable; status: not checked')
        first = first.replace('Last successful battery: 62; UTC: 2026-11-25T06:34:42.4935390+00:00',
                              'Last successful battery: unavailable; UTC: never')
        row = timeline([first, second])['snapshots'][0]['aula']
        self.assertEqual(row['state'], 'not_checked')
        self.assertIsNone(row['receiver_present'])
        self.assertIsNone(row['fresh_percent'])
        with self.assertRaises(ValueError):
            timeline([first.replace('Display cache active: False',
                                    'Display cache active: True'), second])

    def test_extra_traversal_or_missing_member(self) -> None:
        """Reject any name outside the exact ordered set."""
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'test.zip'
            for name in ('../escape.txt', 'snapshot-03.txt', '/absolute.txt'):
                texts, manifest = fixture()
                texts[name] = 'unexpected'
                write_zip(path, texts, manifest)
                with self.assertRaises(ValueError):
                    load_session(path)

    def test_manifest_mismatch(self) -> None:
        """Reject unexpected provenance, byte counts, markers and timestamps."""
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'test.zip'
            for field, value in [('marker', 'invented'), ('bytes', 1),
                                 ('bytes', True), ('addedUtc', 'never'),
                                 ('file', '../escape.txt')]:
                texts, manifest = fixture()
                manifest['entries'][1][field] = value
                write_zip(path, texts, manifest)
                with self.assertRaises(ValueError):
                    load_session(path)
            texts, manifest = fixture()
            manifest['identityBinding'] = 'VERIFIED'
            write_zip(path, texts, manifest)
            with self.assertRaises(ValueError):
                load_session(path)

    def test_duplicate_json_and_member(self) -> None:
        """Reject duplicate keys and duplicate archive names."""
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'test.zip'
            texts, manifest = fixture()
            write_zip(path, texts, json.dumps(manifest)[:-1] + ', "schema":"diagnostic-session-v1"}')
            with self.assertRaises(ValueError):
                load_session(path)
            write_zip(path, texts, manifest)
            with zipfile.ZipFile(path, 'a') as archive, self.assertWarns(UserWarning):
                archive.writestr('snapshot-01.txt', 'duplicate')
            with self.assertRaises(ValueError):
                load_session(path)

    def test_oversize_and_symlink_member(self) -> None:
        """Reject oversized compressed content and archive symlink types."""
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'test.zip'
            texts, manifest = fixture()
            texts['snapshot-01.txt'] = 'x' * (MAX_REPORT + 1)
            write_zip(path, texts, manifest)
            with self.assertRaises(ValueError):
                load_session(path)
            texts, manifest = fixture()
            with zipfile.ZipFile(path, 'w') as archive:
                link = zipfile.ZipInfo('snapshot-01.txt')
                link.create_system = 3
                link.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(link, texts['snapshot-01.txt'])
                archive.writestr('snapshot-02.txt', texts['snapshot-02.txt'])
                archive.writestr('manifest.json', json.dumps(manifest))
            with self.assertRaises(ValueError):
                load_session(path)

    def test_invalid_annotation_time_and_corrupt_zip(self) -> None:
        """Fail without partial JSON or echoing untrusted filenames."""
        texts, manifest = fixture()
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'test.zip'
            manifest['entries'][0]['addedUtc'] = '2026-11-25T07:00:00+00:00'
            write_zip(path, texts, manifest)
            entries = load_session(path)
            with self.assertRaises(ValueError):
                timeline([t for t, _ in entries], [a for _, a in entries])
            path.write_bytes(b'not a zip')
            out, err = StringIO(), StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                self.assertEqual(main(['--session', str(path)]), 2)
            self.assertEqual(out.getvalue(), '')
            self.assertNotIn(str(path), err.getvalue())


if __name__ == '__main__':
    unittest.main()
