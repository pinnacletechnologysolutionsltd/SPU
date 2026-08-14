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
| `dissonance[7:0]` | Saturating absolute value of the Quadray gasket residual \(|A+B+C+D|\). `0` means zero residual; `0xff` means saturated or larger. Exported by both `spu4_core` and `spu4_standalone_top`. | No; it is an invariant telemetry value. |
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

## Signal-boundary finding, 2026-08-14 — OPEN, needs a product decision

The table above originally listed `dissonance[7:0]` without qualification while
explicitly flagging the chiral-adder overflow as unexported. That was
inconsistent. `dissonance` is a port of **`spu4_core` only**.
`spu4_standalone_top` — the wrapper the claim ledger names as the product
interface — does not carry it, and `debug_status` does not contain it
(`{seq_busy, seq_done, henosis_pulse, snap_en, whisper_en, pc[2:0]}`).

**Consequence:** the allowed wording below, *"The SPU-4 reports deterministic
completion, normalization events, and a saturating Quadray residual,"* is false
for the standalone wrapper. Do not use that sentence for a standalone-wrapper
product until this is resolved.

**Why it is not simply fixed.** Adding the port was tried on 2026-08-14 and
reverted. The residual is trivially derivable at the wrapper — same expression
as `spu4_core.v:187-194`, over ALU outputs already present — but synthesising
it grew the probe from 835 to **865 LUT4** and moved the bitstream SHA-256 from
`9599f5e4…22664` to `6457e31e…630890`. That first hash is what
`docs/hardware_evidence.md` §3.2j records as the flashed, silicon-proven
bitstream, and what T7.0 was closed on. Adding the port silently costs the
repo's bit-reproducibility of its own silicon evidence.

**The three honest options:**

1. **Narrow the wording.** Mark `dissonance` `spu4_core`-only in the table and
   drop "saturating Quadray residual" from the standalone-wrapper claim.
   Zero cost; the product interface is then telemetry-poorer than advertised.
2. **Add the port and re-anchor.** Export it, accept the new bitstream, and
   re-run the probe on hardware to re-establish §3.2j against the new SHA.
   Costs a bench session; keeps evidence and product aligned.
3. **Split the wrappers.** Keep the probe path bit-frozen as the silicon
   anchor and give the product its own wrapper that exports the residual.
   Most work, cleanest boundary long-term.

This is T7.4 territory — the tranche that selects the customer-facing wrapper —
and should be decided there rather than incidentally.

The chiral-adder overflow remains genuinely unexported, and its row is
unchanged.

## Follow-on package

A future hardened wrapper may add sticky fault latches, explicit overflow and
protocol faults, reset recovery, and an independent fault-injection oracle.
That is a separate product option. It must not be implied by the base SPU-4
claim and should be added only with RTL, trace, poison, and silicon evidence.
