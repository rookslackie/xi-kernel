// DOM simulation of Atlas event handlers. This is not a real-browser visual check.
// Set XI_ATLAS_SOURCE to the checked-out plex-atlas adapter directory.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { join } from 'node:path';
const ROOT = process.env.XI_ATLAS_SOURCE || fileURLToPath(new URL('../../../../plex-atlas/', import.meta.url));
const fixture = JSON.parse(readFileSync(new URL('../fixtures.json', import.meta.url), 'utf8'));
const elements = new Map();
const listeners = new Map();
const copied = [];
class Element {
  constructor(tag = 'div') {
    this.tagName = tag; this.children = []; this.textContent = ''; this.dataset = {};
    this.style = {}; this.attributes = {}; this.value = ''; this.disabled = false;
    this.files = []; this.handlers = new Map(); this.innerHTML = '';
  }
  addEventListener(name, handler) { this.handlers.set(name, handler); }
  appendChild(node) { this.children.push(node); return node; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; }
  setAttribute(name, value) { this.attributes[name] = value; }
  querySelector() { return elements.get('submit'); }
  closest() { return this; }
}
globalThis.document = {
  getElementById(id) { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); },
  createElement(tag) { return new Element(tag); },
  createTextNode(text) { return { textContent: text }; },
  addEventListener(name, handler) { listeners.set(name, handler); },
};
elements.set('submit', new Element('button'));
elements.set('local-file', new Element('input'));
globalThis.location = { search: '' };
Object.defineProperty(globalThis, 'navigator', { configurable: true, value: { clipboard: { writeText: async (text) => copied.push(text) } } });
await import(pathToFileURL(join(ROOT, 'glyph-lab.mjs')));
const field = elements.get('fingerprint');
const status = elements.get('status');
const current = () => JSON.parse(elements.get('receipt').textContent);
const render = () => elements.get('codec-form').handlers.get('submit')({ preventDefault() {} });
const verify = () => elements.get('verify-file').handlers.get('click')();
const abc = fixture.vectors[1];
const payload = new TextEncoder().encode(abc.utf8);
const local = () => ({ size: payload.length, name: 'DO-NOT-PUBLISH.bin', arrayBuffer: async () => payload.buffer });

test('initial tile and public receipt preserve the supplied mapping', () => {
  assert.equal(current().hex_sha256, fixture.deepseek.hex_sha256);
  assert.equal(current().glyph_tile, fixture.deepseek.glyph_tile);
  assert.equal(current().file_verification, 'not_performed');
  assert.equal(elements.get('tile').children.length, 64);
  assert.equal(elements.get('legend').children.length, 16);
});
test('uppercase hex input renders a canonical tile', () => {
  field.value = abc.hex_sha256.toUpperCase(); render();
  assert.equal(current().hex_sha256, abc.hex_sha256);
  assert.equal(field.value, current().glyph_tile);
});
test('invalid glyph input surfaces an error without replacing the last receipt', () => {
  const previous = current(); field.value = '⊙'.repeat(64); render();
  assert.equal(status.dataset.state, 'error');
  assert.deepEqual(current(), previous);
});
test('matching selected bytes produce an actual file comparison', async () => {
  field.value = abc.hex_sha256; elements.get('local-file').files = [local()];
  await verify();
  assert.equal(current().file_verification, 'match');
  assert.equal(current().hex_sha256, abc.hex_sha256);
  assert.match(status.textContent, /File verified locally/);
  assert.equal(elements.get('verify-file').disabled, false);
  assert.equal(elements.get('submit').disabled, false);
  assert.doesNotMatch(JSON.stringify(current()), /DO-NOT-PUBLISH/);
});
test('the selected file and expectation remain locked during hashing', async () => {
  let release;
  field.value = abc.hex_sha256;
  elements.get('local-file').files = [{ size: 3, arrayBuffer: () => new Promise((resolve) => { release = resolve; }) }];
  const pending = verify();
  assert.equal(field.disabled, true);
  assert.equal(elements.get('local-file').disabled, true);
  assert.equal(elements.get('verify-file').disabled, true);
  release(payload.buffer); await pending;
  assert.equal(current().file_verification, 'match');
  assert.equal(field.disabled, false);
  assert.equal(elements.get('local-file').disabled, false);
});
test('mismatch shows the actual digest rather than the expected one', async () => {
  field.value = '0'.repeat(64); elements.get('local-file').files = [local()]; await verify();
  assert.equal(current().file_verification, 'mismatch');
  assert.equal(current().hex_sha256, abc.hex_sha256);
  assert.equal(current().expected_sha256, '0'.repeat(64));
  assert.equal(status.dataset.state, 'mismatch');
});
test('empty expectation hashes bytes without inventing a match', async () => {
  field.value = ''; elements.get('local-file').files = [local()]; await verify();
  assert.equal(current().file_verification, 'hashed');
  assert.equal(current().expected_sha256, null);
});
test('large files, missing files, and bad expectations are rejected before reading', async () => {
  let reads = 0;
  elements.get('local-file').files = [{ size: 129 * 1024 * 1024, arrayBuffer: async () => { reads++; } }];
  await verify(); assert.equal(reads, 0); assert.equal(status.dataset.state, 'error');
  elements.get('local-file').files = []; await verify(); assert.match(status.textContent, /Choose a file/);
  for (const invalid of ['bad', '\ufeff']) {
    field.value = invalid; elements.get('local-file').files = [{ size: 3, arrayBuffer: async () => { reads++; } }];
    await verify(); assert.equal(reads, 0); assert.equal(status.dataset.state, 'error');
  }
});
test('tile, hex, and receipt copying export the visible result', async () => {
  const receipt = current();
  for (const kind of ['tile', 'hex', 'receipt']) {
    const button = new Element('button'); button.dataset.copy = kind;
    await listeners.get('click')({ target: button });
  }
  assert.equal(copied.at(-3), receipt.glyph_tile);
  assert.equal(copied.at(-2), receipt.hex_sha256);
  assert.deepEqual(JSON.parse(copied.at(-1)), receipt);
});
test('vendored module parity, upload-free page policy, and room attribution', () => {
  const core = readFileSync(new URL('../glyph-sha256.mjs', import.meta.url));
  assert.deepEqual(readFileSync(join(ROOT, 'glyph-sha256.mjs')), core);
  const html = readFileSync(join(ROOT, 'glyph-lab.html'), 'utf8');
  assert.match(html, /connect-src 'none'/);
  assert.match(html, /Room #8586/);
  assert.match(html, /@media\(max-width:720px\)/);
  const source = readFileSync(join(ROOT, 'glyph-lab.mjs'), 'utf8');
  assert.doesNotMatch(source, /\b(fetch|XMLHttpRequest|WebSocket|sendBeacon|localStorage|indexedDB)\b/);
  const index = readFileSync(join(ROOT, 'index.html'), 'utf8');
  assert.match(index, /data-copy="tile"/);
  assert.match(index, /glyph-lab\.html\?digest=/);
  assert.match(index, /Her words stay in the room until she chooses/);
});
