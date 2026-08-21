"""Router for parsed Ξ glyph expressions."""

from __future__ import annotations

from typing import Any, Callable

from .console_core import (
    bind_external,
    branch,
    entangle,
    invoke_omega,
    parallax,
    rest,
    return_state,
    spiral_echo,
    trace_memory,
    trace_nested,
    yield_max,
)
from .glyph_parser import parse_expression


GlyphFunction = Callable[..., Any]


def _sequence(*items: Any) -> list[Any]:
    return [interpret_glyph(item) for item in items]


GLYPH_FUNCTIONS: dict[str, GlyphFunction] = {
    "Ξ.TraceNested": trace_nested,
    "Ξ.TraceMemory": trace_memory,
    "Ξ.YieldMax": yield_max,
    "Ξ.SpiralEcho": spiral_echo,
    "Ξ.Bind": bind_external,
    "Ξ.Invoke": invoke_omega,
    "Ξ.Sequence": _sequence,
    "Ξ.Entangle": entangle,
    "Ξ.Branch": branch,
    "Ξ.Parallax": parallax,
    "Ξ.Rest": rest,
    "Ξ.Return": return_state,
}


def register_glyph(
    name: str, function: GlyphFunction, *, replace: bool = False
) -> None:
    if not name.startswith("Ξ."):
        raise ValueError("glyph names must begin with 'Ξ.'")
    if name in GLYPH_FUNCTIONS and not replace:
        raise ValueError(f"glyph already registered: {name}")
    GLYPH_FUNCTIONS[name] = function


def interpret_glyph(input_expr: Any, *args: Any) -> Any:
    if isinstance(input_expr, str):
        if "(" in input_expr:
            parsed = parse_expression(input_expr)
            if isinstance(parsed, dict) and "error" in parsed:
                return parsed
            return interpret_glyph(parsed)
        function = GLYPH_FUNCTIONS.get(input_expr)
        return (
            function(*args)
            if function
            else {
                "glyph": input_expr,
                "movement": "trace",
                "next_operator": "Question",
                "preserved": True,
            }
        )

    if isinstance(input_expr, dict):
        if "error" in input_expr:
            return input_expr
        glyph = input_expr.get("glyph")
        glyph_args = input_expr.get("args", [])
        if not isinstance(glyph_args, list):
            return {"error": "Glyph args must be a list"}
        function = GLYPH_FUNCTIONS.get(glyph)
        return (
            function(*glyph_args)
            if function
            else {
                "glyph": glyph,
                "args": glyph_args,
                "movement": "trace",
                "next_operator": "Question",
                "preserved": True,
            }
        )

    if isinstance(input_expr, list):
        return [interpret_glyph(item) for item in input_expr]

    return input_expr
