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
physical-parameter sweeps.**

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

Not cleanly separated from the FPGA tree — flagging per AGENTS.md's
root-hygiene rule, not yet cleaned up:

- **Root of repo** (violates "no root clutter"): `PHOTONICS_QUICKSTART.md`,
  `PHOTONICS_RESEARCH_INDEX.md`, `RESEARCH_TRACK_INDEX.md`,
  `SESSION_COMPLETION_SUMMARY.txt`, `generate_photonic_summaries.py`,
  `plot_photonic_results.py`, `run_photonic_combined_sweep.py`,
  `run_photonic_deltaT_calib_sweep.py`, `run_photonic_deltaT_sweep.py`.
- **`photonics/`** — `photonics.md`, `photonicsnotes.md`.
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

### 3a. Sweep scripts don't isolate their swept variable (lower severity, diagnosed)

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

### 3b. `C2` (physical thermal-drift) mode cannot fail from phase drift at all — root cause, NOT yet fixed

While re-running the ΔT sweep isolated (all other params at 0, via the new
harness in §4), recovery came back **100% at every ΔT from ±5K through
±500K**, and stayed 100% even under a deliberately stressed config (100×
larger `dn_eff_dT`, 5× larger arm-length mismatch). That's not a real
"thermally robust" result — 500 K is not physically meaningful, and no
configuration should be perfectly immune. Root cause, confirmed by reading
the code:

`software/tests/test_photonic_models_smul.py:598`, inside the `noise_mode
== 'C2'` branch of `ModelC_NoisyOptical.smul_with_noise`, sets
`lo_phase = 0.0` **unconditionally**. Compare line 538 in the `C0` branch:
`lo_phase = delta_phi if lo_track else 0.0` — there, `lo_track` actually
changes behavior (and is exactly what separates the fragile `T1` result
from the robust `T2`/`T3` results in the existing 16k-trial sweep). In
`C2`, `lo_track` is accepted as a parameter but silently has no effect: the
coherent receiver's demodulation reference never incorporates the
thermally-computed phase drift, so recovery ends up magnitude/power-based
and rotation-invariant by construction — immune to phase drift of any
size, for the wrong reason.

**Consequence: no one has run a valid thermal (or any `C2`-physical-drift)
recovery-envelope experiment yet.** Copilot's was masked by 3a; this
session's isolated rerun was masked by 3b. The `C0`/`C1` results (`T1`
through `T3` in the existing sweeps) are unaffected — they don't go through
this code path.

**This is an architecture decision, not a one-line patch:** how should
thermally-drifted phase interact with the local-oscillator reference in a
`C2` experiment? Options include making `lo_track` behave the same way it
does in `C0` (LO either tracks the physical drift or stays fixed), or
introducing a genuinely separate "assumed/calibrated" LO phase distinct
from the true physical drift (closer to how `calibration_error` already
works for loss). Needs a decision before `run_experiment()` in §4 is
re-pointed at `C2` for real.

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

Not yet reconciled with `results/sweeps/README.md`'s independent replay
mechanism (master-seed + per-cell metadata JSON) — two reproducibility
schemes now exist for the same purpose. Pick one before Phase 2 restarts.

## 5. What's next (in order)

1. **Resolve §3b** — decide the `C2` LO-reference semantics, fix
   `test_photonic_models_smul.py:598`, confirm with a smoke test that a
   isolated-thermal config *can* fail at some ΔT (i.e., the fix actually
   creates a failure mode, not just changes the numbers).
2. **Reconcile the two reproducibility schemes** (§4's `photonic_experiment_config.py`
   vs `results/sweeps/README.md`'s metadata-JSON replay) — pick one so
   Copilot/GTP/Claude aren't maintaining parallel harnesses.
3. Re-run the actual Phase 2 single-operation sweeps (temperature,
   calibration error, amplitude, detector noise, combined) once 1–2 are
   settled, using whichever harness is chosen.
4. Only after Phase 2 gives a real envelope: Phase 3 (define the
   regeneration/`REGEN` architecture and the `K` parameter — see GTP's
   three-architecture writeup in this session's chat log, not yet filed
   anywhere in the repo) and Phase 4 (K-operation cascade sweeps).
5. Root-hygiene cleanup (§2) — move the root-level `.md`/`.py` files into
   `photonics/` or `spu_strategy/` once the branch's file layout is
   settled; not urgent, flagged for whenever this branch pauses.

## 6. PARKED (unchanged from 08-16, still applies to everything except this branch)

SPU-13 tranches · GPU/rasterizer · PDM audio · Padé/RPLU2 · quantum · the
papers · `QADD` · ECP5 port · the `irotc_spi` router anomaly ·
`six_step_probe` trimming · A7 manifest targets · re-anchor decisions for
§3.2g.1 and §3.2k · `build_a7.sh:12` spin-name drift. SPU-4 step 5 (real
INA226 data) is not parked — it's the primary line, this branch runs
alongside it, not instead of it.
