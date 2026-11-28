"""Test local compiler preflight and execution boundaries."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from build_local_inno674_candidate import (
    FIXED_STAMP_NS, ICONS, NAMES, OUTPUTS, arguments, fresh, main, normalized_timestamps,
)


class LocalBuildTests(unittest.TestCase):
    """Never overwrite output or execute compilation by default."""

    def test_existing_output(self) -> None:
        """Existing setup or evidence blocks compilation."""
        with TemporaryDirectory() as folder:
            root = Path(folder)
            fresh(root)
            for name in OUTPUTS:
                path = root / name
                path.touch()
                with self.assertRaises(ValueError):
                    fresh(root)
                path.unlink()

    def test_default_dry_run(self) -> None:
        """Only explicit compile may invoke the compiler."""
        with TemporaryDirectory() as folder:
            args = ['--compiler', folder, '--notices', folder, '--output', folder]
            with patch('build_local_inno674_candidate.snapshot', return_value={}), \
                    patch('build_local_inno674_candidate.compile_candidate') as run, \
                    patch('build_local_inno674_candidate.normalized_timestamps') as stamps:
                self.assertEqual(main(args + ['--reproducible']), 0)
                stamps.assert_not_called()
                run.assert_not_called()
                self.assertEqual(main(args + ['--compile']), 0)
                run.assert_called_once()

    def test_normalization_restores_all_inputs_on_failure(self) -> None:
        """Test the exact stamped paths and cleanup after a compiler failure."""
        with TemporaryDirectory() as folder:
            root = Path(folder)
            notices = root / 'notices'
            assets = root / 'src/AjazzBatteryTray/Assets'
            paths = [root / 'dist/app/AJAZZBatteryTray.exe']
            paths.extend(assets / name for name in ICONS)
            paths.extend(notices / name for name in sorted(NAMES))
            for path in paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'payload')
                os.utime(path, ns=(1600000000 * 10**9, 1600000001 * 10**9))
            original = [path.stat().st_mtime_ns for path in paths]
            with self.assertRaisesRegex(RuntimeError, 'compiler failed'):
                with normalized_timestamps(root, notices):
                    self.assertTrue(all(path.stat().st_mtime_ns == FIXED_STAMP_NS for path in paths))
                    raise RuntimeError('compiler failed')
            self.assertEqual([path.stat().st_mtime_ns for path in paths], original)
            self.assertTrue(all(path.read_bytes() == b'payload' for path in paths))

    def test_arguments(self) -> None:
        """Use normal basename, no version override and no shell."""
        root = Path('path with spaces')
        source = root / 'detached source'
        args = arguments(root, root, root, source)
        self.assertEqual(args[-1], str(source / 'installer/AJAZZBatteryTray.iss'))
        self.assertEqual(args[0], str(root / 'ISCC.exe'))
        self.assertIn('/DProductionNoticeCandidate=1', args)
        self.assertFalse(any(arg.startswith(('/F', '/DAppVersion')) for arg in args))


if __name__ == '__main__':
    unittest.main()
