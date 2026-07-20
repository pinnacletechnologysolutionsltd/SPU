# SPU-13 Session Handover — 2026-07-20

## Stop state

The proof-hardening, engineer onboarding, and non-engineer audience-explainer
tranches are closed.

- The last work commit before this handover is
  `c0e7c44ccdebb17b1127e87a34255cd6f1fc0b60`.
- `origin/master` remains at
  `9c2aa40790144d2852497a0706445b0467cfbd2b`; local `master` was nine commits
  ahead before this handover was added. Nothing from this session has been
  pushed.
- The tracked worktree was clean before this file was added. The private,
  ignored SOM roadmap records the audience-explainer tranche as closed.
- The last independent full-regression audit was 173/173. Changes after that
  audit are documentation-only.
- The GitHub Pages site is configured to deploy on a docs push. The new
  audience page passed local content, claim, navigation, and link/anchor gates;
  MkDocs was not installed locally, so the rendered build remains a CI gate.

Key landed work:

- `6edcf9b` — two-transaction and width-plumbing formal proof hardening for the
  Karatsuba candidate; production multiplier unchanged.
- `11a2a92` — first-hour onboarding, programmer Quadray guide, and demo tour.
- `9d73065` — two-minute non-engineer explainer with maintenance, robotics, and
  evaluator doors.
- `1c14d4e` through `c0e7c44` — documentation corrections for current hardware
  and test status.

## Next SOM product tranche: INA226 physical acquisition

Yes: the next decisive SOM product experiment is the frozen INA226 coarse
normal/load/stall capture. It is Phase B physical acquisition, gated on the
sensor, breadboard, safely rated replaceable actuator, current-limited supply,
and interlock parts being physically available. The repository does not record
that those parts have arrived, so confirm the bench inventory first.

Do not treat this as bearing diagnosis. The frozen question is only whether one
100 Hz current channel can distinguish normal operation, elevated load, and a
safely current-limited stall. The contract, features, folds, trainer, and pass
gates must not change after physical data is seen.

Read these in order before powering anything:

1. `hardware/pcb/bench_adapter/power_ready_interlock_breadboard.md`
2. `docs/INA226_COARSE_MONITOR_CONTRACT.md`
3. `docs/INA226_CAPTURE_RUNBOOK.md`

## Bench-day order

1. **Prove the power-ready interlock first.** Test target-off, target-on, and
   power-down transitions with the SN74CBTLV3125/TLV3011B circuit. Keep the
   100-ohm SPI series resistors and never drive an unpowered FPGA.
2. **Qualify the measurement setup.** Confirm the breakout is marked `R100`,
   use a documented actuator whose continuous current is below the 750 mA
   measurement headroom, set the supply limit no higher than that rating, and
   keep a physical cutoff within reach. Do not measure an FPGA supply rail.
3. **Initialize the manifest with real values.** Replace every example actuator
   model, voltage, current rating, and supply limit in the runbook. The manifest
   is part of the evidence; do not leave placeholders.
4. **Validate identity, cadence, and scaling before labels.** The INA226 startup
   check must pass, timestamps must sustain the frozen 100 Hz cadence, and
   shunt voltage/current must satisfy the R100 consistency check.
5. **Capture the frozen thirty sessions.** Use ten blocks containing normal,
   elevated-load, and current-limited-stall sessions in the prescribed rotated
   order. Each file must provide at least 128 valid rows. Stall exposure is at
   most 1.5 seconds, followed by at least 30 seconds of unblocked cooldown.
6. **Seal before scoring.** Run the manifest `seal` and `verify` commands. A bad
   session is repeated whole; never delete an inconvenient row or select a
   favourable interval.
7. **Run twice and compare artifacts byte-for-byte.** The expected materialized
   dataset is 30 sessions and 120 windows. Preserve the result JSON, manifest,
   capture hashes, confusion matrices, feature ranges, and confidence gaps.
8. **Respect the frozen truth gate.** FPGA replay is allowed only if aggregate
   balanced accuracy is at least 90%, the worst fold and every class recall are
   at least 80%, all acquisitions validate, and every generated SOM1 record
   matches the exact software oracle. A failed gate is a publishable negative,
   not permission to tune version 1.

If the software gate passes, proceed to the documented Tang and Artix SOM1
replay. If it fails, record the result honestly and stop; any changed
hypothesis needs a separately frozen versioned contract.

## Useful restart commands

```sh
git status --short --branch
git log --oneline --decorate origin/master..HEAD
python3 tools/ina226_capture_pipeline.py --help
python3 run_all_tests.py
```

Before public outreach, push the local commits and confirm both the full CI job
and Pages deployment are green. The Show HN/external-replication gate is open
once that publication step is complete and does not depend on the INA226
result.

## Explicitly parked

- changing the frozen INA226 task after observing results;
- high-rate bearing-fault diagnosis and another public-dataset feature search;
- production Karatsuba replacement, integration place-and-route, and the A31
  tower schedule tranche;
- custom bench-adapter PCB fabrication;
- new FPGA purchases as a prerequisite for the INA226 experiment;
- pricing, branding, custom-domain purchase, and new marketing demos.

The highest-leverage next action is therefore conditional: if the safe bench
parts are present, start Phase B in the order above; if they are not, push and
verify the documentation/CI stack, prepare outreach, and wait rather than
spending the frozen experiment's evidence budget on more synthetic tuning.
