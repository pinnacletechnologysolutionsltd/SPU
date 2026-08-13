# SPU-4 Sentinel — Fault-reporting contract (T7.3)

**Status:** Design decision, 2026-08-13  
**Scope:** Base reusable SPU-4 IP and its standalone wrapper

## Decision

The base SPU-4 does **not** claim comprehensive self-fault detection. It
exposes deterministic arithmetic results plus bounded telemetry signals. A
customer may use those signals to build an application-specific supervisor,
but the core must not be marketed as detecting every internal arithmetic,
protocol, or fabric fault.

This keeps the product claim aligned with the implemented design. The
SPU-13 axiomatic gatekeeper is a separate module and is not part of the SPU-4
fault contract.

## Signal meanings

| Signal | Meaning | Fault? |
|---|---|---|
| `done` | The programmed operation or sequence reached its completion condition. | No. |
| `busy` | The standalone sequencer is executing. | No. |
| `henosis_pulse` | The Euclidean ALU applied its defined fold/normalization path for an arithmetic result. | No; it is an observable normalization event. |
| `dissonance[7:0]` | Saturating absolute value of the Quadray gasket residual \(|A+B+C+D|\). `0` means zero residual; `0xff` means saturated or larger. | No; it is an invariant telemetry value. |
| `debug_status` | Wrapper state bits, including busy, done, henosis, and decoder/status indicators. | No; fields are status, not a universal fault bitmap. |
| chiral-adder `overflow` | The phinary adder crossed its configured laminar threshold during that operation. | Local event only; not currently exported by `spu4_standalone_top`. |

## Product wording

Allowed:

- “The SPU-4 reports deterministic completion, normalization events, and a
  saturating Quadray residual.”
- “The telemetry can feed a customer-defined supervisor or cluster bridge.”
- “The base core does not silently claim fault coverage beyond these defined
  signals.”

Not allowed until separately implemented and verified:

- “The SPU-4 is self-checking.”
- “The SPU-4 detects all arithmetic overflow or corruption.”
- “A zero `dissonance` value proves the computation is fault-free.”

## Follow-on package

A future hardened wrapper may add sticky fault latches, explicit overflow and
protocol faults, reset recovery, and an independent fault-injection oracle.
That is a separate product option. It must not be implied by the base SPU-4
claim and should be added only with RTL, trace, poison, and silicon evidence.
