# Photonic REGEN Event Correlation — Synthesis (E18–E21)

**Status: simulation-only.** Every number in this document comes from
`PhotonicQuadrayBackend` (`software/tests/test_regen_equivalence.py`),
not RTL or silicon. Do not cite anything here as `silicon-verified`
without a matching entry in [`docs/hardware_evidence.md`](hardware_evidence.md)
— none exists yet.

**This document closes the E18–E21 descriptor-search campaign** (closed
2026-08-24, explicit decision — not a pause pending more ideas) and
draws out what the campaign's results mean for SPU-13 photonic REGEN
design. It is a synthesis of already-frozen contracts, not a new
experiment: no new measurement is reported here.

**This document's implications, alongside the design-rule doc and the
corrected-reliability-model result, are now consolidated into one
interface-level specification:**
[`docs/PHOTONIC_REGEN_COMPILATION_CONTRACT.md`](PHOTONIC_REGEN_COMPILATION_CONTRACT.md)
— what a photonic compiler/backend actually needs from this evidence.

## 1. Origin and scope

[`docs/PHOTONIC_REGEN_PLACEMENT_DESIGN_RULE.md`](PHOTONIC_REGEN_PLACEMENT_DESIGN_RULE.md)
§4 validated a compile-time REGEN placement compiler, but flagged a
**residual, open issue**: the underlying per-event law
(`P_event(m0,σ_det)`, §1 of that document) is measurably *conservative*
— predicted whole-chain recovery is systematically lower than what the
real simulator produces. The design-rule document named the leading
candidate mechanism and explicitly deferred it: *"REGEN events within a
trial are not fully independent, so the product-of-marginals model
discards real correlation... a separate, not-yet-authorized research
question."*

E18–E21 is that research question, run to a decisive, if incomplete,
conclusion.

## 2. The elimination chain

| Experiment | Candidate explanation | Result |
|---|---|---|
| E18 | Does `R_i` (event `i`'s success) predict `R_{i+1}` beyond `m0_{i+1}` alone? | **Yes, decisively** — 24/30 tested cells materially dependent, effect sizes up to 78.5 points, `z>100` on several cells. Direction: failures cluster (`R_i=False → lower P(R_{i+1})`). |
| E19 | Is the missing information *how large* the corruption was (`err_i`)? | **Ruled out** — 13/13 analyzed cells negligible, attenuation `A` essentially zero (`-0.010` to `+0.020`). |
| E20 | Is it *which* lane-0 component deviated (`j`), its *sign*, or the *operation type* (`op_i`) active at the boundary? | `j` and `sign`: **ruled out** (0/23, 0/24 cells omnibus-significant). `op_i`: **small but real** — 7/24 cells significant (several `p<1e-20`), effect size small (η² 0.018–0.041), not large. |
| E21 Q1 | Is it *how many* components deviated (`S_i`, corruption support)? | **Ruled out** — clean null, 23/23 cells negligible, η² `5.2e-08`–`0.0058`. |
| E21 Gate 0 | Is `op_i`'s association really a `m0_i` (pre-boundary state) confound? | **Ruled out** — `op_i` survives in 7/7 cells, attenuation ratio ≈1.0 (0.972–1.130). |
| E21 Gate 5 | Does conditioning on `S_i` attenuate `op_i`'s association? | **No** — survives in 7/7 cells, ratio ≈1.0 (0.922–1.030). |

Every check in E19–E21 used a deterministic replay of the *same*
300,000 trials (`SEED`, `σ_det=3e-5`, `M=2`), with hard equivalence and
replay-fidelity gates before any result was trusted, and bit-identical
reproducibility on every frozen artifact. See §7 for the full citation
list.

## 3. Frozen headline statement

> Under the frozen E18–E21 experimental configuration, the observed
> operation-type association is small but reproducible, and is robust
> to conditioning on corruption magnitude, component identity/sign,
> corruption support, and pre-boundary state. The present experiments
> therefore do not attribute the association to these state-level
> corruption descriptors.

This is the entire empirical conclusion of the campaign. It is
deliberately narrow: it says what does *not* explain the correlation,
not what does.

## 4. What's actually observable in real hardware — the key distinction for design implications

E18–E21's variables split into two groups that matter very differently
for engineering:

**Requires an oracle — simulation/diagnostic-only, not physically
realizable at deployment:** `R_i` (and therefore `S_i`, `err_i`, `j`,
`sign`) are all defined by comparing the recovered state `rec` against
the *exact, noiseless* reference trajectory `qr`. Real photonic
hardware has no independent noiseless oracle at runtime — if it did,
REGEN would be unnecessary. **None of these are runtime-observable
signals a real controller could condition on**, no matter how strong
their statistical association with `R_{i+1}` turns out to be. E18's
large, decisive finding (§2) is therefore a fact about the *joint
distribution* of REGEN outcomes — relevant to how whole-chain
reliability should be *modeled* (§5.1) — not a lever any real controller
could pull.

**Genuinely observable, no oracle needed:** `op_i` (which instruction is
executing) is known for free — the compiler already has the full
instruction stream, and even a runtime fetch/decode stage sees it
trivially. `m0_i`/`m0_{i+1}` are observable *in principle* but require
new hardware (the design-rule document's §5 already notes this: "needs
the datapath to expose `m0` to a comparator" — not present in the
current ISA).

This distinction is why E21's result, despite ruling out `S_i` and
`m0_i` as *explanations*, still matters practically: `op_i` — the one
variable in this whole campaign that's trivially observable at compile
time — is exactly the one whose association survived every falsification
check thrown at it.

## 5. Design implications for SPU-13

### 5.1 Whole-chain reliability modeling: the existing product-of-marginals model is conservative, not wrong

E18 explains *why* §4 of the design-rule document found the DP
placement's predicted-vs-actual gap: positively correlated REGEN events
push a chain's *true* joint success probability above what an
independent-events product model predicts. Any SPU-13 tooling that
estimates whole-chain reliability by multiplying per-event
`P_event(m0,σ_det)` values is therefore giving a **conservative lower
bound**, not an unbiased estimate. For safety-margin purposes this is
the right direction to be wrong in. If a tight (non-conservative)
reliability estimate is ever needed — e.g. for a yield/throughput
tradeoff rather than a safety margin — the current model should not be
used as-is; a corrected joint model would need to be built, which this
campaign deliberately did not attempt (§6).

**Update (2026-08-24): that follow-on was attempted and rejected**, not
left open. `spu_strategy/contract_photonics_corrected_reliability_model_2026-08-24.md`
built a corrected estimator from this section's own dependence and
validated it on a fresh 300,000-trial sample: it cut the naive model's
point-estimate error by 71% (confirming the dependence carries real
predictive signal, not just statistical significance) but the corrected
mean landed outside the empirical rate's 95% CI — over-corrected past
conservative into unsafe territory — and was rejected on that basis.
`predicted_p_chain` remains the adopted estimator. The result itself is
informative: local conditional dependence can be real and predictive
while a naive composition of locally calibrated conditionals is still
non-conservative at the whole-chain level. Further pair-0-coverage work
(§9 there, the leading hypothesis for the overshoot) is explicitly
parked, not authorized.

### 5.2 Compile-time placement (§4 of the design-rule document): no change needed

`greedy_place`/`optimal_placement` choose REGEN boundaries from the
*noiseless* `m0` trajectory, before any `R_i` exists. A compile-time
optimizer structurally cannot condition on a stochastic per-trial
outcome, so E18's correlation — however large — was never exploitable
by the kind of compiler already built and validated. **This is a
reassurance, not a new implication: the placement result stands exactly
as validated, and E18–E21 gives no reason to revisit it.**

### 5.3 A future, small compile-time scheduling heuristic — *not yet actionable*

`op_i`'s association is the one result in this campaign that is both
real (survives every check) and observable at compile time (§4). In
principle, a scheduler that knows a `ROTC_thirds` op is about to execute
immediately before a REGEN boundary could apply some form of extra
caution there (e.g. a tighter `m0,safe` margin specifically for that
case). **This is explicitly not being proposed as a change today:**

- The effect size is small (η² 0.018–0.041) — even a perfect exploit
  would buy little.
- **The mechanism is unexplained.** Per AGENTS.md's Halt-and-Flag
  discipline, a correction should never be built on an association
  alone, without understanding *why* it holds — an unexplained
  correlation from a fixed simulation configuration (`SCALE=0.1`,
  `deltaT=2.0`, this specific `FGH` circulant table) is not a safe basis
  for a general design rule that would need to hold across
  configurations.
- The pattern that motivated E21 (`ROTC_plain > QSUB > ROTC_thirds` at
  `bin=9`) is concentrated at one `m0_{i+1}` region — whether it
  generalizes elsewhere in the operating range is untested.

If a future contract (§6) explains the mechanism well enough to trust
generalizing it, *that* would be the point to propose a concrete
scheduling change — not this one.

## 6. Open questions — recorded as future hypotheses, not scoped or investigated

Two candidate directions survive the campaign, explicitly not opened by
any contract to date:

1. **Arithmetic/structural action of the operation itself.** `ROTC_thirds`
   mixes all three of a lane's non-scalar components through the
   circulant `(F,G,H)` coefficients (`FGH` table, `test_regen_
   equivalence.py`); `ROTC_plain` is a pure permutation (denominator 1,
   no mixing); `QSUB` is elementwise. A structural difference in how
   corruption propagates through the *next* operation, not captured by
   any state descriptor tested here, is the leading remaining candidate.
2. **The actual corrupted values**, rather than any summary descriptor
   (magnitude, identity, sign, count) of them.

Also explicitly deferred, unrelated to the two hypotheses above:
`ΔS_i` (support before vs. after the corrupting op) — the simulator has
no mid-REGEN-group rounded readout without new instrumentation that
would perturb the noise-accumulation semantics under study (confirmed
by inspection, `contract_photonics_corruption_support_2026-08-24.md`
§2) — and the raw corruption mask `M_i` (which *specific* components
co-deviate at `S=2`), retained in E21's frozen evidence but not
analyzed.

Any of these becoming concretely actionable is a **new research
question needing its own contract**, not a resumed E-series tail.

## 7. Non-goals

- No RTL or silicon claim — simulation-only, same discipline as the
  design-rule document.
- No corrected joint reliability model **adopted for engineering use** —
  the follow-on corrected estimator named in §5.1 was subsequently
  built, validated, and experimentally **rejected** as non-conservative
  (§5.1's update note); `predicted_p_chain` remains the adopted
  estimator. This campaign itself (E18–E21) still built none — the
  correction was a separate, later contract, referenced here, not
  performed by this document.
- No change to `greedy_place`/`optimal_placement` or any other
  production code — this campaign was measurement-only throughout
  (E18–E21, each contract's own non-goals).
- No scheduling heuristic implemented from `op_i`'s association (§5.3)
  — explicitly not actionable yet.
- No investigation of the two open hypotheses (§6) — recorded, not
  started.

## References

- `spu_strategy/contract_photonics_correlation_mechanism_2026-08-23.md` (E18)
- `spu_strategy/contract_photonics_corrupted_state_sufficiency_2026-08-23.md` (E19)
- `spu_strategy/contract_photonics_discrete_corruption_descriptor_2026-08-24.md` (E20)
- `spu_strategy/contract_photonics_corruption_support_2026-08-24.md` (E21)
- `results/sweeps/README.md` — frozen artifact index, sha256 for every
  cited number
- [`docs/PHOTONIC_REGEN_PLACEMENT_DESIGN_RULE.md`](PHOTONIC_REGEN_PLACEMENT_DESIGN_RULE.md)
  — the compile-time placement result this synthesis's §5.2 confirms is
  unaffected, and the document whose §4 residual-conservatism note
  motivated this whole campaign
