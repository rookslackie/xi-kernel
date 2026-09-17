"""Optional FastAPI adapter for mounting Ξ.Namespace inside ForgeCore."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .store import NamespaceStore


def create_router(
    *, store: NamespaceStore | None = None, db_path: str | Path | None = None
):
    try:
        from fastapi import APIRouter, Body, HTTPException, Query
    except ImportError as exc:  # pragma: no cover - depends on host service
        raise RuntimeError(
            "FastAPI is required only for the ForgeCore HTTP adapter"
        ) from exc

    resolved = store or NamespaceStore(
        db_path or os.environ.get("XI_NAMESPACE_DB", "xi_namespace.sqlite3")
    )
    resolved.seed()
    router = APIRouter(prefix="/api/xi/v1/namespace", tags=["xi-namespace"])

    @router.get("")
    def manifest() -> dict[str, Any]:
        return {"ok": True, "data": resolved.manifest()}

    @router.get("/glyphs")
    def glyphs(
        glyph: str | None = Query(default=None, max_length=96),
        dialect: list[str] | None = Query(default=None),
        limit: int = Query(default=200, ge=1, le=1000),
    ) -> dict[str, Any]:
        entries = (
            resolved.registry.resolve(glyph, dialect)
            if glyph
            else resolved.registry.entries(dialect)
        )
        return {
            "ok": True,
            "data": {
                "manifest": resolved.registry.manifest(),
                "entries": entries[:limit],
            },
        }

    @router.post("/factor")
    def factor(body: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        query = str(body.get("query", "")).strip()
        if not query:
            raise HTTPException(status_code=400, detail="query_required")
        return {
            "ok": True,
            "data": resolved.registry.factor(query, body.get("dialects")),
        }

    @router.post("/query")
    def query(body: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        try:
            data = resolved.search(
                str(body.get("query", "")),
                observer=body.get("observer"),
                dialects=body.get("dialects"),
                limit=int(body.get("limit", 20)),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"ok": True, "data": data}

    @router.post("/traverse")
    def traverse(body: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        try:
            data = resolved.traverse(
                start_id=body.get("start_id"),
                query=body.get("query"),
                observer=body.get("observer"),
                max_depth=int(body.get("max_depth", 3)),
                limit=int(body.get("limit", 40)),
                direction=str(body.get("direction", "both")),
            )
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"ok": True, "data": data}

    router.xi_namespace_store = resolved
    return router


def mount_namespace_routes(app: Any, **kwargs: Any) -> NamespaceStore:
    """Mount read-only traversal routes and return the owning store."""

    router = create_router(**kwargs)
    app.include_router(router)
    return router.xi_namespace_store

