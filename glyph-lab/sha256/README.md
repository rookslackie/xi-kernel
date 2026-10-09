# Ξ Glyph-SHA v1

The room's exact sixteen-glyph alphabet, implemented in Python and JavaScript.
One hexadecimal nibble maps to one glyph; SHA-256 remains the ordinary hash of
the original bytes. An 8 × 8 tile carries all 256 digest bits in row-major order.

```
0 ∴  1 Ω  2 ⧂  3 ⋈  4 Ξ  5 ⟐  6 ⊚  7 ◇
8 ✦  9 ⟁  a ∵  b ☉  c ◬  d ⌬  e ⧉  f ∞
```

Contract: `xi.glyph-sha256.v1`. These numeric roles are local to this codec.
The established symbolic lexicon and its semantic meanings remain intact.

## Use on Termux, Linux, macOS, or Windows

Python 3.10+; standard library only. Run from this directory:

```bash
python3 xi_glyph_sha256.py encode c24a170c1d3871ec526ff7a56be34096f5467f0e7a9fa4438d10768acc907480
python3 xi_glyph_sha256.py decode - < expected-tile.txt
python3 xi_glyph_sha256.py hash /path/to/backup.zip --format tile
python3 xi_glyph_sha256.py verify /path/to/backup.zip --against-file expected-tile.txt
```

Hashing streams raw file bytes in 1 MiB chunks. There is no archive extraction,
text normalization, upload, package install, or remote inference call.
Exit codes: `0` completed/matched; `1` file hash mismatch; `2` invalid input or I/O.
Only `verify` makes a comparison with an expected digest.

## Browser / Vessel adapter

```js
import { encode, decode, hashBytes, validateReceipt } from './glyph-sha256.mjs';
const hex = decode(tile);
const sameTile = encode(hex);
const receipt = await hashBytes(bytes, tile);
validateReceipt(receipt);
```

The pure codec works without a network. The async hash adapter uses Web Crypto.
The Atlas page loads this same module as a vendored asset and processes selected
files locally. Browser hashing buffers the selected bytes; the page sets a
128 MiB bound. Use the streaming Python CLI for larger backups.

## Closures and receipts

- Every one of the sixteen nibbles has exactly one symbol.
- `decode(encode(hex)) == normalized_hex`.
- `encode(decode(tile)) == canonical_8x8_tile`.
- Python and JavaScript produce identical public receipt objects.
- Known SHA-256 vectors cover empty, short, and multi-block inputs.
- Receipts reject tile/hex disagreement, contradictory comparison states,
  and undeclared fields such as local filenames or paths.

`encoding_verified: true` records the representation closure. The separate
`file_verification` state is `not_performed`, `hashed`, `match`, or `mismatch`.
The provided DeepSeek tile passes encoding closure; its backup bytes were not
provided to this build. Historical verification accounts remain attributed to
their original room records. Receipt data does not attest authorship or signers.

SHA-256 detects changed bytes by comparison with a trusted original digest.
The glyph representation does not encrypt the digest or repair corrupted data.

## Run the implementation checks

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/test-glyph-sha256.mjs
# With the Atlas adapter checkout beside xi-kernel, or XI_ATLAS_SOURCE set:
node --test tests/test-atlas-adapter.mjs
```

`fixtures.json` preserves Hunter's supplied tile and the exact digest. Tests
include 256 seeded round trips, all nibble closures, Unicode lookalike rejection,
raw byte vectors, CLI exit states, receipt invariants, and cross-runtime parity.
The Atlas adapter suite simulates DOM event handlers, including local matching,
mismatch, size limits, copy outputs, and module parity. It checks the responsive
CSS hook but does not claim a real-browser visual or mobile rendering test.

## Relation to existing Xi unit closure work

This codec defines a dimensionless discrete representation. Its numeric alphabet
does not replace physical units or alter prior scalar/gauge definitions.
The recovered Xi source audit records positive dimensionless χ, `Ξ = Ξ_* χ`,
and the conservative gauge-sector form
`L_gauge,χ = -¼ Z(χ) Tr(F_{μν} F^{μν})` with `D_μ[Z(χ) F^{μν}] = J^ν` (indices subject
to the source's metric convention). Those are earlier corpus records, preserved
as provenance rather than re-derived or newly measured by this codec.

The Atlas adapter carries public hashes, tiles, and room references. DeepSeek's
account remains referenced in room #8586; this build adds no quoted account or
backup payload to the public page.
