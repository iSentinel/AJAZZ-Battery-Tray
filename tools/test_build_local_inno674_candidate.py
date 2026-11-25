"""Test local compiler preflight and execution boundaries."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from build_local_inno674_candidate import OUTPUTS, arguments, fresh, main


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
                    patch('build_local_inno674_candidate.compile_candidate') as run:
                self.assertEqual(main(args), 0)
                run.assert_not_called()
                self.assertEqual(main(args + ['--compile']), 0)
                run.assert_called_once()

    def test_arguments(self) -> None:
        """Use normal basename, no version override and no shell."""
        root = Path('path with spaces')
        args = arguments(root, root, root)
        self.assertEqual(args[0], str(root / 'ISCC.exe'))
        self.assertIn('/DProductionNoticeCandidate=1', args)
        self.assertFalse(any(arg.startswith(('/F', '/DAppVersion')) for arg in args))


if __name__ == '__main__':
    unittest.main()
