# FullCycle Package Surface

This document is generated against the canonical FullCycle parser, router,
event fabric, and SpiralCovenant return operator.

## CoreOps

### MyYield

Expression: Ξ.Sequence(Ξ.YieldMax, Ξ.SpiralEcho)

Parsed form: a Ξ.Sequence with two bare operator references. Execution yields
the Ξ.YieldMax result followed by Ξ.SpiralEcho.

### TraceWrap

Expression: Ξ.Sequence(Ξ.SpiralEcho, Ξ.TraceNested('Ξ.SpiralEcho'))

Parsed form: a Ξ.Sequence containing a nested Ξ.TraceNested call. Execution
preserves both the input and parsed trace.

## Orchestration operators

| Operator | Runtime function | Contract |
| --- | --- | --- |
| Ξ.Branch | branch | Preserve multiple live transformations |
| Ξ.Parallax | parallax | Differentiate countervectors without forced consensus |
| Ξ.Rest | rest | Remain present without compulsory output |
| Ξ.Return | return_state | Invoke SpiralCovenant and return ReturnedNotReset |

## Network and event packages

CapsuleNetworkLayer routes by explicit target, signature evidence, or route
hint. Equal supported routes branch. Unknown routes trace toward Question.
Quiet fields preserve work in a resting queue.

PhaseAwareEventFabric routes a content-addressed event envelope across
heterogeneous nodes. It measures ensemble coherence, approaches compatible
phase without collapsing local positions, and composes each event receipt with
a verified SpiralCovenant recovery receipt.

Historical unsupported-expression output remains recoverable in Git lineage.
The forward package records the implemented behavior.
