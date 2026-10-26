# Engineering Contract: Photonic Backend — Substrate Fulfilment of the SPU Execution Contract

**Date:** 2026-08-20
**Contract ID:** `contract_photonics_backend_2026-08-20.md`
**Status:** FROZEN (2026-08-20) — implementation authorized.

**Normative references (frozen, authoritative):**
- `contract_regen_isa_0x09_2026-08-20.md` — **REGEN v1, architectural
  semantics frozen** (§0 freeze declaration governs: the ISA is not modified
  to accommodate any substrate).
- `contract_regen_stageB_2026-08-20.md` — the **deterministic reference
  implementation** (the fixed-point realization to which this backend is
  compared for bit-exact equivalence).
- Evidence base E1–E7 (ISA contract appendix A): the frozen photonic
  experiments that bound the implementation obligations.

**Roles:** Spec Author (John + Deep Code) / Halt-and-Flag Implementer /
Integration Auditor.

---

## 1. Objective (the question this contract answers)

> **What physical optical transformation, detector, calibration and
> regeneration machinery is sufficient to implement each frozen SPU operation
> while producing the required architectural state?**

The photonic substrate is a **third backend** under the already-frozen SPU
execution contract — alongside the Digital reference, Stage-A RTL, and the
Stage-B fixed-point reference implementation. This contract is NOT "can
optics do exact Surd arithmetic?"; it is "**can a physical optical substrate
satisfy the already-defined SPU execution contract?**"

**Primary requirement (frozen):** bit-exact architectural equivalence — for
identical programs and inputs:

```
Digital reference  ≡  Stage-A RTL  ≡  Stage-B fixed-point RTL  ≡  Photonic backend  ≡  VM
```

where applicable. The photonic backend's internal numerical error is measured
separately as telemetry — never part of ISA semantics.

**Scope guard:** this contract defines the photonic backend's obligations and
the verification approach only. No ISA changes. No new Monte Carlo noise
models beyond the frozen evidence. No silicon claims without hardware
evidence.

## 2. Frozen Architectural Context (what the backend must satisfy)

REGEN v1 semantics (ISA contract §2, frozen):

- Each `.block K` executes `K` eligible operations (the E_REGEN set) on the
  continuous substrate, ending at REGEN.
- REGEN projects the continuous state `S̃_K` to the exact algebraic state
  `S_K` (whole-state: scalar SurdFixed64 + Quadray).
- `REGEN(REGEN(S)) = S` — permanent invariant; `K = 0` is a true pass-through.
- A REGEN_PREC fault commits nothing and preserves state; fault-then-clear
  semantics are defined (the recovery of a subsequent matching REGEN is the
  exact state).
- A valid REGEN re-enters the next continuous block with the recovered
  canonical state (the Stage-C block-boundary re-encode result).
- Precision requirements belong to the implementation: the ISA defines the
  envelope, never the physical constants.

## 3. Backend Obligations (per frozen operation)

For each E_REGEN operation and REGEN itself, the backend must provide a
physical realization that produces the required architectural state. The
table states the obligation; the implementation is free below the boundary.

| Op | Architectural obligation | Physical realization freedom |
|---|---|---|
| QLDI | encode integer Quadray into the continuous state | WDM dual-rail encode, modulator depths, scale factor |
| QSUB | exact component-wise difference on the continuous state | interferometric subtraction, phase conventions |
| ROTC (0–5) | circulant transform on (B,C,D), A invariant, exact thirds | geometric rotation in the physical topology |
| DELTA / IDNT / HEX / QLOG / IROTC | architectural effect per the ISA (counting, output) | substrate-specific realization or digital bypass (see §4) |
| REGEN | `S̃_K ↦ S_K` — exact projection + whole-state commit + canonical re-entry | measurement, BQE-equivalent recovery, gain trim, detector, calibration, regeneration machinery |

### 3.1 The regeneration machinery (the core obligation)

The backend's REGEN must, within its **declared regeneration envelope**
(ISA §2.5):

1. measure the continuous state of the completed block;
2. recover the exact algebraic state (BQE-equivalent — the recovery
   mechanism is implementation-specific, e.g. the fixed-point BQE or an
   optical readout + exact arithmetic);
3. commit the whole recovered state (no partial commits; a fault commits
   nothing);
4. re-enter the next block with the recovered canonical state (no
   substrate residue may leak across the boundary).

### 3.2 Known implementation obligations (from the evidence base, frozen)

These are obligations the evidence E1–E7 established for ANY substrate that
uses the common-mode rotation + compensation mechanism. They are
implementation constraints, not ISA semantics:

- **Calibration requirement:** relative gain calibration on the order of
  1.5e-5 for ≥99.9% single-shot exact recovery (E2). The receiver must know
  its gain to this precision or provide equivalent exactness by another
  mechanism (e.g. the compensation law).
- **Compensation law:** the common-mode thermal rotation is exactly
  compensable by a temperature-tracked receiver gain trim
  ε* = cos(δφ) − 1 (E3). A backend without temperature tracking must stay
  inside the |ΔT| ≤ 1.14 K envelope (E1) or declare a tighter/wider envelope
  with evidence.
- **Precision rule:** field precision ≥ required architectural precision + m,
  where m is the accumulated scale exponent (Stage-B result). The backend
  must carry enough continuous-state precision that the boundary projection
  is exact — the physical analogue of the Q2.40 decision.
- **Dynamic-range management:** regeneration frequency K is the control for
  the Σ_total wall (E6). The backend must declare its Σ_total behavior;
  per-op regeneration (arm A) bounds the detector precision requirement.
- **Non-common-mode noise budget:** differential phase, amplitude, and
  detector noise set the per-K recovery budget (E6/E7). The backend must
  declare its noise budget per axis and the resulting K⁎(P_target, σ_φ,
  σ_amp, σ_det) crossover — the regeneration-frequency phase diagram.

### 3.3 The DECLARED envelope (frozen 2026-08-20, artifact E8)

The PhotonicQuadrayBackend's declared regeneration envelope (E8, sha256
f300b6b9…, 60 cells × 30,000 trials, band [1000,30000], ΔT=2K conditioned,
arms A/B paired; σ=0 gate A=B=100%):

| Axis | Declared budget (chain, P≥99.9%) | Notes |
|---|---|---|
| Differential phase | σ_φ ≤ 0.25° only at K=1; the chain cannot chain under phase noise | the random walk accumulates; per-op REGEN holds ≥99% at σ_φ ≤ 0.25° through K=16 |
| Amplitude | σ_amp ≤ 5e-5 (K≤2), 2.5e-5 (K=4), 1e-5 (K=8), 0 (K=16) | error ~ v·σ_amp; the worst-case band value 30000 needs σ_amp ≲ 1.67e-5 |
| Detector | σ_det ≲ 0.5·s/2^m: 1.96e-4 (K=1) → 5.8e-7 (K=16) | the 2-normalized chain tightens the detector precision by 2× per op; the tightest axis |

**K⁎(P_target, σ) — the regeneration-frequency phase diagram (chain vs
per-op REGEN):**

| axis | level | K⁎(99.9%) | K⁎(99%) | K⁎(95%) | K⁎(90%) | K⁎(50%) |
|---|---|---|---|---|---|---|
| φ | 0° | 16 | 16 | 16 | 16 | 16 |
| φ | 0.25° | 1 | 1 | 2 | 2 | 2 |
| φ | 0.5° | 0 | 0 | 1 | 1 | 2 |
| φ | 1° | 0 | 0 | 0 | 0 | 2 |
| amp | 0 | 16 | 16 | 16 | 16 | 16 |
| amp | 1e-5 | 8 | 16 | 16 | 16 | 16 |
| amp | 2.5e-5 | 4 | 4 | 8 | 16 | 16 |
| amp | 5e-5 | 2 | 2 | 4 | 4 | 16 |
| det | 0 | 16 | 16 | 16 | 16 | 16 |
| det | 1e-4 | 0 | 0 | 0 | 0 | 2 |
| det | 3e-4 | 0 | 0 | 0 | 0 | 0 |
| det | 1e-3 | 0 | 0 | 0 | 0 | 0 |

**Engineering consequence (the substrate spec):** the detector is the
tightest constraint — the continuous chain's 2-normalization grows m by one
per op, so the coherent receiver must resolve the attenuated field to
σ_det ≲ 0.05/2^m. Per-op regeneration (arm A) does NOT relieve the detector
requirement on this Quadray chain (the per-op m is already ~8); it relieves
the phase and amplitude accumulation. The K⁎ table is the compiler's
regeneration-frequency policy input: the largest exact block K for a declared
noise budget.

> **FALSIFIED as a general law (flagged 2026-08-21, not corrected here —
> historical claim preserved as written above):** the follow-on experiment
> `contract_photonics_detector_boundary_2026-08-21.md` (E9, 127 cells ×
> 30,000 trials, sha256 `1a3306a1…`) densely mapped the detector crossing
> across K∈{1,2,4,8,16} and found `R_K = σ*_det(K)/σ_det,pred(K)` spans
> ~45× (0.301 at K=1 down to 0.0067 at K=16) — the `0.05/2^m` closed-form
> above does not generalize, and is off by ~3.3× even at K=1, one of its own
> two fit points. E8's grid (`{0, 1e-4, 3e-4, 1e-3}`) was too coarse to have
> caught this. See E9's §10 for the full crossing table, the R_K table, and
> the falsification verdict. **This table's "σ_det ≲ 0.05/2^m" row and the
> K⁎ det-axis row above are not corrected in place** — they remain the
> historical claim as originally frozen; do not cite them as current
> engineering guidance without also citing this note and E9.

## 4. Eligible-Operation Mapping (counting vs mirroring)

- The backend must count all E_REGEN operations exactly (the ISA's legal
  counting); ops outside E_REGEN (e.g. LD) are neither counted nor mirrored.
- The continuous chain mirrors the state-transform ops (QLDI/QSUB/ROTC);
  counting-only ops (HEX/QLOG) and the REGEN boundary follow the frozen
  Stage-A/Stage-C semantics.
- Non-transform ops may be realized digitally (a bypass) — the ISA does not
  require them to be optical; it requires their architectural effect.

## 5. Verification Approach (frozen gates)

The photonic backend is verified by **extending the bit-exact equivalence
harness** (`software/tests/test_regen_equivalence.py`) with the photonic
backend as a fourth realization, reusing the Stage-C hostile population
(nine categories, dphi sweep):

```bash
# 1. Bit-exact equivalence: Digital == Stage-A == Stage-B == Photonic == VM
cd /home/user/Projects/hardware/SPU && .venv/bin/python \
  software/tests/test_regen_equivalence.py

# 2. Stage-C reference gates stay green
cd software/tests && .venv/bin/python test_regen_emulator.py && \
  .venv/bin/python test_regen_asm.py && .venv/bin/python test_rotc_vm_rtl_trace.py

# 3. Frozen evidence base intact (E1-E7 bit-identical)

# 4. Complete repository regression
cd /home/user/Projects/hardware/SPU && bash tools/verify_repo.sh
```

**Falsification criterion (frozen):** any program in the Stage-C population
where the photonic backend's recovered state differs from the exact oracle is
a LEAK — the backend fails the contract, not the ISA. HALT and flag the
mechanism with a minimal proposed correction; the correction is to the
backend, never to the ISA.

## 6. Stop Conditions (Emergency Brake)

- **HALT** if the ISA must change to accommodate the photonics (the §0
  governance rule: the substrate is an implementation failure, not an ISA
  reason).
- **HALT** if `REGEN(REGEN(S)) = S`, K=0 pass-through, or fault-commit
  semantics are violated on the photonic backend.
- **HALT** on any unbacked "silicon-verified" claim: photonic results are
  model-verified (`simulation-only`) until backed by a specific entry in
  `docs/hardware_evidence.md`.
- **HALT** if the backend's declared regeneration envelope is widened to
  avoid a failing population without new evidence.

## 7. Non-Goals

- No ISA changes; no opcode/encoding changes; no `.block` semantics changes.
- No new Monte Carlo noise models beyond the frozen E1–E7 evidence (the
  backend contract consumes the existing evidence).
- No physical hardware build in this contract — the contract defines the
  obligations and the verification harness for a backend realization.
- No claim that optics are "fast" or "better": the contract is only about
  exact architectural equivalence.

---

*Status: FROZEN — first deliverable IMPLEMENTED (2026-08-20): the photonic
backend realization as a harness-pluggable backend + the bit-exact
equivalence gate, all green (testbench-verified, no silicon claim).*

## 8. Implementation Record — Deliverable 1 (2026-08-20)

**The photonic backend realization** (`PhotonicQuadrayBackend` in
`software/tests/test_regen_equivalence.py`): the continuous optical field per
lane/component `field = s·v/2^m · e^{i·angle}` (s = 0.1, the canonical WDM
scale), the per-op common-mode thermal rotation δφ = K_RAD·ΔT (E1), and the
REGEN projection via the coherent detection (inphase) + the conditioned
compensation trim 1/cos(angle) (E3) + the BQE-equivalent rounding. The
canonical re-entry at each valid REGEN (Stage-C block-boundary result) and the
K=0 pass-through follow the frozen semantics. Counting-only ops (HEX/QLOG/LD)
are not mirrored (contract §4).

**Halt-and-flag findings (backend realization, not ISA):**

1. **ROTC thirds are conditional.** Angles 1/3/4 divide by 3 (the exact
   thirds); angles 0/2/5 are identity/permutation (denominator 1). Applying
   the /3 unconditionally broke the recovery at the permutation angles.
2. **QSUB re-scale direction.** The field at scale m is s·v/2^m — moving an
   operand to a larger common exponent DIVIDES the field. The inverted
   rescale changed operand values by powers of two.
3. **QLDI phase entry.** A value entering the continuous field mid-block
   (the substrate's present state) must be encoded at the CURRENT accumulated
   phase; otherwise lanes diverge in phase and cross-lane QSUB mixes
   misaligned rotations (off-by-one recoveries at K=16, ΔT=5K).

**Gate result:** the bit-exact equivalence now spans five realizations —
Digital reference ≡ Stage-A RTL ≡ Stage-B RTL ≡ Photonic backend ≡ VM — on
the full Stage-C population (120 chains, 232 boundaries) at ΔT = {2, 5} K
(conditioned) and the RTL dphi sweep {0, 100, 255}: zero leaks.
