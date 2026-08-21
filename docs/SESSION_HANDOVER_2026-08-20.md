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
`2e322400…`).

**Result: Arm T and Arm N's crossing brackets coincide exactly**
([1.5e-9, 2.0e-9] for both at 99.9%/99%; [2.0e-9, 3.0e-9] for both at 95%)
— uncompensated `/3` divisions do **not** explain the collapse. A
secondary finding refined the prediction itself: the closed-form
`0.05/2^m` is a single-component threshold, but arm-B scoring requires all
4 lane-0 components to round correctly — aggregating that tightens the
predicted 50%-point from 5.96e-9 to ≈4.2e-9, closer to (though not
exactly) what both arms actually showed. This correction is K-independent
and doesn't touch E9's actual finding. **The K=8→K=16 collapse remains
unexplained — no new hypothesis was retrofit onto this result, per
explicit instruction.** Next candidate mechanisms (operation ordering,
accumulated loss, effective optical depth, regeneration placement) remain
open, each needing its own separately-authorized contract. Reproducibility
rerun and freeze: not yet authorized.
