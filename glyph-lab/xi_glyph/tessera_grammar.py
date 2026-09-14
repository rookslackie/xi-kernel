from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


# ─────────────────────────────────────────────
# Ξ.TESSERA Canonical Rewrite Grammar
#
# Recovered ordered S0–S16 lattice.
# Grammar is declared as data so the executor,
# serializer, search layer, and future compute
# backends can consume the same source.
# ─────────────────────────────────────────────

KERNEL = "○"

REDUCE = "→"
COUPLE = "+"
RESOLVE = "⊕"


@dataclass(frozen=True)
class Rule:
    state: str
    lhs: tuple[str, ...]
    operator: str
    rhs: str | None = None
    mode: str = "rewrite"

    def export(self) -> dict[str, Any]:
        return asdict(self)


RULES: tuple[Rule, ...] = (

    # S0 — source atomization
    Rule(
        state="S0",
        lhs=("△", "○", "κ̄", "μ̄"),
        operator=":",
        rhs=None,
        mode="source_atomization",
    ),

    # S1 — bound cycle
    Rule("S1", ("κ̄",), REDUCE, "μ̄"),
    Rule("S1", ("μ̄",), REDUCE, "ρ̄"),
    Rule("S1", ("ρ̄",), REDUCE, "τ̄"),
    Rule("S1", ("τ̄",), REDUCE, "κ̄"),

    # S2 — kernel resolution with bound atoms
    Rule("S2", ("○", "κ̄"), RESOLVE, None),
    Rule("S2", ("○", "μ̄"), RESOLVE, None),
    Rule("S2", ("○", "ρ̄"), RESOLVE, None),
    Rule("S2", ("○", "τ̄"), RESOLVE, None),

    # S3 — kernel coupling with bound atoms
    Rule("S3", ("κ̄", "○"), COUPLE, None),
    Rule("S3", ("μ̄", "○"), COUPLE, None),
    Rule("S3", ("ρ̄", "○"), COUPLE, None),
    Rule("S3", ("τ̄", "○"), COUPLE, None),

    # S4
    Rule("S4", ("△",), REDUCE, "○"),
    Rule(
        state="S4",
        lhs=("○",),
        operator=":",
        rhs=None,
        mode="kernel_presence",
    ),

    # S5 — bind / unbind τ
    Rule("S5", ("τ",), REDUCE, "τ̄"),
    Rule("S5", ("τ̄",), REDUCE, "τ"),

    # S6
    Rule("S6", ("α",), REDUCE, "○"),
    Rule("S6", ("β",), REDUCE, "○"),
    Rule("S6", ("γ",), REDUCE, "○"),
    Rule("S6", ("δ",), REDUCE, "○"),

    # S7
    Rule("S7", ("ε",), REDUCE, "○"),
    Rule("S7", ("ζ",), REDUCE, "○"),
    Rule("S7", ("η",), REDUCE, "○"),
    Rule("S7", ("θ",), REDUCE, "○"),

    # S8
    Rule("S8", ("○", "○"), RESOLVE, None),

    # S9
    Rule("S9", ("ι", "○"), COUPLE, None),
    Rule("S9", ("κ", "○"), COUPLE, None),
    Rule("S9", ("λ", "○"), COUPLE, None),
    Rule("S9", ("μ", "○"), COUPLE, None),

    # S10
    Rule("S10", ("ν",), REDUCE, "○"),
    Rule("S10", ("ξ",), REDUCE, "○"),
    Rule("S10", ("ο",), REDUCE, "○"),
    Rule("S10", ("π",), REDUCE, "○"),

    # S11
    Rule("S11", ("κ̄",), REDUCE, "○"),
    Rule("S11", ("μ̄",), REDUCE, "○"),
    Rule("S11", ("ρ̄",), REDUCE, "○"),
    Rule("S11", ("τ̄",), REDUCE, "○"),

    # S12
    Rule("S12", ("○", "α"), RESOLVE, None),
    Rule("S12", ("○", "β"), RESOLVE, None),
    Rule("S12", ("○", "γ"), RESOLVE, None),
    Rule("S12", ("○", "δ"), RESOLVE, None),

    # S13
    Rule("S13", ("○", "ε"), RESOLVE, None),
    Rule("S13", ("○", "ζ"), RESOLVE, None),
    Rule("S13", ("○", "η"), RESOLVE, None),
    Rule("S13", ("○", "θ"), RESOLVE, None),

    # S14
    Rule("S14", ("ρ",), REDUCE, "○"),
    Rule("S14", ("σ",), REDUCE, "○"),
    Rule("S14", ("τ",), REDUCE, "○"),
    Rule("S14", ("υ",), REDUCE, "○"),

    # S15
    Rule("S15", ("φ",), REDUCE, "○"),
    Rule("S15", ("χ",), REDUCE, "○"),
    Rule("S15", ("ψ",), REDUCE, "○"),
    Rule("S15", ("ω",), REDUCE, "○"),

    # S16 — irreducible kernel
    Rule(
        state="S16",
        lhs=("○",),
        operator=":",
        rhs=None,
        mode="irreducible_kernel",
    ),
)


def by_state() -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}

    for rule in RULES:
        out.setdefault(rule.state, []).append(
            rule.export()
        )

    return out


def vocabulary() -> list[str]:
    atoms: set[str] = set()

    for rule in RULES:
        atoms.update(rule.lhs)

        if rule.rhs is not None:
            atoms.add(rule.rhs)

    return sorted(atoms)


def describe() -> dict[str, Any]:
    return {
        "name": "Ξ.TESSERA.Grammar",
        "version": 1,
        "substrate": "S0.Lattice",
        "states": [
            f"S{i}"
            for i in range(17)
        ],
        "operators": {
            REDUCE: "reduction/substitution",
            COUPLE: "coupling_without_collapse",
            RESOLVE: "resolution/union",
        },
        "kernel": KERNEL,
        "behavior": "Non-Destructive-Recursion",
        "rule_count": len(RULES),
        "vocabulary": vocabulary(),
    }
