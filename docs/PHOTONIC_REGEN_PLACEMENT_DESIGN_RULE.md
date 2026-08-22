# Photonic REGEN Placement — Design Rule

**Status: simulation-only.** Every number in this document comes from
`PhotonicQuadrayBackend`, a behavioral Model-C simulation of the photonic
REGEN datapath (`software/tests/test_regen_equivalence.py`), not RTL or
silicon. Do not cite anything here as `silicon-verified` without a
matching entry in [`docs/hardware_evidence.md`](hardware_evidence.md) —
none exists yet. This document answers a design question raised by the
K=16 detector-noise anomaly investigation (E9–E16, `results/sweeps/`,
frozen contracts in `spu_strategy/`): **given a logical optical
computation of depth K, how should REGEN boundaries be placed so that
exact digital recovery stays reliable?**

## 1. The validated law

Every REGEN event reads out lane 0's field value, scaled by `2^m0` where
`m0` is that lane's shared scale exponent at the instant of readout
(`_apply_op_field`/readout formula, `test_regen_equivalence.py:198-330`).
Detector noise (`sigma_det`) is injected into the readout *before* this
rescale, so the same physical noise is amplified by `2^m0` when converted
back to an integer. `m0` does not reset to a fixed baseline after REGEN —
it is re-derived from the *recovered value's own bit-length*
(`_load_exp`), so it tracks the state's actual dynamic range, not just
how many operations preceded it.

Measured directly (`contract_photonics_m0_dynamic_range_2026-08-22.md`
§10, E16 v2, corrected and reproducibility-confirmed, sha256
`c6841f14ac...dd661e5b`), the per-REGEN-event recovery probability is:

```
P_event(m0, sigma_det) ≈ sigmoid(β · (a − log2(sigma_det) − m0))
a = -4.79,  β = 3.19
```

confirmed **M-invariant** — the same law holds regardless of how
frequently REGEN occurs (0/122 pairwise comparisons significant across
M∈{2,4,8,16}, max difference 0.029). Within the tested Model-C
parameterization, this fitted per-event `(m0, sigma_det)` law, composed
as a product across a trial's REGEN events, reproduces the
independently frozen E9 native-K and E13/E14 M-sweep whole-chain
recovery curves out of sample (all 12 tested crossing brackets overlap,
typically within 2 percentage points, across four decades of
`sigma_det`). See §5 for what this claim does and does not generalize
to.

**This corrects, rather than replaces, the original backend contract's
claim** (`contract_photonics_backend_2026-08-20.md` §3.3:
`sigma_det ≲ 0.05/2^m`, falsified by E9 as a function of `K` alone,
2026-08-21). The functional form was right; the mistake was treating `m`
as a fixed function of logical depth `K`. It is really a per-event,
state-dependent quantity, and once measured as such the original form
holds almost exactly (`a=-4.79` vs. the naive `log2(0.05)=-4.32`).

## 2. Practical rule for today's ISA (fixed-period REGEN)

The current REGEN ISA (opcode `0x09`, `.block K`) places REGEN at a
fixed, compile-time period `M`. Given that structure, the rule is:

1. **Compute the noiseless `m0` trajectory** for the target computation
   at the candidate period `M` (cheap — no noise model needed, just the
   exact op-by-op scale-exponent bookkeeping; see
   `photonics/run_photonic_m0_dynamic_range_sweep.py`'s
   `m0_trajectory_noiseless`-equivalent logic for the reference
   implementation).
2. **Find the worst-case `m0` across all REGEN groups** in that
   trajectory, `m0_worst(M)`.
3. **Require a safety margin below the 50% crossing**, not just staying
   under it. At `m0 = m0,crit(sigma_det)` recovery is only 50%; a
   deployed system needs P_event close to 1 at *every* event, since
   whole-chain recovery is a product over all events. Solving the fitted
   law for a target `P_event`:

```
m0,safe(sigma_det, P_target) = a − log2(sigma_det) − ln(P_target/(1−P_target)) / β
```

   e.g. for `P_target = 0.999` (chosen per-event so that a K=16 chain
   with ~8 REGEN events stays above ~99.2% whole-chain, `0.999^8`):
   `ln(0.999/0.001)/β = 6.907/3.19 ≈ 2.166`, so
   `m0,safe = a − log2(sigma_det) − 2.166 = -6.96 − log2(sigma_det)`.

4. **Choose the smallest `M` (most frequent REGEN) such that
   `m0_worst(M) < m0,safe(sigma_det, P_target)`.** Smaller `M` is not
   free — E14 showed the benefit of shrinking `M` saturates once
   `m0_worst` stops decreasing (REGEN re-derives `m` from the recovered
   *magnitude*, which has a floor set by the computation's own dynamic
   range, not by op count) — so there is a real minimum achievable
   `m0_worst` for a given problem, below which more frequent REGEN buys
   nothing.

**Worked example (this investigation's own K=16 case, `results/sweeps/`
frozen data):** at `M=2` vs. `M=4` (`regen_placement_m2_sweep_frozen_v1`
vs. `regen_placement_sweep_frozen_v1`), 99.9%-crossing improved only
2.00× (M=4→M=2) versus 31.62× (M=8→M=4) — consistent with `m0_worst`
saturating: mean max-`m0`-at-readout was 12.20 (M=4) vs. 10.56 (M=2), a
much smaller drop than the halved period would naively suggest, because
the re-entry baseline (set by the recovered magnitude, not op count)
dominates once groups get short. Applying step 4 above: for this
problem's band, `M=4` is close to the point of diminishing returns;
`M=2` buys real but small additional margin, matching what was measured.

## 3. Choosing `sigma_det` headroom, not just `M`

Where the detector-noise budget itself is a design variable (component
selection, not just REGEN placement), §1's law inverts directly: for a
fixed `M` (hence fixed `m0_worst`), the maximum tolerable noise is

```
sigma_det,max(m0_worst, P_target) = 2^(a − m0_worst − ln(P_target/(1−P_target))/β)
```

This is the same formula as §2 step 3, solved for `sigma_det` instead of
`m0`. Use whichever direction the actual design constraint runs.

## 4. Future direction (not specified here): REGEN as a placement problem

The `M-invariance` result (§1) implies a REGEN policy is not required to
be periodic at all — it only needs to keep `m0 < m0,safe(sigma_det,
P_target)` at every readout. That reframes REGEN placement from "pick a
constant `M`" to an optimization: minimize REGEN frequency subject to
`m0 < m0,safe`. Two different architectures could implement this, and
they are not the same proposal:

- **A runtime, state-adaptive controller** — REGEN whenever the *current*
  `m0` reaches `m0,safe`, decided dynamically as the computation runs.
  Handles data-dependent magnitude (the same program, different inputs,
  different `m0` trajectories) but needs the datapath to expose `m0` to
  a comparator and gate a REGEN trigger from it — new hardware, not just
  new firmware.
- **A static, compile-time placement** — since `m0`'s trajectory for a
  *given* op sequence and initial magnitude band is computable in
  advance (exactly how §2 step 1 computes it for the fixed-`M` rule
  above), a compiler could place REGEN boundaries only where the
  recoverability constraint actually requires them, using the *existing*
  ISA (`.block K` at compiler-chosen points, not a fixed period) — no
  new hardware, but only correct for programs whose magnitude range is
  known statically, not genuinely data-dependent ones.

Both are **explicitly not specified by this document** — each needs its
own contract (Spec Author role, `spu_strategy/contract_template.md`).
The static variant is the cheaper, more immediately actionable one (only
a compiler-pass argument, not a new comparator/trigger path in the
datapath) and would be the natural first step; the runtime controller
covers a strictly larger set of cases (mid-run data-dependence) at
significantly larger hardware cost. Neither is validated by this
document or by E9–E16 — both remain future work, and both would need
their own noiseless-trajectory-based verification methodology before any
correctness claim, following §2's cite of
`run_photonic_m0_dynamic_range_sweep.py`'s reference implementation.

## 5. Non-goals

- No RTL or silicon claim. Nothing here is `testbench-verified` for any
  hardware target; it is a simulation-derived design guideline, stated
  as such per the repo's silicon-claims discipline.
- No adaptive-REGEN specification (§4) — a future, separate contract.
- No generalization beyond the detector-noise axis (`sigma_phi`,
  `sigma_amp` were held at 0 throughout E9–E16; this law does not cover
  phase or amplitude noise).
- No claim that `a=-4.79, β=3.19` are universal constants independent of
  `SCALE`, `deltaT`, or the specific circulant/ROTC catalog used —
  they were fit for this backend's frozen parameters
  (`PhotonicQuadrayBackend.SCALE=0.1`, `deltaT=2.0`). A different
  backend configuration would need its own fit, following the same
  methodology (`contract_photonics_m0_dynamic_range_2026-08-22.md` §4/§10).

## References

- `contract_photonics_m0_dynamic_range_2026-08-22.md` §10 (E16 v2,
  corrected) — the validated law and its out-of-sample confirmation.
- `contract_photonics_backend_2026-08-20.md` §3.3 — the original claim
  this corrects.
- `contract_photonics_detector_boundary_2026-08-21.md` (E9),
  `contract_photonics_regen_placement_2026-08-22.md` (E13),
  `contract_photonics_regen_placement_m2_2026-08-22.md` (E14) — the
  independently-frozen curves §1's law reconstructs out of sample.
- `results/sweeps/README.md` — evidence artifact index, sha256 hashes.
