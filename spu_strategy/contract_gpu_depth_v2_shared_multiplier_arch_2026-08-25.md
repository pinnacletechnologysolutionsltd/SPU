**Roles:**
- **Spec Author:** Claude (architecture only — see §6, RTL still not authorized)
- **Halt-and-Flag Implementer:** unassigned
- **Integration Auditor:** `bash tools/verify_repo.sh`

---

# Engineering Contract: Tang 25K depth-v2 + Reciprocal — Shared-Multiplier Architecture
**Date:** 2026-08-25
**Contract ID:** `contract_gpu_depth_v2_shared_multiplier_arch_2026-08-25.md`
**Status:** DRAFT — architecture, not implementation

## 0. Why this exists
Both precision (reciprocal contract) and Tang 25K capacity (raster synth
probe, 5.7% baseline, 94.3% headroom) are now closed questions. What
remains is the actual RTL shape: a sequential/shared-multiplier design
for depth-v2's ~14 multiply operations, per `contract_gpu_depth_v2_scoping_2026-08-25.md`
§4b's finding that a combinational chain risks `series_stream_probe`'s
proven 305% blowup on this exact toolchain. This contract designs that
shape without yet authorizing its RTL.

## 1. Register width correction (measured, not re-estimated)
The depth-v2 contract's "40+ bit" note was the *shift amount*
(`frac_bits`, 33–34), not the accumulator's true width. Ran the existing
oracle (`software/lib/gpu_depth_v2_oracle.py`) directly to get the real
numbers rather than re-deriving by hand:

| case | A_z/B_z/C_z signed bit widths | peak per-pixel accumulator bits |
|---|---|---|
| screen-corner | 41 / 35 / 45 | 51 |
| thin sliver | 42 / 36 / 41 | 51 |
| near-degenerate | 42 / 39 / 1 | 52 |

**Correction:** the setup-time *output* coefficients (`A_z/B_z/C_z`,
after scaling by `inv_denom`) need ~42-bit signed registers, and the
per-pixel accumulator in `spu_attr_stepper.v` needs ~52-bit signed (peak
magnitude across a full 640×480 scan, seed `C_z` plus up to
640×|A_z| + 480×|B_z|). Round up to 56-bit for margin — wide, but not
unprecedented (`pade_eval_4_4.v` already carries 128–192-bit
intermediates; this is smaller than the existing Padé evaluator, not a
new category of cost).

**Second correction, 2026-08-25 (external review caught this before any
RTL was written):** `A_z/B_z/C_z`'s ~42-bit width is the final-scale
multiply's *output*, not its *input operands* — conflating the two led
directly to the wrong multiplier sizing in §2 below (now fixed). The
multiply is `|Sa| × y1`: `Sa` (the dot-product sum, *pre*-scale) is only
~35-bit signed magnitude (three ~32-bit terms summed), and `y1`
(reciprocal output) is ~17-bit magnitude. **The shared multiplier only
needs to be 35×17, not 42×42.**

## 2. Module boundaries (Lithic, ≤150 lines each) — CORRECTED 2026-08-25, TWICE
**Original decision (two independent multiplier instances) is WRONG,
shown by measurement.** First correction (still on record for the
history): `contract_gpu_mult42_isolation_probe_2026-08-25.md` measured
42×42 at 11,259 LUT4 = 48.9% — two instances would exceed the chip.
**Second correction, same day, from external review**: that 42×42
sizing was itself wrong (see §1's second correction — it used `A_z`'s
output width, not the multiply's actual operand widths). The real
measurement, `contract_gpu_mult35_corrected_probe_2026-08-25.md`: a
correctly-sized **35×17 unsigned multiplier costs 3,532 LUT4 = 15.3%**,
about a third the wrongly-sized version. The conclusion "one shared
instance, not two" survives both corrections — 2× 3,532 = 7,064 LUT4
would still fit fine, but there's no reason to pay for a second instance
either, and the sequential-FSM reasoning in §8 for why one suffices
doesn't depend on which sizing was used.

**Corrected design: ONE shared 35×17 unsigned multiplier** (magnitude-
only — see §8's note that sign is extracted and reapplied outside the
multiplier, not carried through it), selected between
`spu_reciprocal_core.v`'s 2 NR multiplies and `spu_depth_setup.v`'s 12
(9 dot-product + 3 final-scale) — 14 total serialized through a single
instance. Budget: raster (1,317) + one multiplier (3,532) = 4,849 LUT4
= **21.0%, leaving 18,191 LUT4 (79.0%) headroom** — close to the
raster-only 94.3% picture after all, now that the multiplier is sized
correctly. Still not the full 94.3%, and still doesn't include the
leading-one detector, barrel shifter, 256-entry ROM, or FSM control
logic (see §6, all still unmeasured). This changes the module boundary:
the multiplier itself should live in a shared primitive both FSMs
select into (e.g. `spu_shared_mult35.v`, plain unsigned, static-select
per §8 — not request/grant, see the terminology correction there).

Module list, updated:

- **`spu_reciprocal_core.v`** — normalize (leading-one detector +
  barrel shift) → 256×16-bit LUT → its own 1 shared multiplier reused
  for both NR multiplies (`d*y0`, `y0*err`) → denormalize. Self-
  contained, reusable by any future consumer (not just depth-v2).
- **`spu_depth_setup.v`** — dot-product FSM (9 multiplies via its own
  shared multiplier) → calls `spu_reciprocal_core.v` for `inv_denom` →
  3 final-scale multiplies (reusing the same shared multiplier) →
  presents `A_z/B_z/C_z` to the per-pixel stepper.
- **`spu_attr_stepper.v`** — per-pixel incremental accumulator, same
  shape as `spu_edge_stepper.v`'s `f`/`f_row` but 56-bit and outputting
  a value (shifted by `frac_bits` at readout), not a boolean.

## 3. New ports required
`spu_depth_setup.v` needs per-vertex depth inputs not present in the
existing `spu_raster_unit`/`spu_dual_raster` interface: `z0, z1, z2`
(16-bit unsigned, 0–65535, matching the oracle's tested range) plus a
`depth_setup` pulse, alongside the existing `a/b/c` edge coefficients
(already loaded via `setup0`/`setup1`). `D` itself needs no new
multiply: **`D = c0 + c1 + c2`** — since `F_i(0,0) = c_i`, and
`F0+F1+F2` is constant (verified computationally in `triangle_edges()`),
evaluating at the origin gives the same constant `D` for free. This
wasn't obvious from the earlier characterization work and is worth
carrying into the RTL spec directly: no extra multiplier cycles needed
to obtain the denominator.

## 4. FSM: one multiply issued per state, ~14 states + bookkeeping
Sequenced through **`spu_depth_setup.v`**'s own shared multiplier
(dot products + final scale) and **`spu_reciprocal_core.v`**'s
(2 NR multiplies), following the same accumulate-through-shared-
multiplier shape `pade_eval_4_4.v` already uses (its non-
`USE_LOCAL_POLY` FSM path), not the combinational `USE_LOCAL_POLY=1`
path that risks the `series_stream_probe` failure mode:

```
IDLE → M_SA0(a0*z0) → M_SA1(+a1*z1) → M_SA2(+a2*z2)          [Sa done]
     → M_SB0(b0*z0) → M_SB1(+b1*z1) → M_SB2(+b2*z2)          [Sb done]
     → M_SC0(c0*z0) → M_SC1(+c1*z1) → M_SC2(+c2*z2)          [Sc done]
     → NORM (leading-one detector + shift, combinational, 1 cycle)
     → LUT_LOOKUP (ROM read, 1 cycle)
     → M_NR0(mant*y0) → SUB(2-prod) → M_NR1(y0*err)          [inv_denom done]
     → M_SCALE_A(Sa*inv_denom) → M_SCALE_B(Sb*inv_denom) → M_SCALE_C(Sc*inv_denom)
     → DONE (present A_z/B_z/C_z to spu_attr_stepper, pulse ready)
```
~14 multiply-issuing states + ~4 bookkeeping states ≈ **18 cycles per
triangle setup**.

## 5. Throughput budget (why setup-time latency doesn't matter here)
At the coverage path's already-measured 109.82 MHz (raster synth probe),
18 cycles ≈ 165 ns per triangle setup. A 640×480@60Hz frame budget is
16.67 ms — the setup sequencer could in principle process ~100,000
triangles/frame before becoming a bottleneck, wildly beyond what a
2-unit dual-rasterizer would ever need. This is the concrete payoff of
§3b's "reciprocal computed once at setup, not per pixel" finding: FSM
latency here is a non-issue by a wide margin, which is exactly why the
sequential-multiplier discipline (§2, §4) costs nothing in practice
while directly avoiding the proven area-blowup failure mode.

## 6. What is and isn't authorized here — UPDATED 2026-08-25
- **Still NOT authorized:** writing `spu_reciprocal_core.v`,
  `spu_depth_setup.v`, or `spu_attr_stepper.v`. This contract fixes
  their shape and interface, not their code.
- **The untested risk named here is no longer untested — and the first
  measurement of it was itself wrong, caught by external review before
  any of the three modules were written.**
  `contract_gpu_mult42_isolation_probe_2026-08-25.md` first measured
  11,259 LUT4 = 48.9% for a 42×42 multiplier — but that sizing used
  `A_z`'s *output* width instead of the multiply's actual *operand*
  widths. Corrected in `contract_gpu_mult35_corrected_probe_2026-08-25.md`:
  a properly-sized **35×17 unsigned multiplier costs 3,532 LUT4 = 15.3%**,
  zero DSP inferred either way. §2 above carries both corrections (one
  shared multiplier, correctly sized).
- **This changes the go/no-go back toward comfortable, not away from
  it.** With one correctly-sized shared multiplier, Tang 25K has 18,191
  LUT4 (79.0%) left for everything else: the leading-one detector and
  barrel shifter (needed for the 34-bit `d_in` per the pre-implementation
  halt-and-flag review — wider than the original 25-bit sketch, for
  correctness, not characterized for area yet), the reciprocal's 256-
  entry ROM, both FSMs' control logic, `spu_attr_stepper.v`'s
  accumulator, and the *second* rasterizer unit sharing this same setup
  logic. That last point: does each of the two triangle units in
  `spu_dual_raster.v` get its OWN depth-setup sequencer (2× the
  multiplier cost), or do they share one sequencer serialized across
  both triangles' setup pulses? Given setup-time latency is already
  shown cheap (§5), **sharing one sequencer across both units is the
  obvious answer** — don't duplicate the multiplier a second time for
  the second triangle unit without a reason to. Resolved in §8 below.

## 7. Stop Conditions — one triggered, resolved twice
- ~~Do not write any of the three modules in §2 until the multiplier-
  isolation probe has run and reports a real LUT count.~~ **Resolved,
  then re-resolved**: it ran (42×42, wrong sizing), was corrected by
  review, ran again (35×17, correct sizing). See §2/§6.
- **The condition it was gated on fired twice** — first on the wrong
  number (48.9%, alarming), then, after correction, on the right one
  (15.3%, comfortable). 79.0% headroom after one correctly-sized
  multiplier is close to the raster-only 94.3% picture, though the
  LOD/barrel-shifter/ROM/FSM-control costs remain unmeasured on top of
  it. A7 100T (proven DSP inference via RPLU2PADE: 72 DSP, 34% LUT)
  remains worth naming as a fallback in principle, but the case for it
  is much weaker now than it looked under the wrong 42×42 number —
  don't let the earlier alarm linger past the correction that resolved
  it.
- Do not write any of the three modules in §2 until a design for the
  shared-multiplier arbitration interface (request/grant between
  `spu_reciprocal_core.v` and `spu_depth_setup.v`) exists — that
  interface doesn't exist yet even in sketch form and is now load-
  bearing, not incidental.

## 8. Shared-multiplier interface sketch (2026-08-25 addendum)
**Correction before sketching:** "arbitration" implies two independent
masters contending for a resource, needing request/grant and starvation
analysis. That's not this. `spu_depth_setup.v`'s dot-product phase (9
multiplies) completes and its results are latched *before* it pulses
`spu_reciprocal_core.v`'s `start`; it then waits on `done` before the
final-scale phase (3 multiplies) begins. The two consumers are
**provably sequential, never concurrent**, by construction of the one
top-level FSM in §4. A static priority mux keyed off one "who's active"
bit is correct by construction — no queuing, no fairness, no deadlock
analysis needed, because there is nothing to arbitrate between.

**Terminology correction (2026-08-25, tightened before any RTL is
written against this):** don't describe this as "`spu_depth_setup`
owns the shared multiplier and arbitrates with `spu_reciprocal_core`."
It is: **`spu_depth_setup` is the sole top-level sequencing owner;
`spu_reciprocal_core` is a subordinate micro-sequencer, temporarily
selected as the multiplier operand source during the reciprocal phase.**
The `busy` signal in the sketch below is **ownership/select state, not
arbitration state**. This distinction is load-bearing for the
implementer: "arbitration" invites a generic request/grant protocol,
a queue, or fairness logic — none of which this design needs or should
get. Use "select" / "owner" language in the actual RTL's signal names
and comments, not "grant" / "arbiter".

**Explicit invariant for the physical primitive (width corrected
2026-08-25):** `spu_shared_mult35.v` must present the full, untruncated
`unsigned 35 × unsigned 17 → unsigned 52` product — magnitude-only, per
§1's second correction; sign is extracted and reapplied by the caller
(`spu_depth_setup.v`), never carried through the multiplier itself.
Truncation/bit-selection of the product happens at each **consuming FSM
state**, never implicitly inside the shared multiplier module. This
keeps the physical primitive simple, reusable, and auditable — a future
reviewer checking `spu_shared_mult35.v` alone should see plain
unsigned multiplication with no hidden precision or sign decisions;
every truncation and every sign application is attributable to a
specific, named consumer state instead.

**Also resolves the second open question from §6** (does each
`spu_dual_raster.v` triangle unit get its own depth-setup sequencer):
same answer, same reasoning. Both units' setups are already independent
pulses (`setup0`/`setup1`) that don't fire concurrently in current usage
(one CPU, one triangle loaded at a time). **One shared
`spu_depth_setup.v` instance, fixed priority to unit 0 if both pulse the
same cycle, unit 1's setup simply waits one FSM pass (~18 cycles ≈
165 ns, per §5 — negligible)**, not two duplicated sequencers. This is
the same "don't pay for concurrency that doesn't exist" reasoning as the
multiplier sharing above, applied consistently rather than ad hoc.

**Sketch (widths corrected 2026-08-25 — 35×17 unsigned multiplier per
§1/§2's second correction; `d_in` widened to 34 bits and a `degenerate`
output added per the pre-implementation halt-and-flag review):**

```verilog
// spu_shared_mult35.v -- the physical resource, no state of its own.
// Magnitude-only (unsigned): every caller extracts signs and negates
// outside this module, per §1's magnitude-only correction.
module spu_shared_mult35 (
    input  wire [34:0] a,
    input  wire [16:0] b,
    output wire [51:0] p
);
    assign p = a * b;
endmodule
```

```
// spu_reciprocal_core.v -- does NOT own a multiplier instance. Its own
// internal NR micro-sequencer drives mult_a/mult_b and reads mult_p
// only while `busy` is asserted; the caller routes the shared
// multiplier to it during that window. d_in widened to 34 bits (was a
// 25-bit sketch, sized to c0+c1+c2's actual possible range, not just
// the typical 640x480 case -- pre-implementation halt-and-flag finding).
// degenerate=1 on d_in==0 (no valid leading-one position): forces
// y_out=0 instead of running the detector on undefined input.
module spu_reciprocal_core (
    input  wire clk, rst_n, start,
    input  wire [33:0] d_in,             // |denominator|, up to 34 bits
    output reg  [16:0] y_out,            // 1/d ~= y_out / 2**exp_out
    output reg  [5:0]  exp_out,
    output reg  done,
    output reg  degenerate,              // d_in==0: y_out forced to 0
    output wire [34:0] mult_a,           // request port (zero-extended
    output wire [16:0] mult_b,           // to the shared multiplier's width)
    input  wire [51:0] mult_p,           // shared result, valid when busy
    output wire busy
);
```

```
// spu_depth_setup.v -- the one owner. Static select, not an arbiter:
// mult port routes to the reciprocal core only while it's busy,
// otherwise to depth_setup's own dot-product/final-scale states. Sign
// of D is extracted here (d_sign = D[33]) before magnitude is sent to
// the reciprocal core, and reapplied to A_z/B_z/C_z after the
// final-scale multiply -- the shared multiplier never sees a sign.
wire [34:0] recip_a; wire [16:0] recip_b;
wire recip_busy;
spu_reciprocal_core u_recip(..., .mult_a(recip_a), .mult_b(recip_b),
                             .mult_p(shared_p), .busy(recip_busy), ...);

wire [34:0] shared_a = recip_busy ? recip_a : own_mult_a;
wire [16:0] shared_b = recip_busy ? recip_b : own_mult_b;
wire [51:0] shared_p;
spu_shared_mult35 u_mult(.a(shared_a), .b(shared_b), .p(shared_p));
```

Outputs to the two triangle units' `spu_attr_stepper.v` instances:
`A_z0/B_z0/C_z0/ready0` and `A_z1/B_z1/C_z1/ready1` (56-bit per §1),
selected by which unit the top-level FSM most recently processed.

## 9. Edge case closed 2026-08-25: concurrent depth_setup0/depth_setup1
**Not dropped. 1-deep pending register per unit, matching the pulse-
style convention every other `setup` signal in this codebase already
uses** (`spu_edge_stepper.v`'s `setup`, `spu_dual_raster.v`'s
`setup0`/`setup1` are all one-cycle pulses, not held-until-accepted
signals — a queue keeps `spu_depth_setup.v` consistent with that
instead of inventing a different handshake style for one new module).

```
reg pending0, pending1;

// On each depth_setupN pulse: if the FSM is IDLE (or the DONE state is
// dispatching a new pass this same cycle), start unit N immediately;
// otherwise latch pendingN. Coincident pulses: fixed priority to unit 0
// (per §8), pending1 set so unit 1 is guaranteed the very next pass.

// At DONE: if pending0, clear it and dispatch unit 0; else if
// pending1, clear it and dispatch unit 1; else return to IDLE.
```

Worst case for either unit: one extra FSM pass of latency (~18 cycles ≈
165 ns, per §5 — the same "negligible against a 16.67 ms frame budget"
conclusion applies unchanged). Nothing is silently lost.

**Explicitly assigned to the host-side contract, not solved in
hardware, because there's no evidence it's needed**: a *second*
`depth_setupN` pulse for the same unit arriving before its first pending
request is even dispatched (i.e., `pendingN` already 1) would have its
coefficients overwritten before use. This is the same class of timing
requirement that already implicitly exists for the plain rasterizer's
`setup0`/`setup1` (edge coefficients are sampled combinationally at the
pulse, so re-pulsing before that edge lands is already a host bug, not
new). The depth-setup host contract states it explicitly: **wait for
`readyN` (or for `pendingN` to clear) before re-pulsing the same unit's
`depth_setupN`.** A deeper queue would handle this without that
requirement, but nothing here shows the current one-triangle-at-a-time
usage pattern needs it — building it now would be exactly the
speculative complexity AGENTS.md §2.2 rules out.

## 10. Remaining before RTL is authorized
- The arbitration sketch (§8) and the pending-queue resolution (§9) are
  both still sketches, not verified logic — a Halt-and-Flag pass on the
  actual Verilog, once written, is the real gate, not this prose.
- No software oracle yet models the shared-sequencer-across-two-units
  behavior end-to-end (existing oracles model one triangle's depth-v2
  pipeline in isolation). Worth extending before RTL if John wants that
  scenario characterized rather than reasoned about only in prose.

Related: `contract_gpu_reciprocal_scoping_2026-08-25.md`,
`contract_gpu_depth_v2_scoping_2026-08-25.md`,
`contract_gpu_raster_synth_probe_2026-08-25.md`.
