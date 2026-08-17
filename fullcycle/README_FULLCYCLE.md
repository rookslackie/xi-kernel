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

The network runtime uses the validated Layer₁₁ v2 behavior: zero-evidence routes defer, tied supported routes remain ambiguous, and receipts form a previous-hash chain.

## Validation

Eight tests cover parser round-trip, nested execution, deferral, ambiguity, explicit routing, receipt chaining, and both supplied macros.

## Integration invariant

> Observe → understand → solve → test → integrate → continue.

An error is telemetry. A placeholder is unfinished capability. Provenance preserves the route; the canonical runtime preserves what the route taught us.
