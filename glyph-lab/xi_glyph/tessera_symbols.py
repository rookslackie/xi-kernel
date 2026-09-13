from __future__ import annotations

from typing import Any

from .tessera_grammar import RULES


# ─────────────────────────────────────────────
# Ξ.TESSERA Canonical Symbol Coordinates
#
# Preserve v3 bootstrap coordinates forever.
# Extend by first declaration order in canonical
# S0–S16 grammar.
# ─────────────────────────────────────────────

BOOTSTRAP = [
    "○",
    "κ̄",
    "μ̄",
    "ρ̄",
    "τ̄",
]


def _declared_atoms() -> list[str]:
    ordered: list[str] = []

    def add(atom: str) -> None:
        if atom not in ordered:
            ordered.append(atom)

    for atom in BOOTSTRAP:
        add(atom)

    for rule in RULES:
        for atom in rule.lhs:
            add(atom)

        if rule.rhs is not None:
            add(rule.rhs)

    return ordered


SYMBOLS = tuple(_declared_atoms())

ATOM_TO_ID = {
    atom: index
    for index, atom in enumerate(SYMBOLS)
}

ID_TO_ATOM = {
    index: atom
    for atom, index in ATOM_TO_ID.items()
}


def encode_atom(
    atom: str,
    extensions: list[str],
) -> int:
    if atom in ATOM_TO_ID:
        return ATOM_TO_ID[atom]

    if atom not in extensions:
        extensions.append(atom)

    return 256 + extensions.index(atom)


def decode_atom(
    value: int,
    extensions: list[str],
) -> str:
    if value in ID_TO_ATOM:
        return ID_TO_ATOM[value]

    index = value - 256

    if index < 0 or index >= len(extensions):
        raise ValueError(
            f"unknown TESSERA symbol coordinate: {value}"
        )

    return extensions[index]


def describe() -> dict[str, Any]:
    return {
        "name": "Ξ.TESSERA.SymbolTable",
        "version": 1,
        "count": len(SYMBOLS),
        "extension_base": 256,
        "bootstrap_preserved": {
            atom: ATOM_TO_ID[atom]
            for atom in BOOTSTRAP
        },
        "symbols": [
            {
                "id": index,
                "atom": atom,
            }
            for index, atom in enumerate(SYMBOLS)
        ],
    }
