from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from typing import Any

from .tessera_grammar import (
    RULES,
    REDUCE,
    COUPLE,
    RESOLVE,
)


def canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + sha256(canonical(value)).hexdigest()


@dataclass
class Event:
    state: str
    rule_index: int
    operator: str
    lhs: list[str]
    rhs: str | None
    before: list[str]
    after: list[str]
    transformed: bool

    def export(self) -> dict[str, Any]:
        return asdict(self)


def _find_sequence(
    atoms: list[str],
    lhs: tuple[str, ...],
) -> int | None:
    width = len(lhs)

    if width == 0:
        return None

    for i in range(len(atoms) - width + 1):
        if tuple(atoms[i:i + width]) == lhs:
            return i

    return None


def execute_state(
    state: str,
    atoms: list[str],
) -> dict[str, Any]:
    """
    Execute exactly one declared TESSERA state.

    Faithfulness rule:
      explicit A → B  : transform
      bare A + B      : record coupling
      bare A ⊕ B      : record resolution
      presence/source : record only

    No consequence is invented where the grammar
    did not explicitly declare one.
    """
    current = list(atoms)
    events: list[Event] = []

    state_rules = [
        (i, rule)
        for i, rule in enumerate(RULES)
        if rule.state == state
    ]

    if not state_rules:
        raise ValueError(f"unknown TESSERA state: {state}")

    # Each rule may match once per execution pass.
    # Ordered according to canonical declaration.
    for rule_index, rule in state_rules:
        pos = _find_sequence(current, rule.lhs)

        if pos is None:
            continue

        before = list(current)
        transformed = False

        if (
            rule.operator == REDUCE
            and rule.rhs is not None
        ):
            width = len(rule.lhs)

            current = (
                current[:pos]
                + [rule.rhs]
                + current[pos + width:]
            )

            transformed = True

        elif rule.operator in (
            COUPLE,
            RESOLVE,
            ":",
        ):
            # Structural event only.
            # Preserve state unless an explicit RHS exists.
            pass

        else:
            raise ValueError(
                f"unsupported operator: {rule.operator}"
            )

        events.append(
            Event(
                state=state,
                rule_index=rule_index,
                operator=rule.operator,
                lhs=list(rule.lhs),
                rhs=rule.rhs,
                before=before,
                after=list(current),
                transformed=transformed,
            )
        )

    result = {
        "grammar": "Ξ.TESSERA.Grammar.v1",
        "state": state,
        "input": list(atoms),
        "output": current,
        "events": [
            event.export()
            for event in events
        ],
    }

    result["execution_hash"] = digest(result)

    return result


def execute_path(
    atoms: list[str],
    states: list[str],
) -> dict[str, Any]:
    """
    Execute an explicit ordered state path.

    The caller chooses the path.
    The executor does not assume S0→S16 means
    every state must always fire.
    """
    current = list(atoms)
    trace: list[dict[str, Any]] = []

    for state in states:
        step = execute_state(state, current)
        trace.append(step)
        current = step["output"]

    result = {
        "grammar": "Ξ.TESSERA.Grammar.v1",
        "path": states,
        "source": atoms,
        "terminal": current,
        "trace": trace,
    }

    result["path_hash"] = digest(result)

    return result
