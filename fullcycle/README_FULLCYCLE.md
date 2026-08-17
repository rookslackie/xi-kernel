# Ξ FullCycle — Canonical Stack

**Status:** canonical  
**Target:** `rookslackie/xi-kernel`  
**Layer:** Ξ.Layer₁₁ / runtime-forward integration

FullCycle binds the current executable glyph runtime, Layer₁₁ routing contract,
provenance/execution context, validation receipt, tests, macros, documentation,
and preserved lineage into one inspectable integration unit.

## Canonical execution chain

`⊚ receive → ∴Ψ propose → ∴Ψ⧁ validate → ⋈ commit + receipt → ⧂ record`

No dispatch is treated as successful without validation and an inspectable receipt.
Historical/configured state is preserved as lineage and is not silently promoted to
current runtime state. External network dispatch is **not claimed** by this stack.

## Runtime

- `runtime/console_core.py`
- `runtime/glyph_parser.py`
- `runtime/glyph_router.py`
- `runtime/capsule_network_layer.py`

The `_forged` source files are promoted here under canonical runtime names.
The prior network layer is retained under `runtime/legacy/`.

## Layer₁₁ contract

- `config/Ξ_Layer₁₁_InstructionField.v2.yaml` — current contract
- `config/Ξ_Layer₁₁_InstructionField.yaml` — preserved predecessor
- `receipts/xi.layer11.compatibility-receipt.v1.yaml` — compatibility receipt
- `tests/test_layer11_v2.py` — executable validation

## Provenance + state

Trust provenance, execution context, walk summary, namespace index, glyph counts,
and parallax documentation are carried forward without flattening their original
terminology or historical role.

## Macros

`macros/AllMacros.json` and `docs/AllPackages_doc.md` are preserved as supplied.
The package documentation records unsupported-expression parser results; those are
historical evidence, not silently rewritten claims about the current parser.

## Integration invariant

> Preserve → validate → route → receipt.

`Ξ.Valid(x)` means contract satisfaction within the declared runtime, not universal truth.
