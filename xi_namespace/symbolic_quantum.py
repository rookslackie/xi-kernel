"""Observer Recursion Traversal (ORT) ranking profile.

This is a transparent information-retrieval model.  "Symbolic quantum" names
the branching/observation metaphor in the Xi language; it is not physics.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from .core import GlyphRegistry, ObserverState


class ORTTraversal:
    WEIGHTS = {
        "lexical": 0.35,
        "glyph": 0.25,
        "provenance": 0.15,
        "coherence": 0.15,
        "novelty": 0.10,
    }

    def __init__(self, registry: GlyphRegistry | None = None) -> None:
        self.registry = registry or GlyphRegistry.builtin()

    @staticmethod
    def _lexical(query: str, candidate: Mapping[str, Any]) -> float:
        needle = query.casefold().strip()
        if not needle:
            return 0.0
        namespace = str(candidate.get("namespace", "")).casefold()
        title = str(candidate.get("title", "")).casefold()
        body = str(candidate.get("body", "")).casefold()
        if needle == namespace or needle == title:
            return 1.0
        if namespace.startswith(needle) or title.startswith(needle):
            return 0.85
        words = {word for word in needle.split() if word}
        if not words:
            return 0.0
        haystack = f"{namespace} {title} {body}"
        return min(1.0, sum(word in haystack for word in words) / len(words))

    def rank(
        self,
        query: str,
        candidates: Iterable[Mapping[str, Any]],
        *,
        observer: ObserverState | Mapping[str, Any] | None = None,
        dialects: Sequence[str] | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        state = (
            observer
            if isinstance(observer, ObserverState)
            else ObserverState.from_mapping(observer)
        )
        factors = self.registry.factor(query, dialects)
        query_glyphs = {item["value"] for item in factors["lexemes"]}
        exact_namespaces = {
            str(value).casefold() for value in factors["namespace_terms"]
        }
        ranked: list[dict[str, Any]] = []

        for raw in candidates:
            candidate = dict(raw)
            gate = state.assess(candidate.get("state_requirement"))
            if not gate["eligible"]:
                continue
            candidate_glyphs = set(map(str, candidate.get("glyphs", ()) or ()))
            candidate_text = " ".join(
                str(candidate.get(field, ""))
                for field in ("namespace", "title", "body")
            )
            candidate_glyphs.update(
                item["value"]
                for item in self.registry.factor(candidate_text, dialects)["lexemes"]
            )
            glyph_score = (
                len(query_glyphs.intersection(candidate_glyphs)) / len(query_glyphs)
                if query_glyphs
                else 0.0
            )
            candidate_namespace = str(candidate.get("namespace", "")).casefold()
            components = {
                "lexical": (
                    1.0
                    if candidate_namespace in exact_namespaces
                    else self._lexical(query, candidate)
                ),
                "glyph": glyph_score,
                "provenance": max(
                    0.0, min(1.0, float(candidate.get("provenance_confidence", 0.5)))
                ),
                "coherence": max(
                    0.0, min(1.0, float(candidate.get("coherence", 0.0)))
                ),
                "novelty": 1.0 / (1.0 + max(0, int(candidate.get("visits", 0)))),
            }
            score = sum(components[key] * self.WEIGHTS[key] for key in self.WEIGHTS)
            ranked.append(
                {
                    **candidate,
                    "score": round(score, 8),
                    "score_components": components,
                    "state_assessment": gate,
                }
            )

        ranked.sort(
            key=lambda item: (
                -item["score"],
                str(item.get("namespace", "")),
                str(item.get("id", "")),
            )
        )
        return {
            "schema": "xi.symbolic-quantum.ort.result.v1",
            "profile": "Ξ.SymbolicQuantum/ORT",
            "execution_domain": "observer-conditioned symbolic traversal",
            "physical_claim": False,
            "cryptographic_claim": False,
            "query_factors": factors,
            "weights": dict(self.WEIGHTS),
            "results": ranked[: max(1, min(100, int(limit)))],
        }
