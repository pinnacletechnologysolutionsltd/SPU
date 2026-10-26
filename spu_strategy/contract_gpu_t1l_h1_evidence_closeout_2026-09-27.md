# Engineering Contract: T1l H1 Evidence Closeout

**Date:** 2026-09-27  
**Contract ID:** `GPU-T1L-H1-EVIDENCE-CLOSEOUT-2026-09-27`  
**Status:** `APPROVED; DOCUMENTATION CLOSEOUT COMPLETE`  
**Owner:** John Curley

## 0. Review command

The owner approved the documentation-only closeout. The updates are applied;
the command below is the completed documentation check:

```bash
git diff --check -- docs/hardware_evidence.md \
  spu_strategy/contract_gpu_t1l_pipeline_partition_2026-09-27.md \
  spu_strategy/contract_gpu_t1l_h1_evidence_closeout_2026-09-27.md
```

This closeout performs no simulation, UART transmission, synthesis, place and
route, FPGA programming, or RTL modification.

## 1. Objective

Record the bounded T1l H1 evidence accurately and release the already
timing-qualified GPU bitstream from further H1 investigation. Preserve the
distinction between broad physical repeatability and physical confirmation of
the internal U-stripe pattern.

## 2. Frozen artifacts and prior evidence

* Qualified image:
  `build/spu_a7_100t_GPUVGA_T1L_PIPELINE_PARTITION_B1_S1.bit`
* Image SHA-256:
  `79c9de8fab4a9c40bbc3be845b0a4d2c124279b0704acd76d18aa85e52fe7040`
* Profile: `T1L_MATERIAL_OP=3`, `T1L_PIPELINE_PARTITION=1`,
  `GPU_POST_WINNER_REG=1`.
* Routed `clk_pixel` Fmax: **40.03 MHz**, above the 25 MHz gate.
* Independent production U-stripe oracle: **PASS**, 1,228,800 A/B/C/A pixel
  comparisons; exact initial-A / return-A equality in simulation.
* Physical replay transcript:
  `build/gpu/t1l_pipeline_partition_20260927/h1_repeat_sequence.json`.
* Photos: `docs/bench_captures/t1l_h1_2026-09-27/IMG_1769.jpeg`,
  `IMG_1770.jpeg`, and `IMG_1771.jpeg`. `IMG_1769` is initial A,
  `IMG_1770` is B, and `IMG_1771` is return A. Scene C was operator-observed
  but not photographed.

The selected material predicate is `selected_u_q[12]` for a valid
winner-selected fragment, with true mapped to white and false or invalid
mapped to black. The material is a one-bit U-stripe predicate, not the T1k
diamond grid or the T1j checker.

## 3. H1 claim and classification

Record the following two claims separately:

> **Return-A broad-pattern repeatability: PASS at operator/photo-comparison
> level.** The same two broad white regions are present in the initial and
> return-A captures; differences appear attributable to framing/brightness
> rather than a changed large-scale material pattern.

> **Physical U-stripe visibility/correspondence: INCONCLUSIVE.** The photos do
> not resolve the internal stripe structure clearly enough to claim that the
> expected U-stripe bands themselves were visibly confirmed.

The physical record must not claim per-pixel equality. Exact A/B/C/A return
equality remains the independent simulation-oracle claim. The operator
reported that B showed four separated regions and C looked similar to initial
A. These observations do not override the oracle or establish exact physical
stripe correspondence.

## 4. Authorized documentation scope

The approved documentation-only updates are complete:

* `spu_strategy/contract_gpu_t1l_pipeline_partition_2026-09-27.md` — replace
  `H1 READY / NOT RUN` with the two H1 claims from §3 and link the archived
  photos and replay transcript;
* `docs/hardware_evidence.md` — add the same bounded physical evidence,
  explicitly separating return-A broad-pattern repeatability from unresolved
  stripe correspondence.

Do not change the RTL, fixtures, scene sender, pipeline, timing constraints,
build scripts, or bitstream. Do not authorize another FPGA build or physical
replay as part of this closeout.

## 5. Stop conditions and next tranche boundary

Stop if the source artifacts, bitstream identity, photo labels, or transcript
do not match §2. Do not reinterpret the result as an RTL, timing, or packet
handling defect. Do not reopen those paths under this closeout.

T1l is closed at the stated evidence boundary: digital U-stripe behavior is
oracle-qualified; hardware shows broad return-A repeatability; exact physical
stripe correspondence remains unconfirmed. Any further GPU feature requires a
separate contract with a frozen objective and verification boundary.

## 6. Evidence dimensions

| Evidence dimension | T1l result |
|---|---|
| Structural validation | Profile and pipeline-partition checks PASS |
| Functional simulation | Production oracle PASS: 1,228,800 pixels |
| Synthesis / place-and-route | PASS; routed `clk_pixel` 40.03 MHz |
| Interface validation | Frozen 175-byte scene writes drained; display responded |
| Silicon observation | Broad return-A repeatability PASS; stripe correspondence INCONCLUSIVE |
