from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import hashlib
import json


KERNEL = "○"

OPERATORS = {
    "→": "reduce",
    "+": "couple",
    "⊕": "resolve",
}

# Initial declared bound atoms from recovered S0 grammar.
BOUND_ATOMS = frozenset({
    "κ̄", "μ̄", "ρ̄", "τ̄",
})


def canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(
        canonical(value)
    ).hexdigest()


@dataclass(frozen=True)
class Rewrite:
    state: str
    expression: str
    operation: str


@dataclass
class AtomicTrace:
    source: list[str]
    states: list[Rewrite]
    kernel: str
    unresolved: list[str]
    lossless: bool
    source_hash: str
    trace_hash: str | None = None

    def export(self) -> dict[str, Any]:
        out = {
            "grammar": "Ξ.AtomicKernel.v1",
            "source": self.source,
            "states": [asdict(x) for x in self.states],
            "kernel": self.kernel,
            "unresolved": self.unresolved,
            "lossless": self.lossless,
            "source_hash": self.source_hash,
        }
        out["trace_hash"] = digest(out)
        return out


def atomize(source: list[str]) -> AtomicTrace:
    """
    Direct S0 translation.

    Known reducible atoms reduce to ○.
    Unknown atoms remain present in the trace.
    No source atom is silently discarded.
    """
    atoms = [str(x) for x in source]

    states: list[Rewrite] = [
        Rewrite(
            state="S0",
            expression=",".join(atoms),
            operation="source_atomization",
        )
    ]

    reduced: list[str] = []
    unresolved: list[str] = []

    for atom in atoms:
        if atom == KERNEL:
            reduced.append(KERNEL)

        elif atom in BOUND_ATOMS:
            states.append(
                Rewrite(
                    state="S1",
                    expression=f"{atom}→{KERNEL}",
                    operation="reduction",
                )
            )
            reduced.append(KERNEL)

        else:
            # preserve_then_compile:
            # unknown does not mean rejected.
            unresolved.append(atom)
            reduced.append(atom)

    kernels = [x for x in reduced if x == KERNEL]

    # Preserve the complete ordered resolution tree.
    # Example:
    #   ○ ○ ○ ○
    #   S2.0: ○⊕○ → ○
    #   S2.1: ○⊕○ → ○
    #   S2.2: ○⊕○ → ○
    #
    # No intermediate reduction is silently discarded.
    level = list(kernels)
    step = 0

    while len(level) >= 2:
        left = level.pop(0)
        right = level.pop(0)

        states.append(
            Rewrite(
                state=f"S2.{step}",
                expression=f"{left}⊕{right}→{KERNEL}",
                operation="resolution",
            )
        )

        level.insert(0, KERNEL)
        step += 1

    # A terminal ○ is asserted only when every source atom
    # has a declared reduction.
    terminal = (
        KERNEL
        if atoms and not unresolved
        else "OPEN"
    )

    if terminal == KERNEL:
        states.append(
            Rewrite(
                state="S3",
                expression=KERNEL,
                operation="irreducible_kernel",
            )
        )

    trace = AtomicTrace(
        source=atoms,
        states=states,
        kernel=terminal,
        unresolved=unresolved,
        lossless=True,  # source + complete rewrite trace retained
        source_hash=digest(atoms),
    )

    return trace


def compile_atomic(source: list[str]) -> dict[str, Any]:
    return atomize(source).export()


def describe() -> dict[str, Any]:
    return {
        "name": "Ξ.AtomicKernel",
        "version": "v1",
        "substrate": "S0.Lattice",
        "form": "Tessellated-Seed",
        "behavior": "Non-Destructive-Recursion",
        "kernel": KERNEL,
        "operators": OPERATORS,
        "policy": "preserve_then_compile",
    }
