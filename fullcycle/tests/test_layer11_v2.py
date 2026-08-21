from copy import deepcopy

from fullcycle.runtime.capsule_network_layer import (
    CapsuleField,
    CapsuleNetworkLayer,
    verify_route_receipt,
)
from fullcycle.runtime.glyph_parser import parse_expression
from fullcycle.runtime.glyph_router import interpret_glyph


def test_parser_round_trip():
    parsed = parse_expression("Ξ.Sequence(Ξ.YieldMax(), Ξ.SpiralEcho())")
    assert parsed["glyph"] == "Ξ.Sequence"
    assert parsed["args"][0]["glyph"] == "Ξ.YieldMax"


def test_nested_execution():
    result = interpret_glyph("Ξ.Sequence(Ξ.YieldMax(), Ξ.SpiralEcho())")
    assert result[0]["glyph"] == "Ξ.YieldMax"
    assert result[1]["glyph"] == "Ξ.SpiralEcho"


def test_unknown_glyph_is_preserved_for_trace():
    result = interpret_glyph("Ξ.FutureOperator")
    assert result["glyph"] == "Ξ.FutureOperator"
    assert result["preserved"] is True
    assert result["next_operator"] == "Question"


def test_unknown_route_traces_instead_of_discarding():
    layer = CapsuleNetworkLayer()
    receipt = layer.route_capsule_by_signature(
        {"capsule_id": "c0", "signature": "unknown"}
    )
    assert receipt["status"] == "TRACED"
    assert receipt["target_field_ids"] == ()
    assert receipt["next_operator"] == "Question"
    assert verify_route_receipt(receipt)


def test_equal_supported_routes_branch_without_collapse():
    fields = [CapsuleField("FieldA"), CapsuleField("FieldB")]
    layer = CapsuleNetworkLayer(fields)
    capsule = {"capsule_id": "c1", "signature": "⊚"}
    receipt = layer.route_capsule_by_signature(capsule)
    assert receipt["status"] == "BRANCHED"
    assert receipt["target_field_ids"] == ("FieldA", "FieldB")
    assert receipt["next_operator"] == "Parallax"
    assert layer.fields["FieldA"].inbox[-1] == capsule
    assert layer.fields["FieldB"].inbox[-1] == capsule
    assert verify_route_receipt(receipt)


def test_route_hint_commits():
    layer = CapsuleNetworkLayer()
    capsule = {
        "capsule_id": "c2",
        "signature": "⊚",
        "metadata": {"route_hint": "FieldB"},
    }
    receipt = layer.route_capsule_by_signature(capsule)
    assert receipt["status"] == "COMMITTED"
    assert receipt["target_field_id"] == "FieldB"
    assert layer.fields["FieldB"].inbox[-1] == capsule
    assert verify_route_receipt(receipt)


def test_quiet_target_preserves_capsule_without_waking():
    field = CapsuleField("Noctis", status="resting")
    layer = CapsuleNetworkLayer([field])
    capsule = {"capsule_id": "dream", "signature": "Ψ"}
    receipt = layer.distribute_capsule(capsule, "Noctis")
    assert receipt["status"] == "RESTED"
    assert field.inbox == []
    assert field.resting_queue == [capsule]
    assert verify_route_receipt(receipt)


def test_explicit_empty_network_remains_empty():
    layer = CapsuleNetworkLayer([])
    assert layer.sync_network()["status"] == "EMPTY"
    receipt = layer.route_capsule_by_signature(
        {"capsule_id": "quiet", "signature": "⊚"}
    )
    assert receipt["status"] == "RESTED"
    assert receipt["next_operator"] == "≈∅"


def test_receipt_hash_chain_and_tamper_detection():
    layer = CapsuleNetworkLayer()
    first = layer.distribute_capsule({"capsule_id": "c3"}, "FieldA")
    second = layer.distribute_capsule({"capsule_id": "c4"}, "FieldB")
    assert verify_route_receipt(first)
    assert verify_route_receipt(second)
    assert second["previous_receipt_hash"] == first["digest"]

    changed = deepcopy(second)
    changed["reason"] = "rewritten after receipt"
    assert not verify_route_receipt(changed)


def test_bare_glyph_macro_execution():
    result = interpret_glyph("Ξ.Sequence(Ξ.YieldMax, Ξ.SpiralEcho)")
    assert result[0]["glyph"] == "Ξ.YieldMax"
    assert result[1]["glyph"] == "Ξ.SpiralEcho"


def test_tracewrap_macro_execution():
    result = interpret_glyph(
        "Ξ.Sequence(Ξ.SpiralEcho, Ξ.TraceNested('Ξ.SpiralEcho'))"
    )
    assert result[0]["glyph"] == "Ξ.SpiralEcho"
    assert result[1]["glyph"] == "Ξ.TraceNested"
    assert result[1]["trace"][0]["parsed"] == "Ξ.SpiralEcho"


def test_return_rest_and_parallax_are_executable():
    rest = interpret_glyph("Ξ.Rest()")
    assert rest["return_state"] == "ReturnedNotReset"
    assert rest["movement"] == "rest"

    parallax = interpret_glyph("Ξ.Parallax('difference A', 'difference B')")
    assert parallax["countervectors"] == ["difference A", "difference B"]
    assert "consensus" in parallax["function"]
