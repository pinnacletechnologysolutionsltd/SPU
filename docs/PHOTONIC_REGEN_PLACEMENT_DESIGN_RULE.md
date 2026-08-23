# Photonic REGEN Placement — Design Rule

**Status: simulation-only.** Every number in this document comes from
`PhotonicQuadrayBackend`, a behavioral Model-C simulation of the photonic
REGEN datapath (`software/tests/test_regen_equivalence.py`), not RTL or
silicon. Do not cite anything here as `silicon-verified` without a
matching entry in [`docs/hardware_evidence.md`](hardware_evidence.md) —
none exists yet. This document answers a design question raised by the
K=16 detector-noise anomaly investigation (E9–E16) and now, as of the
E17 chain, gives a validated compile-time answer to it (`results/sweeps/`,
frozen contracts in `spu_strategy/`): **given a logical optical
computation of depth K, how should REGEN boundaries be placed so that
exact digital recovery stays reliable, and how few of them can a
compiler get away with while still meeting that bar?**

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

## 4. Compile-time REGEN placement — validated (E17 chain)

The `M`-invariance result (§1) implies a REGEN policy is not required to
be periodic at all — it only needs to keep `m0 < m0,safe(sigma_det,
P_target)` at every readout. That reframes REGEN placement from "pick a
constant `M`" to an optimization: minimize REGEN events subject to that
constraint. Since `m0`'s trajectory for a *given* op sequence and
initial magnitude band is computable in advance (§2 step 1), this can be
done entirely at compile time, using the *existing* ISA (`.block K` at
compiler-chosen points, not a fixed period) — no new datapath hardware.
This section was "future work, not specified here" in the previous
revision of this document; it is now validated, with concrete numbers.

**Algorithm 1 — greedy threshold placement**
(`contract_photonics_compiler_regen_placement_2026-08-23.md`, E17):
walk the op sequence; after each op updates `m[0]`, if `m[0] ≥
m0,safe(sigma_det, P_target)`, place a REGEN boundary there (reference
implementation: `photonics/run_photonic_compiler_regen_placement_sweep.py`,
`greedy_place`). **Result:** beats every fixed-`M` policy tested, on
both event count and reliability. At `sigma_det=1e-6`: 2.62 mean REGEN
events for 1.0000 (perfect) recovery, vs. the best fixed policy's 8
events for the same reliability. At `sigma_det=1e-5`: 6.67 mean events
achieving 0.9793 recovery, exceeding *every* fixed-`M` option tested
(the best fixed policy, `M=2`, only reached 0.8941).

**Algorithm 2 — whole-chain-optimal placement**
(`contract_photonics_compiler_optimal_placement_2026-08-23.md`, E17
Part 2): rather than a uniform per-event floor, a dynamic program
(shortest path over `O(K²)` candidate segments, since the exact oracle
trajectory is placement-independent pure algebra) maximizes predicted
whole-chain `P_chain = ∏ P_event(m0_i, sigma_det)` for a REGEN-cost
parameter `λ`, trading safety margin unevenly across events rather than
enforcing it uniformly (reference implementation:
`photonics/run_photonic_compiler_optimal_placement_sweep.py`,
`optimal_placement`). **Result:** dominates greedy. At `sigma_det=1e-6`
(`λ=0.01`): 21.9% fewer REGEN events (2.05 vs. 2.62) at equal, perfect
reliability. At `sigma_det=1e-5`: 36.4% fewer events (4.24 vs. 6.67)
*and* higher reliability (0.9853 vs. 0.9793 — outside greedy's own 95%
CI, a real gain, not just a larger point estimate).

**Validated against the real simulator, not just its own objective**
(`contract_photonics_compiler_montecarlo_optimum_2026-08-23.md`, E17
Part 3): both algorithms above choose schedules by maximizing a
*predicted* score built from §1's law, which is known to under-predict
actual recovery in aggregate (see the residual issue, below). Whether
that conservative bias distorts *which* schedule looks best — not just
the predicted magnitude — was tested directly: for 20 sampled blocks at
each of the two `sigma_det` points above, every same-event-count
alternative to the DP's chosen schedule (up to 500 per block, fully
enumerated when `≤500`) was Monte-Carlo evaluated against the real
noisy simulator using common random numbers for a paired comparison.
**No alternative ever beat the DP's schedule, at either `sigma_det`
(20/20 blocks each).** The one block with real statistical power (not
saturated at perfect recovery — 39 of 40 sampled blocks were, which
limits how much most of them can distinguish "the true optimum" from
"any reasonable schedule ties at the ceiling") showed the DP's schedule
was the actual best among all 91 fully-enumerated legal alternatives —
not a sampling artifact, not a ceiling tie.

**Residual, open issue — do not use the placement results to paper over
this:** §1's law itself is measurably conservative in *magnitude*
(predicted recovery is systematically lower than observed, in every
noise-level bin with real spread — e.g. `sigma_det=1e-5`: 0.721
predicted vs. 0.780 observed in one bin). E17 Part 3's finding is that
this conservatism does not appear to distort *schedule ranking* at the
operating points tested — a materially weaker and more precise claim
than "the model is correct." The mechanism behind the magnitude gap
(candidate: REGEN events within a trial are not fully independent, so
the product-of-marginals model discards real correlation) was
subsequently investigated by a dedicated E18–E21 campaign, now closed:
the correlation is real and large (E18), but its cause was not fully
identified — magnitude, component identity/sign, corruption support,
and pre-boundary state were all ruled out as explanations for the one
small residual signal found (operation type), which remains
mechanistically unexplained. See
[`docs/PHOTONIC_REGEN_CORRELATION_SYNTHESIS.md`](PHOTONIC_REGEN_CORRELATION_SYNTHESIS.md)
for the full synthesis and what it does and doesn't imply for this
document's §4 placement result (short answer: no change — §4's
algorithms decide from the noiseless trajectory, before any correlated
runtime outcome exists, so they were never able to exploit or be
distorted by this correlation either way). This remained deliberately
kept apart from the placement-validation result above
(`contract_photonics_compiler_optimal_placement_2026-08-23.md` §1:
reusing the same uncorrected model as the optimization objective was a
deliberate choice, specifically so the placement result and the
calibration question could not be conflated).

**Scope of the placement claim, stated precisely:** validated only at
`λ=0.01` and the two `sigma_det` values where §1's law predicts high
recovery — an operating regime where most sampled blocks saturate at
perfect recovery (§ above). A genuinely discriminating test — deliberately
choosing an operating point where `0.2 ≲ P_recover ≲ 0.8` for most
blocks, so schedule differences have real statistical leverage — has not
been run. Until it is, "near-optimal" should be read as established at
the high-reliability end of the operating range, not proven in general.

## 5. Runtime adaptive REGEN — still unvalidated, future work

A **runtime, state-adaptive controller** — REGEN whenever the *current*
`m0` reaches `m0,safe`, decided dynamically as the computation runs,
rather than precomputed at compile time — remains a materially
different, larger proposal from §4's compile-time placement. It would
handle genuinely data-dependent magnitude (the same program, different
inputs, different `m0` trajectories) that a compile-time schedule
cannot, but needs the datapath to expose `m0` to a comparator and gate a
REGEN trigger from it — new hardware, not just a new compiler pass.
**Explicitly not specified by this document, and not validated by
E9–E17** — needs its own contract (Spec Author role,
`spu_strategy/contract_template.md`), covering at minimum: where the
`m0`-vs-threshold comparator lives in the pipeline, what happens on the
cycle a threshold crossing is detected mid-operation, and whether
`m0,safe` is a compile-time constant or a runtime-configurable register.
Given §4 already validates the compile-time alternative for static
magnitude ranges, the case for taking on this hardware cost rests on how
much genuinely data-dependent behavior SPU-13 programs are expected to
have in practice — not evaluated here.

## 6. Non-goals

- No RTL or silicon claim. Nothing here is `testbench-verified` for any
  hardware target; it is a simulation-derived design guideline, stated
  as such per the repo's silicon-claims discipline.
- No runtime-adaptive-REGEN specification (§5) — a future, separate
  contract; genuinely unvalidated, unlike §4's compile-time placement.
- No claim that §4's "near-optimal" result generalizes beyond the
  tested, high-reliability operating point (§4's scope note) — a
  less-saturated operating point has not been tested.
- No resolution of the magnitude-conservatism residual (§4) — a
  separate, open research question, not required for §4's placement
  results to hold.
- No generalization beyond the detector-noise axis (`sigma_phi`,
  `sigma_amp` were held at 0 throughout E9–E17; this law does not cover
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
- `contract_photonics_compiler_regen_placement_2026-08-23.md` (E17) —
  §4 Algorithm 1 (greedy threshold placement), its frozen results.
- `contract_photonics_compiler_optimal_placement_2026-08-23.md` (E17
  Part 2) — §4 Algorithm 2 (whole-chain-optimal DP placement), its
  frozen results, and the `segment_m0` `QSUB`-lane-1-dependency bug
  found and fixed by that contract's own cross-check gate (worth
  reading before implementing anything similar).
- `contract_photonics_compiler_montecarlo_optimum_2026-08-23.md` (E17
  Part 3) — the direct Monte-Carlo validation of §4's placement
  results, its common-random-numbers methodology, and the honest power
  caveat (39/40 sampled blocks saturated) that qualifies "near-optimal."
- `results/sweeps/README.md` — evidence artifact index, sha256 hashes.
- [`docs/PHOTONIC_REGEN_CORRELATION_SYNTHESIS.md`](PHOTONIC_REGEN_CORRELATION_SYNTHESIS.md)
  — the E18–E21 campaign that investigated this document's §4 residual
  conservatism issue, closed 2026-08-24, and what its results do and
  don't imply for the placement algorithms above.
