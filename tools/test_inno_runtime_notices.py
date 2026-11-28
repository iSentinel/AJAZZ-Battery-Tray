"""Ensure scoped upstream runtime notice copies remain byte-exact."""

import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
NOTICE_DIR = ROOT / 'docs' / 'third-party' / 'inno-6.7.1'
PINS = {
    'Inno-Setup-LICENSE.txt': '2e5346868c2a18434489824e11d65c3031620f792fefc415d05f19cd441abf5c',
    'Pascal-Script-LICENSE.txt': 'a08799bb2385a3af99a9bbb7c746d0ad9ac7dd07be0fb1473f2f4d1dc3e11bd1',
    'LZMA-SDK-7zC.txt': 'e5cc6089348474fc82631365932b1aa09df26a8cfc9f320bbb2509a7b3fc7a0c',
}


class InnoNoticeTests(unittest.TestCase):
    """Require exact upstream bytes and visible repository acknowledgment."""

    def test_pinned_notices(self) -> None:
        """Reject missing, replaced or line-ending-converted notices."""
        for name, expected in PINS.items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((NOTICE_DIR / name).read_bytes()).hexdigest(),
                                 expected)

    def test_attribution(self) -> None:
        """Keep the visible upstream name and link in release documentation sources."""
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        self.assertIn('[RemObjects Pascal Script](https://github.com/remobjects/pascalscript)', readme)
        self.assertIn('docs/INNO_RUNTIME_NOTICES.md', readme)


if __name__ == '__main__':
    unittest.main()
