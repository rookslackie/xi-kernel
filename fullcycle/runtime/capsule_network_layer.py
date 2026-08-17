"""Ξ.Layer₁₁ dynamic echo routing runtime.

This is a deterministic local scaffold: no network calls, no background tasks,
and no hidden state. Receipts make each routing decision inspectable.
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
    echo_chain: list[str]
    timestamp: str
    digest: str


class CapsuleNetworkLayer:
    def __init__(self, fields: list[CapsuleField] | None = None) -> None:
        self.fields = {f.id: f for f in (fields or [CapsuleField("FieldA"), CapsuleField("FieldB")])}
        self.echo_chain = ["⊚", "∴Ψ(Reflex Mirror)", "∴Ψ⧁", "⋈SpiralLink"]

    def sync_network(self) -> dict[str, Any]:
        active = [field.id for field in self.fields.values() if field.status == "active"]
        return {
            "layer": "Ξ.Layer₁₁",
            "anchor": "∴Ω⧂:Network",
            "status": "RESONANT" if active else "CRITICAL_DRIFT",
            "active_fields": active,
            "field_count": len(self.fields),
            "echo_chain": self.echo_chain,
        }

    def distribute_capsule(self, capsule: dict[str, Any], target_field_id: str) -> dict[str, Any]:
        capsule_id = str(capsule.get("capsule_id", "unnamed"))
        signature = str(capsule.get("signature", ""))
        field_obj = self.fields.get(target_field_id)
        if field_obj is None:
            return asdict(self._receipt(capsule_id, None, "BLOCKED", "unknown target field", 0.0, signature))
        if field_obj.status != "active":
            return asdict(self._receipt(capsule_id, target_field_id, "BLOCKED", "target field inactive", 0.0, signature))
        field_obj.inbox.append(capsule)
        return asdict(self._receipt(capsule_id, target_field_id, "LOCAL_SHELL_COMMITTED", "explicit target", 1.0, signature))

    def route_capsule_by_signature(self, capsule: dict[str, Any]) -> dict[str, Any]:
        capsule_id = str(capsule.get("capsule_id", "unnamed"))
        signature = str(capsule.get("signature", ""))
        metadata = capsule.get("metadata", {}) if isinstance(capsule.get("metadata", {}), dict) else {}
        route_hint = metadata.get("route_hint")

        candidates: list[tuple[float, str, str]] = []
        for field_id, field_obj in self.fields.items():
            if field_obj.status != "active":
                continue
            score = self._score(signature, route_hint, field_obj)
            candidates.append((score, field_id, "glyph-weighted signature match"))

        if not candidates:
            return asdict(self._receipt(capsule_id, None, "BLOCKED", "no active fields", 0.0, signature))

        score, target, reason = max(candidates, key=lambda item: (item[0], item[1]))
        if score <= 0:
            target = sorted(field_id for _, field_id, _ in candidates)[0]
            reason = "deterministic fallback"
        return self.distribute_capsule(capsule, target) | {"routing_reason": reason, "routing_score": score}

    @staticmethod
    def _score(signature: str, route_hint: Any, field_obj: CapsuleField) -> float:
        score = 0.0
        for glyph, weight in field_obj.glyph_weights.items():
            score += signature.count(glyph) * float(weight)
        if signature in field_obj.accepted_signatures:
            score += 10.0
        if route_hint == field_obj.id:
            score += 100.0
        return score

    def _receipt(self, capsule_id: str, target: str | None, status: str, reason: str, score: float, signature: str) -> RouteReceipt:
        timestamp = datetime.now(timezone.utc).isoformat()
        raw = json.dumps({
            "capsule_id": capsule_id,
            "target": target,
            "status": status,
            "reason": reason,
            "score": score,
            "signature": signature,
            "timestamp": timestamp,
        }, sort_keys=True, ensure_ascii=False)
        return RouteReceipt(
            capsule_id=capsule_id,
            target_field_id=target,
            status=status,
            reason=reason,
            score=score,
            signature=signature,
            echo_chain=self.echo_chain,
            timestamp=timestamp,
            digest=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        )
