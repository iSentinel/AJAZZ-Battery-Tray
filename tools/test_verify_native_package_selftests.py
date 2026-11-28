"""Synthetic regressions for exact native package evidence replay."""

from io import BytesIO
import json
import unittest
from unittest.mock import patch
import zipfile

from observe_native_package_selftests import CASES, CORPUS_SHA
from review_beta61_admission import normalized_plan
from review_normalized_package_set import PACKAGES
from validate_scoped_sbom_schema import digest
from verify_native_package_selftests import check_observation, replay, review

EXE = 'a' * 64


def sample(edition: str) -> dict:
    """Create a synthetic record; not an actual hosted observation."""
    return {
        'schema': 'native-package-selftests-v1',
        'edition': edition,
        'source_sha': normalized_plan()['source_sha'],
        'package_sha256': PACKAGES[edition][1],
        'executable_sha256': EXE,
        'corpus_sha256': CORPUS_SHA,
        'runner_os': 'Windows-test' if edition == 'windows' else 'macOS-test',
        'cases': [
            {'mode': mode, 'exit_code': code, 'expected_exit_code': code,
             'result': 'PASS'} for mode, code, _ in CASES[edition]
        ],
        'post_test_inventory': 'MATCH',
        'gui_launch': 'NOT_RUN',
        'physical_acceptance': 'NOT_VERIFIED',
        'release_admission': 'BLOCKED',
    }


def encoded(row: dict) -> bytes:
    """Serialize synthetic observations."""
    return json.dumps(row).encode()


def archive_with(files: dict[str, bytes]) -> bytes:
    """Construct a synthetic ZIP without touching disk."""
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return buffer.getvalue()


class NativeReplayTests(unittest.TestCase):
    """Check strict scope and artifact identity independently of execution."""

    def test_three_editions(self) -> None:
        """All reviewed cases are required in each edition."""
        for edition in CASES:
            row = sample(edition)
            self.assertEqual(check_observation(encoded(row), edition, EXE), row)
            row['cases'].pop()
            with self.assertRaises(ValueError):
                check_observation(encoded(row), edition, EXE)

    def test_identity_and_scope(self) -> None:
        """Reject changed identities, platform and elevated acceptance claims."""
        for key, value in (
            ('source_sha', 'b' * 40), ('package_sha256', 'b' * 64),
            ('executable_sha256', 'b' * 64), ('corpus_sha256', 'b' * 64),
            ('runner_os', 'Linux-test'), ('gui_launch', 'PASS'),
            ('physical_acceptance', 'PASS'), ('release_admission', 'PASS'),
        ):
            row = sample('windows')
            row[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                check_observation(encoded(row), 'windows', EXE)

    def test_exit_codes_and_duplicate_keys(self) -> None:
        """Reject wrong exits, booleans and duplicate JSON keys."""
        for code in (False, 0.0, 124, 125):
            row = sample('windows')
            row['cases'][0]['exit_code'] = code
            with self.subTest(code=code), self.assertRaises(ValueError):
                check_observation(encoded(row), 'windows', EXE)
        raw = encoded(sample('windows'))
        with self.assertRaises(ValueError):
            check_observation(raw[:-1] + b', "edition":"windows"}', 'windows', EXE)

    def test_pinned_archive(self) -> None:
        """Reject replacement archives and verify a synthetic matching pin."""
        raw = archive_with({'windows-selftests.json': encoded(sample('windows'))})
        with self.assertRaises(ValueError):
            replay(raw, 'windows', {'windows': EXE})
        with patch.dict('verify_native_package_selftests.OBSERVATIONS',
                        {'windows': (1, digest(raw), ('windows',))}):
            row = replay(raw, 'windows', {'windows': EXE})
        self.assertEqual(row['editions']['windows']['observation'], sample('windows'))

    def test_extra_member_and_missing_group(self) -> None:
        """Reject an extra ZIP member and incomplete evidence sets."""
        raw = archive_with({'windows-selftests.json': encoded(sample('windows')),
                            'extra.txt': b'extra'})
        with patch.dict('verify_native_package_selftests.OBSERVATIONS',
                        {'windows': (1, digest(raw), ('windows',))}):
            with self.assertRaises(ValueError):
                replay(raw, 'windows', {'windows': EXE})
        with self.assertRaises(ValueError):
            review({}, {})


if __name__ == '__main__':
    unittest.main()
