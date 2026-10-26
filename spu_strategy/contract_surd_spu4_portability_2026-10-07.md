# SPU-4 Surd portability screen

Status: one bounded target-mapping investigation; no SPU-4 product integration.

## Retained workload basis

Use the already accepted S0 retained robotics results at
`build/spu_surd_register/s0_20261007_attempt04/run_01/results.json` and the
independent unnormalized-chain observations at
`build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/results.json`.
Keep synthetic Surd operands separate. Do not rerun or alter either baseline.

The S0 retained cohort has 32 exact vectors and rational-only joint coefficients
(`b=0`, common coefficient scale 3), exercised at 1, 3, 6 and 12 joints. For the
per-joint FIT_RESCUE policy, all 33,088 retained operations across the frozen
chain set had zero fallbacks at W=16, 32 and 64. Across the retained run the
largest recorded raw accumulator was 11 signed bits; recorded denominator
products were at most 8 unsigned bits. These are observations for this cohort,
not input-domain proofs. S0 includes a normalizing state boundary after each
joint. Keep that fact distinct from the earlier unnormalized-chain model, whose
12-joint explicit-denominator path observed a 35-bit peak and 167 W=32 fallbacks.

## First target candidate

Map only W=16, LANES=1 with one multiplier and one shared exact normalizer on
GW5A-LV25MG121NES, at the existing SPU-4 12 MHz target. Preserve the current
Quadray register file, SPU-4 core, sequencer, and customer ABI. The wrapper is an
isolated mapping workload; it is not CPU integration or a bitstream for use.
Do not add tuple storage or an instruction.

Run once, with durable detached evidence:

```bash
tools/run_detached_job.sh \
  --output build/spu_surd_register/spu4_portability_20261007/gw5a_w16_lanes1_01 \
  --timeout 1800 --notify-desktop -- \
  bash tools/bench_spu4_surd_gw5a.sh \
  build/spu_surd_register/spu4_portability_20261007/gw5a_w16_lanes1_01 16 1
```

Inspect only its durable terminal marker before interpreting logs. Record mapped
LUT, FF, multiplier/DSP, carry resources and nextpnr timing against 12 MHz. Do
not pack, load, or claim silicon evidence.

## Decision and bounded expansion

If W=16 LANES=1 maps and routes at 12 MHz, record it as a feasible optional
hardware budget point only. It does not establish robotics speedup or justify
adding the block to SPU-4 by default. Do not broaden the mapping sweep unless a
retained workload violates W=16 exactness or the measured device budget leaves a
specific width/lane comparison decision unresolved. Any additional mapping
attempt needs a separately frozen budget. Main CPU integration remains the
priority; this screen does not modify CPU or SPU-4 production RTL.
