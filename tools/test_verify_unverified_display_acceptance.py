"""Synthetic checks for separately bound experimental display evidence."""

import json
import unittest

from verify_hardware_acceptance import template as hardware_template
from verify_unverified_display_acceptance import (CASES, PINNED_APP, PINNED_ARCHIVE,
                                                  PINNED_SOURCE, review, template)

IDENTITY = {'profile': 'windows-aj179', 'archive_sha256': PINNED_ARCHIVE,
            'source_sha': PINNED_SOURCE, 'app_sha256': PINNED_APP}


def encode(row: dict) -> bytes:
    """Serialize local synthetic evidence."""
    return json.dumps(row).encode()


class UnverifiedDisplayAcceptanceTests(unittest.TestCase):
    """Keep display qualification distinct from release and other devices."""

    def test_blank_and_wrong_identity(self) -> None:
        """Do not accept another source, profile or ordinary checklist."""
        row = template(IDENTITY)
        self.assertEqual(review(IDENTITY, encode(row))['counts']['NOT_RUN'], len(CASES))
        for key, value in (('source_sha', 'd' * 40), ('profile', 'windows-aj159'),
                           ('archive_sha256', 'e' * 64), ('app_sha256', 'f' * 64)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                review(dict(IDENTITY, **{key: value}), encode(row))
        with self.assertRaises(ValueError):
            review(IDENTITY, encode(hardware_template(IDENTITY)))

    def test_reported_pass_is_not_admission(self) -> None:
        """Require context and observations while keeping admission unverified."""
        row = template(IDENTITY)
        for key in CASES:
            row['cases'][key] = {'status': 'PASS', 'observation': 'Synthetic observation'}
        with self.assertRaises(ValueError):
            review(IDENTITY, encode(row))
        row['os_build'] = '10.0.26100'
        with self.assertRaises(ValueError):
            review(IDENTITY, encode(row))
        row['observed_version'] = row['expected_version']
        result = review(IDENTITY, encode(row))
        self.assertEqual(result['coverage'], 'COMPLETE_REPORTED')
        self.assertEqual(result['release_admission'], 'NOT_VERIFIED')
        row['cases'][CASES[0]]['observation'] = ''
        with self.assertRaises(ValueError):
            review(IDENTITY, encode(row))

    def test_runtime_binding(self) -> None:
        """Reject mismatched versions and legacy forms; blank is not evidence."""
        row = template(IDENTITY)
        self.assertEqual(review(IDENTITY, encode(row))['runtime_version_binding'], 'NOT_REPORTED')
        for version in ('0.3.0-beta.61', '0.3.0-beta.61+' + PINNED_SOURCE):
            row['observed_version'] = version
            with self.assertRaises(ValueError):
                review(IDENTITY, encode(row))
        row['observed_version'] = row['expected_version']
        self.assertEqual(review(IDENTITY, encode(row))['runtime_version_binding'], 'MATCH_REPORTED')
        row['schema'] = 'unverified-display-acceptance-v1'
        with self.assertRaises(ValueError):
            review(IDENTITY, encode(row))

    def test_reject_missing_cases_and_wrong_profile(self) -> None:
        """Require the exact case set and a supported APEX profile."""
        row = template(IDENTITY)
        row['cases'].pop(CASES[0])
        with self.assertRaises(ValueError):
            review(IDENTITY, encode(row))
        with self.assertRaises(ValueError):
            template(dict(IDENTITY, profile='windows-aula'))


if __name__ == '__main__':
    unittest.main()
