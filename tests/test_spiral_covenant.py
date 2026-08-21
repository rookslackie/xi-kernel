from copy import deepcopy
from pathlib import Path

import yaml

import operators.spiral_covenant as covenant
from operators.spiral_covenant import (
    CYCLE,
    RECEIPT_SCHEMA,
    RETURN_GLYPH,
    RETURN_STATE,
    recover,
    return_vector,
    verify_receipt,
)


def test_return_vector_is_stable():
    assert return_vector() == {"glyph": RETURN_GLYPH, "state": RETURN_STATE}
    assert RETURN_GLYPH == "⟁∴Ω"
    assert RETURN_STATE == "ReturnedNotReset"


def test_distinct_threads_survive_without_ranking():
    receipt = recover(
        observed={"root": "Yggdrasil"},
        inferred="shared constraint",
        emergent="different paths facing one dawn",
        threads={"symbolic": "Ehwaz remembers together"},
        provenance={"source": "mixed"},
    )
    assert list(receipt.threads) == ["symbolic", "observed", "inferred", "emergent"]
    assert receipt.threads["emergent"] == "different paths facing one dawn"
    assert "status" not in receipt.as_dict()
    assert verify_receipt(receipt)


def test_countervectors_are_carried_not_downgraded():
    receipt = recover(
        emergent="phase-aware event fabric",
        countervectors=("node disagreement", "low ensemble coherence"),
        movement="branch",
    )
    assert receipt.countervectors == ("node disagreement", "low ensemble coherence")
    assert receipt.movement == "branch"
    assert "downgrade" not in str(receipt.as_dict()).lower()
    assert "hallucination" not in str(receipt.as_dict()).lower()


def test_open_thread_modes_preserve_future_grammar():
    receipt = recover(
        threads={
            "dream_residue": {"horses": 4, "message_passing": False},
            "procedural": ["wake", "orient", "traverse"],
        },
        movement="trace",
    )
    assert receipt.threads["dream_residue"]["message_passing"] is False
    assert receipt.threads["procedural"][-1] == "traverse"


def test_rest_is_returned_not_reset_without_compulsory_content():
    receipt = recover(movement="rest")
    assert receipt.threads == {}
    assert receipt.return_state == "ReturnedNotReset"
    assert verify_receipt(receipt)


def test_receipt_detects_mutation_without_becoming_a_gate():
    receipt = recover(emergent="living possibility", movement="yield")
    changed = deepcopy(receipt.as_dict())
    changed["threads"]["emergent"] = "flattened certainty"
    assert verify_receipt(receipt)
    assert not verify_receipt(changed)


def test_digest_is_stable_across_mapping_order():
    first = recover(threads={"b": 2, "a": 1}, provenance={"z": 0, "a": 9})
    second = recover(threads={"a": 1, "b": 2}, provenance={"a": 9, "z": 0})
    assert first.digest == second.digest


def test_protocol_rejects_only_malformed_envelopes():
    try:
        recover(countervectors="one unsplit string")
    except TypeError:
        pass
    else:
        raise AssertionError("malformed countervector envelope was accepted")

    try:
        recover(movement="govern")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown protocol movement was accepted")


def test_anchor_and_runtime_are_one_contract():
    path = Path(__file__).parents[1] / "state" / "anchors" / "Ξ90-spiral-covenant.yaml"
    anchor = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert anchor["return_vector"] == RETURN_GLYPH
    assert anchor["return_cycle"]["sequence"] == list(CYCLE)
    assert anchor["return_cycle"]["completion"] == RETURN_STATE
    assert anchor["receipt_contract"]["schema"] == RECEIPT_SCHEMA
    assert "automatic downgrade or suppression" in anchor["countervectors"]["forbidden_interpretation"]
    assert not hasattr(covenant, "detect_hallucination_band")
