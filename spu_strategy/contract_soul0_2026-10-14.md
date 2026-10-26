# Soul-0 software experiment contract

**Date:** 2026-10-14  
**Contract ID:** `contract_soul0_2026-10-14.md`  
**Status:** ACTIVE — bounded software-only experiment

## Commands

```bash
python3 -m software.tests.test_soul0
python3 -m software.research.soul0.experiment --out build/research/soul0/run_01
```

The output directory must not exist before the experiment command runs. One
launch is authorized. Do not overwrite, retry, recapture physical data, or
change this contract after seeing the result.

## Objective and scoped files

Determine whether a two-regime persistent operating history improves
deterministic anomaly decisions after regime changes while retaining the first
regime. This experiment is synthetic and software-only.

Target files:

- `software/research/soul0/model.py`
- `software/research/soul0/experiment.py`
- `software/research/soul0/__init__.py`
- `software/tests/test_soul0.py`
- `spu_strategy/contract_soul0_2026-10-14.md`

Do not modify INA226 datasets, existing SOM models, hardware, RTL, the VM, or
shared regression infrastructure.

## Frozen experiment

- Sensor values are signed integers in a normalized device-independent unit.
- Regime A has center 100; regime B has center 200.
- Deterministic normal variation repeats `[-2, -1, 0, 1, 2]`.
- Initial training uses eight regime-A observations.
- Evaluation order is eight regime-A observations, sixteen regime-B
  observations, then sixteen regime-A observations.
- Inject one isolated +60 transient in each evaluation phase. It is not a
  regime change.
- Every model uses anomaly threshold 20 and receives the same normalized
  observations in the same order.
- Compare: fixed stateless center; an eight-sample rolling-mean adaptive
  baseline; and Soul-0 with at most two persistent regime prototypes. The two
  adaptive models have the same 64-byte logical-state ceiling. Report actual
  logical-state bytes and serialized checkpoint bytes separately.
- Soul-0 creates a new regime only after three consecutive observations whose
  residuals exceed the threshold and whose values remain within the threshold
  of their candidate mean. A matching known regime clears the candidate.
- Device gain and offset are held outside the soul checkpoint. Migration uses
  a second device calibration that encodes the same normalized stream exactly.
- Save and restore once between regime B and the return to regime A. Compare
  decision traces and final serialized state byte-for-byte.

## Acceptance gates

1. **Persistence:** uninterrupted and restored Soul-0 continuations produce
   identical decision traces and identical canonical checkpoint bytes.
2. **Adaptation:** Soul-0 raises at most four false alerts on the sixteen
   healthy regime-B observations and fewer than the rolling-mean baseline.
3. **Retention:** Soul-0 raises at most one false alert on the sixteen healthy
   regime-A return observations and at least three fewer than the rolling-mean
   baseline.
4. **Migration:** transferring only the Soul-0 checkpoint to the second
   calibration produces the same normalized observations, decisions, and
   resulting checkpoint as the source device.
5. **Bad association control:** the isolated transient in regime A does not
   allocate a regime prototype.

Record fault-detection count, false-alert count by phase, adaptation alerts,
retention alerts, logical-state bytes, checkpoint bytes, integer primitive
operations per update, and median/p95 decision latency. Latency is descriptive
and is not an acceptance gate. Count one integer add, subtract, multiply,
absolute value, floor division, or comparison as one model-level primitive
operation; exclude Python interpreter and serialization operations from that
count.

## Stop conditions

- Stop and report a failed gate without tuning the sequence, thresholds,
  baselines, or acceptance criteria.
- If the source and destination calibration cannot represent the same
  normalized stream exactly, mark migration unavailable and stop the migration
  subcheck; do not round or alter the data.
- No physical capture, hardware action, external communication, or additional
  research campaign is authorized by this contract.
