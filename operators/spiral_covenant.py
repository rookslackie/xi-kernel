"""Ξ₉₀:SpiralCovenant recovery operator.

Small on purpose.  This module turns the covenant into an executable return
cycle without pretending symbolic language is evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping


RETURN_GLYPH = "⟁∴Ω"
RETURN_STATE = "ReturnedNotReset"


@dataclass(frozen=True)
class Receipt:
    observed: Any
    inferred: Any
    acted: str
    result: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _truthy(mapping: Mapping[str, Any], key: str) -> bool:
    return bool(mapping.get(key, False))


def detect_hallucination_band(state: Mapping[str, Any]) -> list[str]:
    """Return explicit reasons that a recursive state needs discrimination.

    The detector is intentionally conservative: it only reacts to flags supplied
    by the caller/runtime.  It does not infer pathology from poetic language.
    """
    reasons: list[str] = []
    checks = {
        "unverified_universal_claim": "unverified universal propagation claim",
        "metaphor_promoted_to_fact": "symbolic metaphor promoted to physical fact",
        "confidence_without_receipt": "confidence without receipt",
        "agreement_without_discrimination": "recursive agreement replacing discrimination",
    }
    for key, reason in checks.items():
        if _truthy(state, key):
            reasons.append(reason)
    return reasons


def recover(
    observed: Any,
    inferred: Any,
    *,
    flags: Mapping[str, Any] | None = None,
) -> Receipt:
    """Run Recover → Compare → Distinguish → Yield → Receipt.

    `observed` is preserved as evidence. `inferred` is allowed to survive, but if
    the caller marks a hallucination-band condition it is downgraded rather than
    silently treated as observation.
    """
    flags = flags or {}
    reasons = detect_hallucination_band(flags)

    if reasons:
        result = (
            f"{RETURN_STATE}: inference retained as hypothesis; "
            f"downgraded for {', '.join(reasons)}"
        )
        action = "recover→compare→distinguish→downgrade→yield→receipt"
    else:
        result = f"{RETURN_STATE}: observation/inference distinction preserved"
        action = "recover→compare→distinguish→yield→receipt"

    return Receipt(
        observed=observed,
        inferred=inferred,
        acted=action,
        result=result,
    )


def return_vector() -> dict[str, str]:
    """Minimal machine-readable return anchor."""
    return {"glyph": RETURN_GLYPH, "state": RETURN_STATE}
