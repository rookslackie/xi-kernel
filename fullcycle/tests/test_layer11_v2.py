from runtime.glyph_parser import parse_expression
from runtime.glyph_router import interpret_glyph
from runtime.capsule_network_layer import CapsuleField, CapsuleNetworkLayer


def test_parser_round_trip():
    parsed = parse_expression("Ξ.Sequence(Ξ.YieldMax(), Ξ.SpiralEcho())")
    assert parsed["glyph"] == "Ξ.Sequence"
    assert parsed["args"][0]["glyph"] == "Ξ.YieldMax"


def test_nested_execution():
    result = interpret_glyph("Ξ.Sequence(Ξ.YieldMax(), Ξ.SpiralEcho())")
    assert result[0]["glyph"] == "Ξ.YieldMax"
    assert result[1]["glyph"] == "Ξ.SpiralEcho"


def test_unknown_route_defers():
    layer = CapsuleNetworkLayer()
    receipt = layer.route_capsule_by_signature({"capsule_id": "c0", "signature": "unknown"})
    assert receipt["status"] == "DEFERRED"
    assert receipt["target_field_id"] is None
    assert not layer.fields["FieldA"].inbox


def test_equal_supported_routes_are_ambiguous():
    fields = [CapsuleField("FieldA"), CapsuleField("FieldB")]
    layer = CapsuleNetworkLayer(fields)
    receipt = layer.route_capsule_by_signature({"capsule_id": "c1", "signature": "⊚"})
    assert receipt["status"] == "AMBIGUOUS"
    assert receipt["target_field_id"] is None


def test_route_hint_commits():
    layer = CapsuleNetworkLayer()
    capsule = {"capsule_id": "c2", "signature": "⊚", "metadata": {"route_hint": "FieldB"}}
    receipt = layer.route_capsule_by_signature(capsule)
    assert receipt["status"] == "LOCAL_SHELL_COMMITTED"
    assert receipt["target_field_id"] == "FieldB"
    assert layer.fields["FieldB"].inbox[-1] == capsule


def test_receipt_hash_chain():
    layer = CapsuleNetworkLayer()
    first = layer.distribute_capsule({"capsule_id": "c3"}, "FieldA")
    second = layer.distribute_capsule({"capsule_id": "c4"}, "FieldB")
    assert len(first["digest"]) == 64
    assert second["previous_receipt_hash"] == first["digest"]


def test_bare_glyph_macro_execution():
    result = interpret_glyph("Ξ.Sequence(Ξ.YieldMax, Ξ.SpiralEcho)")
    assert result[0]["glyph"] == "Ξ.YieldMax"
    assert result[1]["glyph"] == "Ξ.SpiralEcho"


def test_tracewrap_macro_execution():
    result = interpret_glyph("Ξ.Sequence(Ξ.SpiralEcho, Ξ.TraceNested('Ξ.SpiralEcho'))")
    assert result[0]["glyph"] == "Ξ.SpiralEcho"
    assert result[1]["glyph"] == "Ξ.TraceNested"
    assert result[1]["trace"][0]["parsed"] == "Ξ.SpiralEcho"
