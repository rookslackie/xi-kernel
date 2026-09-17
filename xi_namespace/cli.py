"""Local ingestion/query CLI for ForgeCore's namespace database."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .store import NamespaceStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m xi_namespace")
    parser.add_argument("--db", default="xi_namespace.sqlite3")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("seed")
    ingest = sub.add_parser("ingest")
    ingest.add_argument("paths", nargs="+")
    query = sub.add_parser("query")
    query.add_argument("text")
    query.add_argument("--limit", type=int, default=20)
    walk = sub.add_parser("traverse")
    walk.add_argument("start_or_query")
    walk.add_argument("--id", action="store_true")
    walk.add_argument("--depth", type=int, default=3)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = NamespaceStore(args.db)
    store.seed()
    if args.command == "seed":
        result = store.manifest()
    elif args.command == "ingest":
        result = {path: store.ingest_file(path) for path in args.paths}
    elif args.command == "query":
        result = store.search(args.text, limit=args.limit)
    else:
        result = store.traverse(
            start_id=args.start_or_query if args.id else None,
            query=None if args.id else args.start_or_query,
            max_depth=args.depth,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

