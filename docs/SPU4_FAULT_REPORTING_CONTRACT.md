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
| `dissonance[7:0]` | Saturating absolute value of the Quadray gasket residual \(|A+B+C+D|\). `0` means zero residual; `0xff` means saturated or larger. Monotone and correct across the **full reachable range** (±131072) since the 2026-08-16 width fix — before that a maximal residual could read `0x00`. Exported by both `spu4_core` and `spu4_standalone_top` from one shared module. | No; it is an invariant telemetry value. |
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

## Signal-boundary finding — RESOLVED 2026-08-15 (T7.4)

**Decision: option 2, add the port and re-anchor.** `spu4_standalone_top` now
carries `dissonance[7:0]`, so the allowed wording below is true for the
standalone wrapper and the signal table above is accurate as written. The
history that led here is kept below because the cost trade is worth preserving.

Implementation, all measured on this tree:

- The residual expression is **one shared module**, `spu4_dissonance.v`,
  instantiated by both `spu4_core` and `spu4_standalone_top`. Core and wrapper
  must never report different residuals for the same state; sharing the module
  makes that structural. *(It was a copied expression in two files until
  2026-08-16, kept in step only by a comment. They had already diverged once —
  T7.4 found the wrapper had no port at all — and the width bug below then had
  to be fixed twice.)*
- The probe's UART line was extended so the value is **observable on silicon**.
  A port that reaches no pin would have re-anchored the bitstream while proving
  nothing about the signal, making the bench session pure cost.
- `spu4_standalone_top_tb` now asserts it, checking the **saturated** `0xFF`
  produced by the QROT residual rather than the laminar `0x00`, because `0x00`
  is also what an unconnected or stuck-at-zero port reads.

| Variant | LUT4 | ALU | DFF | Bitstream | Golden line |
|---|---|---|---|---|---|
| Baseline (07-08 silicon) | 835 | 390 | 336 | `9599f5e4…22664` | 36-char |
| Port only, not exposed | 865 | 390 | 336 | `6457e31e…630890` | 36-char |
| Port + UART (adopted by T7.4) | 979 | 460 | 336 | `cbd6f83a…e6ed06` | 41-char |
| **+ 19-bit width fix (current)** | **982** | **462** | **336** | **`0061b02f…56d67c`** | **41-char, unchanged** |

The adopted line is `SPU4:P A=0000 B=0155 C=0155 D=0155 R=FF`. The field is
**`R`**, not `E`: `E=` already denotes an error code on the IROTC and
series-stream probes, where `00` is the healthy value, whereas the healthy
SPU-4 fixture reads `FF`. `R=FF` is correct and expected — the QROT fixture
settles at A=0, B=C=D=0x155, a residual of 0x3FF that saturates — so this
probe's fixture is deliberately not a zero-residual state.

The port-only row reproduces the 2026-08-14 attempt's figures and its predicted
hash exactly, which independently confirms both that measurement and this one.

**Width limit — FIXED 2026-08-16.** The shared expression sign-extended to
17 bits and summed four 16-bit signed addends, whose true range (±131072)
needs 19. A large residual therefore wrapped before the saturation test saw
it and could read *small* — `A=B=C=D=0x8000`, the maximum reachable residual,
reported `0x00`, i.e. perfectly laminar.

Widened to 19 bits (18 holds the range, but negating −131072 in 18-bit signed
wraps back to itself, so the abs step needs the extra bit). Covered by
`hardware/tests/spu4/spu4_dissonance_width_tb.v` — 2016 checks against an
independent 32-bit reference, verified non-vacuous by replaying against the
old expression. Full write-up: `hardware_evidence.md` §3.2j.1.

**Cost: +3 LUT4, +2 ALU, 0 DFF**, and the bitstream moves
`cbd6f83a…` → `0061b02f…` (982 / 462 / 336, 160.38 MHz, reproduced 2×). The
**golden line does not change** — the QROT fixture's 0x3FF saturates under
both widths — so the §3.2j bench re-run that T7.4 already owed now validates
both changes in one session. That is why the fix was taken before the bench
run rather than after.

With this closed, `dissonance` **is** a reliable saturating magnitude across
the full reachable input range. It remains, per the base contract above, a
telemetry value and not a universal fault indicator.

**Outstanding: §3.2j needs a bench re-run.** The 2026-07-08 silicon proof and
its golden line are superseded by this change. `docs/hardware_evidence.md`
§3.2j retains the flashed hash as the record of what ran on the board, marked
superseded; it must not be cited as current until the probe is re-run and the
new 41-char line observed. Apply the standing bench discipline: N≥10 per
condition with a positive control.

## Signal-boundary finding, 2026-08-14 — the original open question

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

*Decided 2026-08-15: option 2, with the probe telemetry extended so the bench
session proves the signal rather than only re-anchoring the hash. See the
RESOLVED section above.*

The chiral-adder overflow remains genuinely unexported, and its row is
unchanged.

## Follow-on package

A future hardened wrapper may add sticky fault latches, explicit overflow and
protocol faults, reset recovery, and an independent fault-injection oracle.
That is a separate product option. It must not be implied by the base SPU-4
claim and should be added only with RTL, trace, poison, and silicon evidence.
