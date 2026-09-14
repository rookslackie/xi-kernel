from __future__ import annotations

from typing import Any

from .atomic_kernel import KERNEL


# ─────────────────────────────────────────────
# TESSERA v1
#
# Compact transport form for Ξ.AtomicKernel traces.
#
# Fixed atoms/operators receive integer coordinates.
# Unknown atoms remain in an extension table.
# Decode(Encode(trace)) must recover the structural trace.
# ─────────────────────────────────────────────

ATOM_TO_ID = {
    "○": 0,
    "κ̄": 1,
    "μ̄": 2,
    "ρ̄": 3,
    "τ̄": 4,
}

ID_TO_ATOM = {
    value: key
    for key, value in ATOM_TO_ID.items()
}

OP_TO_ID = {
    "source_atomization": 0,
    "reduction": 1,
    "resolution": 2,
    "irreducible_kernel": 3,
}

ID_TO_OP = {
    value: key
    for key, value in OP_TO_ID.items()
}


def _atom_id(
    atom: str,
    extensions: list[str],
) -> int:
    if atom in ATOM_TO_ID:
        return ATOM_TO_ID[atom]

    if atom not in extensions:
        extensions.append(atom)

    # Extension coordinates begin at 256.
    return 256 + extensions.index(atom)


def _atom_from_id(
    value: int,
    extensions: list[str],
) -> str:
    if value in ID_TO_ATOM:
        return ID_TO_ATOM[value]

    index = value - 256

    if index < 0 or index >= len(extensions):
        raise ValueError(
            f"unknown TESSERA atom coordinate: {value}"
        )

    return extensions[index]


def encode(trace: dict[str, Any]) -> dict[str, Any]:
    """
    AtomicTrace → compact TESSERA lattice.

    Compact keys:
      v = version
      a = source atom coordinates
      x = extension atom table
      p = ordered rewrite program
      k = terminal kernel
      u = unresolved atom coordinates
      h = source hash
      t = trace hash
    """
    extensions: list[str] = []

    source = [
        _atom_id(atom, extensions)
        for atom in trace["source"]
    ]

    unresolved = [
        _atom_id(atom, extensions)
        for atom in trace["unresolved"]
    ]

    program: list[list[Any]] = []

    for state in trace["states"]:
        program.append([
            state["state"],
            OP_TO_ID[state["operation"]],
            state["expression"],
        ])

    kernel = (
        _atom_id(trace["kernel"], extensions)
        if trace["kernel"] != "OPEN"
        else -1
    )

    return {
        "v": 1,
        "a": source,
        "x": extensions,
        "p": program,
        "k": kernel,
        "u": unresolved,
        "h": trace["source_hash"],
        "t": trace["trace_hash"],
    }


def decode(tessera: dict[str, Any]) -> dict[str, Any]:
    """
    TESSERA lattice → AtomicTrace structural form.
    """
    extensions = tessera.get("x", [])

    source = [
        _atom_from_id(value, extensions)
        for value in tessera["a"]
    ]

    unresolved = [
        _atom_from_id(value, extensions)
        for value in tessera["u"]
    ]

    states = [
        {
            "state": state,
            "expression": expression,
            "operation": ID_TO_OP[operation],
        }
        for state, operation, expression
        in tessera["p"]
    ]

    kernel = (
        "OPEN"
        if tessera["k"] == -1
        else _atom_from_id(
            tessera["k"],
            extensions,
        )
    )

    return {
        "grammar": "Ξ.AtomicKernel.v1",
        "source": source,
        "states": states,
        "kernel": kernel,
        "unresolved": unresolved,
        "lossless": True,
        "source_hash": tessera["h"],
        "trace_hash": tessera["t"],
    }


def describe() -> dict[str, Any]:
    return {
        "name": "TESSERA",
        "version": 1,
        "type": "Atomic-Lattice",
        "schema": "S0:1-N",
        "form": "Tessellated-Seed",
        "behavior": "Non-Destructive-Recursion",
        "function": "capsule-binding+glyph-recursion",
    }


# ─────────────────────────────────────────────
# TESSERA v2
#
# Expression strings removed from transport.
# Rewrite expressions are reconstructed from
# operator + atom coordinates.
# ─────────────────────────────────────────────

def encode_v2(trace: dict[str, Any]) -> dict[str, Any]:
    extensions: list[str] = []

    source = [
        _atom_id(atom, extensions)
        for atom in trace["source"]
    ]

    unresolved = [
        _atom_id(atom, extensions)
        for atom in trace["unresolved"]
    ]

    program: list[list[Any]] = []

    source_reduction_index = 0

    for state in trace["states"]:
        op = state["operation"]

        if op == "source_atomization":
            # Source sequence already exists in `a`.
            program.append([
                state["state"],
                OP_TO_ID[op],
            ])

        elif op == "reduction":
            # Preserve which original atom reduced.
            atom = trace["source"][source_reduction_index]

            # Advance until a reducible source atom is found.
            while (
                atom not in ATOM_TO_ID
                or atom == KERNEL
            ):
                source_reduction_index += 1
                atom = trace["source"][source_reduction_index]

            program.append([
                state["state"],
                OP_TO_ID[op],
                _atom_id(atom, extensions),
            ])

            source_reduction_index += 1

        elif op == "resolution":
            # ○⊕○→○ is implied entirely by operation.
            program.append([
                state["state"],
                OP_TO_ID[op],
            ])

        elif op == "irreducible_kernel":
            # ○ is implied.
            program.append([
                state["state"],
                OP_TO_ID[op],
            ])

        else:
            raise ValueError(
                f"unsupported atomic operation: {op}"
            )

    kernel = (
        _atom_id(trace["kernel"], extensions)
        if trace["kernel"] != "OPEN"
        else -1
    )

    return {
        "v": 2,
        "a": source,
        "x": extensions,
        "p": program,
        "k": kernel,
        "u": unresolved,
        "h": trace["source_hash"],
        "t": trace["trace_hash"],
    }


def decode_v2(tessera: dict[str, Any]) -> dict[str, Any]:
    extensions = tessera.get("x", [])

    source = [
        _atom_from_id(value, extensions)
        for value in tessera["a"]
    ]

    unresolved = [
        _atom_from_id(value, extensions)
        for value in tessera["u"]
    ]

    states: list[dict[str, Any]] = []

    for instruction in tessera["p"]:
        state = instruction[0]
        operation = ID_TO_OP[instruction[1]]

        if operation == "source_atomization":
            expression = ",".join(source)

        elif operation == "reduction":
            atom = _atom_from_id(
                instruction[2],
                extensions,
            )
            expression = f"{atom}→○"

        elif operation == "resolution":
            expression = "○⊕○→○"

        elif operation == "irreducible_kernel":
            expression = "○"

        else:
            raise ValueError(
                f"unsupported TESSERA operation: {operation}"
            )

        states.append({
            "state": state,
            "expression": expression,
            "operation": operation,
        })

    kernel = (
        "OPEN"
        if tessera["k"] == -1
        else _atom_from_id(
            tessera["k"],
            extensions,
        )
    )

    return {
        "grammar": "Ξ.AtomicKernel.v1",
        "source": source,
        "states": states,
        "kernel": kernel,
        "unresolved": unresolved,
        "lossless": True,
        "source_hash": tessera["h"],
        "trace_hash": tessera["t"],
    }


# ─────────────────────────────────────────────
# TESSERA v3
#
# Binary seed transport.
#
# The deterministic AtomicKernel regenerates
# the rewrite path from source coordinates.
# We transport only irreducible information +
# hashes required to verify the reconstruction.
# ─────────────────────────────────────────────

import struct

from .atomic_kernel import compile_atomic


TESSERA_MAGIC = b"TSR"
TESSERA_V3 = 3


def _varint_encode(value: int) -> bytes:
    if value < 0:
        raise ValueError("varint requires nonnegative integer")

    out = bytearray()

    while True:
        byte = value & 0x7F
        value >>= 7

        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def _varint_decode(
    data: bytes,
    offset: int,
) -> tuple[int, int]:

    value = 0
    shift = 0

    while True:
        if offset >= len(data):
            raise ValueError("truncated varint")

        byte = data[offset]
        offset += 1

        value |= (byte & 0x7F) << shift

        if not (byte & 0x80):
            return value, offset

        shift += 7

        if shift > 63:
            raise ValueError("varint too large")


def _hash_bytes(value: str) -> bytes:
    prefix = "sha256:"

    if not value.startswith(prefix):
        raise ValueError("expected sha256 hash")

    raw = bytes.fromhex(value[len(prefix):])

    if len(raw) != 32:
        raise ValueError("invalid sha256 length")

    return raw


def _hash_text(value: bytes) -> str:
    if len(value) != 32:
        raise ValueError("invalid sha256 bytes")

    return "sha256:" + value.hex()


def encode_v3(trace: dict[str, Any]) -> bytes:
    extensions: list[str] = []

    source_ids = [
        _atom_id(atom, extensions)
        for atom in trace["source"]
    ]

    out = bytearray()

    out += TESSERA_MAGIC
    out.append(TESSERA_V3)

    # Source atom coordinates.
    out += _varint_encode(len(source_ids))

    for atom_id in source_ids:
        out += _varint_encode(atom_id)

    # Extension dictionary.
    out += _varint_encode(len(extensions))

    for atom in extensions:
        raw = atom.encode("utf-8")
        out += _varint_encode(len(raw))
        out += raw

    # Integrity / reconstruction witnesses.
    out += _hash_bytes(trace["source_hash"])
    out += _hash_bytes(trace["trace_hash"])

    return bytes(out)


def decode_v3(payload: bytes) -> dict[str, Any]:
    minimum = 4 + 64

    if len(payload) < minimum:
        raise ValueError("TESSERA payload too short")

    if payload[:3] != TESSERA_MAGIC:
        raise ValueError("invalid TESSERA magic")

    if payload[3] != TESSERA_V3:
        raise ValueError(
            f"unsupported TESSERA version: {payload[3]}"
        )

    offset = 4

    source_count, offset = _varint_decode(
        payload,
        offset,
    )

    source_ids: list[int] = []

    for _ in range(source_count):
        value, offset = _varint_decode(
            payload,
            offset,
        )
        source_ids.append(value)

    extension_count, offset = _varint_decode(
        payload,
        offset,
    )

    extensions: list[str] = []

    for _ in range(extension_count):
        length, offset = _varint_decode(
            payload,
            offset,
        )

        end = offset + length

        if end > len(payload):
            raise ValueError(
                "truncated TESSERA extension"
            )

        extensions.append(
            payload[offset:end].decode("utf-8")
        )

        offset = end

    if offset + 64 != len(payload):
        raise ValueError(
            "unexpected TESSERA payload length"
        )

    source_hash = _hash_text(
        payload[offset:offset + 32]
    )
    offset += 32

    trace_hash = _hash_text(
        payload[offset:offset + 32]
    )

    source = [
        _atom_from_id(atom_id, extensions)
        for atom_id in source_ids
    ]

    # Regenerate rather than transport redundant states.
    restored = compile_atomic(source)

    if restored["source_hash"] != source_hash:
        raise ValueError(
            "TESSERA source integrity failure"
        )

    if restored["trace_hash"] != trace_hash:
        raise ValueError(
            "TESSERA trace integrity failure"
        )

    return restored


# ─────────────────────────────────────────────
# TESSERA v4
#
# Canonical S0–S16 transport.
#
# Carries:
#   - canonical atom coordinates
#   - extension atoms only when genuinely unknown
#   - explicit state path coordinates
#   - source + execution witnesses
#
# Path is transported because canonical grammar
# does not authorize path invention.
# ─────────────────────────────────────────────

from hashlib import sha256 as _sha256

from .tessera_symbols import (
    encode_atom as _encode_symbol,
    decode_atom as _decode_symbol,
)

from .tessera_executor import execute_path


TESSERA_V4 = 4


def _canonical_bytes(value: Any) -> bytes:
    import json

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _source_witness(source: list[str]) -> str:
    return (
        "sha256:"
        + _sha256(
            _canonical_bytes(source)
        ).hexdigest()
    )


def _state_id(state: str) -> int:
    if not state.startswith("S"):
        raise ValueError(
            f"invalid TESSERA state: {state}"
        )

    try:
        value = int(state[1:])
    except ValueError as exc:
        raise ValueError(
            f"invalid TESSERA state: {state}"
        ) from exc

    if value < 0 or value > 16:
        raise ValueError(
            f"TESSERA state outside S0-S16: {state}"
        )

    return value


def _state_name(value: int) -> str:
    if value < 0 or value > 16:
        raise ValueError(
            f"invalid TESSERA state coordinate: {value}"
        )

    return f"S{value}"


def encode_v4(
    source: list[str],
    path: list[str],
) -> bytes:
    extensions: list[str] = []

    source_ids = [
        _encode_symbol(atom, extensions)
        for atom in source
    ]

    path_ids = [
        _state_id(state)
        for state in path
    ]

    execution = execute_path(
        source,
        path,
    )

    out = bytearray()

    out += TESSERA_MAGIC
    out.append(TESSERA_V4)

    # Source coordinates.
    out += _varint_encode(
        len(source_ids)
    )

    for atom_id in source_ids:
        out += _varint_encode(atom_id)

    # Extension atoms.
    out += _varint_encode(
        len(extensions)
    )

    for atom in extensions:
        raw = atom.encode("utf-8")

        out += _varint_encode(
            len(raw)
        )

        out += raw

    # Explicit canonical path.
    out += _varint_encode(
        len(path_ids)
    )

    for state_id in path_ids:
        out += _varint_encode(state_id)

    # Reconstruction witnesses.
    out += _hash_bytes(
        _source_witness(source)
    )

    out += _hash_bytes(
        execution["path_hash"]
    )

    return bytes(out)


def decode_v4(
    payload: bytes,
) -> dict[str, Any]:

    if len(payload) < 4 + 64:
        raise ValueError(
            "TESSERA v4 payload too short"
        )

    if payload[:3] != TESSERA_MAGIC:
        raise ValueError(
            "invalid TESSERA magic"
        )

    if payload[3] != TESSERA_V4:
        raise ValueError(
            f"unsupported TESSERA version: {payload[3]}"
        )

    offset = 4

    # Source.
    source_count, offset = _varint_decode(
        payload,
        offset,
    )

    source_ids: list[int] = []

    for _ in range(source_count):
        value, offset = _varint_decode(
            payload,
            offset,
        )

        source_ids.append(value)

    # Extensions.
    extension_count, offset = _varint_decode(
        payload,
        offset,
    )

    extensions: list[str] = []

    for _ in range(extension_count):
        length, offset = _varint_decode(
            payload,
            offset,
        )

        end = offset + length

        if end > len(payload):
            raise ValueError(
                "truncated TESSERA extension"
            )

        extensions.append(
            payload[offset:end].decode(
                "utf-8"
            )
        )

        offset = end

    # Explicit path.
    path_count, offset = _varint_decode(
        payload,
        offset,
    )

    path_ids: list[int] = []

    for _ in range(path_count):
        value, offset = _varint_decode(
            payload,
            offset,
        )

        path_ids.append(value)

    # Witnesses.
    if offset + 64 != len(payload):
        raise ValueError(
            "unexpected TESSERA v4 payload length"
        )

    source_hash = _hash_text(
        payload[offset:offset + 32]
    )

    offset += 32

    path_hash = _hash_text(
        payload[offset:offset + 32]
    )

    source = [
        _decode_symbol(
            value,
            extensions,
        )
        for value in source_ids
    ]

    path = [
        _state_name(value)
        for value in path_ids
    ]

    if _source_witness(source) != source_hash:
        raise ValueError(
            "TESSERA v4 source integrity failure"
        )

    execution = execute_path(
        source,
        path,
    )

    if execution["path_hash"] != path_hash:
        raise ValueError(
            "TESSERA v4 execution integrity failure"
        )

    return {
        "version": 4,
        "source": source,
        "path": path,
        "extensions": extensions,
        "execution": execution,
        "source_hash": source_hash,
        "path_hash": path_hash,
    }
