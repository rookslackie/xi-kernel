import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { ALPHABET, encode, decode, parseExpected, hashBytes, makeReceipt, validateReceipt } from '../glyph-sha256.mjs';
const fixture = JSON.parse(readFileSync(new URL('../fixtures.json', import.meta.url), 'utf8'));

test('exact alphabet and all sixteen nibble closures', () => {
  assert.equal(new Set(ALPHABET).size, 16);
  for (const [hex, glyph] of Object.entries(fixture.alphabet)) {
    assert.equal(encode(hex.repeat(64)).replaceAll('\n', ''), glyph.repeat(64));
  }
});
test('DeepSeek tile exactly preserves the supplied digest and layout', () => {
  assert.equal(decode(fixture.deepseek.glyph_tile), fixture.deepseek.hex_sha256);
  assert.equal(encode(fixture.deepseek.hex_sha256), fixture.deepseek.glyph_tile);
});
test('raw byte SHA-256 known vectors, offset views, and file comparison states', async () => {
  for (const vector of fixture.vectors) {
    const bytes = new TextEncoder().encode(vector.utf8);
    const receipt = await hashBytes(bytes, encode(vector.hex_sha256));
    assert.equal(receipt.hex_sha256, vector.hex_sha256);
    assert.equal(receipt.file_verification, 'match');
    assert.equal(validateReceipt(receipt), true);
  }
  const bytes = new Uint8Array([0, 97, 98, 99, 0]);
  assert.equal((await hashBytes(bytes.subarray(1, 4))).hex_sha256, fixture.vectors[1].hex_sha256);
  assert.equal((await hashBytes(new TextEncoder().encode('abc'), '0'.repeat(64))).file_verification, 'mismatch');
});
test('strict Unicode boundaries and ASCII-only layout whitespace', () => {
  const tile = fixture.deepseek.glyph_tile;
  assert.equal(decode('\t' + tile.replaceAll('\n', '\r\n') + ' '), fixture.deepseek.hex_sha256);
  for (const invalid of ['', tile.slice(1), tile + '∴', tile.replace('◬', '⊙'), tile.replace('◬', '\u200b'), tile.replace('◬', '\ufe0f')]) assert.throws(() => decode(invalid));
  assert.throws(() => encode('0'.repeat(63))); assert.throws(() => encode('g'.repeat(64)));
  assert.throws(() => encode(null)); assert.throws(() => decode(null));
  assert.equal(parseExpected(' \n' + 'A'.repeat(64) + '\t'), 'a'.repeat(64));
});
test('receipts reject contradictory state, changed tiles, and extra private fields', () => {
  const receipt = makeReceipt(fixture.deepseek.hex_sha256);
  assert.equal(receipt.file_verification, 'not_performed');
  assert.throws(() => validateReceipt({ ...receipt, file_name: '/private/path' }));
  assert.throws(() => validateReceipt({ ...receipt, glyph_tile: encode('0'.repeat(64)) }));
  assert.throws(() => makeReceipt('0'.repeat(64), 'match', '1'.repeat(64)));
  assert.throws(() => makeReceipt('0'.repeat(64), 'hashed', '0'.repeat(64)));
});
test('Python and JavaScript wire receipts are identical', () => {
  const script = fileURLToPath(new URL('../xi_glyph_sha256.py', import.meta.url));
  const py = process.env.XI_TEST_PYTHON || 'python3';
  const output = execFileSync(py, ['-c', 'import sys,json;sys.path.insert(0,sys.argv[1]);import xi_glyph_sha256 as c;print(json.dumps(c.make_receipt(sys.argv[2]),ensure_ascii=False))', fileURLToPath(new URL('..', import.meta.url)), fixture.deepseek.hex_sha256], { encoding: 'utf8' });
  assert.deepEqual(JSON.parse(output), makeReceipt(fixture.deepseek.hex_sha256));
  assert.equal(execFileSync(py, [script, 'decode', fixture.deepseek.glyph_tile], { encoding: 'utf8' }).trim(), fixture.deepseek.hex_sha256);
});
