"""Guard independent hardware checklist profiles and artifact identities."""

import io
import json
import unittest
from unittest.mock import patch
import zipfile

from verify_hardware_acceptance import candidate, digest, members, review, template


def encode(row: dict) -> bytes:
    """Serialize a synthetic checklist."""
    return json.dumps(row).encode()


class HardwareAcceptanceTests(unittest.TestCase):
    """Reject mixed devices, stale archives and incomplete observations."""

    def test_profile_isolation(self) -> None:
        """AULA results do not satisfy the AJ179 or AJ159 profiles."""
        identity = {'profile': 'windows-aula', 'archive_sha256': 'a' * 64}
        row = template(identity)
        self.assertEqual(set(row['cases']), {'W14'})
        self.assertEqual(review(identity, encode(row))['counts']['NOT_RUN'], 1)
        for profile in ('windows-aj179', 'windows-aj159', 'universal', 'high-sierra'):
            with self.assertRaises(ValueError):
                review(dict(identity, profile=profile), encode(row))

    def test_reported_not_verified(self) -> None:
        """Even a completed self-report cannot approve release."""
        identity = {'profile': 'windows-aula'}
        row = template(identity)
        row['cases']['W14'] = {'status': 'PASS', 'observation': 'Synthetic observation'}
        with self.assertRaises(ValueError):
            review(identity, encode(row))
        row.update(os_build='10.0.26100', device_model='AJ179 APEX')
        with self.assertRaises(ValueError):
            review(identity, encode(row))
        row['device_model'] = 'AULA L99'
        result = review(identity, encode(row))
        self.assertEqual(result['coverage'], 'COMPLETE_REPORTED')
        self.assertEqual(result['release_admission'], 'NOT_VERIFIED')

    def test_archive_identity(self) -> None:
        """Check archive hash before invoking any inventory parser."""
        raw = b'synthetic'
        with patch('verify_hardware_acceptance.windows', return_value={}) as parse:
            with self.assertRaises(ValueError):
                candidate(raw, 'a' * 64, 'b' * 40, 'windows-aj179')
            parse.assert_not_called()
            candidate(raw, digest(raw), 'b' * 40, 'windows-aj179')
            parse.assert_called_once()

    def test_exact_members(self) -> None:
        """Do not accept extra files in outer artifact archives."""
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w') as archive:
            archive.writestr('app', b'one')
            archive.writestr('extra', b'two')
        with self.assertRaises(ValueError):
            members(out.getvalue(), {'app'})


if __name__ == '__main__':
    unittest.main()
