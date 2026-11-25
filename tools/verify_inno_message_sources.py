"""Compare scoped English Inno message bytes with pinned compiler inputs."""

import re
import struct

from compare_inno_loader import digest
from verify_inno_messages import COUNT, LANG_ID, OPTIONS_SIZE, verify_messages

ISL_SHA = '42a5f6f7dbbddf26cc278f67db5d894235ce1d126a6856702e31bd02023a1316'
IDS_SHA = '1313988fb59528672bd2f160ff42ce83b1d56eb8026052c14265445e7e2ed550'
SCRIPT_SHA = '668ff74c3c55db0cd8de544d30bac23497ad6e7a38aaf6da77016c78de2b2a65'
MAX_SOURCE = 128 * 1024


def ordered_ids(raw: bytes) -> list[str]:
    """Read the exact scoped Pascal enum, rejecting duplicates and malformed IDs."""
    if len(raw) > MAX_SOURCE:
        raise ValueError('message ID source exceeds limit')
    text = raw.decode('utf-8-sig')
    match = re.search(r'TSetupMessageID\s*=\s*\((.*?)\);', text, re.S)
    if not match:
        raise ValueError('missing message ID enumeration')
    ids = [name.strip() for name in match.group(1).split(',')]
    if (len(ids) != COUNT or len(set(ids)) != COUNT
            or any(not re.fullmatch(r'msg[A-Za-z0-9]+', name) for name in ids)):
        raise ValueError('unexpected message ID enumeration')
    return [name[3:] for name in ids]


def english_messages(raw: bytes) -> dict[str, str]:
    """Read the pinned ISL Messages section and documented newline expansion."""
    if len(raw) > MAX_SOURCE:
        raise ValueError('message source exceeds limit')
    values, active = {}, False
    for line in raw.decode('utf-8-sig').splitlines():
        if line.startswith('['):
            active = line == '[Messages]'
        elif active and line.strip() and not line.lstrip().startswith(';'):
            key, sep, value = line.partition('=')
            if not sep or not key or key in values:
                raise ValueError('invalid or duplicate message')
            values[key] = value.replace('%n', '\r\n')
    if len(values) != COUNT:
        raise ValueError('unexpected English message count')
    return values


def expected_body(isl: bytes, ids: bytes) -> bytes:
    """Serialize all source strings in exact compiler enum order."""
    keys, values = ordered_ids(ids), english_messages(isl)
    if set(keys) != set(values):
        raise ValueError('message keys differ from enum')
    return ''.join(values[key] + '\0' for key in keys).encode('utf-16le')


def expected_options() -> bytes:
    """Reconstruct the reviewed modern English installer appearance record."""
    font = 'Segoe UI'.encode('utf-16le').ljust(64, b'\0')
    return LANG_ID + font + struct.pack('<7iBB', 9, 7, 15, 120, 120,
                                        0x1fffffff, 0x1fffffff, 0, 0x22)


def compare_content(raw: bytes, isl: bytes, ids: bytes) -> dict:
    """Check exact body and options, without inferring script execution."""
    result = verify_messages(raw)
    total = result['total_size']
    if raw[80:total] != expected_body(isl, ids):
        raise ValueError('message content differs from source')
    if len(raw[total:]) != OPTIONS_SIZE or raw[total:] != expected_options():
        raise ValueError('language options differ from reviewed defaults')
    return {**result, 'message_semantics': 'MATCH_PINNED_ENGLISH_TEXT',
            'language_options_semantics': 'MATCH_REVIEWED_DEFAULTS'}


def compare_sources(raw: bytes, isl: bytes, ids: bytes, script: bytes) -> dict:
    """Require exact reviewed source inputs before comparing output bytes."""
    if [digest(x) for x in (isl, ids, script)] != [ISL_SHA, IDS_SHA, SCRIPT_SHA]:
        raise ValueError('message source digest differs')
    result = compare_content(raw, isl, ids)
    return {**result, 'default_isl_sha256': ISL_SHA, 'message_ids_sha256': IDS_SHA,
            'installer_script_sha256': SCRIPT_SHA,
            'compiled_script': 'NOT_VERIFIED', 'release_admission': 'NOT_VERIFIED'}
