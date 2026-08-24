# SPU-13 Photonic Reliability & Compilation Contract

**Status: simulation-only.** Every claim in this document is already
established elsewhere in this chain (`PHOTONIC_REGEN_PLACEMENT_DESIGN_RULE.md`,
`PHOTONIC_REGEN_CORRELATION_SYNTHESIS.md`, and
`spu_strategy/contract_photonics_corrected_reliability_model_2026-08-24.md`).
**This document adds no new experiment or claim.** It exists because the
investigation phase (E9–E21, plus the corrected-reliability follow-on) is
now closed, and what a photonic backend/compiler for SPU-13 actually
needs from that body of evidence was scattered across five documents,
not stated as one interface-level specification. Do not cite anything
here as `silicon-verified` without a matching entry in
[`docs/hardware_evidence.md`](hardware_evidence.md) — none exists yet.

**Posture change this document records:** the photonic branch moves from
*mechanism discovery* (does X explain Y?) to *engineering around what has
been established*. The rule going forward: **an unanswered question
authorizes a new experiment only when it blocks an engineering decision
below, not merely because it is unanswered.** §5 lists what is
consequently parked.

**Follow-on (2026-08-24):**
[`docs/PHOTONIC_SPU13_ARCHITECTURE_SPEC.md`](PHOTONIC_SPU13_ARCHITECTURE_SPEC.md)
takes this contract's interface and asks what a hypothetical photonic
implementation satisfying it would have to look like as a system —
including the physical component picture this document deliberately
stays silent on. Also resolves a question this document didn't ask:
REGEN (opcode `0x09`) turns out to already be a real, RTL-implemented,
architecturally frozen SPU-13 instruction, not something specific to
this branch.

## 1. The reliability contract — what a compiler/backend needs

**Per-operation physical error model.** Detector noise (`sigma_det`) is
the only characterized noise axis; `sigma_phi`/`sigma_amp` were held at
zero throughout E9–E21 (design-rule doc §6) — phase/amplitude noise is
out of scope for every number in this contract, not just unmeasured.

**Per-event recovery law** (design-rule doc §1, `a=-4.79, beta=3.19`,
fit for `PhotonicQuadrayBackend.SCALE=0.1, deltaT=2.0` only — a
different backend configuration needs its own fit, same methodology):

```
P_event(m0, sigma_det) = sigmoid(beta * (a - log2(sigma_det) - m0))
```

**REGEN boundary policy.** Two validated options, both compile-time,
both requiring only the *noiseless* `m0` trajectory (cheap, no noise
model needed to compute):
- Fixed-period `M` (design-rule doc §2) — simplest, not `M`-invariance-
  optimal.
- Compile-time greedy or whole-chain-optimal placement (design-rule doc
  §4, E17) — dominates every fixed-`M` policy tested; validated against
  the real simulator (E17 Part 3), not just its own objective.

**Whole-chain reliability estimate — the adopted estimator:**

```
P_chain(m0_trace, sigma_det) = Π_i P_event(m0_i, sigma_det)
```

(`predicted_p_chain`, `run_photonic_compiler_regen_placement_sweep.py`).
**This is the estimator a compiler should use.** It is a **conservative
lower bound, not an unbiased estimate** (synthesis doc §5.1: E18 found
REGEN events are positively correlated — failures cluster — so the true
joint success probability exceeds the independent-events product). For
margin-setting this is the right direction to be wrong in.

**The corrected alternative is explicitly not part of this contract.**
`contract_photonics_corrected_reliability_model_2026-08-24.md` built a
whole-chain estimator folding E18's measured dependence into the product
above and validated it on a fresh 300,000-trial sample: it closed 71% of
the point-estimate gap but the corrected mean exceeded the empirical
rate's 95% CI — over-corrected into non-conservative territory, rejected
by its own pre-registered gate. **A compiler must not use it.** If a
tight (non-conservative) estimate is ever needed for a genuine
engineering reason (§5), that is new, unstarted work, not a drop-in
replacement sitting on the shelf.

**Acceptable recovery probability / how `M`, `K`, `sigma_det` enter the
budget** (design-rule doc §2 step 3, §3): choose a per-event target
`P_target` such that `P_target^(events per chain) ≥` the chain-level bar
required; invert the fitted law for the safety-margin threshold:

```
m0,safe(sigma_det, P_target) = a - log2(sigma_det) - ln(P_target/(1-P_target))/beta
sigma_det,max(m0_worst, P_target) = 2^(a - m0_worst - ln(P_target/(1-P_target))/beta)
```

Use whichever direction the actual design constraint runs (headroom on
`M`/placement vs. headroom on component noise budget).

## 2. Placement — no change, and why that's a real conclusion

`greedy_place`/`optimal_placement` choose boundaries from the noiseless
`m0` trajectory, computed before any noise is drawn — structurally
before `R_i` exists. The E18–E21 correlation, however large, was never
exploitable by a compile-time optimizer and the corrected-reliability
model's rejection changes nothing about this (synthesis doc §5.2,
corrected-reliability-model contract §6). **State this as the standing
rule, not a re-derivation each time it comes up:**

> **Placement optimizes the existing conservative objective
> (`predicted_p_chain`). The correlation findings (E18–E21) and the
> corrected-model result inform how that objective's output should be
> *interpreted* — as a conservative bound, not a tight estimate — not
> how placement chooses boundaries.**

## 3. Compiler representation — the pipeline this evidence supports

```
SPU-13 operation
      |
      v
photonic primitive(s)            <- WDM dual-rail encoding, transfer-matrix
      |                              multiply, dual-rail photodetection
      v                              (Model B, PHOTONICS_MODEL_STATUS.md)
noise / loss budget               <- sigma_det only (characterized);
      |                              sigma_phi/sigma_amp NOT modeled (§1)
      v
REGEN boundary                    <- compile-time, from noiseless m0
      |                              trajectory (greedy_place/optimal_placement,
      v                              §1/§2 above)
conservative recovery probability <- P_event(m0, sigma_det) per boundary
      |                              (§1's fitted law)
      v
whole-chain reliability estimate  <- P_chain = product across boundaries
                                      (adopted; conservative; §1)
```

**What's validated vs. what's conceptual, per stage:**
- *Photonic primitive → noise/loss budget*: Model B (ideal, 100/100
  vectors) and Model C (noisy, this whole E-series) are both
  behavioral-simulation-only (`PhotonicQuadrayBackend`,
  `test_regen_equivalence.py`). No RTL, no silicon, no physical
  component measurements back this stage — it is a physics-motivated
  simulator, not a validated device model.
- *REGEN boundary*: real, working compiler passes today
  (`greedy_place`, `optimal_placement`), validated against the real
  simulator (E17), usable with the *existing* ISA (opcode `0x09`,
  `.block K`) — no new hardware required for this stage.
- *Conservative recovery probability / whole-chain estimate*: a fitted
  empirical law (§1), not a first-principles derivation — valid only for
  the frozen backend configuration it was fit against (design-rule doc
  §6's last non-goal). Treat `a=-4.79, beta=3.19` as backend-specific
  constants, not universal physics.

A **runtime-adaptive** REGEN controller (deciding boundaries from the
*actual* running `m0`, not the noiseless compile-time trajectory) is a
materially different, larger proposal — unvalidated, needs new datapath
hardware (a comparator tap), and is explicitly out of scope here
(design-rule doc §5). Nothing in this contract argues for or against
building it; it simply isn't covered by anything validated to date.

## 4. What this contract is not

- **Not a new claim.** Every number here has a citation to an already-
  frozen contract or doc (§6). If a number here and its source ever
  disagree, the source is authoritative and this document is stale.
- **Not an RTL or silicon specification.** Nothing here is
  `testbench-verified` for any hardware target.
- **Not a decision to build a photonic backend.** This states what such
  a backend would need to know, given current evidence — it is not a
  go/no-go recommendation on whether to build one.
- **Not a reopening of any closed campaign** (E9–E21, or the
  corrected-reliability-model contract). Their conclusions are inputs
  here, not under re-examination.

## 5. Parked — explicitly not authorized by this contract

Per the posture change in the preamble, none of the following are
opened by writing this document. Each becomes live only when a specific
engineering decision above actually needs it — not by default, and not
because the question is interesting:

- **Pair-0 calibration/ablation** (leading, undemonstrated hypothesis
  for the corrected model's overshoot — corrected-reliability-model
  contract §9). Irrelevant unless a tight, non-conservative estimate
  becomes a genuine engineering requirement (§1) — the conservative
  estimator does not need it.
- **The two E18–E21 mechanism hypotheses** (arithmetic/structural action
  of `ROTC_thirds` vs. `ROTC_plain`/`QSUB`; the actual corrupted values)
  — synthesis doc §6.
- **`sigma_phi`/`sigma_amp` generalization** — no per-event law exists
  for phase or amplitude noise; every formula in §1 is detector-noise-
  only.
- **Runtime-adaptive REGEN** — design-rule doc §5, needs its own
  contract and new hardware, not authorized here.
- **A corrected, non-conservative whole-chain estimator** — the one
  attempt was rejected (§1); no replacement design exists or is
  proposed.

## 6. References

- `docs/PHOTONIC_REGEN_PLACEMENT_DESIGN_RULE.md` — §1 (fitted law), §2/§3
  (design rules), §4 (placement, validated), §5 (runtime-adaptive,
  unvalidated), §6 (non-goals, incl. `sigma_phi`/`sigma_amp` scope).
- `docs/PHOTONIC_REGEN_CORRELATION_SYNTHESIS.md` — E18–E21 campaign
  closure, §4 (observability distinction), §5 (design implications this
  document formalizes into an interface).
- `spu_strategy/contract_photonics_corrected_reliability_model_2026-08-24.md`
  (gitignored; evidence and code committed — see
  `results/sweeps/README.md`'s `corrected_reliability_sweep_frozen_v1_2026-08-24.json`
  entry, sha256
  `047154a6cd83ea5972f8efe543289c984a4bb21340f357d92239f1ee495c035c`) —
  the corrected-estimator attempt and rejection, §1/§5 above.
- `spu_strategy/PHOTONICS_MODEL_STATUS.md` — Model A/B/C definitions
  (§3's photonic-primitive stage).
