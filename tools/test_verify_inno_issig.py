"""Test strict ISSig parsing and actual OpenSSL verification on synthetic data."""

import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from verify_inno_issig import (
    ORDER, SPKI, der_integer, public_key, signature, verify_crypto, verify_one,
)

OPENSSL = shutil.which('openssl')
NAME = 'fixture.exe'
PAYLOAD = b'synthetic file, not an executable'
SHA = hashlib.sha256(PAYLOAD).hexdigest()


def record(key_id: str, r: int = 1, s: int = 2) -> str:
    """Build a synthetic v2 metadata record."""
    return (f'format issig-v2\nfile-name "{NAME}"\nfile-size {len(PAYLOAD)}\n'
            f'file-hash {SHA}\nfile-tag ""\nkey-id {key_id}\n'
            f'sig-r {r:064x}\nsig-s {s:064x}\n')


def scalar_pair(der: bytes) -> tuple[int, int]:
    """Decode a small OpenSSL-generated DER signature for the test fixture."""
    assert der[0] == 48 and der[1] == len(der) - 2
    assert der[2] == 2
    end = 4 + der[3]
    assert der[end] == 2 and end + 2 + der[end + 1] == len(der)
    return int.from_bytes(der[4:end], 'big'), int.from_bytes(der[end + 2:], 'big')


class ISSigTests(unittest.TestCase):
    """Reject malformed inputs and test real P-256 signature verification."""

    def test_canonical_scalars(self) -> None:
        """Reject zero and out-of-range scalars; preserve positive DER encoding."""
        self.assertEqual(der_integer(128), b'\x02\x02\x00\x80')
        for value in (0, -1, ORDER, ORDER + 1):
            with self.assertRaises(ValueError):
                der_integer(value)

    def test_metadata_and_format(self) -> None:
        """Reject changed metadata, duplicate records and unsupported versions."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixture.issig'
            valid = record('a' * 64)
            path.write_text(valid)
            self.assertEqual(signature(path, NAME, len(PAYLOAD), SHA)[0], 'a' * 64)
            for bad in (valid.replace('issig-v2', 'issig-v1'),
                        valid.replace('file-tag ""', 'file-tag "x"'),
                        valid.replace(NAME, 'other.exe'),
                        valid.replace(SHA, '0' * 64),
                        valid.replace('file-size ', 'file-size 0'),
                        valid + 'sig-r ' + '0' * 64 + '\n',
                        valid.rstrip('\n')):
                path.write_text(bad)
                with self.assertRaises(ValueError):
                    signature(path, NAME, len(PAYLOAD), SHA)

    def test_key_id_and_pin(self) -> None:
        """A matching hash pin cannot override an inconsistent key identifier."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'key'
            raw = ('format issig-public-key\nkey-id ' + '0' * 64 +
                   '\npublic-x ' + '1' * 64 + '\npublic-y ' + '2' * 64 + '\n')
            path.write_bytes(raw.encode())
            with self.assertRaises(ValueError):
                public_key(path, hashlib.sha256(raw.encode()).hexdigest())
            with self.assertRaises(ValueError):
                public_key(path, 'f' * 64)

    @unittest.skipUnless(OPENSSL, 'OpenSSL required for real signature verification')
    def test_native_signature_and_mutations(self) -> None:
        """Sign synthetic bytes, then verify and reject changed file/signature/key."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private, public = root / 'private.pem', root / 'public.der'
            subprocess.run([OPENSSL, 'ecparam', '-name', 'prime256v1', '-genkey',
                            '-noout', '-out', str(private)], check=True, timeout=10)
            subprocess.run([OPENSSL, 'pkey', '-in', str(private), '-pubout',
                            '-outform', 'DER', '-out', str(public)], check=True, timeout=10)
            spki = public.read_bytes()
            self.assertEqual(spki[:len(SPKI)], SPKI)
            xy = spki[len(SPKI):]
            key_id = hashlib.sha256(xy).hexdigest()
            sidecar, payload = root / 'fixture.issig', root / NAME
            payload.write_bytes(PAYLOAD)
            sidecar.write_text(record(key_id))
            _, msg, _ = signature(sidecar, NAME, len(PAYLOAD), SHA)
            (root / 'msg').write_bytes(msg)
            subprocess.run([OPENSSL, 'dgst', '-sha256', '-sign', str(private),
                            '-out', str(root / 'sig'), str(root / 'msg')], check=True, timeout=10)
            der = (root / 'sig').read_bytes()
            r, s = scalar_pair(der)
            sidecar.write_text(record(key_id, r, s))
            self.assertEqual(verify_one(OPENSSL, {key_id: spki}, payload, sidecar,
                                        NAME)['signature'], 'VALID_FOR_PINNED_KEY')
            with self.assertRaises(ValueError):
                verify_crypto(OPENSSL, spki, msg + b'x', der)
            with self.assertRaises(ValueError):
                verify_one(OPENSSL, {}, payload, sidecar, NAME)
            payload.write_bytes(PAYLOAD + b'x')
            with self.assertRaises(ValueError):
                verify_one(OPENSSL, {key_id: spki}, payload, sidecar, NAME)


if __name__ == '__main__':
    unittest.main()
