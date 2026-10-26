# Soul-0 held-out adaptation experiment contract

**Date:** 2026-10-14  
**Contract ID:** `contract_soul0_heldout_2026-10-14.md`  
**Status:** COMPLETE — the authorized one-launch campaign was consumed

## Commands

```bash
python3 -m unittest software.tests.test_soul0_heldout -v
timeout 60s python3 -m software.research.soul0.heldout_experiment --out build/research/soul0/heldout_01
```

The output directory must not exist before the experiment command runs. The
campaign budget is one launch, a 60-second per-attempt wall-clock limit, and a
60-second cumulative budget, authorized by the owner on 2026-10-14. A launched
attempt consumes the single slot even if it fails, times out, or becomes
unavailable. Do not retry, tune, or extend the budget without a new
owner-authorized contract.

## Objective and scoped files

Determine whether persistent regime memory improves false-alert behavior on
held-out regime changes and preserves earlier regimes, compared with stateless
and conventional rolling-mean models under a common 32-byte logical-state
ceiling. Characterize the known integer running-mean stall for a seeded
profile at center 180 with count 2; this experiment does not claim that the
current update rule recovers that profile. Synthetic software-only
experiment; no physical data.

Target files:

- `software/research/soul0/model.py`
- `software/research/soul0/counted.py`
- `software/research/soul0/heldout_experiment.py`
- `software/research/soul0/heldout_fixtures_v1.json`
- `software/research/soul0/heldout_manifest_v1.json`
- `software/tests/test_soul0_heldout.py`
- `spu_strategy/contract_soul0_heldout_2026-10-14.md`

Do not modify the original Soul-0 experiment, its run artifacts, INA226
datasets/models, hardware, RTL, the VM, or shared regression infrastructure.

## Frozen experiment

- Use signed integer sensor values in a device-independent normalized unit.
- Training regime A: center 100, eight observations, repeating noise
  `[-2, -1, 0, 1, 2]`.
- Evaluation order: 16 observations at held-out regime B (center 200), 16 at
  held-out regime C (center 150), 16 returning to A (center 100), then 16
  returning to B (center 200). Use the same repeating noise sequence in each
  phase, restarting at index zero.
- Inject one isolated +140 transient at index 10 in each phase. Exclude that
  sample from healthy false-alert counts and require the model to alert on it.
- All models receive the same normalized observations in the same order and
  use threshold 20.
- Compare a fixed stateless center, an eight-sample rolling mean, and Soul-0
  with three persistent regime prototypes and three-observation confirmation.
  Keep each model's declared logical state at or below 32 bytes. Record actual
  logical-state bytes and serialized Soul-0 checkpoint bytes separately.
- Preserve the existing Soul-0 state-transition and serialization semantics.
  Correct the operation counter by incrementing it at each executed arithmetic
  or comparison primitive; do not change the original experiment or use a
  different threshold after observing outcomes.
- For the seeded-profile regression, initialize one Soul-0 profile at center
  180 with count 2, then provide 16 healthy observations from regime B (center
  200, same noise). Record alerts and final profile center. Preserve and
  report the known outcome: integer running-mean updates stall at center 193,
  seven units below the target and outside the five-unit characterization
  tolerance. Do not change the seed or model rule to make this check pass.
- Classify this fixture only as an **out-of-range transient detection** test.
  Faults that resemble another normal regime are an unresolved ambiguity and
  are not tested or claimed here.

## Frozen fixture and source hashes

The fixture enumerates the observed phases and the full noise envelope. The
manifest hashes the fixture, counted models, evaluator, base model, and focused
test. The experiment refuses to run if any manifest entry differs.

| Artifact | SHA-256 |
|---|---|
| `software/research/soul0/heldout_fixtures_v1.json` | `279a4a78d332eb1f04be47be9084fef027759772f0fc643444e8ea29b7816e16` |
| `software/research/soul0/heldout_manifest_v1.json` | `f19ae3ab010cedc44d33442a62b94e3d286d2533b10266be3865296b3bfddceb` |
| `software/research/soul0/counted.py` | `807107914dfb415b7fdfb204cbfa1888d0dd84645f61783049904b79f49ba6f3` |
| `software/research/soul0/heldout_experiment.py` | `9b7169adbb1d70b342978f3d9d9ce2996ec3b0c9fb3f19bdc6a9fdfb944709b4` |
| `software/research/soul0/model.py` | `6e454df7a819a775ee2a9f936adf0ecad50a4d1cbdc6365d2023da73d7203d83` |

Minimum distance to any normal prototype range, including both sensor noise
and prototype-center noise, is strictly above the threshold:

| Phase | Minimum distance | Threshold | Margin |
|---|---:|---:|---:|
| A / A return | 36 | 20 | 16 |
| B / B return | 136 | 20 | 116 |
| C | 86 | 20 | 66 |

Distance equal to 20 is accepted as normal by the classifier; these minima are
strictly greater, so the fixture tests out-of-range transients.
- Count model-level primitive operations at the operation sites in the new
  evaluator: integer add, subtract, multiply, absolute value, floor division,
  and comparison. Count each executed primitive once; exclude loop/index
  mechanics, allocation, serialization, and Python runtime overhead. Include
  a test that checks operation counts on fixed short traces.
- Report false alerts by phase, transient detections by phase, adaptation
  alerts, return-regime alerts, logical state bytes, checkpoint bytes,
  primitive operations by phase, and median/p95 Python decision latency.
  Latency is descriptive, not an acceptance gate.

## Acceptance gates

1. **Held-out adaptation:** Soul-0 raises at most four healthy alerts during
   B and fewer than the rolling-mean baseline during B.
2. **Capacity adaptation:** Soul-0 raises at most four healthy alerts during
   C and allocates no more than three prototypes.
3. **Retention:** Soul-0 raises at most one healthy alert during return to A
   and at least three fewer than the rolling-mean baseline.
4. **Second return:** Soul-0 raises at most one healthy alert during return to
   B.
5. **Transient detection:** every model detects all five injected transients.
6. **Seeded-profile regression:** report the center-180/count-2 profile's
   final center, target error, and `recovery_succeeded: false`; the regression
   is captured only when the final center is 193, error is 7, and no profile
   is added. This gate records the limitation; it does not claim recovery.
7. **Memory:** every model remains within the 32-byte logical-state ceiling.
8. **Deterministic replay:** the same command and fixed input sequence produce
   byte-identical canonical JSON output after excluding latency fields.
9. **Prototype separation:** for every phase fault, enumerate every fault
   value allowed by its noise range and every normal prototype center allowed
   by the stated center-noise bound. The minimum absolute distance must be
   strictly greater than 20; equality is inside the acceptance region.

Do not combine gates into a composite score. A failed gate is reported as
failed; do not retune or rerun under this contract.

## Verification commands

Run the focused test command first. After implementation, run the one
authorized experiment command exactly once only after the proposed budget is
approved. Then run:

```bash
git diff --check -- software/research/soul0/model.py software/research/soul0/heldout_experiment.py software/tests/test_soul0_heldout.py spu_strategy/contract_soul0_heldout_2026-10-14.md
```

## Stop conditions

- If pre-execution review finds contradictory gates, invalid state accounting,
  or fixture/hash disagreement, halt and report the defect before launch.
- If any focused test fails, stop before launching the experiment.
- If the one attempt fails, times out, or becomes unavailable, preserve the
  evidence and stop. A new attempt requires a new owner-authorized contract
  and budget.
- No hardware action, physical data capture, external communication, or
  product claim is authorized by this contract.
