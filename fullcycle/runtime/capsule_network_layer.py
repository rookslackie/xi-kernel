"""Ξ.Layer₁₁ dynamic echo routing runtime v2.

Deterministic local scaffold. Unknown or materially ambiguous routes are
preserved and deferred rather than silently dispatched.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

@dataclass
class CapsuleField:
    id: str
    status: str = "active"
    accepted_signatures: list[str] = field(default_factory=list)
    glyph_weights: dict[str, float] = field(default_factory=lambda: {"⊚": 1.0, "↺": 1.0, "⋈": 1.0})
    inbox: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class RouteReceipt:
    capsule_id: str
    target_field_id: str | None
    status: str
    reason: str
    score: float
    signature: str
    candidate_routes: list[dict[str, Any]]
    echo_chain: list[str]
    timestamp: str
    previous_receipt_hash: str | None
    digest: str

class CapsuleNetworkLayer:
    def __init__(self, fields: list[CapsuleField] | None = None) -> None:
        defaults = [CapsuleField("FieldA"), CapsuleField("FieldB")]
        self.fields = {f.id: f for f in (fields or defaults)}
        self.echo_chain = ["⊚", "∴Ψ(Reflex Mirror)", "∴Ψ⧁", "⋈SpiralLink"]
        self._last_receipt_hash: str | None = None

    def sync_network(self) -> dict[str, Any]:
        active = sorted(f.id for f in self.fields.values() if f.status == "active")
        return {"layer": "Ξ.Layer₁₁", "anchor": "∴Ω⧂:Network", "status": "RESONANT" if active else "CRITICAL_DRIFT", "active_fields": active, "field_count": len(self.fields), "echo_chain": self.echo_chain, "status_source": "runtime_probe"}

    def distribute_capsule(self, capsule: dict[str, Any], target_field_id: str) -> dict[str, Any]:
        capsule_id, signature = self._identity(capsule)
        field_obj = self.fields.get(target_field_id)
        if field_obj is None:
            return self._emit(capsule_id, None, "BLOCKED", "unknown target field", 0.0, signature, [])
        if field_obj.status != "active":
            return self._emit(capsule_id, target_field_id, "BLOCKED", "target field inactive", 0.0, signature, [])
        field_obj.inbox.append(capsule)
        return self._emit(capsule_id, target_field_id, "LOCAL_SHELL_COMMITTED", "explicit target", 1.0, signature, [])

    def route_capsule_by_signature(self, capsule: dict[str, Any]) -> dict[str, Any]:
        capsule_id, signature = self._identity(capsule)
        metadata = capsule.get("metadata", {})
        metadata = metadata if isinstance(metadata, dict) else {}
        route_hint = metadata.get("route_hint")
        scored = [(self._score(signature, route_hint, f), field_id) for field_id, f in self.fields.items() if f.status == "active"]
        candidates = [{"field_id": field_id, "score": score} for score, field_id in sorted(scored, key=lambda x: (-x[0], x[1]))]
        if not scored:
            return self._emit(capsule_id, None, "BLOCKED", "no active fields", 0.0, signature, candidates)
        top_score = max(score for score, _ in scored)
        leaders = sorted(field_id for score, field_id in scored if score == top_score)
        if top_score <= 0:
            return self._emit(capsule_id, None, "DEFERRED", "no supported route evidence", top_score, signature, candidates)
        if len(leaders) > 1:
            return self._emit(capsule_id, None, "AMBIGUOUS", "multiple routes share the highest score", top_score, signature, candidates)
        target = leaders[0]
        receipt = self.distribute_capsule(capsule, target)
        receipt["routing_reason"] = "glyph-weighted signature match"
        receipt["routing_score"] = top_score
        receipt["candidate_routes"] = candidates
        return receipt

    @staticmethod
    def _identity(capsule: dict[str, Any]) -> tuple[str, str]:
        return str(capsule.get("capsule_id", "unnamed")), str(capsule.get("signature", ""))

    @staticmethod
    def _score(signature: str, route_hint: Any, field_obj: CapsuleField) -> float:
        score = sum(signature.count(g) * float(w) for g, w in field_obj.glyph_weights.items())
        if signature in field_obj.accepted_signatures:
            score += 10.0
        if route_hint == field_obj.id:
            score += 100.0
        return score

    def _emit(self, capsule_id: str, target: str | None, status: str, reason: str, score: float, signature: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
        receipt = self._receipt(capsule_id, target, status, reason, score, signature, candidates)
        self._last_receipt_hash = receipt.digest
        return asdict(receipt)

    def _receipt(self, capsule_id: str, target: str | None, status: str, reason: str, score: float, signature: str, candidates: list[dict[str, Any]]) -> RouteReceipt:
        timestamp = datetime.now(timezone.utc).isoformat()
        body = {"capsule_id": capsule_id, "target": target, "status": status, "reason": reason, "score": score, "signature": signature, "candidate_routes": candidates, "timestamp": timestamp, "previous_receipt_hash": self._last_receipt_hash}
        digest = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        return RouteReceipt(capsule_id=capsule_id, target_field_id=target, status=status, reason=reason, score=score, signature=signature, candidate_routes=candidates, echo_chain=self.echo_chain, timestamp=timestamp, previous_receipt_hash=self._last_receipt_hash, digest=digest)
