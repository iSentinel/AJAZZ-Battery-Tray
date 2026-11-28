"""Test exact ordered location inventory for the proposed compiler."""

import unittest

from compare_inno_loader import digest
from verify_inno674_solid_payload import locations, NOTICES
from verify_inno_setup_data import LOCATION


class Inno674SolidTests(unittest.TestCase):
    """Reject extra bytes, offsets and unexpected file digests."""

    def test_location_table(self) -> None:
        """Two synthetic records must match all scoped fields."""
        payload = b'zlb\x1a1234'
        files = (('app', 3, digest(b'app')), ('notice', 1, digest(b'n')))
        raw = b''.join(LOCATION.pack(0, 0, 0, sub, size, 4, bytes.fromhex(sha),
                                    0, 0, 0, flags)
                       for (_, size, sha), sub, flags in zip(files, (0, 3), (20, 16)))
        locations(raw, payload, files)
        for bad in (raw + b'x', raw[:-1] + b'\x14', bytes(len(raw))):
            with self.assertRaises(ValueError):
                locations(bad, payload, files)

    def test_notice_order(self) -> None:
        """The ten distinct source paths include the manifest."""
        self.assertEqual(len(set(NOTICES)), 10)
        self.assertEqual(NOTICES[-1], 'manifest.json')


if __name__ == '__main__':
    unittest.main()
