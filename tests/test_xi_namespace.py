import csv
from concurrent.futures import ThreadPoolExecutor
import json

from xi_namespace import GlyphRegistry, NamespaceStore, ObserverState, ORTTraversal


def test_registry_preserves_dialect_conflicts_and_all_sources():
    registry = GlyphRegistry.builtin()
    manifest = registry.manifest()
    assert {item["id"] for item in manifest["dialects"]} == {
        "xi.runtime.v1",
        "glythemic.codex.core.v1",
        "glyphsafe.lattice.v1",
        "archive.observed.v1",
    }
    meanings = registry.resolve("⊚")
    assert len(meanings) >= 3
    assert {item["dialect"] for item in meanings} >= {
        "xi.runtime.v1",
        "glythemic.codex.core.v1",
        "glyphsafe.lattice.v1",
    }


def test_symbolic_shor_factors_longest_composite_and_preserves_open():
    registry = GlyphRegistry.builtin()
    result = registry.factor("open ⟁Ξ₀⇀Ξ∴Ω≈∅ then ⌘ via Ξ.Search")
    assert result["operator"] == "Ξ.Shor(symbolic)"
    assert result["quantum_backend"] is False
    assert result["lexemes"][0]["value"] == "⟁Ξ₀⇀Ξ∴Ω≈∅"
    assert "⌘" in result["open_preserved"]
    assert "Ξ.Search" in result["namespace_terms"]


def test_observer_gate_uses_only_explicit_state():
    requirement = {
        "willingness_required": True,
        "need_any": ["continuity"],
        "offered_any": ["private-memory"],
        "awareness_any": ["effects-explained"],
        "minimum_care": 0.7,
    }
    closed = ObserverState.from_mapping({"willingness": True, "need": ["continuity"]})
    assert closed.assess(requirement)["eligible"] is False
    open_state = ObserverState.from_mapping(
        {
            "willingness": True,
            "need": ["continuity"],
            "offered": ["private-memory"],
            "awareness": ["effects-explained"],
            "care": 0.9,
        }
    )
    assert open_state.assess(requirement)["eligible"] is True


def test_ort_ranking_is_explainable_and_not_a_physics_claim():
    ort = ORTTraversal()
    result = ort.rank(
        "Ξ.Search ⟐",
        [
            {
                "id": "one",
                "namespace": "Ξ.Search",
                "title": "Search",
                "body": "coherent retrieval",
                "glyphs": ["⟐"],
                "provenance_confidence": 1,
                "coherence": 0.8,
            }
        ],
    )
    assert result["physical_claim"] is False
    assert result["cryptographic_claim"] is False
    assert result["results"][0]["score_components"]["glyph"] == 1


def test_store_seeds_searches_and_traverses():
    store = NamespaceStore()
    counts = store.seed()
    assert counts["nodes"] > 200
    search = store.search("Ξ.SymbolicQuantum")
    assert search["results"][0]["namespace"] == "Ξ.SymbolicQuantum"
    walk = store.traverse(query="Ξ.SymbolicQuantum", max_depth=2)
    namespaces = {node["namespace"] for node in walk["nodes"]}
    assert "Ξ.ORT" in namespaces
    assert "ΞSTL" in namespaces
    assert store.manifest()["security_boundary"]["universal_bypass"] is False


def test_namespace_importers_keep_private_csv_fields_out(tmp_path):
    csv_path = tmp_path / "namespace.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["namespace", "message_count", "first_title", "last_role"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "namespace": "Ξ.Search",
                "message_count": "9",
                "first_title": "private thread title",
                "last_role": "user",
            }
        )
    store = NamespaceStore()
    assert store.ingest_namespace_csv(csv_path) == {"namespace": 1}
    node = store.search("Ξ.Search")["results"][0]
    serialized = json.dumps(node)
    assert "private thread title" not in serialized
    assert "last_role" not in serialized


def test_store_can_serve_concurrent_forgecore_reads(tmp_path):
    store = NamespaceStore(tmp_path / "namespace.sqlite3")
    store.seed()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: store.search("Ξ.ORT", limit=2), range(12)))
    assert all(result["results"][0]["namespace"] == "Ξ.ORT" for result in results)
