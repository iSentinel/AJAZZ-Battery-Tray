#!/usr/bin/env python3
"""Verify scoped ISSig-v2 signatures against explicitly pinned public keys."""

import argparse
import hashlib
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile

from compare_inno_compiler import NAMES, LIMIT
from run_offline_qa import write_json
from verify_installer_payload import file_digest

HEX = r'[0-9a-f]{64}'
ORDER = int('ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551', 16)
SPKI = bytes.fromhex('3059301306072a8648ce3d020106082a8648ce3d03010703420004')
KEYS = {
    'def01.ispublickey': '3b0b7e1e478c9ab327746a990512e2b245c9231e88a7fdd60d7874dd439db562',
    'def02.ispublickey': '32bea6bceb4ac7c4e6b3becdf3fb38de77378c5e76d494ab907d87cfab9e597b',
}
OFFICIAL = 'innosetup-6.7.1.exe'


def lines(path: Path, count: int, expected_sha: str | None = None) -> list[str]:
    """Read bounded ASCII records with exact line count and final newline."""
    digest = file_digest(path, 4096)
    if expected_sha is not None and digest != expected_sha:
        raise ValueError('record digest differs')
    with path.open('rb') as stream:
        raw = stream.read(4097)
    if len(raw) > 4096 or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('record changed')
    text = raw.decode('ascii').replace('\r\n', '\n')
    if '\r' in text or not text.endswith('\n'):
        raise ValueError('invalid line endings')
    result = text[:-1].split('\n')
    if len(result) != count:
        raise ValueError('invalid record length')
    return result


def field(line: str, label: str, pattern: str) -> str:
    """Parse one exact field without duplicate or extra records."""
    match = re.fullmatch(re.escape(label) + ' (' + pattern + ')', line)
    if match is None:
        raise ValueError('invalid record field')
    return match[1]


def public_key(path: Path, expected_sha: str) -> tuple[str, bytes]:
    """Validate key identifier and construct a P-256 SPKI DER public key."""
    version, key, x, y = lines(path, 4, expected_sha)
    if version != 'format issig-public-key':
        raise ValueError('unsupported public key format')
    key_id = field(key, 'key-id', HEX)
    xy = bytes.fromhex(field(x, 'public-x', HEX) + field(y, 'public-y', HEX))
    if hashlib.sha256(xy).hexdigest() != key_id:
        raise ValueError('key identifier differs')
    return key_id, SPKI + xy


def der_integer(value: int) -> bytes:
    """Encode an ECDSA scalar as a canonical positive DER integer."""
    if not 0 < value < ORDER:
        raise ValueError('invalid ECDSA scalar')
    raw = value.to_bytes((value.bit_length() + 7) // 8, 'big')
    if raw[0] & 128:
        raw = b'\0' + raw
    return bytes((2, len(raw))) + raw


def signature(path: Path, name: str, size: int, sha: str) -> tuple[str, bytes, bytes]:
    """Bind the signed v2 empty-tag record to actual file name, size and digest."""
    v, n, s, h, tag, k, r, z = lines(path, 8)
    if v != 'format issig-v2' or tag != 'file-tag ""':
        raise ValueError('unsupported signature format')
    if (n != 'file-name "' + name + '"' or
            int(field(s, 'file-size', r'0|[1-9][0-9]{0,15}')) != size or
            field(h, 'file-hash', HEX) != sha):
        raise ValueError('signed file metadata differs')
    key = field(k, 'key-id', HEX)
    scalars = der_integer(int(field(r, 'sig-r', HEX), 16))
    scalars += der_integer(int(field(z, 'sig-s', HEX), 16))
    encoded = name.encode('ascii')
    message = struct.pack('<I', len(encoded)) + encoded + struct.pack('<Iq', 0, size)
    return key, message + bytes.fromhex(sha), bytes((48, len(scalars))) + scalars


def verify_crypto(openssl: str, key: bytes, message: bytes, sig: bytes) -> None:
    """Delegate signature verification to OpenSSL, fail on any nonzero result."""
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for name, data in (('key.der', key), ('msg', message), ('sig', sig)):
            (root / name).write_bytes(data)
        result = subprocess.run(
            [openssl, 'dgst', '-sha256', '-keyform', 'DER', '-verify',
             str(root / 'key.der'), '-signature', str(root / 'sig'), str(root / 'msg')],
            capture_output=True, timeout=10, check=False)
        if result.returncode != 0:
            raise ValueError('signature verification failed')


def verify_one(openssl: str, keys: dict, path: Path, sidecar: Path, name: str) -> dict:
    """Verify a single immutable local file and sidecar against allowed keys."""
    sha = file_digest(path, LIMIT)
    size = path.stat().st_size
    key, message, sig = signature(sidecar, name, size, sha)
    if key not in keys:
        raise ValueError('unknown signing key')
    verify_crypto(openssl, keys[key], message, sig)
    return {'file': name, 'sha256': sha, 'bytes': size, 'key_id': key,
            'signature': 'VALID_FOR_PINNED_KEY'}


def main(argv: list[str] | None = None) -> int:
    """Verify official package and exact seventeen extracted component sidecars."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('official', 'official-signature', 'official-dir', 'key-dir', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        openssl = shutil.which('openssl')
        if not openssl:
            raise ValueError('OpenSSL unavailable')
        keys = dict(public_key(args.key_dir / name, sha) for name, sha in KEYS.items())
        results = [verify_one(openssl, keys, args.official, args.official_signature, OFFICIAL)]
        for name in sorted(n for n in NAMES if n.endswith('.issig')):
            results.append(verify_one(openssl, keys, args.official_dir / name[:-6],
                                      args.official_dir / name, name[:-6]))
        write_json(args.output, {'schema': 1, 'results': results,
                   'publisher_key_trust': 'NOT_VERIFIED',
                   'authenticode_trust': 'NOT_VERIFIED',
                   'extraction_provenance': 'CALLER_REVIEW_REQUIRED',
                   'release_admission': 'NOT_VERIFIED'})
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        print('FAIL: scoped ISSig verification', file=sys.stderr)
        return 2
    print('PASS: 18 ISSig signatures for pinned keys; publisher trust not verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
