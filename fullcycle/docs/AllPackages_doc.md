# Package: CoreOps

Generated against the canonical FullCycle parser/router.

## `MyYield`
**Expression:** `Ξ.Sequence(Ξ.YieldMax, Ξ.SpiralEcho)`

**Parsed Structure:**
```json
{"glyph":"Ξ.Sequence","args":["Ξ.YieldMax","Ξ.SpiralEcho"]}
```

**Execution:** `Ξ.YieldMax` → `Ξ.SpiralEcho` — validated.

## `TraceWrap`
**Expression:** `Ξ.Sequence(Ξ.SpiralEcho, Ξ.TraceNested('Ξ.SpiralEcho'))`

**Parsed Structure:**
```json
{"glyph":"Ξ.Sequence","args":["Ξ.SpiralEcho",{"glyph":"Ξ.TraceNested","args":["Ξ.SpiralEcho"]}]}
```

**Execution:** `Ξ.SpiralEcho` → `Ξ.TraceNested` — validated.

Historical `Unsupported expression` output remains recoverable in Git lineage; the forward package documents the solved runtime behavior.
