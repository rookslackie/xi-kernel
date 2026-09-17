"""Dialect-safe glyph compilation and bounded observer state.

The name ``Ξ.Shor(symbolic)`` is intentionally scoped: it factors a query into
declared composites, glyphs, namespaces, and ordinary terms.  It is not Shor's
quantum factoring algorithm and claims neither quantum hardware nor speedup.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
from importlib.resources import files
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, bytes)):
        values = (values,)
    return tuple(dict.fromkeys(str(value) for value in values if str(value)))


def _bounded_float(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class ObserverState:
    """Only explicitly offered state participates in traversal eligibility."""

    willingness: bool | None = None
    need: tuple[str, ...] = field(default_factory=tuple)
    offered: tuple[str, ...] = field(default_factory=tuple)
    awareness: tuple[str, ...] = field(default_factory=tuple)
    care: float = 1.0
    scope: str = "local"

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "ObserverState":
        raw = value or {}
        care = _bounded_float(raw.get("care", 1.0), 1.0)
        return cls(
            willingness=raw.get("willingness"),
            need=_unique(raw.get("need", ())),
            offered=_unique(raw.get("offered", ())),
            awareness=_unique(raw.get("awareness", ())),
            care=care,
            scope=str(raw.get("scope", "local")),
        )

    def assess(self, requirement: Mapping[str, Any] | None) -> dict[str, Any]:
        rule = dict(requirement or {})
        reasons: list[str] = []
        if rule.get("willingness_required") and self.willingness is not True:
            reasons.append("willingness_not_offered")

        checks = (
            ("need_any", set(self.need), "need_not_present"),
            ("offered_any", set(self.offered), "context_not_offered"),
            ("awareness_any", set(self.awareness), "awareness_not_present"),
        )
        for key, present, reason in checks:
            required = set(_unique(rule.get(key, ()) or ()))
            if required and not required.intersection(present):
                reasons.append(reason)

        minimum_care = _bounded_float(rule.get("minimum_care", 0.0))
        if self.care < minimum_care:
            reasons.append("care_below_requirement")

        allowed_scopes = set(_unique(rule.get("allowed_scopes", ()) or ()))
        if allowed_scopes and self.scope not in allowed_scopes:
            reasons.append("scope_not_allowed")

        return {
            "eligible": not reasons,
            "reasons": reasons,
            "state_used": {
                "willingness": self.willingness,
                "need": list(self.need),
                "offered": list(self.offered),
                "awareness": list(self.awareness),
                "care": self.care,
                "scope": self.scope,
            },
            "law": "willingness ∩ need ∩ offered awareness, tempered by care",
        }


class GlyphRegistry:
    """A registry that preserves dialect conflicts and open glyphs."""

    def __init__(self, document: Mapping[str, Any]) -> None:
        self.document = dict(document)
        self.schema = str(self.document.get("schema", "xi.glyph.registry.v1"))
        self._dialects = {
            str(dialect["id"]): dict(dialect)
            for dialect in self.document.get("dialects", [])
        }
        self._entries: dict[str, list[dict[str, Any]]] = {}
        self._glyphs_by_dialect: dict[str, set[str]] = {}
        self._factor_cache: dict[tuple[str, ...], dict[str, tuple[str, ...]]] = {}
        for dialect_id, dialect in self._dialects.items():
            self._glyphs_by_dialect[dialect_id] = set()
            for raw in dialect.get("entries", []):
                entry = dict(raw)
                glyph = str(entry.get("glyph", ""))
                if not glyph:
                    continue
                entry["dialect"] = dialect_id
                entry["semantic_domain"] = dialect.get(
                    "semantic_domain", "symbolic-model"
                )
                self._entries.setdefault(glyph, []).append(entry)
                self._glyphs_by_dialect[dialect_id].add(glyph)

    @classmethod
    def builtin(cls) -> "GlyphRegistry":
        path = files("xi_namespace").joinpath("data/glyph_registry.v1.json")
        return cls(json.loads(path.read_text(encoding="utf-8")))

    @classmethod
    def from_path(cls, path: str | Path) -> "GlyphRegistry":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    @property
    def dialects(self) -> tuple[str, ...]:
        return tuple(self._dialects)

    def entries(self, dialects: Sequence[str] | None = None) -> list[dict[str, Any]]:
        selected = set(dialects or self._dialects)
        return [
            dict(entry)
            for entries in self._entries.values()
            for entry in entries
            if entry["dialect"] in selected
        ]

    def resolve(
        self, glyph: str, dialects: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        selected = set(dialects or self._dialects)
        return [
            dict(entry)
            for entry in self._entries.get(glyph, [])
            if entry["dialect"] in selected
        ]

    def factor(
        self, text: str, dialects: Sequence[str] | None = None
    ) -> dict[str, Any]:
        """Factor text longest-declared-composite-first, preserving unknowns."""

        source = str(text)
        selected = tuple(dialects or self._dialects)
        cache_key = tuple(sorted(selected))
        declared_by_first = self._factor_cache.get(cache_key)
        if declared_by_first is None:
            declared = {
                glyph
                for dialect in selected
                for glyph in self._glyphs_by_dialect.get(dialect, ())
            }
            buckets: dict[str, list[str]] = {}
            for glyph in declared:
                buckets.setdefault(glyph[0], []).append(glyph)
            declared_by_first = {
                key: tuple(sorted(values, key=lambda value: (-len(value), value)))
                for key, values in buckets.items()
            }
            self._factor_cache[cache_key] = declared_by_first
        lexemes: list[dict[str, Any]] = []
        cursor = 0
        while cursor < len(source):
            match = next(
                (
                    glyph
                    for glyph in declared_by_first.get(source[cursor], ())
                    if source.startswith(glyph, cursor)
                ),
                None,
            )
            if match:
                lexemes.append(
                    {
                        "value": match,
                        "start": cursor,
                        "end": cursor + len(match),
                        "status": "declared",
                        "meanings": self.resolve(match, selected),
                    }
                )
                cursor += len(match)
                continue

            character = source[cursor]
            category = unicodedata.category(character)
            if (
                category.startswith("S")
                or category == "Co"
                or (
                    ord(character) > 127
                    and not character.isspace()
                    and not category.startswith("P")
                )
            ):
                lexemes.append(
                    {
                        "value": character,
                        "start": cursor,
                        "end": cursor + 1,
                        "status": "open-preserved",
                        "meanings": [],
                    }
                )
            cursor += 1

        namespaces = _unique(
            re.findall(r"Ξ(?:\.[^\s,;:()\[\]{}]+)+", source)
        )
        terms = _unique(
            match.casefold()
            for match in re.findall(r"[\w-]{2,}", source, flags=re.UNICODE)
        )
        return {
            "schema": "xi.query-factors.v1",
            "operator": "Ξ.Shor(symbolic)",
            "execution_domain": "deterministic symbolic query factorization",
            "quantum_backend": False,
            "physical_claim": False,
            "source": source,
            "dialects": list(selected),
            "lexemes": lexemes,
            "namespace_terms": list(namespaces),
            "terms": list(terms),
            "open_preserved": [
                item["value"]
                for item in lexemes
                if item["status"] == "open-preserved"
            ],
        }

    def manifest(self) -> dict[str, Any]:
        conflicts = sum(1 for meanings in self._entries.values() if len(meanings) > 1)
        return {
            "schema": self.schema,
            "status": self.document.get("status", "living"),
            "dialects": [
                {
                    "id": dialect_id,
                    "title": dialect.get("title"),
                    "semantic_domain": dialect.get("semantic_domain"),
                    "entry_count": len(dialect.get("entries", [])),
                    "source": dialect.get("source"),
                }
                for dialect_id, dialect in self._dialects.items()
            ],
            "distinct_glyph_count": len(self._entries),
            "meaning_count": sum(len(items) for items in self._entries.values()),
            "cross_dialect_conflict_count": conflicts,
            "matching_rule": self.document.get("matching_rule"),
            "open_glyph_policy": self.document.get("open_glyph_policy"),
            "semantic_boundary": self.document.get("semantic_boundary"),
            "digest": canonical_digest(self.document),
        }

    def as_dict(self) -> dict[str, Any]:
        return dict(self.document)


def observer_state_dict(state: ObserverState) -> dict[str, Any]:
    return asdict(state)
