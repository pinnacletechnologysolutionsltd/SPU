# D4 P1b noisy-input experiment result

Date: 2026-10-10. Status: bounded software tranche qualification PASS; no hardware promotion.

The one authorized attempt completed with exactly one COMPLETE marker, exit 0, in 309/1,800 seconds. All 240 fold/arm/capacity rows, 48 aggregate rows and 96 profile summaries are present. The independent audit recomputed 1,050,624 predictions. Frozen source hashes match preflight, and the manifest was checked again during review.

Evidence: [runner result](../build/d4_canonical_decision_p1b/full_run_01/result.json), [experiment review](../build/d4_canonical_decision_p1b/full_run_01/experiment_review.json), [full exact results](../build/d4_canonical_decision_p1b/noisy_01.json), and [frozen manifest](../build/d4_canonical_decision_p1b/preparation_01/manifest.json).

## Complete error curves

Primary held-out classification error (%) below uses equal base and equal profile weights. Percentages are rounded; exact fractions, both profiles and base-orbit-weighted results remain in the full report. K is prototype count. Quantized codebooks cost 18K bits; noisy controls cost 34K bits. Equal K does not imply equal bits.

| Arm | K=1 | K=2 | K=4 | K=8 | K=16 | K=32 |
|---|---:|---:|---:|---:|---:|---:|
| canonical_q_som | 57.89 | 57.89 | 57.89 | 39.47 | 41.23 | 42.98 |
| canonical_q_codebook | 57.89 | 42.98 | 37.72 | 31.58 | 40.35 | 33.33 |
| raw_q_som | 57.89 | 57.89 | 57.89 | 59.41 | 53.85 | 51.29 |
| raw_q_codebook | 57.89 | 59.42 | 61.04 | 60.64 | 53.72 | 47.00 |
| raw_q_augmented_som | 57.89 | 57.89 | 57.89 | 59.44 | 57.52 | 48.37 |
| raw_q_augmented_codebook | 57.89 | 57.89 | 57.89 | 59.90 | 55.12 | 51.91 |
| raw_noisy_codebook | 57.89 | 62.99 | 62.88 | 60.66 | 52.25 | 45.45 |
| raw_noisy_augmented_codebook | 57.89 | 57.89 | 57.89 | 57.89 | 55.27 | 45.74 |

## Interpretation and limits

Canonical codebooks improve over raw quantized codebooks at the larger tested capacities. At K=32 and 576 codebook bits, canonical codebook error is 33.33%, compared with 47.00% for raw codebook and 51.91% for augmented raw codebook. Canonical SOM error is 42.98% at that capacity; canonicalization does not establish a general SOM advantage. All capacities are retained above.

The direct quantized norm rule has 8/57 (14.04%) equal-profile error, matching the empirical majority-label error for the pooled quantized observations. The noisy-coordinate norm rule has 9/38 (23.68%) error. Both controls outperform every learned arm on the primary metric. The profile-1 quantized norm-rule crossing rate is 16/57; it remains distinct from the pooled quantized-input majority error. Raw noisy codebooks retain more information but use wider storage and do not demonstrate better learned classification in this experiment.

Canonical action reconstruction and equivariance assertions passed for the specified scalar-multiple family. Action-class error, actual quantized-vector error and displacement from the rational noisy action are reported separately, including zero-vector cases. No arbitrary-policy equivariance follows.

This is a bounded synthetic software result. Canonicalizer, quantizer and training-workspace costs are unmeasured; no RTL area, throughput, timing, power or silicon result follows. The result supports retaining the software reference and complete curves. It does not justify hardware promotion against the better simple-rule controls.

Required repository-wide, trace, math and Artix-7 qualification gates for this tranche passed against the isolated snapshot. This is separate from the earlier ISA qualification. No rerun or new hardware campaign is authorized by this closeout.


## Qualification closeout

The repaired attempt has exactly one COMPLETE marker, exit 0 and duration
2,037/7,200 seconds. All 13 fresh gate records exit 0, including scoped
regression 75/0, repository verification 243/0, ROTC/IROTC traces, mathematical
oracles and the separate requested-25-MHz Artix-7 Padé build. Initial and final
identity checks passed for all 2,034 frozen source files and dependencies.

Eleven completed computational gates were explicitly reused from the original
attempt, with matching source, command, log, exit and result-artifact hashes.
That original attempt was canceled at the owner's request after buffered
output obscured advancing tests; its durable FAILED/143 result is preserved.
The restarted wrapper's unbuffered output and gate timestamps restored progress
visibility. No test expectation, arithmetic rule or corpus was changed.

[Qualification review](../build/d4_canonical_decision_p1b/qualification_02/qualification_review.json)
records fresh and reused evidence separately, source/evidence digests and the
separate Padé result. [Runner result](../build/d4_canonical_decision_p1b/qualification_02/result.json),
[reuse ledger](../build/d4_canonical_decision_p1b/qualification_02/reused_gate_results.json)
and [Padé log](../build/d4_canonical_decision_p1b/qualification_02/gates/artix7.log)
remain independently reviewable.

This closes the bounded D4 software tranche for the frozen snapshot. The
restart campaign ends after its first successful attempt; two authorized
slots remain unused and do not authorize a redundant run after success.
The learned-model limitations above remain unchanged. No integrated
Surd/REGEN image or silicon evidence follows from this qualification.
