"""Validate the scoped Inno 6.7.1 message block, not its text provenance."""

import hashlib
import struct
import zlib

HEADER = b'Inno Setup Messages (6.5.0) (u)'.ljust(64, b'\0')
LANG_ID = b'!mlo!670'
COUNT = 281
OPTIONS_SIZE = 102
LIMIT = 1024 * 1024


def verify_messages(raw: bytes) -> dict:
    """Check exact framing, CRC, UTF-16 terminators and language record extent."""
    if not 80 + OPTIONS_SIZE < len(raw) <= LIMIT or raw[:64] != HEADER:
        raise ValueError('unexpected message block')
    count, total, complement, crc = struct.unpack_from('<IIII', raw, 64)
    if (count != COUNT or total ^ 0xffffffff != complement
            or total != len(raw) - OPTIONS_SIZE or total <= 80 or total % 2):
        raise ValueError('invalid message header')
    body, options = raw[80:total], raw[total:]
    if zlib.crc32(body) != crc or options[:8] != LANG_ID:
        raise ValueError('message CRC or language identifier differs')
    text = body.decode('utf-16le')
    if not text.endswith('\0') or len(text[:-1].split('\0')) != count:
        raise ValueError('message count or terminator differs')
    return {'count': count, 'total_size': total, 'crc32': f'{crc:08x}',
            'body_sha256': hashlib.sha256(body).hexdigest(),
            'language_options_bytes': len(options),
            'language_options_sha256': hashlib.sha256(options).hexdigest(),
            'structure': 'MATCH', 'message_semantics': 'NOT_VERIFIED',
            'language_options_semantics': 'NOT_VERIFIED'}
