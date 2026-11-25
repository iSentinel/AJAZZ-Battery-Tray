"""Synthetic exact component coverage and candidate-binding regressions."""

from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from compare_inno_compiler import NAMES, ENTRY, compare, inventory
from verify_installer_candidate import digest

CANDIDATE = {'source_sha': 'a' * 40, 'setup_sha256': 'b' * 64}


def fixture(root: Path) -> list[dict]:
    """Generate synthetic files for every reviewed component name."""
    rows = []
    for name in sorted(NAMES):
        raw = name.encode()
        (root / name).write_bytes(raw)
        rows.append({'name': name, 'state': 'PRESENT',
                     'bytes': len(raw), 'sha256': digest(raw)})
    return rows


def archive(rows: list[dict]) -> bytes:
    """Emit the expected inventory schema."""
    data = {'schema': 'inno-compiler-inventory-v1', **CANDIDATE,
            'engine_version': '6.7.1', 'trust': 'NOT_VERIFIED',
            'scope': 'observed top-level compiler inputs, not actual loaded or embedded components',
            'files': rows}
    output = BytesIO()
    with zipfile.ZipFile(output, 'w') as z:
        z.writestr(ENTRY, json.dumps(data))
    return output.getvalue()


class CompilerComparisonTests(unittest.TestCase):
    """Never accept partial, changed or unrelated compiler evidence."""

    def test_exact_scope(self) -> None:
        """All 38 observed files must match."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = fixture(root)
            raw = archive(rows)
            self.assertEqual(len(compare(inventory(raw, digest(raw), CANDIDATE), root)), 38)

    def test_missing_duplicate_and_changed(self) -> None:
        """Reject absence, duplicates, and modified official bytes."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = fixture(root)
            for bad in (rows[:-1], rows[:-1] + [rows[0]],
                        [{**rows[0], 'state': 'ABSENT'}, *rows[1:]]):
                with self.assertRaises(ValueError):
                    compare(bad, root)
            (root / rows[0]['name']).write_bytes(b'changed')
            with self.assertRaises(ValueError):
                compare(rows, root)

    def test_archive_and_candidate_binding(self) -> None:
        """Reject a different source/setup or archive digest."""
        with tempfile.TemporaryDirectory() as directory:
            raw = archive(fixture(Path(directory)))
            for key in CANDIDATE:
                with self.assertRaises(ValueError):
                    inventory(raw, digest(raw), {**CANDIDATE, key: '0' * 64})
            with self.assertRaises(ValueError):
                inventory(raw, '0' * 64, CANDIDATE)


if __name__ == '__main__':
    unittest.main()
