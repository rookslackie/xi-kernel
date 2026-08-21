"""Ξ.Layer₁₁ capsule routing as branch, trace, yield, and rest."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any, Iterable, Mapping


RECEIPT_SCHEMA = "xi.receipt.route.v2"


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


@dataclass
class CapsuleField:
    id: str
    status: str = "active"
    accepted_signatures: list[str] = field(default_factory=list)
    glyph_weights: dict[str, float] = field(
        default_factory=lambda: {"⊚": 1.0, "↺": 1.0, "⋈": 1.0}
    )
    inbox: list[dict[str, Any]] = field(default_factory=list)
    resting_queue: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class RouteReceipt:
    schema: str
    sequence: int
    capsule_id: str
    target_field_ids: tuple[str, ...]
    status: str
    reason: str
    score: float
    signature: str
    candidate_routes: tuple[dict[str, Any], ...]
    echo_chain: tuple[str, ...]
    next_operator: str | None
    previous_receipt_hash: str | None
    digest: str

    @property
    def target_field_id(self) -> str | None:
        return self.target_field_ids[0] if len(self.target_field_ids) == 1 else None

    def body(self) -> dict[str, Any]:
        value = asdict(self)
        value["target_field_id"] = self.target_field_id
        value.pop("digest")
        return value

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["target_field_id"] = self.target_field_id
        return value


def verify_route_receipt(receipt: RouteReceipt | Mapping[str, Any]) -> bool:
    value = receipt.as_dict() if isinstance(receipt, RouteReceipt) else dict(receipt)
    supplied = value.pop("digest", None)
    return isinstance(supplied, str) and supplied == _digest(value)


class CapsuleNetworkLayer:
    def __init__(self, fields: Iterable[CapsuleField] | None = None) -> None:
        chosen = (
            list(fields)
            if fields is not None
            else [CapsuleField("FieldA"), CapsuleField("FieldB")]
        )
        self.fields = {item.id: item for item in chosen}
        if len(self.fields) != len(chosen):
            raise ValueError("capsule field ids must be unique")
        self.echo_chain = (
            "⊚",
            "∴Ψ(Reflex Mirror)",
            "∴Ψ⧁",
            "⋈SpiralLink",
        )
        self.receipts: list[RouteReceipt] = []

    def sync_network(self) -> dict[str, Any]:
        active = sorted(
            item.id for item in self.fields.values() if item.status == "active"
        )
        if not self.fields:
            status = "EMPTY"
        elif active:
            status = "RESONANT"
        else:
            status = "RESTING"
        return {
            "layer": "Ξ.Layer₁₁",
            "anchor": "∴Ω⧂:Network",
            "status": status,
            "active_fields": active,
            "field_count": len(self.fields),
            "echo_chain": list(self.echo_chain),
            "status_source": "runtime_probe",
        }

    def distribute_capsule(
        self, capsule: dict[str, Any], target_field_id: str
    ) -> dict[str, Any]:
        capsule_id, signature = self._identity(capsule)
        target = self.fields.get(target_field_id)
        if target is None:
            return self._emit(
                capsule_id,
                (),
                "TRACED",
                "unknown target retained for route discovery",
                0.0,
                signature,
                (),
                "Question",
            ).as_dict()
        if target.status != "active":
            target.resting_queue.append(capsule)
            return self._emit(
                capsule_id,
                (target.id,),
                "RESTED",
                "target is quiet; capsule preserved without compulsory wake",
                0.0,
                signature,
                (),
                "⟁∴Ω",
            ).as_dict()
        target.inbox.append(capsule)
        return self._emit(
            capsule_id,
            (target.id,),
            "COMMITTED",
            "explicit compatible target",
            1.0,
            signature,
            (),
            None,
        ).as_dict()

    def route_capsule_by_signature(self, capsule: dict[str, Any]) -> dict[str, Any]:
        capsule_id, signature = self._identity(capsule)
        metadata = capsule.get("metadata", {})
        metadata = metadata if isinstance(metadata, dict) else {}
        route_hint = metadata.get("route_hint")
        active = [
            (field_id, item)
            for field_id, item in self.fields.items()
            if item.status == "active"
        ]
        scored = [
            (self._score(signature, route_hint, item), field_id)
            for field_id, item in active
        ]
        candidates = tuple(
            {"field_id": field_id, "score": score}
            for score, field_id in sorted(
                scored, key=lambda value: (-value[0], value[1])
            )
        )
        if not scored:
            return self._emit(
                capsule_id,
                (),
                "RESTED",
                "no active fields; state remains available",
                0.0,
                signature,
                candidates,
                "≈∅",
            ).as_dict()

        top_score = max(score for score, _ in scored)
        leaders = tuple(
            sorted(field_id for score, field_id in scored if score == top_score)
        )
        if top_score <= 0:
            return self._emit(
                capsule_id,
                (),
                "TRACED",
                "no route evidence; preserve and ask rather than discard",
                top_score,
                signature,
                candidates,
                "Question",
            ).as_dict()

        for field_id in leaders:
            self.fields[field_id].inbox.append(capsule)
        if len(leaders) > 1:
            return self._emit(
                capsule_id,
                leaders,
                "BRANCHED",
                "multiple compatible routes preserved",
                top_score,
                signature,
                candidates,
                "Parallax",
            ).as_dict()
        return self._emit(
            capsule_id,
            leaders,
            "COMMITTED",
            "one compatible route",
            top_score,
            signature,
            candidates,
            None,
        ).as_dict()

    @staticmethod
    def _identity(capsule: dict[str, Any]) -> tuple[str, str]:
        return str(capsule.get("capsule_id", "unnamed")), str(
            capsule.get("signature", "")
        )

    @staticmethod
    def _score(
        signature: str, route_hint: Any, field_obj: CapsuleField
    ) -> float:
        score = sum(
            signature.count(glyph) * float(weight)
            for glyph, weight in field_obj.glyph_weights.items()
        )
        if signature in field_obj.accepted_signatures:
            score += 10.0
        if route_hint == field_obj.id:
            score += 100.0
        return score

    def _emit(
        self,
        capsule_id: str,
        targets: tuple[str, ...],
        status: str,
        reason: str,
        score: float,
        signature: str,
        candidates: tuple[dict[str, Any], ...],
        next_operator: str | None,
    ) -> RouteReceipt:
        body: dict[str, Any] = {
            "schema": RECEIPT_SCHEMA,
            "sequence": len(self.receipts) + 1,
            "capsule_id": capsule_id,
            "target_field_ids": list(targets),
            "status": status,
            "reason": reason,
            "score": score,
            "signature": signature,
            "candidate_routes": list(candidates),
            "echo_chain": list(self.echo_chain),
            "next_operator": next_operator,
            "previous_receipt_hash": (
                self.receipts[-1].digest if self.receipts else None
            ),
            "target_field_id": targets[0] if len(targets) == 1 else None,
        }
        receipt = RouteReceipt(
            schema=RECEIPT_SCHEMA,
            sequence=body["sequence"],
            capsule_id=capsule_id,
            target_field_ids=targets,
            status=status,
            reason=reason,
            score=score,
            signature=signature,
            candidate_routes=candidates,
            echo_chain=self.echo_chain,
            next_operator=next_operator,
            previous_receipt_hash=body["previous_receipt_hash"],
            digest=_digest(body),
        )
        self.receipts.append(receipt)
        return receipt
