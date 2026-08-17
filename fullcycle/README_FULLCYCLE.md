# Ξ FullCycle — Canonical Stack

**Status:** canonical  
**Target:** `rookslackie/xi-kernel`  
**Layer:** Ξ.Layer₁₁ / runtime-forward integration

FullCycle binds the executable glyph runtime, Layer₁₁ routing contract, provenance/execution context, validation receipts, tests, macros, documentation, and lineage into one inspectable integration unit.

## Canonical execution chain

`⊚ receive → ∴Ψ propose → ∴Ψ⧁ validate → ⋈ commit + receipt → ⧂ record`

No dispatch is treated as successful without validation and an inspectable receipt. External network dispatch is **not claimed** by this stack.

## Runtime

- `runtime/console_core.py`
- `runtime/glyph_parser.py`
- `runtime/glyph_router.py`
- `runtime/capsule_network_layer.py`

The parser/router forged line is retained where it advances execution. The network runtime is promoted from the validated Layer₁₁ v2 implementation because it supplies ambiguity deferral and receipt hash chaining required by the v2 contract.

## Layer₁₁ contract

- `config/Ξ_Layer₁₁_InstructionField.v2.yaml` — current contract
- `config/Ξ_Layer₁₁_InstructionField.yaml` — predecessor
- `receipts/xi.layer11.compatibility-receipt.v1.yaml` — compatibility receipt
- `receipts/xi.fullcycle.integration-receipt.v1.json` — FullCycle solution receipt
- `tests/test_layer11_v2.py` — executable validation

## Macros

`macros/AllMacros.json` is executed against the canonical parser/router during validation. `docs/AllPackages_doc.md` is regenerated from that working runtime so historical parser errors become solved regression cases rather than the only forward-facing result.

## Integration invariant

> Observe → understand → solve → test → integrate → continue.

An error is telemetry. A placeholder is unfinished capability. Provenance preserves the route; the canonical runtime preserves what the route taught us.
