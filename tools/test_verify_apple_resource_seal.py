"""Synthetic checks for scoped Apple ad-hoc integrity evidence."""

import hashlib
import plistlib
import struct
import unittest

from inventory_dotnet_bundle import BundleError
from verify_apple_resource_seal import CMS, REQ, directory, resource_seal, superblob, verify_slice

IDENT = 'com.example.test'
PLIST = b'info'
SEAL = b'resources'


def fixture() -> bytes:
    """Construct one signed-range fixture with two pages and three special slots."""
    limit = 4200
    name = IDENT.encode() + b'\0'
    offset = 88 + len(name) + 96
    size = offset + 64
    length = 36 + size + len(REQ) + len(CMS)
    raw = bytearray(limit)
    struct.pack_into('<8I', raw, 0, 0xfeedfacf, 0x01000007, 0, 2, 1, 16, 0, 0)
    struct.pack_into('<4I', raw, 32, 0x1d, 16, limit, length + 16)
    cd = bytearray(size)
    struct.pack_into('>9I', cd, 0, 0xfade0c02, size, 0x20400, 2, offset, 88, 3, 2, limit)
    cd[36:40] = bytes((32, 2, 0, 12))
    cd[88:88 + len(name)] = name
    for i, item in enumerate((PLIST, REQ, SEAL), 1):
        cd[offset-i*32:offset-(i-1)*32] = hashlib.sha256(item).digest()
    for i in range(2):
        cd[offset+i*32:offset+(i+1)*32] = hashlib.sha256(raw[i*4096:(i+1)*4096]).digest()
    region = struct.pack('>9I', 0xfade0cc0, length, 3, 0, 36, 2, 36+size,
                         0x10000, 36+size+len(REQ))
    return bytes(raw) + region + bytes(cd) + REQ + CMS + bytes(16)


def seal_fixture(raw: bytes) -> bytes:
    """Build exact dual-hash resource entries for a synthetic icon."""
    return plistlib.dumps({'files': {'Resources/icon': hashlib.sha1(raw).digest()},
                           'files2': {'Resources/icon': {'hash2': hashlib.sha256(raw).digest()}},
                           'rules': {}, 'rules2': {}})


class SealTests(unittest.TestCase):
    """Fail closed on altered covered bytes and unsupported signature format."""

    def test_resource_hashes(self) -> None:
        """Verify both hashes; reject modified or missing resources."""
        data = seal_fixture(b'icon')
        self.assertEqual(resource_seal(data, {'Resources/icon': b'icon'}), 1)
        for items in ({}, {'Resources/icon': b'changed'}, {'Resources/extra': b'icon'}):
            with self.assertRaises(BundleError):
                resource_seal(data, items)

    def test_pages_and_slots(self) -> None:
        """Check partial final page and explicit ad-hoc non-trust status."""
        report = verify_slice(fixture(), IDENT, PLIST, SEAL)
        self.assertEqual(report['code_pages'], 2)
        self.assertEqual(report['special_slots'], 3)
        self.assertEqual(report['signature_type'], 'AD_HOC_EMPTY_CMS')

    def test_page_mutation(self) -> None:
        """Reject tampering in either full or partial covered page."""
        for offset in (100, 4199):
            raw = bytearray(fixture())
            raw[offset] ^= 1
            with self.assertRaises(BundleError):
                verify_slice(bytes(raw), IDENT, PLIST, SEAL)

    def test_special_slot_mutation(self) -> None:
        """Reject changed plist, seal or identifier independently."""
        for identifier, plist, seal in ((IDENT, b'bad', SEAL), (IDENT, PLIST, b'bad'),
                                        ('com.example.other', PLIST, SEAL)):
            with self.assertRaises(BundleError):
                verify_slice(fixture(), identifier, plist, seal)

    def test_superblob_mutation(self) -> None:
        """Reject duplicate slots, overlapping blobs and nonzero padding."""
        for offset, value in ((20, 0), (24, 36), (len(fixture()) - 4200 - 4, 1)):
            raw = bytearray(fixture()[4200:])
            struct.pack_into('>I', raw, offset, value)
            with self.assertRaises(BundleError):
                superblob(bytes(raw))

    def test_directory_scope(self) -> None:
        """Reject non-ad-hoc flags, unexpected algorithms and wrong limits."""
        cd = superblob(fixture()[4200:])[0]
        for offset in (15, 37):
            raw = bytearray(cd)
            raw[offset] ^= 1
            with self.assertRaises(BundleError):
                directory(bytes(raw), 4200, IDENT)
        with self.assertRaises(BundleError):
            directory(cd, 4199, IDENT)


if __name__ == '__main__':
    unittest.main()
