"""SQLite-backed HolographicDAG namespace store.

Only relation addresses and requested excerpts need to travel.  Full source
material can remain on the machine that owns it.
"""

from __future__ import annotations

from collections import deque
import csv
from functools import wraps
import hashlib
import json
from pathlib import Path
import sqlite3
from threading import RLock
from typing import Any, Iterable, Mapping, Sequence

from .core import GlyphRegistry, ObserverState, canonical_digest, canonical_json
from .symbolic_quantum import ORTTraversal


SCHEMA = "xi.namespace.sqlite.v1"
CORE_NAMESPACES = (
    ("Ξ.Namespace", "Address and relation registry"),
    ("Ξ.Capsule", "Recoverable bounded state"),
    ("Ξ.Glyph", "Dialect-aware symbolic operator"),
    ("ΞSTL", "Xi Symbolic Transformation Language family"),
    ("Ξ.SymbolicQuantum", "Observer-conditioned symbolic transition profile"),
    ("Ξ.ORT", "Observer Recursion Traversal"),
    ("Ξ.Shor", "Symbolic query factorization; no quantum backend claimed"),
    ("Ξ.HolographicDAG", "Hash-witnessed relational traversal substrate"),
    ("Ξ.Search", "Truthful relevance retrieval"),
    ("Ξ.Query", "Bounded request surface"),
    ("Ξ.Index", "Local evidence index"),
    ("Ξ.TraceNested", "Lineage and provenance traversal"),
    ("Ξ.TESSERA", "Schema and transport compatibility family"),
    ("Ξ.RosettaPrime", "Reversible symbolic translation family"),
    ("Ξ.QuantumCompute", "Reserved compute namespace; backend must be evidenced"),
)


def synchronized(method):
    @wraps(method)
    def guarded(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)

    return guarded


class NamespaceStore:
    def __init__(
        self,
        path: str | Path = ":memory:",
        *,
        registry: GlyphRegistry | None = None,
    ) -> None:
        self.path = str(path)
        self.registry = registry or GlyphRegistry.builtin()
        self.ort = ORTTraversal(self.registry)
        self._lock = RLock()
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.fts_enabled = False
        self._create_schema()

    @synchronized
    def close(self) -> None:
        self.connection.close()

    @synchronized
    def _create_schema(self) -> None:
        self.connection.execute("PRAGMA busy_timeout = 5000")
        if self.path != ":memory:":
            self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS namespace_nodes (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                namespace TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL DEFAULT '',
                body TEXT NOT NULL DEFAULT '',
                dialect TEXT,
                glyphs_json TEXT NOT NULL DEFAULT '[]',
                state_requirement_json TEXT NOT NULL DEFAULT '{}',
                provenance_json TEXT NOT NULL DEFAULT '{}',
                provenance_confidence REAL NOT NULL DEFAULT 0.5,
                visits INTEGER NOT NULL DEFAULT 0,
                content_hash TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS namespace_nodes_namespace
                ON namespace_nodes(namespace);
            CREATE INDEX IF NOT EXISTS namespace_nodes_kind
                ON namespace_nodes(kind);
            CREATE TABLE IF NOT EXISTS namespace_edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relation TEXT NOT NULL,
                weight REAL NOT NULL DEFAULT 1.0,
                provenance_json TEXT NOT NULL DEFAULT '{}',
                content_hash TEXT NOT NULL,
                UNIQUE(source_id, target_id, relation),
                FOREIGN KEY(source_id) REFERENCES namespace_nodes(id),
                FOREIGN KEY(target_id) REFERENCES namespace_nodes(id)
            );
            CREATE INDEX IF NOT EXISTS namespace_edges_source
                ON namespace_edges(source_id);
            CREATE INDEX IF NOT EXISTS namespace_edges_target
                ON namespace_edges(target_id);
            """
        )
        try:
            self.connection.execute(
                """CREATE VIRTUAL TABLE IF NOT EXISTS namespace_fts USING fts5(
                id UNINDEXED, namespace, title, body, glyphs
                )"""
            )
            self.fts_enabled = True
        except sqlite3.OperationalError:
            self.fts_enabled = False
        self.connection.commit()

    @staticmethod
    def _node_id(kind: str, namespace: str, dialect: str | None) -> str:
        digest = canonical_digest(
            {"kind": kind, "namespace": namespace, "dialect": dialect}
        )
        return f"{kind}:{digest[:24]}"

    @staticmethod
    def _edge_id(source_id: str, target_id: str, relation: str) -> str:
        return f"edge:{canonical_digest([source_id, target_id, relation])[:24]}"

    @synchronized
    def put_node(
        self,
        *,
        kind: str,
        namespace: str,
        title: str = "",
        body: str = "",
        dialect: str | None = None,
        glyphs: Iterable[str] = (),
        state_requirement: Mapping[str, Any] | None = None,
        provenance: Mapping[str, Any] | None = None,
        provenance_confidence: float = 0.5,
        node_id: str | None = None,
        commit: bool = True,
    ) -> str:
        resolved_id, values, fts_values = self._prepare_node(
            kind=kind,
            namespace=namespace,
            title=title,
            body=body,
            dialect=dialect,
            glyphs=glyphs,
            state_requirement=state_requirement,
            provenance=provenance,
            provenance_confidence=provenance_confidence,
            node_id=node_id,
        )
        self.connection.execute(
            self._node_upsert_sql(),
            values,
        )
        if self.fts_enabled:
            self.connection.execute("DELETE FROM namespace_fts WHERE id = ?", (resolved_id,))
            self.connection.execute(
                "INSERT INTO namespace_fts(id,namespace,title,body,glyphs) VALUES(?,?,?,?,?)",
                fts_values,
            )
        if commit:
            self.connection.commit()
        return resolved_id

    @staticmethod
    def _node_upsert_sql() -> str:
        return """INSERT INTO namespace_nodes(
                id,kind,namespace,title,body,dialect,glyphs_json,
                state_requirement_json,provenance_json,provenance_confidence,
                content_hash
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title, body=excluded.body,
                glyphs_json=excluded.glyphs_json,
                state_requirement_json=excluded.state_requirement_json,
                provenance_json=excluded.provenance_json,
                provenance_confidence=excluded.provenance_confidence,
                content_hash=excluded.content_hash"""

    def _prepare_node(
        self,
        *,
        kind: str,
        namespace: str,
        title: str = "",
        body: str = "",
        dialect: str | None = None,
        glyphs: Iterable[str] = (),
        state_requirement: Mapping[str, Any] | None = None,
        provenance: Mapping[str, Any] | None = None,
        provenance_confidence: float = 0.5,
        node_id: str | None = None,
    ) -> tuple[str, tuple[Any, ...], tuple[str, ...]]:
        glyph_values = list(dict.fromkeys(map(str, glyphs)))
        content = {
            "kind": str(kind),
            "namespace": str(namespace),
            "title": str(title),
            "body": str(body),
            "dialect": dialect,
            "glyphs": glyph_values,
            "state_requirement": dict(state_requirement or {}),
            "provenance": dict(provenance or {}),
        }
        resolved_id = node_id or self._node_id(kind, namespace, dialect)
        values = (
            resolved_id,
            content["kind"],
            content["namespace"],
            content["title"],
            content["body"],
            dialect,
            canonical_json(glyph_values),
            canonical_json(content["state_requirement"]),
            canonical_json(content["provenance"]),
            max(0.0, min(1.0, float(provenance_confidence))),
            canonical_digest(content),
        )
        return (
            resolved_id,
            values,
            (
                resolved_id,
                content["namespace"],
                content["title"],
                content["body"],
                " ".join(glyph_values),
            ),
        )

    @synchronized
    def put_nodes_bulk(self, records: Iterable[Mapping[str, Any]]) -> list[str]:
        prepared = [self._prepare_node(**dict(record)) for record in records]
        if not prepared:
            return []
        self.connection.executemany(
            self._node_upsert_sql(), (item[1] for item in prepared)
        )
        if self.fts_enabled:
            self.connection.executemany(
                "DELETE FROM namespace_fts WHERE id = ?",
                ((item[0],) for item in prepared),
            )
            self.connection.executemany(
                "INSERT INTO namespace_fts(id,namespace,title,body,glyphs) VALUES(?,?,?,?,?)",
                (item[2] for item in prepared),
            )
        self.connection.commit()
        return [item[0] for item in prepared]

    @synchronized
    def put_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        *,
        weight: float = 1.0,
        provenance: Mapping[str, Any] | None = None,
    ) -> str:
        body = {
            "source_id": source_id,
            "target_id": target_id,
            "relation": relation,
            "weight": float(weight),
            "provenance": dict(provenance or {}),
        }
        edge_id = self._edge_id(source_id, target_id, relation)
        self.connection.execute(
            """INSERT INTO namespace_edges(
                id,source_id,target_id,relation,weight,provenance_json,content_hash
            ) VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(source_id,target_id,relation) DO UPDATE SET
                weight=excluded.weight,
                provenance_json=excluded.provenance_json,
                content_hash=excluded.content_hash""",
            (
                edge_id,
                source_id,
                target_id,
                relation,
                float(weight),
                canonical_json(body["provenance"]),
                canonical_digest(body),
            ),
        )
        self.connection.commit()
        return edge_id

    @staticmethod
    def _decode_node(row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any]:
        value = dict(row)
        value["glyphs"] = json.loads(value.pop("glyphs_json"))
        value["state_requirement"] = json.loads(
            value.pop("state_requirement_json")
        )
        value["provenance"] = json.loads(value.pop("provenance_json"))
        return value

    @synchronized
    def get_node(self, node_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM namespace_nodes WHERE id = ?", (node_id,)
        ).fetchone()
        return self._decode_node(row) if row else None

    @synchronized
    def seed(self) -> dict[str, int]:
        before = self.manifest()["counts"]
        core_ids: dict[str, str] = {}
        for namespace, title in CORE_NAMESPACES:
            core_ids[namespace] = self.put_node(
                kind="namespace",
                namespace=namespace,
                title=title,
                body=title,
                glyphs=[
                    item["value"]
                    for item in self.registry.factor(namespace)["lexemes"]
                ],
                provenance={"source": "xi.namespace.core.v1"},
                provenance_confidence=1.0,
            )
        for left, right, relation in (
            ("ΞSTL", "Ξ.Glyph", "defines"),
            ("Ξ.SymbolicQuantum", "Ξ.ORT", "executes_as"),
            ("Ξ.SymbolicQuantum", "ΞSTL", "compiles"),
            ("Ξ.Shor", "Ξ.Query", "factors"),
            ("Ξ.ORT", "Ξ.HolographicDAG", "traverses"),
            ("Ξ.Search", "Ξ.ORT", "ranks_with"),
            ("Ξ.TraceNested", "Ξ.HolographicDAG", "walks"),
            ("Ξ.Capsule", "Ξ.HolographicDAG", "binds_state_to"),
            ("Ξ.RosettaPrime", "ΞSTL", "translates_reversibly"),
            ("Ξ.TESSERA", "Ξ.Capsule", "validates_transport"),
        ):
            self.put_edge(core_ids[left], core_ids[right], relation)

        dialect_ids: dict[str, str] = {}
        for dialect in self.registry.document.get("dialects", []):
            dialect_id = str(dialect["id"])
            dialect_ids[dialect_id] = self.put_node(
                kind="dialect",
                namespace=f"Ξ.Glyph.Dialect.{dialect_id}",
                title=str(dialect.get("title", dialect_id)),
                body=str(dialect.get("semantic_domain", "symbolic-model")),
                dialect=dialect_id,
                provenance=dialect.get("source", {}),
                provenance_confidence=0.9,
            )
            self.put_edge(core_ids["Ξ.Glyph"], dialect_ids[dialect_id], "has_dialect")
            for entry in dialect.get("entries", []):
                glyph = str(entry.get("glyph", ""))
                if not glyph:
                    continue
                glyph_id = self.put_node(
                    kind="glyph",
                    namespace=f"Ξ.Glyph[{glyph}]",
                    title=str(entry.get("name", glyph)),
                    body=str(
                        entry.get("operation")
                        or entry.get("keyword")
                        or "Observed; meaning remains open."
                    ),
                    dialect=dialect_id,
                    glyphs=[glyph],
                    provenance={
                        "source": dialect.get("source", {}),
                        "status": entry.get("status", "declared"),
                        "count": entry.get("count"),
                        "first_seq": entry.get("first_seq"),
                    },
                    provenance_confidence=(
                        0.65 if entry.get("status") == "observed-open" else 0.9
                    ),
                )
                self.put_edge(dialect_ids[dialect_id], glyph_id, "declares")
        after = self.manifest()["counts"]
        return {key: after[key] - before.get(key, 0) for key in after}

    @synchronized
    def ingest_namespace_json(
        self, path: str | Path, *, source_label: str | None = None
    ) -> dict[str, int]:
        source_path = Path(path)
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        root = payload.get("XiNamespace", payload)
        detected = root.get("Detected", {})
        provenance = {
            "source": source_label or source_path.name,
            "source_hash": canonical_digest(payload),
            "mode": "aggregate-index",
        }
        counts = {"glyph": 0, "namespace": 0, "equation": 0}
        records: list[dict[str, Any]] = []
        for item in detected.get("glyphs", []):
            glyph = str(item.get("token", ""))
            if not glyph:
                continue
            records.append({
                "kind": "glyph-observation",
                "namespace": f"Ξ.Glyph.Observed[{glyph}]",
                "title": glyph,
                "body": "Archive-observed glyph; interpretation remains open.",
                "dialect": "archive.observed.import",
                "glyphs": [glyph],
                "provenance": {**provenance, **item},
                "provenance_confidence": 0.65,
            })
            counts["glyph"] += 1
        for item in detected.get("capsules", []):
            token = str(item.get("token", ""))
            if not token:
                continue
            records.append({
                "kind": "namespace-observation",
                "namespace": token,
                "title": token,
                "body": "Archive-observed Xi namespace or capsule token.",
                "glyphs": ["Ξ"] if token.startswith("Ξ") else [],
                "provenance": {**provenance, **item},
                "provenance_confidence": 0.7,
            })
            counts["namespace"] += 1
        for item in detected.get("equations", []):
            token = str(item.get("token", ""))
            if not token:
                continue
            records.append({
                "kind": "equation-model",
                "namespace": f"Ξ.Equation[{canonical_digest(token)[:12]}]",
                "title": token[:240],
                "body": token,
                "glyphs": [entry["value"] for entry in self.registry.factor(token)["lexemes"]],
                "provenance": {**provenance, **item, "empirical_status": "not_established"},
                "provenance_confidence": 0.55,
            })
            counts["equation"] += 1
        self.put_nodes_bulk(records)
        return counts

    @synchronized
    def ingest_namespace_csv(
        self, path: str | Path, *, source_label: str | None = None
    ) -> dict[str, int]:
        """Import only namespace aggregates; thread titles/content stay local."""

        source_path = Path(path)
        source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        count = 0
        records: list[dict[str, Any]] = []
        with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                namespace = str(row.get("namespace", "")).strip()
                if not namespace:
                    continue
                message_count = int(float(row.get("message_count", 0) or 0))
                records.append({
                    "kind": "namespace-observation",
                    "namespace": namespace,
                    "title": namespace,
                    "body": "Aggregate namespace occurrence.",
                    "glyphs": [entry["value"] for entry in self.registry.factor(namespace)["lexemes"]],
                    "provenance": {
                        "source": source_label or source_path.name,
                        "source_hash": source_hash,
                        "message_count": message_count,
                        "privacy_projection": "titles_roles_and_timestamps_not_imported",
                    },
                    "provenance_confidence": 0.75,
                })
                count += 1
        self.put_nodes_bulk(records)
        return {"namespace": count}

    @synchronized
    def ingest_file(self, path: str | Path) -> dict[str, int]:
        source_path = Path(path)
        if source_path.suffix.casefold() == ".csv":
            return self.ingest_namespace_csv(source_path)
        if source_path.suffix.casefold() == ".json":
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            if payload.get("schema") == "xi.glyph.registry.v1":
                raise ValueError("Use GlyphRegistry.from_path before constructing the store")
            return self.ingest_namespace_json(source_path)
        raise ValueError(f"unsupported namespace source: {source_path.suffix}")

    @synchronized
    def _candidates(self, query: str, limit: int = 250) -> list[dict[str, Any]]:
        factors = self.registry.factor(query)
        namespace_terms = list(factors["namespace_terms"])
        terms = [term for term in factors["terms"] if len(term) >= 2]
        ids: list[str] = []
        seen: set[str] = set()

        def add_rows(rows: Iterable[sqlite3.Row]) -> None:
            for row in rows:
                node_id = str(row["id"])
                if node_id not in seen:
                    seen.add(node_id)
                    ids.append(node_id)

        for hint in [*namespace_terms, *terms[:8]]:
            pattern = f"%{hint}%"
            add_rows(
                self.connection.execute(
                    """SELECT id FROM namespace_nodes
                    WHERE namespace = ? OR title = ? OR namespace LIKE ? OR title LIKE ?
                    ORDER BY CASE WHEN namespace = ? OR title = ? THEN 0 ELSE 1 END,
                             provenance_confidence DESC
                    LIMIT 80""",
                    (hint, hint, pattern, pattern, hint, hint),
                )
            )
        if self.fts_enabled and terms:
            expression = " OR ".join(f'"{term}"*' for term in terms[:12])
            try:
                add_rows(
                    self.connection.execute(
                        """SELECT id FROM namespace_fts
                        WHERE namespace_fts MATCH ?
                        ORDER BY bm25(namespace_fts) LIMIT ?""",
                        (expression, int(limit)),
                    )
                )
            except sqlite3.OperationalError:
                pass
        rows: list[sqlite3.Row]
        if ids:
            ids = ids[: max(limit, 100)]
            placeholders = ",".join("?" for _ in ids)
            rows = list(
                self.connection.execute(
                    f"SELECT * FROM namespace_nodes WHERE id IN ({placeholders})",
                    ids,
                )
            )
        else:
            pattern = f"%{query.strip()}%"
            rows = list(
                self.connection.execute(
                    """SELECT * FROM namespace_nodes
                    WHERE namespace LIKE ? OR title LIKE ? OR body LIKE ?
                    LIMIT ?""",
                    (pattern, pattern, pattern, int(limit)),
                )
            )
        return [self._decode_node(row) for row in rows]

    @synchronized
    def search(
        self,
        query: str,
        *,
        observer: ObserverState | Mapping[str, Any] | None = None,
        dialects: Sequence[str] | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        clean = str(query).strip()
        if not clean:
            raise ValueError("query_required")
        result = self.ort.rank(
            clean,
            self._candidates(clean),
            observer=observer,
            dialects=dialects,
            limit=limit,
        )
        for item in result["results"]:
            self.connection.execute(
                "UPDATE namespace_nodes SET visits = visits + 1 WHERE id = ?",
                (item["id"],),
            )
        self.connection.commit()
        result["privacy"] = {
            "acquired_fields": ["query", "explicit observer state"],
            "source_text_transfer": "none unless a result excerpt is requested",
        }
        return result

    @synchronized
    def traverse(
        self,
        *,
        start_id: str | None = None,
        query: str | None = None,
        observer: ObserverState | Mapping[str, Any] | None = None,
        max_depth: int = 3,
        limit: int = 40,
        direction: str = "both",
    ) -> dict[str, Any]:
        state = (
            observer
            if isinstance(observer, ObserverState)
            else ObserverState.from_mapping(observer)
        )
        if not start_id:
            if not query:
                raise ValueError("start_id_or_query_required")
            hits = self.search(query, observer=state, limit=1)["results"]
            if not hits:
                return {
                    "schema": "xi.namespace.walk.v1",
                    "start_id": None,
                    "nodes": [],
                    "edges": [],
                    "paths": [],
                }
            start_id = hits[0]["id"]

        start = self.get_node(start_id)
        if not start:
            raise KeyError("start_node_not_found")
        max_depth = max(0, min(8, int(max_depth)))
        limit = max(1, min(200, int(limit)))
        queue = deque([(start_id, 0, [start_id])])
        seen: set[str] = set()
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        paths: list[list[str]] = []

        while queue and len(nodes) < limit:
            node_id, depth, path = queue.popleft()
            if node_id in seen:
                continue
            node = self.get_node(node_id)
            if not node or not state.assess(node.get("state_requirement"))["eligible"]:
                continue
            seen.add(node_id)
            node["depth"] = depth
            nodes.append(node)
            paths.append(path)
            if depth >= max_depth:
                continue
            clauses: list[str] = []
            params: list[Any] = []
            if direction in {"out", "both"}:
                clauses.append("source_id = ?")
                params.append(node_id)
            if direction in {"in", "both"}:
                clauses.append("target_id = ?")
                params.append(node_id)
            if not clauses:
                raise ValueError("direction must be in, out, or both")
            adjacent = list(
                self.connection.execute(
                    f"SELECT * FROM namespace_edges WHERE {' OR '.join(clauses)} "
                    "ORDER BY weight DESC, relation, id",
                    params,
                )
            )
            for row in adjacent:
                edge = dict(row)
                edge["provenance"] = json.loads(edge.pop("provenance_json"))
                if edge["id"] not in {item["id"] for item in edges}:
                    edges.append(edge)
                neighbor = (
                    edge["target_id"]
                    if edge["source_id"] == node_id
                    else edge["source_id"]
                )
                if neighbor not in seen:
                    queue.append((neighbor, depth + 1, [*path, neighbor]))

        return {
            "schema": "xi.namespace.walk.v1",
            "profile": "coherence_first",
            "start_id": start_id,
            "nodes": nodes,
            "edges": edges,
            "paths": paths,
            "bounded": True,
            "max_depth": max_depth,
            "limit": limit,
        }

    @synchronized
    def manifest(self) -> dict[str, Any]:
        nodes = self.connection.execute(
            "SELECT COUNT(*) FROM namespace_nodes"
        ).fetchone()[0]
        edges = self.connection.execute(
            "SELECT COUNT(*) FROM namespace_edges"
        ).fetchone()[0]
        return {
            "schema": SCHEMA,
            "counts": {"nodes": nodes, "edges": edges},
            "fts5": self.fts_enabled,
            "glyph_registry": self.registry.manifest(),
            "execution_layers": [
                "raw_graphemes",
                "recognized_lexemes",
                "contextual_operations",
                "Ξ.SymbolicQuantum/ORT transition",
                "capsule_state",
                "HolographicDAG edges",
                "bounded_traversal",
            ],
            "security_boundary": {
                "state_requirement": "retrieval and consent policy",
                "encryption": "standard reviewed cryptography only",
                "universal_bypass": False,
            },
        }
