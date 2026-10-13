import copy
import importlib.util
import json
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('xi_glyph_sha256', ROOT / 'xi_glyph_sha256.py')
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)
FIXTURE = json.loads((ROOT / 'fixtures.json').read_text(encoding='utf-8'))


class ClosureTests(unittest.TestCase):
    def test_exact_alphabet_and_fixture(self):
        self.assertEqual(codec.GLYPHS, '∴Ω⧂⋈Ξ⟐⊚◇✦⟁∵☉◬⌬⧉∞')
        self.assertEqual(len(set(codec.GLYPHS)), 16)
        for digit, symbol in FIXTURE['alphabet'].items():
            self.assertEqual(codec.encode(digit * 64).replace('\n', ''), symbol * 64)
        self.assertEqual(codec.decode(FIXTURE['deepseek']['glyph_tile']), FIXTURE['deepseek']['hex_sha256'])
        self.assertEqual(codec.encode(FIXTURE['deepseek']['hex_sha256']), FIXTURE['deepseek']['glyph_tile'])

    def test_seeded_roundtrips(self):
        rng = random.Random(256)
        for _ in range(256):
            digest = f'{rng.getrandbits(256):064x}'
            tile = codec.encode(digest)
            self.assertEqual([len(row) for row in tile.splitlines()], [8] * 8)
            self.assertEqual(codec.decode(tile), digest)
            self.assertEqual(codec.decode(' \t' + tile.replace('\n', '\r\n') + '\n'), digest)

    def test_malformed_and_lookalikes_rejected(self):
        valid = codec.encode('0' * 64)
        for bad in ('', '0' * 63, 'g' * 64, '0' * 65, None):
            with self.assertRaises(codec.CodecError): codec.encode(bad)
        for bad in (valid + '∴', valid[:-1], valid.replace('∴', '⊙', 1), valid.replace('∴', '\u200b', 1), valid.replace('∴', '\ufe0f', 1), None):
            with self.assertRaises(codec.CodecError): codec.decode(bad)
        self.assertEqual(codec.parse_expected(' \n' + 'A' * 64), 'a' * 64)

    def test_known_sha256_vectors_streaming(self):
        for vector in FIXTURE['vectors']:
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'private-input.bin'
                path.write_bytes(vector['utf8'].encode())
                self.assertEqual(codec.hash_file(path, chunk_size=1), vector['hex_sha256'])
                receipt = codec.verify_file(path, codec.encode(vector['hex_sha256']))
                self.assertEqual(receipt['file_verification'], 'match')
                self.assertNotIn('private-input', json.dumps(receipt))

    def test_receipt_cross_fields_and_privacy(self):
        receipt = codec.make_receipt(FIXTURE['deepseek']['hex_sha256'])
        self.assertEqual(receipt['file_verification'], 'not_performed')
        self.assertTrue(codec.validate_receipt(receipt))
        bad = copy.deepcopy(receipt); bad['glyph_tile'] = codec.encode('0' * 64)
        with self.assertRaises(codec.CodecError): codec.validate_receipt(bad)
        bad = copy.deepcopy(receipt); bad['file_name'] = '/private/path'
        with self.assertRaises(codec.CodecError): codec.validate_receipt(bad)
        with self.assertRaises(codec.CodecError): codec.make_receipt('0' * 64, 'match', '1' * 64)
        with self.assertRaises(codec.CodecError): codec.make_receipt('0' * 64, 'hashed', '0' * 64)

    def test_cli_exit_states_and_stdin(self):
        cli = [sys.executable, str(ROOT / 'xi_glyph_sha256.py')]
        completed = subprocess.run(cli + ['decode', '-'], input=FIXTURE['deepseek']['glyph_tile'], text=True, capture_output=True)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout.strip(), FIXTURE['deepseek']['hex_sha256'])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'secret.bin'; path.write_bytes(b'abc')
            expected = FIXTURE['vectors'][1]['hex_sha256']
            for digest, exit_code, state in ((expected, 0, 'match'), ('0' * 64, 1, 'mismatch')):
                completed = subprocess.run(cli + ['verify', str(path), '--against', digest], text=True, capture_output=True)
                self.assertEqual(completed.returncode, exit_code)
                self.assertEqual(json.loads(completed.stdout)['file_verification'], state)
                self.assertNotIn(str(path), completed.stdout)
            completed = subprocess.run(cli + ['verify', str(path), '--against', 'bad'], text=True, capture_output=True)
            self.assertEqual(completed.returncode, 2)


if __name__ == '__main__': unittest.main()
