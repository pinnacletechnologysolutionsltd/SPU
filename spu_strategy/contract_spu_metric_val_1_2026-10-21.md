# SPU-METRIC-VAL-1 — Intrinsic Geometry Correctness Audit (PREPARATION)

Status: PREPARATION COMPLETE / EXECUTION HOLD (needs explicit GO)
Authority: pasted brief 2026-10-21 ("GO for preparation… HOLD execution").
Class: A host-only validation. No source edits, RTL repair, synthesis, P&R, flashing.

## 0. Source identity (verified in preparation, read-only)

| Item | Value |
|---|---|
| Audited commit | `4e0d5b908e5bb1e0e86ba979b87affb83bd2a372` (= `origin/master`, `git ls-remote`) |
| Where it exists locally | `/home/user/Projects/hardware/spu-release-candidates/release-3d-final` (clean) |
| NOT in | `/home/user/Projects/hardware/SPU` (HEAD `963a685`, 872 commits, no `4e0d5b9` object) |
| Working-tree `spu_vm.py` | sha256 `5fda0bad…` — **dirty** (CPU-PROFILE-2 edits: profile/manifest/opcodes), differs from pinned `c83020ea…` |
| `davis_gate_dsp.v` | `6b252a34…` identical in pinned clone and working tree |
| `davis_gate_dsp_tb.v` | `0d3e0387…` identical |
| `rotc_thirds_native.py` | `2cc850f0…` identical |

Decision: audit the **pinned clone** `release-3d-final` (read-only; copy to `build/metric_val_1/<run>/src` with `cp -r --reflink=auto`, hash-check before and after). The working tree is excluded because it carries unrelated uncommitted edits. Reachability is then assessed against both (QuadrayVector section of `spu_vm.py` has no diff in the sliced comparison; re-verify with full diff at execution).

## 1. Blockers / flags (Halt-and-Flag)

1. **IMG-0A artifacts not found.** No report, proof script, results or log for IMG-0A exists under `SPU/build`, `SPU/spu_strategy`, `/tmp` release dirs, or `~/Projects/hardware`. The only record is the memory note `spu-research-results-2026-10-20.md`. The "32 PASS / 9 FAIL" record cannot be preserved unchanged until the owner supplies its path. **Needed from John: the IMG-0A directory (or confirm it is lost, in which case Validation A–E run without it as prior evidence).**
2. **Spread anomaly numbers disagree.** Brief: "15/16 self-spread". Recorded note: 60° IVM edges → 63/64 (true 3/4); tetrahedral axes → 1 (true 8/9). Code read (no execution): `QuadrayVector.spread` uses pairwise `quadrance()` for pp,qq but the plain `Σ aᵢpᵢ` dot for pq, so `spread(P,P)=pp²−(P·P)²`, which is 0 only if pp = P·P. Execution must reproduce whichever values are real; 15/16 may be one specific vector.
3. **`|cᵢ|≤11585` claim has no source** in `davis_gate_dsp.v`, docs or knowledge (grep empty). Treat as IMG-0A-only claim; derive independently (11585 ≈ 2^15/√8).
4. **Quadrance normalization:** the brief's Q(x)=4Σx²−(Σx)² equals 2× the VM's Σᵢ<ⱼ(cᵢ−cⱼ)² only for scalar-component vectors? Verify: Σᵢ<ⱼ(xᵢ−xⱼ)² = 4Σx²−(Σx)². They are **equal**, no factor 2; confirm in `METRIC_CONVENTIONS.md`.
5. Gowin reachability: `davis_gate_dsp` appears in 3 Gowin Tang scripts (math_probe, rplu2_arith_probe, irotc_spi/southbridge/som_probe/rplu_v2 …) and Artix `synth_a7*.ys`; reachability matrix to be built from `.ys` file lists plus instantiation sites, not assumed.

## 2. Output layout (new directory only)

```
build/metric_val_1/<run-id>/
  AUDIT_REPORT.md  METRIC_CONVENTIONS.md  REPAIR_RECOMMENDATIONS.md  results.json
  REPRODUCERS/{val_a_vm_metric.py, val_b_davis_ref.py, val_b_davis_harness.v, val_c_quadray.py, val_d_transforms.py, val_e_docs.sh}
  identity.json  commands.txt  logs/  (IMG-0A record copied byte-for-byte if supplied)
```

Reproducers import the pinned `src/software` read-only (`python3 -I`, `PYTHONDONTWRITEBYTECODE=1`); oracle uses `fractions.Fraction` only, independent of VM code.

## 3. Validation plan

- **A VM metric:** oracle Q=4Σx²−(Σx)², B=4Σxy−ΣxΣy, spread=1−B²/(QpQq). Cases: self-spread (nonzero), proportional, orthogonal, translation by (t,t,t,t), zero vector (denom 0 → record refusal semantics), random Fraction/surd vectors with fixed seed. Trace callers by `grep -rn '\.spread(\|spread_from_quadrances'` over software, tests, examples; list each as reachable-from (CPU/GPU/VM/Gowin) or VM-only.
- **B Davis Gate:** parse module widths; write bit-accurate Python reference; directed iverilog TB (own copy under REPRODUCERS) at ±min/±max, zero-sum and off-hyperplane (`gasket_sum`), thirds rounding; split valid vs invalid domain per documented interface; derive the 11585 bound.
- **C Conventions:** A₃/A₃* contracts from `spu_vm.py`, `spu13_*` ports, `knowledge/*`; counterexample: integer min=0 host vector with Σ≢0 mod 4 → fractional centered representative.
- **D Transforms:** `cycle`, `rotate` (claimed Q-preserving; check (2+√3) scaling per component), `hex_project` kernel (null vectors, restricted-subspace metric), ROTC thirds; classify isometry/similarity/reflection/projection/general.
- **E Docs:** grep-based inventory of normalization, basis-angle, Weyl-vs-point-group, A₃/A₃*, norm preserve/scale statements; recommendations only.

Every finding: CONFIRMED DEFECT / CONFIRMED LIMITATION / DISPROVED / INCONCLUSIVE / HARNESS DEFECT + reachability from accepted CPU, GPU, VM, Gowin configs.

## 4. Frozen execution limits (proposed; require GO)

1 attempt, 900 s total wall (incl. iverilog), 2 GiB `ulimit -v` per process, 0 retries, no network, no writes outside `build/metric_val_1/<run-id>/`. Run via detached runner if expected >60 s (it should not be):

```bash
tools/run_detached_job.sh --output build/metric_val_1/run_01 --timeout 900 -- \
  bash -c 'ulimit -v 2097152; bash spu_strategy/metric_val_1_run.sh'
```

(`metric_val_1_run.sh` is **not yet written**; to be authored under the execution GO, or on request as part of review.)
Pre/post hash check of the pinned clone and `git -C <clone> status --short` must be empty. Terminal outcome is reported separately from audit disposition: a clean exit is not an audit PASS.

## 5. Out of scope

Repairs, profile/compat decision for `spread()` (SIM-CAP1), multiplier optimization, IMG-0B, documentation edits, hardware.

## 6. Decision tree after execution

Confirmed defect → separate repair+regression tranche (priority: anything reachable from accepted configs). Convention/doc → docs-only change. Optimization → archive for IMG-0B / Gen 2.

---
# AMENDMENT A1 (2026-10-21) — runner preparation; supersedes §1 item 1 and §4 "not yet written"

Status: RUNNER PREPARED / EXECUTION HOLD. Authority: owner decision "GO for preparation of the runner, review materials and static contract amendments only."

## A1.1 IMG-0A provenance (resolved)
Owner supplied `/home/user/Downloads/IMG-0A.zip` (sha256 `0f4b0f19ea6bf6239f5802684da46685947facfce40886421d2c2c5a5958ddf0`). Extracted untouched, read-only, to `build/metric_val_1/prep_01/img0a_received/` (4 files, hashes in `identity_02/logs/img0a_hashes.txt`). The log's final line reads `checks=41 PASS=32 FAIL=9`, matching the report. Nothing from the archive is executed. Its original environment (`/home/claude/img0a`) is unverifiable, so 32/9 stays an **unverified historical summary**, not a reproducible acceptance result; `img0a_proof.py` is prior evidence only. Its two self-declared harness defects (A3-13, VM-2) are carried as HARNESS DEFECT candidates and re-tested properly in val_c / val_a.
Resolved observation: `15/16` = `spread(P,P)` for P=(1,−1,0,0) (VM numerator 60 / denominator 64). `63/64` and `1` are other vectors. All remain unverified observations, not oracle values.

## A1.2 Decisions applied
1. Pinned source = `git archive 4e0d5b9…` from the clean clone into `OUT/src` (read-only, tree hash before/after).
2. `/home/user/Projects/hardware/SPU` is never written. Three files are COPIED (`spu_vm.py`, `davis_gate_dsp.v`, `rotc_thirds_native.py`); originals are hashed before and after.
3. Development comparison: `val_a` runs against pinned **and** against pinned `software/` with only the worktree `spu_vm.py` overlaid; `val_f` compares 14 geometry function bodies by AST hash and records every other changed function.
4. 15/16, 63/64, 1, 11585 are not used as expected values anywhere (grep `REPRODUCERS` to confirm; 11585 appears only as a *tested* reported bound).
5. Davis Gate is simulated on both paths: `DEVICE="SIM"` and `"GW5A"` (Gowin path, with `tests/common/sim_spu_gowin_multiplier.v`, a 1-register `a*b` model). Includes a dynamic stream that probes a suspected pipeline-alignment skew (ivm_accum_r is 2 stages deep but the gasket-square chain is 3) — hypothesis from RTL reading only, falsifiable in the run.
6. Oracle derives the metric (Q=4Σx²−S², B=4Σxy−ΣxΣy) in-script with `fractions.Fraction` and a private Q(√3) class; no VM code is used as oracle.

## A1.3 Prepared files (all under `spu_strategy/metric_val_1/`)
`metric_val_1_run.sh` (modes `run|identity|selftest`), `stage_run.py` (RLIMIT_AS 2 GiB, process-group SIGKILL, rusage), `assemble_results.py`, `REPRODUCERS/{val_a_vm_metric.py,val_b_davis_ref.py,val_b_davis_harness.v,val_c_quadray.py,val_d_transforms.py,val_e_static.sh,val_f_vm_diff.py,val_g_img0a_record.py}`.

## A1.4 Demonstrated before review (no A–E execution)
| Check | Result |
|---|---|
| `identity` mode (`build/metric_val_1/identity_02`) | HEAD == pin, clone clean, src tree sha `5fa4776c…`, worktree file hashes recorded, `IDENTITY_OK` |
| `selftest` mode (`build/metric_val_1/selftest_01`) | `SELFTEST_PASS`: `sleep 30` killed at 2.0 s (TIMEOUT, rc −9); 3 GiB allocation → `MemoryError` under the 2 GiB cap; write probe landed in `OUT/work`, not the cwd; no ledger consumed |
| Static parse of all Python reproducers, `bash -n` on shell scripts | OK |
| Attempt ledger `build/metric_val_1/ATTEMPT_LEDGER` | does not exist (slot unconsumed) |
Not demonstrated: any reproducer's run. `identity_01` is a failed first attempt of identity mode (tool-version capture died under `set -o pipefail`; fixed); retained as evidence, consumed nothing.

## A1.5 Limits / accounting
Inner deadline 840 s (each stage gets min(stage cap, remaining)); outer detached timeout 900 s; `ulimit -v 2097152` for the runner and `RLIMIT_AS` 2 GiB per stage process; stage caps: G 30, A 60×2, B 60×6 (ref, 2 compile, 2 run, check), C/D/E/F 60 each. Stages are independent: a crash or timeout in one is recorded and does not block the others. Environment is scrubbed (`HOME`/`TMPDIR` → `OUT/home`, `PYTHONDONTWRITEBYTECODE`). Ledger slot is consumed *before* extraction; a second `run` refuses.
Terminal marker (`OUT/TERMINAL`): `RUN_COMPLETE` | `RUN_INTEGRITY_OR_INFRA_FAILURE` | `IDENTITY_FAIL`, infrastructure-only. `results.json` leaves every check's disposition UNASSIGNED. A reproducer `ok:false` means "deviation observed", which may be a CONFIRMED DEFECT, LIMITATION or HARNESS DEFECT; the reviewer classifies. Post-run: AUDIT_REPORT.md / METRIC_CONVENTIONS.md / REPAIR_RECOMMENDATIONS.md are authored from results.json in a *separate* step and are not produced by the runner.

## A1.6 Open risks for the reviewer
1. **Zero retries with unexecuted reproducers.** A harness bug costs the only attempt. Mitigations: stage independence, stdout/logs retained, harness defects are a legal finding class. Option for the owner: authorize a separate zero-budget *fixture dry-run* of the reproducers (not counted as validation), or accept the risk.
2. The 11585 bound is derived as the signed-32 reading of `4Σc²`; the unsigned bound is 16383 (16-bit difference limit 2M ≤ 32767). Which reading governs depends on the consumers found by `val_e.quadrance_consumers`; reviewer decides.
3. `val_e` is evidence collection (grep hits, `ok:null`), not adjudication; doc findings need human reading.
4. RTL thirds (`div3` rounding) are only inventoried statically; no thirds RTL simulation is included (scope).
5. Gowin multiplier model is the test-tree behavioral stub; real DSP inference/timing is out of scope.

## A1.7 Exact execution command (NOT AUTHORIZED; for review)
```bash
cd /home/user/Projects/hardware/SPU
tools/run_detached_job.sh --output build/metric_val_1/detached_run_01 --timeout 900 -- \
  bash spu_strategy/metric_val_1/metric_val_1_run.sh run /home/user/Projects/hardware/SPU/build/metric_val_1/run_01
```
Interpret only when exactly one of COMPLETE/FAILED/TIMEOUT is present, then read `run_01/TERMINAL` and `run_01/results.json`.
