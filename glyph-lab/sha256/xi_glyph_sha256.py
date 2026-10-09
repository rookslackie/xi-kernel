"""Xi glyph-SHA v1: dependency-free codec and streaming SHA-256 file verifier."""
from __future__ import annotations
import argparse
import hashlib
import hmac
import json
import os
import re
import sys
from pathlib import Path

DIALECT = 'xi.glyph-sha256.v1'
RECEIPT_SCHEMA = 'xi.glyph-sha256.receipt.v1'
HEX = '0123456789abcdef'
GLYPHS = '∴Ω⧂⋈Ξ⟐⊚◇✦⟁∵☉◬⌬⧉∞'
REVERSE = dict(zip(GLYPHS, HEX))
FIELDS = {'schema', 'dialect', 'algorithm', 'hex_sha256', 'glyph_tile',
          'encoding_verified', 'file_verification', 'expected_sha256'}
STATES = {'not_performed', 'hashed', 'match', 'mismatch'}
ASCII_WS = ' \t\r\n'


class CodecError(ValueError):
    """Malformed or internally contradictory representation."""


def normalize_hex(value: str) -> str:
    if not isinstance(value, str):
        raise CodecError('Expected a SHA-256 string.')
    value = value.strip(ASCII_WS)
    if not re.fullmatch(r'[0-9a-fA-F]{64}', value):
        raise CodecError('SHA-256 must contain exactly 64 hexadecimal digits.')
    return value.lower()


def encode(value: str) -> str:
    symbols = ''.join(GLYPHS[HEX.index(digit)] for digit in normalize_hex(value))
    return '\n'.join(symbols[i:i + 8] for i in range(0, 64, 8))


def decode(value: str) -> str:
    if not isinstance(value, str):
        raise CodecError('Expected a glyph tile string.')
    symbols = ''.join(ch for ch in value if ch not in ASCII_WS)
    if len(symbols) != 64:
        raise CodecError('A SHA-256 tile must contain exactly 64 glyphs.')
    digits = []
    for i, glyph in enumerate(symbols):
        if glyph not in REVERSE:
            raise CodecError(f'Unknown glyph at position {i + 1}: U+{ord(glyph):04X}.')
        digits.append(REVERSE[glyph])
    return ''.join(digits)


def parse_expected(value: str) -> str:
    if not isinstance(value, str):
        raise CodecError('Expected a SHA-256 or glyph tile.')
    return normalize_hex(value) if re.fullmatch(r'[0-9a-fA-F]+', value.strip(ASCII_WS)) else decode(value)


def make_receipt(value: str, file_verification: str = 'not_performed', expected: str | None = None) -> dict:
    digest = normalize_hex(value)
    receipt = {
        'schema': RECEIPT_SCHEMA, 'dialect': DIALECT, 'algorithm': 'SHA-256',
        'hex_sha256': digest, 'glyph_tile': encode(digest), 'encoding_verified': True,
        'file_verification': file_verification,
        'expected_sha256': None if expected is None else normalize_hex(expected),
    }
    validate_receipt(receipt)
    return receipt


def validate_receipt(receipt: dict) -> bool:
    if not isinstance(receipt, dict) or set(receipt) != FIELDS:
        raise CodecError('Receipt fields must match the public v1 schema exactly.')
    if (receipt['schema'], receipt['dialect'], receipt['algorithm']) != (RECEIPT_SCHEMA, DIALECT, 'SHA-256'):
        raise CodecError('Unsupported receipt schema, dialect, or algorithm.')
    digest = normalize_hex(receipt['hex_sha256'])
    if digest != receipt['hex_sha256'] or receipt['glyph_tile'] != encode(digest) or decode(receipt['glyph_tile']) != digest or receipt['encoding_verified'] is not True:
        raise CodecError('Receipt hex and canonical tile must agree.')
    state = receipt['file_verification']
    if not isinstance(state, str) or state not in STATES:
        raise CodecError('Unknown file verification state.')
    comparing = state in {'match', 'mismatch'}
    if not comparing and receipt['expected_sha256'] is not None:
        raise CodecError('An unperformed comparison cannot carry an expected digest.')
    if comparing:
        expected = normalize_hex(receipt['expected_sha256'])
        if expected != receipt['expected_sha256'] or hmac.compare_digest(digest, expected) != (state == 'match'):
            raise CodecError('File comparison state contradicts its digests.')
    return True


def hash_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    if not isinstance(chunk_size, int) or isinstance(chunk_size, bool) or chunk_size < 1:
        raise CodecError('Chunk size must be a positive integer.')
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        before = os.fstat(stream.fileno())
        for chunk in iter(lambda: stream.read(chunk_size), b''):
            digest.update(chunk)
        after = os.fstat(stream.fileno())
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise OSError('File changed while hashing; retry from a stable snapshot.')
    return digest.hexdigest()


def verify_file(path: str | Path, expected: str) -> dict:
    expected_hex = parse_expected(expected)
    actual = hash_file(path)
    return make_receipt(actual, 'match' if hmac.compare_digest(actual, expected_hex) else 'mismatch', expected_hex)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('encode', 'decode'):
        command = commands.add_parser(name)
        command.add_argument('value', help='Hex digest / tile, or - to read UTF-8 stdin')
    hashing = commands.add_parser('hash')
    hashing.add_argument('file', type=Path)
    hashing.add_argument('--format', choices=('hex', 'tile', 'receipt'), default='hex')
    verify = commands.add_parser('verify')
    verify.add_argument('file', type=Path)
    expectation = verify.add_mutually_exclusive_group(required=True)
    expectation.add_argument('--against', help='Trusted hex digest or glyph tile')
    expectation.add_argument('--against-file', type=Path, help='UTF-8 file containing a trusted hex digest or tile')
    args = parser.parse_args(argv)
    try:
        if args.command in ('encode', 'decode'):
            value = sys.stdin.read() if args.value == '-' else args.value
            print(encode(value) if args.command == 'encode' else decode(value))
            return 0
        if args.command == 'hash':
            digest = hash_file(args.file)
            if args.format == 'receipt':
                print(json.dumps(make_receipt(digest, 'hashed'), ensure_ascii=False, indent=2))
            else:
                print(encode(digest) if args.format == 'tile' else digest)
            return 0
        expected = args.against if args.against is not None else args.against_file.read_text(encoding='utf-8')
        receipt = verify_file(args.file, expected)
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0 if receipt['file_verification'] == 'match' else 1
    except (CodecError, OSError) as error:
        print(f'Glyph-SHA: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
