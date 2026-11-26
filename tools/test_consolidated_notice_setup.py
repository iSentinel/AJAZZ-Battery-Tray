"""Keep exact original payload compilation separate from rebuilt release assets."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/test-consolidated-notice-setup.yml'


class ConsolidatedNoticeSetupTests(unittest.TestCase):
    """Review pinned native workflow source without claiming hosted execution."""

    def test_original_payload(self) -> None:
        """Require original archive, checkout and EXE identity rather than rebuild."""
        text = WORKFLOW.read_text()
        for item in ('ref: f939fea7fb422aa588649138d29a750ce62cd22a',
                     'actions/artifacts/15110510075/zip',
                     'e06bda2f95725a37f206cfbaffe6f3b333c735ea0a8e580fe092ccbfed340302',
                     '91f8eea23bd06d926fc2d665d3b69bda64da385cf0051cfeae7a0844a7ff9a6c',
                     'stage_local_inno674_payload.py', 'persist-credentials: false'):
            self.assertIn(item, text)
        self.assertNotIn('dotnet publish', text)

    def test_compiler_and_evidence_scope(self) -> None:
        """Require reviewed compiler and JSON-only output with no release command."""
        text = WORKFLOW.read_text()
        for item in ('Get-AuthenticodeSignature', 'gh release verify-asset',
                     'verify_inno674_components.py', 'stage_windows_notices.py',
                     'build_local_inno674_candidate.py', '--dry-run', '--compile',
                     'verify_windows_notice_transport.py', 'tray_launch =',
                     "release_admission = 'NOT_VERIFIED'"):
            self.assertIn(item, text)
        upload = text.split('name: Retain exact candidate evidence only', 1)[1]
        self.assertIn('archive: true', upload)
        self.assertNotIn('.exe', upload)
        self.assertNotIn('gh release create', text)
        self.assertNotIn('gh release upload', text)


    def test_upgrade_uses_the_clean_setup_and_retains_json(self) -> None:
        """Require upgrade/reinstall to use the same setup and notice evidence."""
        text = WORKFLOW.read_text()
        upgrade = text.index('name: Exercise exact setup upgrade and same-version reinstall')
        upload = text.index('name: Retain exact candidate evidence only')
        self.assertLess(text.index('name: Verify product notice lifecycle'), upgrade)
        self.assertLess(upgrade, upload)
        for item in ('Test-ProductNoticeUpgrade.ps1', '$clean.setup_sha256',
                     '$upgrade.setup_sha256', 'reinstall_restores_missing_notice',
                     'staged-evidence.json'):
            self.assertIn(item, text[upgrade:upload])
        for item in ('product-upgrade-lifecycle.json', 'product-upgrade-notices.json',
                     'product-reinstall-notices.json'):
            self.assertIn(item, text[upload:])


    def test_repeat_observation_keeps_inputs_and_qualifies_primary(self) -> None:
        """Keep repeat builds scoped and preserve the primary lifecycle input."""
        text = WORKFLOW.read_text()
        repeat = text.index('repeat-normalized')
        lifecycle = text.index('name: Verify product notice lifecycle')
        self.assertLess(repeat, lifecycle)
        for item in ('SetLastWriteTimeUtc', 'finally', '$fixedStamp.AddDays(1)',
                     'decode_setup0', 'location_records_sha256'):
            self.assertIn(item, text[repeat:lifecycle])
        uploaded = text.split('name: Retain exact candidate evidence only', 1)[1]
        self.assertIn('setup-repeat-observation.json', uploaded)


    def test_private_build_replay_verifies_the_actual_setup(self) -> None:
        """Require scoped binary comparison and independent payload hashes."""
        text = WORKFLOW.read_text()
        start = text.index('name: Check out private build tooling')
        upload = text.index('name: Retain exact candidate evidence only')
        self.assertLess(start, upload)
        for item in ('--reproducible --dry-run', '--reproducible --compile',
                     'primary != repeat', 'locations(second, payload, files)',
                     'file_hashes(payload, files)', 'script_header(first)'):
            self.assertIn(item, text[start:upload])
        self.assertIn('candidate-payload-replay.json', text[upload:])


if __name__ == '__main__':
    unittest.main()
