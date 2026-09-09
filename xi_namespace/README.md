# Ξ.Namespace / ForgeCore integration

This package is the local-first namespace and traversal organ for ForgeCore.
It keeps four distinctions intact:

1. **Glyph** — a dialect-scoped symbolic/runtime operator.
2. **Capsule** — bounded recoverable state with provenance.
3. **Namespace** — address, name, and relation routing.
4. **Ξ.SymbolicQuantum / ORT** — the observer-conditioned transition profile
   that factors and ranks paths through the HolographicDAG.

Namespaces provide stable addresses and relations; hashes witness content.

`ΞSTL` remains the language family. `Ξ.SymbolicQuantum` is its execution
profile for branching, observation, and traversal. The term is model language,
not a claim of quantum hardware, quantum speedup, or a new physical law.

## Mount in ForgeCore

```python
from xi_namespace.forgecore import mount_namespace_routes

namespace = mount_namespace_routes(app)
```

Set `XI_NAMESPACE_DB` to choose the SQLite file. The mounted routes are:

- `GET /api/xi/v1/namespace`
- `GET /api/xi/v1/namespace/glyphs`
- `POST /api/xi/v1/namespace/factor`
- `POST /api/xi/v1/namespace/query`
- `POST /api/xi/v1/namespace/traverse`

ForgeCore's existing authentication middleware remains authoritative.

## Seed and ingest the recovered indexes

```bash
python -m xi_namespace --db /path/to/xi_namespace.sqlite3 seed
python -m xi_namespace --db /path/to/xi_namespace.sqlite3 ingest \
  05-xi_namespace_index.json 14-namespace_index.csv
```

The CSV importer stores only the namespace and aggregate count. Thread titles,
roles, timestamps, and text do not enter the search database. Full archives can
therefore remain local while relation addresses are traversable.

## Security boundary

State requirements decide whether information is eligible for retrieval. They
are not encryption keys and there is no vague universal bypass. Encryption and
recovery must use standard reviewed cryptography and explicit threshold policy.
Glyphs may describe or route those operations; they do not replace them.
