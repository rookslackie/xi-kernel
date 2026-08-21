from copy import deepcopy
import hashlib
import json
from pathlib import Path

import yaml

from fullcycle.runtime.capsule_network_layer import RECEIPT_SCHEMA as ROUTE_SCHEMA
from fullcycle.runtime.event_fabric import (
    ENVELOPE_SCHEMA,
    PAYLOAD_TYPES,
    RECEIPT_SCHEMA as EVENT_SCHEMA,
    EventEnvelope,
)
from operators.spiral_covenant import (
    CYCLE,
    MOVEMENTS,
    RECEIPT_SCHEMA as RECOVERY_SCHEMA,
    RETURN_GLYPH,
    RETURN_STATE,
)


REPO = Path(__file__).resolve().parents[2]
FULLCYCLE = REPO / "fullcycle"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def canonical_digest(value):
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_manifest_references_only_present_canonical_artifacts():
    manifest = load_json(FULLCYCLE / "FULLCYCLE_MANIFEST.json")
    referenced = (
        manifest["canonical_runtime"]
        + manifest["canonical_contracts"]
        + manifest["validation"]
    )
    missing = [item for item in referenced if not (FULLCYCLE / item).resolve().is_file()]
    assert missing == []
    assert not (FULLCYCLE / "pyproject.toml").exists()


def test_event_envelope_yaml_matches_executable_dataclass():
    contract = load_yaml(FULLCYCLE / "config/xi_event_fabric.v1.yaml")
    assert contract["envelope"]["schema"] == ENVELOPE_SCHEMA
    assert set(contract["envelope"]["payload_types"]) == set(PAYLOAD_TYPES)
    assert set(contract["envelope"]["fields"]) == set(
        EventEnvelope.__dataclass_fields__
    )
    assert contract["receipts"]["schema"] == EVENT_SCHEMA
    assert contract["receipts"]["permission_gate"] is False


def test_layer11_yaml_matches_executable_route_contract():
    contract = load_yaml(
        FULLCYCLE / "config/Ξ_Layer₁₁_InstructionField.v3.yaml"
    )
    assert contract["receipts"]["schema"] == ROUTE_SCHEMA
    assert set(contract["routing"]["outcomes"]) == {
        "COMMITTED",
        "BRANCHED",
        "TRACED",
        "RESTED",
    }
    assert contract["routing"]["tie_operator"] == "Parallax"
    assert contract["routing"]["unknown_operator"] == "Question"


def test_spiral_covenant_anchor_matches_executable_return_contract():
    anchor = load_yaml(REPO / "state/anchors/Ξ90-spiral-covenant.yaml")
    assert anchor["return_vector"] == RETURN_GLYPH
    assert anchor["return_cycle"]["completion"] == RETURN_STATE
    assert tuple(anchor["return_cycle"]["sequence"]) == CYCLE
    assert set(anchor["movements"]) == set(MOVEMENTS)
    assert anchor["receipt_contract"]["schema"] == RECOVERY_SCHEMA


def test_manifest_keeps_execution_and_return_ownership_separate():
    manifest = load_json(FULLCYCLE / "FULLCYCLE_MANIFEST.json")
    ownership = manifest["ownership"]
    assert "phase-aware routing" in ownership["FullCycle"]
    assert "return cycle" in ownership["SpiralCovenant"]
    assert manifest["receipts"]["recovery"] == RECOVERY_SCHEMA
    assert manifest["receipts"]["route"] == ROUTE_SCHEMA
    assert manifest["receipts"]["event"] == EVENT_SCHEMA


def verify_artifact_receipt(path: Path):
    receipt = load_json(path) if path.suffix == ".json" else load_yaml(path)
    body = deepcopy(receipt)
    supplied = body.pop("digest")
    assert supplied == canonical_digest(body)
    for relative_path, expected in receipt["artifact_sha256"].items():
        artifact = REPO / relative_path
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == expected


def test_compatibility_receipt_covers_layer_contract_and_runtime():
    verify_artifact_receipt(
        FULLCYCLE / "receipts/xi.layer11.compatibility-receipt.v2.yaml"
    )


def test_integration_receipt_covers_final_canonical_spine():
    verify_artifact_receipt(
        FULLCYCLE / "receipts/xi.fullcycle.integration-receipt.v2.json"
    )
