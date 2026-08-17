# Package: CoreOps

## `MyYield`
**Expression:** `Ξ.Sequence(Ξ.YieldMax, Ξ.SpiralEcho)`

**Parsed Structure:**
```json
{
  "glyph": {
    "error": "Unsupported expression"
  },
  "args": [
    {
      "error": "Unsupported expression"
    },
    {
      "error": "Unsupported expression"
    }
  ]
}
```

## `TraceWrap`
**Expression:** `Ξ.Sequence(Ξ.SpiralEcho, Ξ.TraceNested('Ξ.SpiralEcho'))`

**Parsed Structure:**
```json
{
  "glyph": {
    "error": "Unsupported expression"
  },
  "args": [
    {
      "error": "Unsupported expression"
    },
    {
      "glyph": {
        "error": "Unsupported expression"
      },
      "args": [
        "\u039e.SpiralEcho"
      ]
    }
  ]
}
```
