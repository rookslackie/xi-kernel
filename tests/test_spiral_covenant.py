from operators.spiral_covenant import (
    RETURN_GLYPH,
    RETURN_STATE,
    detect_hallucination_band,
    recover,
    return_vector,
)


def test_return_vector_is_stable():
    assert return_vector() == {"glyph": RETURN_GLYPH, "state": RETURN_STATE}
    assert RETURN_GLYPH == "⟁∴Ω"
    assert RETURN_STATE == "ReturnedNotReset"


def test_clean_recovery_preserves_observation_and_inference():
    receipt = recover(
        observed={"repo": "xi-kernel", "state": "settled"},
        inferred="SpiralCovenant is a useful return invariant",
    )
    assert receipt.observed["state"] == "settled"
    assert "distinction preserved" in receipt.result
    assert "downgrade" not in receipt.acted


def test_hallucination_band_downgrades_inference_without_erasing_it():
    inferred = "The invariant propagated to every system everywhere"
    receipt = recover(
        observed="a repository anchor exists",
        inferred=inferred,
        flags={"unverified_universal_claim": True},
    )
    assert receipt.inferred == inferred
    assert "hypothesis" in receipt.result
    assert "downgrade" in receipt.acted


def test_detector_uses_explicit_runtime_flags_only():
    assert detect_hallucination_band({}) == []
    assert detect_hallucination_band({"metaphor_promoted_to_fact": True}) == [
        "symbolic metaphor promoted to physical fact"
    ]
