# Session Handover — 2026-08-20

## 0. Scope note

This session is entirely about a **new, explicitly-authorized parallel
research branch: photonic compilation of the SPU-13 ISA**. It does **not**
touch or reopen [[spu4-edge-node-focus]] — John confirmed it's a separate
branch, run in parallel while waiting on FPGA parts/compute, same footing
as the "no hardware dependency, can proceed while waiting" framing in
`spu_strategy/SESSION_SUMMARY.md`. Step 5 of the SPU-4 programme (real
INA226 data) is unchanged and still the primary line.

**First priority for next session, per John's explicit direction at the end
of this one: fix the bug in §3 before running or trusting any more Model C
physical-parameter sweeps.** — **RESOLVED (2026-08-20)**: both §3a and §3b
are fixed and smoke-verified; see the updated §3 below. All sweep data
produced before the fix was invalid and has been deleted.

## 1. What this branch is

A three-model investigation of whether the SPU-13 `SurdFixed64` ISA (over
ℚ(√3)) can compile to physically realizable optical transfer matrices with
bounded, recoverable error:

- **Model A** — exact digital oracle (ground truth).
- **Model B** — ideal (noiseless) WDM-encoded optical transformation.
  Matches Model A exactly, 100/100.
- **Model C** — Model B plus physical noise sources (phase jitter,
  amplitude fluctuation, optical loss, detector noise, thermo-optic drift).
  This is where the open questions live.

Three collaborators are active on it in parallel: GTP (architecture/plan),
Copilot (sweep scripts), Claude (this session — review + Phase 1
reproducibility scaffold + bug-hunting). Nothing on this branch is
committed to git — everything below is untracked (`git status` shows `??`
on all of it).

## 2. Where the files actually are

**Root-hygiene cleanup done (2026-08-21):** all root-level photonics files
(`PHOTONICS_QUICKSTART.md`, `PHOTONICS_RESEARCH_INDEX.md`,
`RESEARCH_TRACK_INDEX.md`, `SESSION_COMPLETION_SUMMARY.txt`,
`generate_photonic_summaries.py`, `plot_photonic_results.py`,
`extract_photonic_envelope.py`, and all `run_photonic_*.py` sweep drivers)
were moved into `photonics/`. Each moved script's `ROOT`/`REPO` path
computation was updated (one extra `os.path.dirname()`) so output still
lands in the real repo-root `results/sweeps/`, not `photonics/results/`.
Verified: `bash tools/verify_repo.sh` root-hygiene check passes, and E1–E5
of the frozen REGEN evidence base (§8) were regenerated with these moved
scripts and confirmed bit-identical to their frozen snapshots.

- **`photonics/`** — `photonics.md`, `photonicsnotes.md`, and now all the
  files listed above.
- **`spu_strategy/`** (gitignored) — `photonics_research_plan.md`,
  `photonics_precision_findings.md`, `photonics_debugging_report.md`,
  `PHOTONICS_MODEL_STATUS.md`, `SESSION_SUMMARY.md` (this is where the
  phased research plan below comes from).
- **`software/tests/`** — `test_photonic_models_smul.py` (the core
  three-model harness, ~1600 lines), `debug_photonic_models.py`,
  `test_photonic_noise_model.py`, `test_photonic_surd_oracle.py`,
  `test_smul_photonic_experiment.py`, and this session's new
  `photonic_experiment_config.py` (see §4).
- **`results/`** — Copilot's sweep outputs: `photonic_sweep_16000*.{json,csv,md}`,
  `figures/`, `sweeps/` (deltaT, calibration×amplitude×detector grids,
  each with its own `.metadata.json` for replay — see `results/sweeps/README.md`
  for that mechanism, which is a **second, independent reproducibility
  scheme** from the one this session added; not yet reconciled with §4).

## 3. Bugs found this session (the actual news)

Two distinct, confirmed bugs — not the same issue:

### 3a. Sweep scripts don't isolate their swept variable — **FIXED** (2026-08-20)

**Resolution:** all three sweep scripts now hold non-swept impairments at zero
instead of inheriting `ModelC.DEFAULTS`:
`run_photonic_deltaT_sweep.py:86-88` → `sigma_phi=0.0, sigma_amp=0.0, loss_dB=0.0`
(temperature only);
`run_photonic_combined_sweep.py:84` → `sigma_phi=0.0` (keeps swept amp/det +
the loss/calibration design);
`run_photonic_deltaT_calib_sweep.py:103-104` → `sigma_phi=0.0, sigma_amp=0.0`
(keeps loss/calibration design).

`run_photonic_deltaT_sweep.py:86-88` calls `smul_with_noise` with
`sigma_phi=ModelC.DEFAULTS['sigma_phi']` (0.5°), `sigma_amp=DEFAULTS['sigma_amp']`
(0.25%), `loss_dB=DEFAULTS['loss_dB']` (1.8 dB) **baked in on every ΔT
point**, instead of holding them at zero as the agreed Phase-2-step-1 plan
("temperature only, hold everything else ideal") called for.
`run_photonic_combined_sweep.py:84` does the same for its calibration ×
amplitude × detector grid. Symptom: `results/sweeps/deltaT_sweep_summary.md`
shows recovery flat at ~1.5–1.8% across the *entire* ΔT ∈ [-5, 5] K range,
**including ΔT = 0.000 → 1.71% recovery** — which should read ~100% (it
does in the unrelated `T0_no_noise` control in `results/photonic_sweep_16000_summary.md`).
The DEFAULTS noise floor was swamping the variable actually being swept.

### 3b. `C2` (physical thermal-drift) mode could not fail from phase drift — **FIXED** (2026-08-20)

The symptom described here was real (recovery came back **100% at every ΔT
from ±5K through ±500K**, and stayed 100% under a deliberately stressed
config — 100× larger `dn_eff_dT`, 5× larger arm-length mismatch), but the
root cause was **deeper than the line-598 diagnosis below**. Verified by
instrumented reruns:

`WDMState.copy()` (in `software/tests/test_photonic_models_smul.py`) only
copied the dual-rail fields and **silently dropped the complex output
fields** `E_a_real/E_a_imag/E_b_real/E_b_imag`. Every noise stage
(`add_amplitude_noise`, `add_optical_loss`) copies the state, so the
coherent receiver fell back to the dual-rail 0/π reconstruction — magnitude
with sign, but no phase information. **This made *every* phase-noise mode
immune to phase drift, not just C2.** The existing T0–T6 sweep showed the
inverted physics directly: T1 (common-phase, LO-tracked) degraded with σ_φ
while T2/T3 (fixed-LO, differential) were 100% immune — the opposite of the
correct behavior.

**Consequence of this correction: the §3b claim that "C0/C1 results
(`T1`–`T3`) are unaffected" was wrong.** They were artifacts of the same
`copy()` defect, as were all prior sweep outputs (`results/photonic_sweep_16000_*`,
`results/sweeps/*`). All of it has been deleted; nothing pre-fix is valid.

**Decision (John, 2026-08-20): Option A — C0-parity tracking.** Fixes applied:

1. `WDMState.copy()` now preserves the complex field attributes when present.
2. C2 branch: `lo_phase = delta_phi_a if lo_track else 0.0` (line ~607) —
   fixed LO = ideal reference; tracking LO phase-locks to the channel-a
   physical drift (common-mode rejection; only the differential residual
   `delta_phi_b - delta_phi_a` hurts).

**Smoke-verified (2000 trials/cell):** ΔT=0 → 100% (baseline); ΔT=±5K,
±500K, stressed → 0% (failure mode exists — the required smoke test);
ΔT=5K with `lo_track=True` → 11.1% (channel-a drift cancelled, residual
channel-b remains). Post-fix T0–T6: T1 robust (100% all σ_φ), T2 degrades
82.75→13.5%, T3 degrades 77.95→4.6% — physically correct.

### 3c. Pre-existing stale assert in `test_photonic_surd_oracle.py` — **FIXED** (2026-08-20)

`test_silicon_photonics_physical_parameters` asserted
`delta_T_max ≈ 14.18 K` but the file's own closed-form formula yields
**53.98 K** (phase coeff 4.850e-3 rad/K, tolerance π/12). Independent of the
harness (imports only `math`/`sys`/`fractions`); it was failing before any
of this session's work. Expected value corrected to 53.98.

## 4. This session's addition: `software/tests/photonic_experiment_config.py`

Phase 1 (reproducibility) scaffold, agreed with GTP before any more Phase 2
sweeps: a `PhysicalParams` dataclass covering every field GTP listed
(λ₀, n_eff, dn_eff/dT, ΔT, path length, loss, calibration error, detector
noise, etc. — `coupler_error`/`crosstalk_dB` are recorded but **not wired**
into the underlying model yet, flagged as `NOT_WIRED` in the module), a
`run_experiment()` that wraps the existing `ModelC_NoisyOptical.smul_with_noise`
(no duplicated logic) and returns/persists full metadata (params + seed +
timestamp + recovery + MAE) as JSON, and `verify_reproducible()` which runs
twice and asserts identical results. 136 lines, Lithic-compliant. All
default-zero impairment fields, unlike the sweep scripts in §3a which
inherited `ModelC.DEFAULTS`.

**Reconciled (2026-08-20): `photonic_experiment_config.py` is now the single
canonical reproducibility scheme.** The `results/sweeps/README.md`
metadata-JSON replay scheme is retired — its metadata recorded only the
swept variable (not the full physical-params dict), its replay snippet baked
`ModelC.DEFAULTS` (§3a pattern), and all data it produced was invalidated by
the §3b `copy()` bug. The README has been rewritten to document the
canonical scheme, and all stale sweep CSVs/JSONs/summaries/figures under
`results/` were deleted (2026-08-20).

## 5. What's next (in order)

1. ✅ **Resolve §3b** — done (Option A, C0-parity LO tracking; smoke-verified
   failure mode at ΔT=±5K; see §3b).
2. ✅ **Reconcile the two reproducibility schemes** — done; canonical scheme is
   `photonic_experiment_config.py` (see §4).
3. **Re-run the actual Phase 2 single-operation sweeps** (temperature,
   calibration error, amplitude, detector noise, combined) with the canonical
   harness. Prerequisites (a) and (b) below are **done (2026-08-20)**:
   (a) all three sweep scripts now call `run_experiment()` and emit canonical
   per-cell JSON (full params + stats) instead of bare CSVs; `PHOTONIC_TRIALS`
   overrides trial count for smoke runs; (b) the default divergence is
   **resolved** — `PhysicalParams` is the single source with silicon-design
   values (n_eff=2.45, dn_eff_dT=1.86e-4, ΔL=6.4322 µm), the C2 fallback
   constants were aligned, and root `physical_params_defaults.json` was
   deleted. (c) the old CSVs are gone, so no resume-trap. Smoke runs at
   PHOTONIC_TRIALS=100–200 verified all three sweeps end-to-end (the ΔT sweep
   shows the expected graceful envelope: ~100% at |ΔT|≤1K → 71.5% at ±2K →
   10% at ±5K). Next: full-trial (16000/cell) runs.
4. Only after Phase 2 gives a real envelope: Phase 3 (define the
   regeneration/`REGEN` architecture and the `K` parameter — see GTP's
   three-architecture writeup in this session's chat log, not yet filed
   anywhere in the repo) and Phase 4 (K-operation cascade sweeps).
5. ✅ Root-hygiene cleanup (§2) — done 2026-08-21 (files moved into
   `photonics/`, evidence base re-verified bit-identical).

## 6. Also this session: SPU-4 doc/RTL-accuracy prep (unrelated to the
photonics branch above — done while waiting on the encoder/INA226 order to
arrive)

No RTL logic or test changes — comment/doc edits only, `verify_repo.sh`
209/209 both before and after. Found by auditing whether another engineer
could reproduce the SPU-4 edge-node result cold, ahead of next week's
capture campaign:

- `hardware/rtl/core/spu4/spu4_som_edge.v` and `spu4_som_flash_loader.v` had
  stale header comments — the first still said "not instantiated... not
  proven in silicon" (false since §3.2j.7/.8), the second pointed the
  training path at `rational_som.py` (the unrelated seven-node SPU-13 SOM's
  math, not this module's). Both fixed to cite the real path/evidence.
- `docs/INA226_COARSE_MONITOR_CONTRACT.md` still said the capture pipeline
  had **not** been wired to score `spu4_som_edge` — stale by 12 minutes,
  commit `3ad5da7` did it the same evening the doc was written. Fixed.
- `tools/bench_metrics/ina226_logger_v2.py` carried a "DO NOT USE FOR
  CAPTURE YET — it will fail validation" header from before the v3 contract
  amendment added `pulses` to the frozen schema. That warning is now false
  and would have blocked the next session from using the right firmware.
  Fixed — this is the file to flash as `main.py` for every capture from now
  on, not `ina226_logger.py` (v1).
- `docs/INA226_CAPTURE_RUNBOOK.md` — the actual bench procedure — was stuck
  at the v1/v2 protocol with **zero** mentions of the encoder, `pulses`, or
  `ENC_PPR`, and still told the operator to flash the v1 logger. Updated:
  encoder wiring row, a new §2a **`ENC_PPR` calibration procedure** (did not
  exist anywhere in the repo before today — ten hand-turned revolutions,
  triplicated, sum the `pulses` column, divide by 10), switched §3 to the
  v2 logger, and §5 now documents the two-model (`som` +
  `spu4_som_edge`) scoring output the v4 contract produces.

**Not done, flagged for whenever the parts physically arrive:** none of the
above has been exercised against a real capture — the runbook says so
explicitly now (top of file). The first real block-0 session is still the
thing that validates it, not this pass.

## 7. PARKED (unchanged from 08-16, still applies to everything except this branch)

SPU-13 tranches · GPU/rasterizer · PDM audio · Padé/RPLU2 · quantum · the
papers · `QADD` · ECP5 port · the `irotc_spi` router anomaly ·
`six_step_probe` trimming · A7 manifest targets · re-anchor decisions for
§3.2g.1 and §3.2k · `build_a7.sh:12` spin-name drift. SPU-4 step 5 (real
INA226 data) is not parked — it's the primary line, this branch runs
alongside it, not instead of it.

## 8. Evening close 2026-08-20: REGEN v1 frozen + Photonic Backend (deliverables 1–2)

**REGEN is now an architectural component of SPU-13, not an experiment.**

- **REGEN v1 frozen** (`spu_strategy/contract_regen_isa_0x09_2026-08-20.md`,
  §0 Architectural Freeze Declaration): authoritative; defines opcode 0x09,
  `.block K`, legal counting, K=0 pass-through, fault semantics, whole-state
  commit, idempotence, implementation obligations. Does NOT define substrate
  geometry, σ/Σ_total, detectors, thermal sensors, Taylor, or any fixed-point
  format. Governance rule: the ISA is not modified to accommodate any
  substrate. Evidence base tagged as appendix A (E1–E7, SA/SB/SC, EM).
- **Stage B frozen as the deterministic reference implementation** (the
  fixed-point realization against which any future substrate is compared).
- **Stage C hostile equivalence** (232 boundaries × 3 phase conditions, zero
  leaks) established the tested claim wording: "no substrate-specific detail
  leaked through the TESTED REGEN boundary under the Stage-C populations" —
  falsifiable, not a universal proof.
- **Photonic Backend contract frozen**
  (`spu_strategy/contract_photonics_backend_2026-08-20.md`): the photonic
  substrate as a THIRD backend under the frozen ISA.
  - Deliverable 1 IMPLEMENTED: `PhotonicQuadrayBackend` (in
    `software/tests/test_regen_equivalence.py`) — continuous optical field
    per lane/component, per-op common-mode thermal rotation, conditioned
    trim, canonical re-entry, K=0 pass-through; bit-exact on the full
    Stage-C population at ΔT {2,5} K. Five-realization equivalence:
    Digital ≡ Stage-A RTL ≡ Stage-B RTL ≡ Photonic ≡ VM.
  - Deliverable 2 IMPLEMENTED: the **declared regeneration envelope** (E8,
    `results/sweeps/photonic_envelope_frozen_v1_2026-08-20.json`, sha
    f300b6b9…, run twice bit-identical). Declared budgets: σ_det ≲
    0.05/2^m (1.96e-4 @ K=1 → 5.8e-7 @ K=16 — the binding constraint,
    tightens 2× per op); σ_amp ≲ 1.67e-5 (band worst case); σ_φ ≤ 0.25°
    with per-op REGEN through K=16. The K⁎(P_target, σ) regeneration-
    frequency phase diagram is in contract §3.3 (the compiler's block-
    sizing policy input).
- **Repo regression: 214 PASS / 0 FAIL** (REGEN suite 3/3 registered).

**Next session candidates — superseded 2026-08-21, see below.**

## 9. 2026-08-21: E9 detector-boundary sweep — RUN COMPLETE, RESULT: FALSIFIED

Root-hygiene cleanup done (§2/§5 above). Two real bugs found and fixed in
the same session (both outside the photonics tree, surfaced by re-verifying
E1–E8 after the cleanup): `software/spu_vm.py` had no dispatch case for
`HALT` (0x08) — silently treated as NOP; `software/tests/test_regen_equivalence.py`'s
iverilog invocation only had `-I hardware/rtl/arch`, missing
`-I hardware/rtl/core/spu13`, broken by that session's Lithic-split of
`fpga_chain.v`/`spu13_regen.v` into `.vh` includes — both fixed, `verify_repo.sh`
214/0 after. **Always use `.venv/bin/python3` for photonics/REGEN work, never
bare `python3`** — the latter lacks numpy here and silently falls back to a
different RNG stream (caused a false "E1–E5 evidence is stale" alarm this
session, corrected once the right interpreter was used).

The K⁎ crossover candidate above is superseded: GTP flagged that E8's
detector axis (the binding constraint per §3.3) was never actually resolved
for K≥4 — three of five K values read `K*(99.9%)=0` at the smallest
nonzero level E8 tested. **E9**
(`spu_strategy/contract_photonics_detector_boundary_2026-08-21.md`) ran to
completion 2026-08-21: 127 cells (23-point grid for K∈{1,2,4,8}, plus a
finer 35-point split sub-grid for K=16 after the smoke pass found its
crossing below the original grid's floor) × 30,000 trials, ~63 min actual
runtime, sha256 `1a3306a1…`.

**Result: the backend contract's `σ_det ≲ 0.05/2^m` general law is
FALSIFIED.** R_K = σ\*_det(K)/σ_det,pred(K) spans ~45× across K (0.301 at
K=1 down to 0.0067 at K=16) — nowhere near the "approximately constant"
band the falsification criterion required. Two findings worth carrying
forward: (1) even K=1, one of the formula's own two fit points, is off by
~3.3×, meaning E8's original grid was too coarse to have ever caught this;
(2) the K=8→K=16 step drops R by ~24× despite m̄ only growing ~3.2 — a
disproportionate collapse suggesting a cascade-depth effect the scalar-m
model doesn't capture. Per John's explicit direction: do **not** retrofit
an explanation yet — that's a hypothesis for a separately-authorized
follow-on contract, not a finding from E9. The backend contract's §3.3 was
**not silently corrected** — a dated pointer to E9 was added directly below
the original claim, preserving the historical wording (falsified claims are
documented assets, not errors to erase).

**Reproducibility rerun: DONE and CONFIRMED (2026-08-21), same session.**
Two independent 127-cell × 30,000-trial runs, bit-identical (a prior
concern that `cell()`'s accept-loop indexing might not reproduce
run-to-run was checked empirically first, not assumed — it is fully
deterministic). Frozen:
`results/sweeps/detector_boundary_sweep_frozen_v1_2026-08-21.json`, sha256
`1a3306a1…`, README entry added. **The falsification is not a Monte Carlo
fluke.** E10 (combined-axis) still explicitly deferred, needs separate
authorization.

**E11 (2026-08-22): cascade-depth mechanism investigation — RUN COMPLETE,
RESULT: HYPOTHESIS RULED OUT.** `spu_strategy/contract_photonics_cascade_depth_2026-08-22.md`.
Tested one code-grounded hypothesis for E9's K=8→K=16 collapse: reading
`PhotonicQuadrayBackend.run_chain_noisy` directly found that `m` grows by
exactly `+1` per ROTC op regardless of angle, but ROTC angles {1,3,4}
("exact thirds") apply an *uncompensated* extra `/3` division that angles
{0,2,5} don't. Controlled two-arm design at K=16 (Arm T: angles {1,3,4};
Arm N: angles {0,2,5}, both pure self-rotation chains with identical
deterministic per-trial m=23) ran through all gates in order — independent
oracle, noiseless validation (100% both arms), smoke pass (29s/70 cells,
extrapolated ≈72.5 min), full run (70 cells × 30,000 trials, sha256
`2e322400…`), **reproducibility CONFIRMED** (two independent full runs,
bit-identical) and **frozen**:
`results/sweeps/cascade_depth_sweep_frozen_v1_2026-08-22.json`.

**Result: Arm T and Arm N's crossing brackets coincide exactly**
([1.5e-9, 2.0e-9] for both at 99.9%/99%; [2.0e-9, 3.0e-9] for both at 95%)
— uncompensated `/3` divisions do **not** explain the collapse. §10 of the
E11 contract shows why mathematically, not just empirically: `(F,G,H)/div`
is an exact unit vector for all six ROTC angles — the `/3` is rotation
normalization, not independent attenuation. A secondary finding refined
the prediction itself: the closed-form `0.05/2^m` is a single-component
threshold, but arm-B scoring requires all 4 lane-0 components to round
correctly — aggregating that tightens the predicted 50%-point from 5.96e-9
to ≈4.2e-9, closer to (though not exactly) what both arms actually showed.
**The K=8→K=16 collapse remains unexplained** — no new hypothesis was
retrofit onto this result.

**E12 (2026-08-22): accumulated optical-depth loss — CLOSED, RESULT:
NEGATIVE.** `spu_strategy/contract_photonics_optical_depth_2026-08-22.md`.
Went through two designs, both caught before wasting the full sweep
budget: (1) fully uncompensated 1.8 dB/op loss (the established single-op
default, never carried into the K-chain backend) gave 0% recovery for
both K regardless of detector noise — an unrealistic strawman (a real
system calibrates known constants, same as REGEN already does for thermal
drift); (2) mean-compensated loss (measuring `L̄(K)` empirically — 0.488
at K=8, 0.496 at K=16, nearly flat, very different from the naive
`LOSS_LINEAR^K` prediction — then correcting for it) *also* gave
`comp_B = 0.0000` regardless of detector noise, because the residual
variance around the mean (CV≈30%) is 2-3 orders of magnitude larger than
the ~10⁻³–10⁻⁴ relative precision exact BQE recovery needs. Closed at the
calibration/invariant stage, full 30,000×4 sweep not run — the result was
already structurally determined. **Conclusion (precisely scoped): no
single fixed scalar compensation per K can recover exact BQE under this
loss model — not the broader claim that no compensation scheme could
ever work.** Two independent failure modes (uncompensated, mean-
compensated) converging on the same precision-mismatch conclusion
substantially lowers the odds that ordinary accumulated loss explains
E9. Also a standalone architectural finding: this system's scalar-
calibrated receiver can't correct for >~0.1% transfer variance, whatever
the source.

**E13 (2026-08-22): regeneration-placement mechanism investigation —
RUN COMPLETE, RESULT: SUBSTANTIAL CONTRIBUTOR.**
`spu_strategy/contract_photonics_regen_placement_2026-08-22.md`. Reading
`run_chain_noisy` (used by E8/E9/E11/E12) confirmed it has **zero**
intermediate-regeneration support — its accumulation state initializes
once, before the block loop, and never resets between blocks, so every
prior "K=16" measurement was necessarily "regenerate only once, after all
16 ops." New code (`run_chain_periodic_noisy`) simulates whole-state REGEN
boundaries every M ops within a 16-op sequence — whole-state re-entry
(all 13 lanes) confirmed architecturally *required*, not just convenient,
by `contract_regen_isa_0x09_2026-08-20.md` §5's "no opportunistic
per-component regeneration" rule. Reviewed before implementation (per
explicit request) — caught a real second-order concern (more frequent
regen also exposes the otherwise-static lane 1 to more noise draws) that
did NOT materialize as a measurable effect once run.

**Result:** M=16 measured directly (control anchor) matched E9's original
arm-B harness exactly at 6 spot-checked levels before anything new was
trusted. Full 36-cell × 30,000-trial sweep, reproducibility confirmed
(two runs, bit-identical): regenerating every 8 ops gives **10.00×**
improvement over never regenerating until op 16; every 4 ops gives
another **31.62×** (316.23× total) — monotonic, accelerating (not a
constant decades-per-halving law), no crossovers at any of 12 grid
points. **Covers 62.0% of the full 4.033-decade gap to E9's native K=8
crossing; a 34.2× gap remains at M=4**, the most frequent regeneration
tested. This is the first candidate mechanism in the E9 chain (after E11
and E12 both ruled out) to produce a large, reproducible effect in the
predicted direction — a real, substantial contributor, not the complete
explanation.

**E14 (2026-08-22): M=2 extension — RUN COMPLETE, RESULT: OUTCOME B
(DIMINISHING RETURNS).** `spu_strategy/contract_photonics_regen_placement_m2_2026-08-22.md`.
Reviewed before implementation (per explicit request): a pre-registered
four-way outcome taxonomy (A: continued acceleration, B: diminishing
returns, C: saturation, D: reversal) and an approved lane-attribution
instrumentation extension, specifically to make outcome D's two candidate
causes (lane-1 exposure vs. regenerating not-yet-computed operands at
M=2's QLDI-only first boundary) empirically distinguishable rather than
inferred from curve shape. E13's M=16/8/4 curve reused frozen, not
rerun — M=2 was the only new measurement.

**Result: M=2 improves on M=4 by only 2.00× at 99.9%** (geomean
3.464e-6 vs M=4's 1.732e-6) — far short of the 31.62× seen going
M=8→M=4. The improvement-per-halving sequence (1.0 dec → 1.5 dec →
**0.3 dec**) peaks at M=4 and sharply reverses — not a smooth saturation.
Reproducibility confirmed, two full runs bit-identical.

**The lane-attribution instrumentation paid off directly:** across
~3,769 failed trials (M=2 at 4 levels, M=4 matched control at 2 levels),
**100% of failures were attributable to lane 0 only — zero lane-1
involvement**, despite M=2 having double M=4's REGEN-boundary count.
This cleanly rules out the lane-1-exposure hypothesis by direct
measurement, leaving M=2's QLDI-only first boundary (no combine op
before the first REGEN, unlike every other M tested) as the surviving,
untested candidate — not proven, just the one candidate not eliminated.

M=2 closes 69.4% of the full 4.033-decade gap to native K=8 (up from
M=4's 62.0%); **a 17.1× gap remains** — narrower than E13's 34.2× but
still open.

**Next (not authorized):** test the QLDI-only-first-boundary hypothesis
directly (e.g. a grouping variant that defers the first REGEN past at
least one combine op) — a new, separately-authorized contract. M=1 (Arm A)
remains the separately-established endpoint. Operation ordering stays
parked (E11 §10). E10 (combined-axis) still deferred.

**E15 (2026-08-22): first-boundary placement — RUN COMPLETE, RESULT:
RULED OUT (small real residual quantified).**
`spu_strategy/contract_photonics_regen_boundary_placement_2026-08-22.md`.
Tests E14's surviving candidate directly: shift every M=2 boundary by
exactly +1 op ([2,4,...,16] → [3,5,...,15,16]), holding the 8-event REGEN
count fixed, so the first REGEN reads a 3-op state (past one combine op)
instead of the 2-op QLDI-only state. Contract frozen after four
Halt-and-Flag amendments: the E13-scaling number demoted from pass/fail
threshold to reference point (E14 already showed that acceleration factor
doesn't generalize); equivalence gate strengthened to per-trial, not
aggregate; "statistically indistinguishable" pre-defined via bracket
overlap / grid-interval movement, before running; a first-boundary
state-equivalence diagnostic added.

**All gates passed cleanly:** per-trial equivalence (500 trials, 0
mismatches — `run_chain_boundary_noisy` confirmed a strict refactoring of
E14's scorer, including matching RNG-stream state); first-boundary state
diagnostic (confirmed via a truncated-block direct test, after catching
that the naive first trial's first combine op was a degenerate angle-0
identity ROTC — picked a representative trial with a real state change
instead); noiseless+rejection (600 trials, 0 failures); smoke pass located
the transition ~5e-6 to ~3e-5; full run (16 cells × 30,000 trials);
reproducibility (two runs, bit-identical, sha256
`30e98021...c4cc08b`); `verify_repo.sh` clean.

**Result, by the pre-registered bracket-overlap criterion: RULED OUT.**
Crossing brackets at 99.9% (overlap), 99% (identical), and 95%
(identical) all show no full-grid-interval shift versus pure M2's frozen
brackets. **But the curve is not indistinguishable from pure M2 either** —
recovery is higher at every shared grid point from 3e-6 to 5e-5, peaking
at 7.8σ (level=3e-5, +0.0436 absolute, 36% relative). Quantified as a
noise-axis shift at the 50%-recovery crossing: **+0.011 decades (~2.7%)**
— roughly three orders of magnitude smaller than E13's regeneration-
frequency effect (1.0–1.5 decades per halving), and far short of closing
any of the 17.1× gap E14 left open. QLDI-only-first-boundary placement is
not a substantial cause of M=2's diminishing return; the direction of the
small residual is consistent with the hypothesis but its magnitude rules
it out as a primary explanation. Lane-attribution spot-check (3 cells,
n=3,000 each) confirms failures remain 99.9% lane-0-only — the shift did
not introduce a new lane-1 pathway.

**Where this leaves the investigation:** E11 (algebraic normalization)
and E12 (accumulated optical loss) ruled out mathematically/by two
independent failure modes; E13 established regeneration frequency as a
substantial (62%) contributor; E14 found the frequency benefit peaks at
M=4 and reverses at M=2; E15 has now ruled out the leading candidate
explanation for that reversal (first-boundary placement) as anything but
a minor (~3%) contributor. **A 17.1× gap to native K=8 remains
unexplained by any tested mechanism.** Per the stated overall objective
(work toward `P_recover = F(K, M, boundary placement, noise, state
dynamic range)`, not open-ended parameter hunting), the next step is a
genuinely new hypothesis for the remaining gap — not yet drafted, not
authorized. Candidates not yet tested: interaction between M and K
directly (is the 17.1× gap actually "K=16 run at M=2" vs "native K=8" a
fair comparison at all, given K=8 has its own different op-count/lane
mix?); dynamic-range/state-magnitude effects distinct from noise-per-op;
higher M=2 REGEN density interacting with the ROTC angle-normalization
division (E11 ruled out the *general* mechanism but not specifically at
M=2's shorter inter-REGEN intervals).

**E16 (2026-08-22): m₀-conditioned recovery — RUN COMPLETE, RESULT:
FALSIFIED overall, decisively concentrated in M=2.**
`spu_strategy/contract_photonics_m0_dynamic_range_2026-08-22.md`. Before
drafting, John/GTP redirected explicitly: not another M sweep, but a
code/architecture analysis of what "dynamic range" concretely means in
`PhotonicQuadrayBackend`. Reading `_apply_op_field`/the REGEN readout
formula directly (not guessing) found the mechanism: every combine op
unconditionally increments the destination lane's shared scale exponent
`m`; REGEN re-derives `m` at re-entry from the recovered value's own
bit-length (does **not** reset to a baseline); detector noise is
injected before the `2^m` readout rescale. Two quick checks: `cos(angle)`
degradation is analytically negligible even at K=16 (ruled out without
an experiment); only lane 0 ever accumulates `m` growth (`gen_block`
never makes lane 1 a combine-op destination) — mechanistically explains
E14's 100%-lane-0-only failures, not just correlates with it. A pilot
measurement (200–20,000 trials) found a sharp threshold matching
`m0,crit(σ) ≈ log2(0.05/σ_det)` closely, and — the decisive signal — M=2
and M=4 at the *same* σ produced nearly the same per-group recovery vs.
`m0` curve.

E16 formalized this at full scale: M∈{2,4,8,16} × a **shared** σ_det
grid `[1e-7,1e-6,1e-5,3e-5]` (not each M's own transition zone — `m0` is
driven mostly by the random initial QLDI magnitude, so even M=16
occasionally produces low-`m0` trials overlapping M=2's range), 30,000
trials/cell, 840,000 total group-observations, reproducibility
bit-identical. Pre-registered test: Bonferroni-corrected two-proportion
z-tests across all `(M1,M2)` pairs at matched `(m0,σ)`.

**Result: FALSIFIED for the full four-M set** (25/128 comparisons
significant, max diff 0.103 — well past the 5%/0.05 Confirmed bar). **But
the falsification has clear structure:** excluding M=2, M∈{4,8,16}
comparisons sit right at the Partially-confirmed boundary (8.8%
significant, max diff 0.055); M=2-involving comparisons are decisively
different (37.5% significant, max diff 0.103). A pre-registered
trial-clustered bootstrap (added before results were seen, per
Halt-and-Flag review that group-level observations within a trial aren't
independent) confirms 23/25 (92%) of the significant differences survive
cluster-aware resampling — not a within-trial-correlation artifact.

Descriptively (not the primary test): the 50%-recovery crossing
**location** is nearly identical across all four M (within ~0.1–0.2 `m0`
units — M=16/M=8/M=4/M=2 at σ=1e-5: 11.75/11.75/11.69/11.66), a
striking compression of what looked like a many-decades-scale K/M
mystery down to sub-1-unit `m0` differences. Both measured crossings sit
~0.5 `m0` units below the naive `log2(0.05/σ)` prediction, consistently
— the functional form looks right, the constant needs recalibration.

**Where this leaves things:** `m0` (the shared scale exponent at REGEN
readout) is now established as the dominant, mechanistically-grounded
driver of recovery — not K, not M, not boundary placement directly, all
of which only matter through the `m0` distribution they produce. It is
not, however, a fully sufficient statistic: M=2 has some real,
cluster-robust, uncharacterized additional effect beyond `m0` alone.
Gate 6 (out-of-sample prediction against E13/E14's frozen curves) was
**not run**, per the contract's own gating (triggered only if the
primary test doesn't fail outright) and §8's bar on new hypothesis
construction without separate authorization. Two natural, not-yet-
authorized follow-ups: (1) restrict the out-of-sample prediction to
M∈{4,8,16} only, since that subset is close to invariant; (2) a new,
separate contract asking what's specific to M=2 (its uniquely short,
frequent regeneration groups are the standing structural difference).

**E16 CORRECTED, same day (2026-08-22): the M=2 anomaly above was a
measurement artifact, not real physics — CONFIRMED, and gate 6
succeeds.** Before drafting a follow-on E17 around the M=2-specific
finding, a code-level re-check found `run_chain_noisy` and every
boundary-generalized descendant use only the *last* op's noise draw at
readout (`test_regen_equivalence.py:363`) — detector noise is memoryless
per REGEN event, not accumulated across a group, ruling out the
"accumulated noise" framing originally proposed for E17. A follow-up
empirical check then found the real flaw was in E16's own v1 measurement:
its `m0_histogram_raw` pooled every group observation, including ones
downstream of an earlier same-trial failure — a corrupted recovered
state stays corrupted, and 59.9% of M=2's group-8 failures at the
transition `m0` had an earlier same-trial failure. M=2 (8 REGEN events
per trial) simply had more opportunities for this contamination than
M=4/8/16, dragging its raw per-`m0` recovery rate down artificially.

Fixed: `collect()` now also reports `m0_histogram_clean` (stops counting
a trial at its first failure). Full 16-cell sweep rerun, reproducibility
bit-identical. **Corrected primary test: 0/122 pairwise comparisons
significant (was 25/128), max diff 0.029 (was 0.103) — CONFIRMED.** The
v1 "M=2 is different" finding does not survive the correction.

With M-invariance genuinely confirmed, **gate 6 (out-of-sample
prediction) was run and succeeds**: fit `P(recover|m0,σ)` by maximum
likelihood on the pooled corrected data (a first fit attempt had a
grid-search range bug excluding the true optimum — caught by checking
against training data before trusting it, then fixed), then predicted
E13/E14's independently-frozen whole-trial curves via a product-of-
independent-per-event-probabilities model using noiseless `m0`-
trajectories. **All 12 crossing brackets (4 M × {99.9%,99%,95%}) overlap
between predicted and frozen**, typically within 0.02 absolute
probability, across four decades of σ including levels far outside E16's
own tested grid.

**This substantially closes the investigation's original objective, via
three separable claims** (contract §10): (1) `K`/`M`/boundary placement
→ the distribution of `m0` (architectural, established by direct code
reading); (2) `m0`, `σ_det` → per-event recovery probability, the
experimentally validated local law (0/122 significant, M-invariant); (3)
that law, composed as a product over a trial's REGEN events, → whole-
chain recovery — the independent-reconstruction claim, since it predicts
E9/E13/E14's curves without being fit to them. All of this holds within
the tested Model-C parameterization (`SCALE=0.1`, `deltaT=2.0`,
detector-noise axis only) — not yet claimed as a universal constant or
as anything beyond behavioral simulation. See
`spu_strategy/contract_photonics_m0_dynamic_range_2026-08-22.md` §10 for
the full writeup; §9 is retained as documented history of the confound,
not current.

**E17 (2026-08-23): compiler-controlled REGEN placement — RUN COMPLETE,
RESULT: efficiency win confirmed, calibration falsified in greedy
placement's favor.**
`spu_strategy/contract_photonics_compiler_regen_placement_2026-08-23.md`.
The natural next step after E16's design-rule consolidation: John/GTP's
explicit next target was a *compile-time* REGEN placement pass (existing
ISA, no new hardware) — insert a REGEN boundary whenever the noiseless
`m0` trajectory reaches `m0_safe(σ_det, P_target=0.999)`, using E16's
frozen law (`a=-4.79, β=3.19`) as the physical cost function driving the
scheduling decision, rather than a fixed period `M`. This is explicitly
framed as a calibration test of E16's law under a *structurally
different* placement rule than it was fit on (fixed `M` → variable,
data-dependent group sizes) — a genuine out-of-sample test of the law
itself, not just of the compiler pass.

Reused E15's `run_chain_boundary_noisy_diag` unmodified (already accepts
arbitrary boundary lists) — only the greedy placement algorithm was new
code. Smoke pass caught exactly the edge case flagged at freeze: σ=1e-4
(the third test point) turned out genuinely degenerate (99th-percentile
predicted recovery = 0.0013) — asked John directly rather than silently
redesigning the locked grid; he chose to keep it as a reported boundary
case. Gate 0 (noiseless correctness) clean at all three σ_det points (0
oracle mismatches, 1,800 trials). Full run (3 × 30,000 trials),
reproducibility bit-identical.

**Result: the pre-registered calibration test FAILED — but favorably.**
At σ=1e-5 (the point with real predicted-probability spread), four bins
exceed the 0.03 per-bin threshold, all in the *same* direction: the
product-of-independent-events model systematically **under**-predicts
actual recovery (e.g. 0.721 predicted vs. 0.780 observed). Greedy,
variable-group-size placement recovers more reliably than the fixed-`M`
fit says it should — some group-to-group correlation the model doesn't
capture is working in greedy placement's favor, not against it.

**Efficiency (reported regardless of calibration): a clear, practical
win.** At σ=1e-6, greedy matches the best fixed policy's 1.0 reliability
using **2.62 mean REGEN events vs. M=2's fixed 8** (and beats M=4's
0.9992 outright). At σ=1e-5, greedy's **0.9793** whole-trial recovery
*exceeds every fixed-`M` option* (best fixed, M=2, only reaches 0.8941)
while using fewer events on average (6.67 vs. 8). At σ=1e-4, no policy —
fixed or greedy — recovers meaningfully, consistent with the calibration
finding that this is a genuine physical boundary, not a placement
failure.

**This validates the core claim behind E17's motivation:** REGEN
placement is a compiler optimization problem, and the *existing* SPU-13
ISA — no new datapath hardware — already benefits from solving it that
way. Where the E16 law's *direction* (which windows are safe) drives
placement, actual outcomes beat both the fixed-period baseline and the
law's own conservative quantitative prediction. Next step (not yet
authorized): investigate the source of the favorable miscalibration
(candidate: group-to-group correlation from re-entry magnitude carrying
information forward that the independent-events product model discards)
— or move toward the whole-chain-product optimization GTP described,
now that the simpler greedy version is validated as a real improvement.
See contract §9 for the full writeup.

**E17 Part 2 (2026-08-23): whole-chain-optimal REGEN placement — RUN
COMPLETE, RESULT: DOMINATES greedy, decisively.**
`spu_strategy/contract_photonics_compiler_optimal_placement_2026-08-23.md`.
John's explicit choice when asked what "continue with E17" meant:
extend E17 itself with the harder, strictly-more-general optimization
(minimize REGEN events subject to a whole-chain reliability constraint)
rather than the greedy per-event floor. A dynamic program — shortest
path over `O(16²)` candidate segments, since the exact oracle trajectory
is placement-independent (pure algebra) — maximizes predicted `P_chain`
for a REGEN-cost parameter λ, tracing a Pareto frontier. Deliberately
reuses the same (uncorrected) E16 product model E17 used, to isolate
"is greedy leaving efficiency on the table" from "is the model missing
physics" (the standing correlation hypothesis, left untouched).

**Gate 0's required cross-check caught a real bug before any prediction
was trusted:** the first `segment_m0` implementation assumed every
combine op adds a flat `+1` to `m[0]` — true for `ROTC` (`src=dst=0`
always) but wrong for `QSUB`, whose production semantics are `m[0] =
max(m[sa], m[sb]) + 1`, and `sa`/`sb` can draw from lane 1, whose
exponent can exceed lane 0's. Caught by comparing against E17's
already-verified `greedy_place` on identical boundary sets — 734–1330
mismatches per 600-trial sample before the fix, 0 after. A 76-
configuration brute-force optimality spot-check (does the DP actually
find the shortest path, not just *a* valid one) also passed clean —
exactly the failure mode a noiseless-oracle gate alone cannot catch,
since any valid boundary set recovers exactly when noiseless regardless
of whether the *predicted* probability driving the DP's choice was
computed correctly.

**Result: DOMINATES E17's greedy placement at both σ_det points.** At
σ=1e-6, 5 of 9 λ values dominate outright; the best point uses **21.9%
fewer REGEN events** (2.05 vs. greedy's 2.62) at equal, perfect
(1.0000) reliability. At σ=1e-5, 8 of 9 λ values dominate; the best
point uses **36.4% fewer events** (4.24 vs. greedy's 6.67) *and*
improves reliability (0.9853 vs. 0.9793) — outside greedy's own 95% CI,
a statistically real gain, not just a larger point estimate. The
frontier's more aggressive λ settings trade some of that reliability
back for even greater efficiency (a genuine, reportable trade-off, not
a failure) rather than degrading uniformly.

**What this does and doesn't establish:** confirms GTP's framing that
greedy, while already beating every fixed-`M` policy (E17), was still
leaving real efficiency on the table relative to the model's own
optimum — trading margin unevenly across events beats a uniform floor.
Does **not** resolve the standing correlation hypothesis: the DP's own
predictions remain conservative in the same direction greedy's were
(predicted < observed, same sign, same pattern) — this contract
deliberately used the uncorrected product model as its objective, so it
cannot distinguish "the model under-predicts" from "the model is
wrong in a way that would change the optimal placement." That
remains separate, later, not-yet-authorized work. See contract §9 for
the full writeup.

**E17 Part 3 (2026-08-23): Monte-Carlo closeness-to-optimum check — RUN
COMPLETE, RESULT: DP near-optimal, CONFIRMED, with an honestly-reported
power caveat.**
`spu_strategy/contract_photonics_compiler_montecarlo_optimum_2026-08-23.md`.
John's answer when asked which of two follow-ups to E17 Part 2's open
correlation question: the Monte-Carlo comparison (direct, model-free)
over refitting a corrected model and rerunning the DP against it (which
risked conflating "better search" with "better model," the exact
distinction E17 Part 2 was built to preserve). Halted before freeze: a
detailed review flagged seven methodological amendments, the most
consequential being **common random numbers (CRN)** — a precomputed
noise table addressable by op position, shared across every candidate
schedule for a given (block, repeat), replacing independent per-candidate
noise streams. This was necessary, not cosmetic: candidates with
different REGEN counts consume different numbers of noise draws, so a
naive shared sequential stream would silently desync between them.
Implementing CRN required a new scoring function
(`score_schedule_addressable`), verified equivalent to E15's original
via its own cross-check gate (0/300 mismatches) before being trusted —
the same discipline every substitute scorer in this chain has required.
Other amendments: paired-difference statistics (captures the CRN
variance reduction automatically), sampled-rank semantics
(`rank_among_evaluated` vs. any claim about the full schedule space),
explicit screening-experiment framing (20 blocks, not a population
estimate), and a smoke-measured (not assumed) compute budget.

The smoke pass extrapolated to ~95 minutes for the full run, with real
uncertainty given a highly skewed 6-block sample — reported explicitly
per the contract's own requirement; John chose to run as locked rather
than reduce scope. Each of the two full runs (for reproducibility) took
~80–90 minutes — the largest single sweep in this branch by compute.

**Result: DOMINATES was not what was tested here — DP near-optimal was,
and it held.** 20/20 blocks at both σ_det points (λ=0.01, E17 Part 2's
dominating point) — no evaluated alternative (up to 500 per block, full
enumeration when tractable) ever beat DP's schedule outside noise.
**Reported honestly rather than declared a clean sweep:** 39 of 40
blocks were saturated at perfect (1.0000) recovery, where *any*
reasonable same-N schedule ties trivially — confirms no regression, but
has essentially no power to detect a subtle ranking advantage. The one
non-saturated block (σ=1e-5, block 2, 0.9460 recovery) is the
substantive result: independently verified that DP's own 3-boundary
schedule was the actual best among all 91 fully-enumerated alternatives
for that block, not a ceiling artifact.

**Interpretation, scoped precisely:** consistent with the E16 law's
conservative calibration bias being roughly uniform across candidate
segments (doesn't distort rankings) rather than context-dependent, at
this specific operating point — but tested only at one λ and two σ_det
values where recovery is already high. Does not rule out a real
ranking-quality gap at a less-saturated operating point (e.g. a more
aggressive λ). A follow-on contract targeting that regime — not this
one — would give the method a fairer test. See contract §10 for the
full writeup.

**E17 Part 4 (2026-08-23): the less-saturated follow-up — RUN COMPLETE,
RESULT: DP near-optimal CONFIRMED, this time with real statistical
power.**
`spu_strategy/contract_photonics_compiler_montecarlo_lesssaturated_2026-08-23.md`.
Directly closes E17 Part 3's stated weakness (39/40 blocks saturated at
ceiling) by deliberately locating an operating point where recovery
lands in `[0.2,0.8]` for a substantial fraction of blocks. Since no
formula predicts where that band falls in advance, a new gate 0c
searches a `σ_det` candidate grid — genuinely HALTed once (initial
8-point grid's best candidate landed at 9/20, one short of the `≥10/20`
bar; reported rather than silently loosened; John chose to widen the
grid rather than lower the bar), then locked `σ=4.5e-5` at 12/20
in-band. A "discrete `N`-jump" guess for the grid's non-monotonic
pattern was checked against the per-block data during the ~2-hour wait
and found wrong — every block's own recovery decreases perfectly
monotonically with `σ_det`; the aggregate non-monotonicity is just a
superposition of many individually-shifted monotonic curves — corrected
in the contract before it could sit on record as an unverified guess.

All other machinery (CRN, `score_schedule_addressable`, paired-
difference statistics) reused verbatim from E17 Part 3, not re-gated.
Full run took ~125 minutes (near the low end of the smoke-pass
extrapolation); reproducibility bit-identical.

**Result: CONFIRMED, decisively — 20/20 blocks rank-1 or
CI-tied-for-best, 0/20 beaten by any evaluated alternative** (up to 501
candidates per block). This time **11/20 blocks (55%) landed genuinely
in the target band**, up from E17 Part 3's 1/40 (2.5%) — a real,
well-powered result, not one exhaustively-tested block carrying the
whole finding. The rare non-rank-1 cases (3 of 20 blocks) are all at
the noise floor (recovery ≈0.0000–0.0015) — not a meaningful ranking
difference.

**Where this leaves the standing correlation question:** across two
very different operating regimes (E17 Part 3's near-ceiling and E17
Part 4's genuinely mixed recovery), no evidence has been found that
E16's conservative calibration bias distorts DP's schedule *ranking* —
it looks like a magnitude effect throughout everything tested so far,
not a placement-ranking effect. The correlation-mechanism investigation
remains open and motivated by the magnitude gap alone, not by any
demonstrated placement-quality consequence. See contract §10 for the
full writeup.

**E18 (2026-08-23): correlation/calibration mechanism investigation —
RUN COMPLETE, RESULT: REAL DEPENDENCE FOUND, decisively.**
`spu_strategy/contract_photonics_correlation_mechanism_2026-08-23.md`.
John/GTP's explicit E18 scoping after E17 Part 4: don't modify the
production DP yet — first directly measure whether `P(R_{i+1}|m0_{i+1},
R_i) ≠ P(R_{i+1}|m0_{i+1})` under the real simulator. Almost the entire
simulation layer is reused verbatim from E16 (`run_chain_boundary_noisy_m0trace`)
— the key realization was that E16's own contamination correction
*discarded exactly this data* (its "clean arrival" rule stops counting
a trial at its first failure specifically to get an unbiased marginal
estimate); E18 goes back to what was discarded and studies it directly
rather than treating it as noise to remove.

Halted before freeze on four amendments: search/inference dataset
separation with disjoint RNG namespaces (the search that locates
`σ_det` must never contribute observations to the inferential test);
a two-part statistical-and-material dependence criterion (Bonferroni CI
excludes zero *and* `|diff|>0.05`, not either alone); a deterministic
`m0` binning hierarchy (exact integer → width-2 → width-4 → exclude,
decided by sample count only, frozen before any significance was
computed — no analyst-chosen binning after seeing results); and a
quantified search acceptance bar (`≥20` eligible cells, `≥5/7` position
pairs represented). Fixed `M=2` placement, not DP — a controlled
measurement question, not a placement-optimization one.

Gate 0 (search, disjoint namespace) located `σ=3e-5` cleanly. Gate 1
(smoke, 2,000 trials) already showed a striking preliminary signal (3/3
eligible cells materially dependent) — explicitly not treated as the
result, since the actual inferential dataset was the full 300,000-trial
run that followed. Both full runs (reproducibility) took only ~11
minutes each — the cheapest contract in the E17/E18 chain by far, since
this reuses a single fixed placement with no candidate enumeration.
Bit-identical.

**Result: 24/30 tested cells (80%) both statistically and materially
dependent** (Bonferroni-adjusted CI excludes zero, `|diff|>0.05`).
**29 of 30 cells agree on direction: `R_i=False → lower P(R_{i+1})` —
failures cluster** — the *opposite* of the originally proposed "noise
anti-correlates" mechanism, exactly the kind of finding the contract's
own falsification criteria were built to let stand on its own terms
rather than force into the expected story. Effect sizes are large (up
to 78.5 percentage points, `z>100` on several cells, visible even at
the smoke pass's `n=2,000`) and vary systematically with `m0_{i+1}`:
largest near the recovery ceiling, vanishing past the steep part of the
cliff (`m0=12`, where both `R_i` states are already near zero).

**What this establishes and what it doesn't:** `m0` is not a
sufficient statistic for next-event recovery probability — plausibly
because it's a coarse bit-length descriptor that discards *which*
specific corrupted value a failed group's BQE rounding produced (a
concrete, testable follow-on hypothesis, not established here). **This
does not reopen E17 Part 3/4's placement-ranking question.**
`greedy_place`/`optimal_placement` choose boundaries from the
*noiseless* trajectory, before any `R_i` exists — a compile-time
optimizer structurally cannot condition on a stochastic per-trial
outcome, so this correlation, however large, isn't exploitable by the
kind of compiler E17 built. What it *does* explain is *why* whole-chain
success has been conservatively mispredicted throughout E9–E17:
positively correlated events push a chain's true joint success above
what the naive independent-events product model predicts — exactly the
direction of every conservative-calibration finding in this
investigation's history. One caveat: pair 0 (groups 1→2) never produced
an eligible cell at any binning resolution at this operating point — the
finding is established across 6 of the 7 adjacent positions, not all 7.
See contract §10 for the full writeup.

**E19 (2026-08-23): corrupted-state sufficiency — RUN COMPLETE, RESULT:
error magnitude does NOT explain E18's gap, decisively.**
`spu_strategy/contract_photonics_corrupted_state_sufficiency_2026-08-23.md`.
John/GTP's explicit E19 scoping after E18: don't fit a corrected model
or touch the compiler yet — first ask whether E18's `R_i`-dependence is
really about *how wrong* a failed group's recovered state is (`err_i`,
a compact descriptor exposed from state E16's scoring function already
computes and discards) or whether *any* deviation triggers a similar
downstream effect regardless of size. A deterministic **replay of E18's
exact 300,000 trials** (same seed, `σ=3e-5`, `M=2`), scoped to E18's own
24 materially-dependent cells — no new operating-point search needed.

Halted before freeze on seven amendments, the most important being an
explicit attenuation metric `A=(p_small−p_false)/(p_true−p_false)`
replacing vague "statistically indistinguishable/closer to" language,
with frozen numerical thresholds (`A≥0.5` per cell, `≥12/24` cells for
the majority classification) — chosen before seeing results. Also:
explicit acknowledgment that the 24 cells are E18-selected (dependent
cells), not an unbiased sample; hard HALT conditions (not advisory) on
both the equivalence and replay-fidelity gates; and consistent
"error-magnitude descriptor" terminology to keep the conclusion
appropriately narrow (`err_i` is one partial summary of the corrupted
state, not the whole of it).

Gate 0a (equivalence, hard): 0/2,000 mismatches. Gate 0b (replay
fidelity): confirmed proportional at smoke scale. Full run + reproducibility
bit-identical (~11 minutes each, same as E18 — a deterministic replay of
the same trial count).

**Result: 13/24 cells analyzed (11 excluded for insufficient large-error
samples), 13/13 negligible, 0 substantial — clears the `≥12/24` bar
outright.** Attenuation `A` is essentially zero everywhere (`-0.010` to
`+0.020`, every CI far below the `0.5` threshold). **A genuinely
interesting structural finding surfaced alongside the exclusions,
reported honestly rather than treated as mere power shortfall:** `err_i`
is overwhelmingly exactly `1` in nearly every cell — several excluded
cells show **zero** `err_i>1` cases across the full 300,000 trials, and
**position pair 1 (groups 2→3) shows this at every one of its bins**,
never producing a large error when it fails. A secondary, exploratory
observation (not the primary classification): the stratification
direction is mixed and appears to track `m0_{i+1}` region (counter-
intuitive at the transition zone, intuitive deeper in the cliff) — noted
as a lead for a future contract, not an established effect given how
thin the large-error samples are.

**Interpretation:** error magnitude is ruled out as the missing
variable — whatever `R_i` carries beyond `m0_{i+1}` is carried by the
*fact* of failure, not by how far the recovery missed. Plausible reading:
the deterministic exact arithmetic downstream of REGEN doesn't treat a
"slightly wrong" input differently from a "very wrong" one — both are
just wrong integers entering the same transform, with `m0` incrementing
identically regardless of magnitude. This points toward a *qualitative*
mechanism (which component deviated, its sign, the op type active at
failure) as the next hypothesis for a separate, later, not-yet-authorized
E20 — not established by this contract, which only rules magnitude out.
See contract §9 for the full writeup.

**E20 (2026-08-24): discrete corruption descriptor — RUN COMPLETE, RESULT:
no large-effect descriptor found; `op_i` carries a small, real signal
`j`/`sign` entirely lack.**
`spu_strategy/contract_photonics_discrete_corruption_descriptor_2026-08-24.md`.
John/GTP's explicit E20 scoping after E19: reconstruct the actual
corrupted lane-0 transition at the failing boundary and test whether a
discrete descriptor — `j` (which component `k∈{0,1,2,3}` deviates
most), `sign(Δ_j)`, or `op_i` (`QSUB`/`ROTC_thirds`/`ROTC_plain`, the op
immediately preceding the boundary) — explains E18's `R_i`-conditioned
dependence. Halted before freeze on a scoping decision (three separate
univariate stratifications, not one joint `(j,sign,op)` model — a joint
descriptor has up to 24 categories, which would fragment the
already-thin `R_i=False` population far below usable sample size) plus
four amendments: the gap-explanation metric changed twice (see below);
the statistical family was frozen as 24 cell-level *omnibus* tests per
descriptor (not post-hoc best-vs-worst category pairwise comparisons),
Bonferroni-corrected within each descriptor's own family; `op_i`'s
definition dropped a causal-responsibility framing for a purely
mechanical one (`block[i-1]`); and the raw signed deviation `Δ_j` (not
just its sign) is retained in frozen evidence for future use.

Gate 0a (equivalence, hard): 0/2,000 mismatches. Gate 0b (replay
fidelity, hard): exact match on all 24 cells against E18/E19's frozen
counts. Full run + reproducibility bit-identical (~11 minutes, same
replay as E18/E19).

**Mid-course correction (results-driven, not a bug):** the frozen
gap-explanation metric `A_D = (p_D-p_F)/(p_T-p_F)` with `p_D = Σ_c
w_c·p_c` (`w_c` = empirical category share) turned out to be
mathematically tautological — by the law of total probability, that sum
collapses identically to the cell's own marginal `p_false` whenever no
category is excluded, so `A_D` read ≈0.00000 in essentially every cell
for every descriptor *regardless of whether the descriptor carried any
information*. Caught by inspecting the first full run's numbers rather
than accepting a suspiciously uniform "does not explain" verdict at face
value. Replaced with eta-squared (proportion of outcome variance
explained by category) — pure re-analysis of the already-frozen raw
event data (`--reanalyze-only` flag added to the driver), no
resimulation, same sha256 for the simulation-derived fields before and
after the swap. The frozen `eta2≥0.14` "large effect" threshold was
**not** weakened after seeing results — the distinction preserved
throughout is *statistically detectable* vs. *materially explanatory*.

**Result:** `j` and `sign` are clean nulls — 0/23 and 0/24 cells
omnibus-significant, eta² ≤0.0025 everywhere. `op_i` is not a clean
null: it clears Bonferroni-corrected omnibus significance in 7/24 cells,
several overwhelmingly (p as low as 4.5e-65 at pair=1/bin=9), but the
effect size is small (eta² 0.018–0.041, Cohen's "small" band, well under
the `≥0.14` bar), so the aggregate tier reads "does not explain the gap"
for all three descriptors — correct against the frozen threshold, but
not because `op_i` has zero effect. **Do not reinterpret `op_i`'s result
as an explanation of E18's gap. It is a statistically robust but
small-effect modifier, not a sufficient-state descriptor.** A secondary,
high-value pattern: at 5 of 6 `bin=9` cells, `op_i`'s three categories
replicate a consistent, non-overlapping-CI ordering — `ROTC_plain`
recovers best (`A_c` +0.30 to +0.45), `QSUB` middling (−0.11 to −0.17),
`ROTC_thirds` worst (−0.20 to −0.38). This is a lead for E21, not a
conclusion: no follow-on was run this session, and John/GTP explicitly
recommended against both weakening the frozen threshold and jumping
straight to a larger joint-descriptor search — any E21 should be
motivated by a specific mechanistic hypothesis about *why* operation
type matters near `m0≈9`, not another generic stratification.

**Interpretation:** the investigation chain (E18: `R_i` carries
information beyond `m0` → E19: not explained by error *magnitude* → E20:
not explained by *which component* failed or *which direction*, only
weakly by *which operation type*) continues to push the missing
information upstream, toward the state or transformation immediately
*before* the failing operation, rather than toward any one discrete
signature of the failure itself examined so far. See contract §9 for the
full writeup.
