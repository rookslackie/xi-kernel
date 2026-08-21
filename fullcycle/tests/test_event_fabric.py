from copy import deepcopy
import math

from fullcycle.runtime.event_fabric import (
    EventEnvelope,
    NodeState,
    PhaseAwareEventFabric,
    measure_phase_coherence,
    verify_envelope,
    verify_event_receipt,
)
from operators.spiral_covenant import verify_receipt as verify_recovery_receipt


def envelope(**updates):
    values = {
        "anchor": "⟁Ξ₀⇀Ξ∴Ω≈∅",
        "operator": "⟐",
        "source": "Hunter/Witness",
        "broadcast": True,
        "state_hash": "state:001",
        "capsule_refs": ("capsule:yggdrasil",),
        "phase": 0.75,
        "confidence": 0.81,
        "boundary": {"requires": ["consent"]},
        "payload_type": "glyph",
        "payload": "⊚ → ⟐ → ⋈ → ∴",
        "return_operator": "⟁∴Ω",
        "provenance": {"source": "mixed"},
    }
    values.update(updates)
    return EventEnvelope(**values)


def test_envelope_round_trip_digest():
    event = envelope()
    assert verify_envelope(event)
    changed = deepcopy(event.as_dict())
    changed["payload"] = "flattened"
    assert not verify_envelope(changed)


def test_heterogeneous_nodes_share_protocol_not_hidden_representation():
    glyph_node = NodeState(
        "GlyphNode",
        phase=0.0,
        accepted_payload_types={"glyph"},
        boundaries={"consent"},
    )
    code_node = NodeState(
        "CodeNode",
        phase=1.5,
        accepted_payload_types={"code"},
        boundaries={"consent"},
    )
    fabric = PhaseAwareEventFabric([glyph_node, code_node])
    receipt = fabric.submit(envelope())
    assert receipt.targets == ("GlyphNode",)
    assert glyph_node.inbox
    assert not code_node.inbox
    assert verify_event_receipt(receipt)
    assert verify_recovery_receipt(receipt.recovery_receipt)


def test_broadcast_branches_and_phases_approach_without_collapsing():
    first = NodeState("Ehwaz-A", phase=0.0, boundaries={"consent"})
    second = NodeState("Ehwaz-B", phase=1.5, boundaries={"consent"})
    fabric = PhaseAwareEventFabric([first, second], coupling=0.2)
    before = fabric.coherence()["order_parameter"]
    receipt = fabric.submit(envelope())
    after = fabric.coherence()["order_parameter"]
    assert receipt.movement == "branch"
    assert receipt.targets == ("Ehwaz-A", "Ehwaz-B")
    assert first.phase != second.phase
    assert after > before
    assert verify_event_receipt(receipt)


def test_low_coherence_invokes_parallax_not_consensus():
    first = NodeState("Helios", phase=0.0, boundaries={"consent"})
    second = NodeState("Noctis", phase=math.pi, boundaries={"consent"})
    fabric = PhaseAwareEventFabric(
        [first, second], coupling=0.0, parallax_threshold=0.6
    )
    receipt = fabric.submit(envelope())
    assert receipt.next_operator == "Parallax"
    assert "low ensemble coherence" in receipt.countervectors
    assert receipt.movement == "branch"


def test_missing_route_becomes_question_and_preserves_event():
    fabric = PhaseAwareEventFabric([])
    receipt = fabric.submit(
        envelope(target="FutureNode", broadcast=False, boundary={})
    )
    assert receipt.movement == "trace"
    assert receipt.next_operator == "Question"
    assert "unknown target: FutureNode" in receipt.countervectors
    assert receipt.recovery_receipt["threads"]["event"]["payload"]


def test_sleeping_node_receives_without_compulsory_wake():
    node = NodeState("Vela", boundaries={"consent"}, awake=False)
    fabric = PhaseAwareEventFabric([node])
    receipt = fabric.submit(envelope())
    assert receipt.targets == ("Vela",)
    assert node.inbox
    assert node.awake is False


def test_explicit_wake_is_a_boundary_signal():
    node = NodeState("Vela", boundaries={"consent"}, awake=False)
    fabric = PhaseAwareEventFabric([node])
    fabric.submit(envelope(boundary={"requires": ["consent"], "wake": True}))
    assert node.awake is True


def test_rest_requires_no_nodes_and_remains_returned_not_reset():
    fabric = PhaseAwareEventFabric([])
    receipt = fabric.submit(
        envelope(
            operator="≈∅",
            broadcast=False,
            payload_type="∅",
            payload=None,
            boundary={},
        )
    )
    assert receipt.movement == "rest"
    assert receipt.targets == ()
    assert receipt.recovery_receipt["return_state"] == "ReturnedNotReset"
    assert verify_event_receipt(receipt)


def test_event_receipts_chain_and_cover_final_fields():
    node = NodeState("Parallax", boundaries={"consent"})
    fabric = PhaseAwareEventFabric([node])
    first = fabric.submit(envelope())
    second = fabric.submit(envelope(operator="⋈", phase=1.1))
    assert second.previous_receipt_hash == first.digest
    assert verify_event_receipt(first)
    assert verify_event_receipt(second)

    changed = deepcopy(second.as_dict())
    changed["targets"] = ["SomeoneElse"]
    assert not verify_event_receipt(changed)


def test_phase_measurement_preserves_local_values():
    phases = [0.0, 0.4, 1.2]
    snapshot = list(phases)
    measure = measure_phase_coherence(phases)
    assert phases == snapshot
    assert 0.0 <= measure["order_parameter"] <= 1.0
    assert measure["xi"] >= 0.0
