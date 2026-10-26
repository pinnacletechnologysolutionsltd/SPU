# GPU compiler reduction catalogue GCR-1

**Date:** 2026-10-12

**Status:** PROPOSED — contract and source review only. Implementation, experiment
execution and qualification budgets are not authorized by this draft.

The [ratification amendment](contract_gpu_reduction_gcr1_ratification_amendment_2026-10-12.md)
specifies the private C2 adapter, mandatory observations, C3 validation/cache rules
and proposed staged budgets. Those execution rules remain subject to review.

Read the named reference surfaces before approving implementation:

```bash
sed -n '1,200p' software/spu_gpu_eval/reference.py
sed -n '1,200p' software/spu_gpu_eval/device_arithmetic.py
sed -n '1,180p' software/spu_gpu_eval/device_model.py
sed -n '1,180p' software/spu_gpu_eval/packet.py
sed -n '1,160p' software/spu_gpu_eval/device_packet.py
```

## 1. Objective, profile and authority

Deliver a verified experimental catalogue of exactly three reductions, not a
production compiler pass. Use the existing `t1d-two-triangle-v1` prepared-scene
profile: 640x480, two triangles, inclusive edge coverage, triangle0 wins depth
ties, existing signed16/signed16/signed32 edge fields, uint16 vertex depths and
RGB4. Preserve the existing 64-byte wire layout and packing order.

The unchanged wire fixture and maintained JSON scenes are baselines. The result
does not qualify T1G/T1H, four-triangle, UV, GPU transport/timing or board profiles.
No production compiler/model edits, RTL, packets formats, ISA, dependencies,
device writes, synthesis, routing or changes to Artix-7/AOR/Padé campaigns.

Reuse completed R0/R1 storage work and S1/S2 models; do not repeat codec invention
or describe the storage tranche as unstarted. This is execution-equivalence work,
not a claim that compressed coefficients are safe to execute unreconstructed.

## 2. Exactly selected candidates

| ID | Reduction | Eligibility and scope |
|---|---|---|
| C1 | Cancel a common positive factor from all nine edge coefficients of one triangle | g=gcd(abs(all nine fields)), g>1; divide every field by the same g, leave edge/depth association and z/RGB unchanged; field bounds and nondegenerate valid geometry required |
| C2 | Bypass reciprocal depth setup for a constant-depth triangle | All three uint16 depths equal z; propose prepared (a_z,b_z,c_z,frac_bits)=(0,0,z,0), with original coverage and ordering preserved |
| C3 | Reuse an identical host depth-preparation result | Exact ordered nine edge fields and three associated z fields match; cache key also contains profile and reciprocal-ROM/source identity; RGB and triangle slot remain distinct |

C1 preserves the exact edge signs and depth quotient but can change the device
reciprocal approximation. Independent per-edge factor cancellation is excluded:
it generally changes barycentric weighting unless separately compensated.

C2 preserves the exact constant plane but can remove existing quantization error.
Correcting an approximation is not equivalent execution; any changed device
depth value rejects that application even when displayed RGB happens to match.
The proposed tuple must fit existing prepared field widths; no new transport
route for prepared coefficients is introduced. It is a host-model candidate only.
Its reciprocal metadata is marked unavailable/synthetic, not fabricated as a
device preparation observation. The amendment specifies a private four-field
record and the same existing settled evaluator, without fabricating PreparedDepth
reciprocal fields or changing production containers.

C3 shares only immutable preparation results; validate inputs before cache use.
Do not share mutable lifecycle state, RGB, triangle identifiers or completion
events. It cannot claim reduced FPGA setup cycles or shared-hardware admission.
Include key construction, validation and cache costs in any host accounting.

## 3. Two independent equivalence questions

1. Mathematical: original input vertices and candidate expression denote the same
   coverage and exact rational depth plane. Use vertex cross-products/Fraction as
   the independent original oracle; evaluate transformed expressions in a separate
   oracle that does not import candidate rewriting or preparation arithmetic.
2. Device: compare original and transformed settled T1d model executions at every
   active pixel. Require identical coverage, ordered covered_by, shifted finite
   depth values for every covered triangle, winner and RGB. Both acceptance/rejection
   paths must preserve input validation and create no output on malformed input.

A pre-existing exact/device discrepancy is recorded separately, not attributed to
the reduction. Agreement between two candidate implementations alone is insufficient.
Preserve 37-bit unsigned term masking, sequential signed40 accumulation, signed34
denominator, ROM/Newton reciprocal steps, signed56 prepared products/accumulator,
arithmetic shifts and triangle0 tie behavior from the frozen S2 source.

Also record raw prepared coefficients, reciprocal metadata and per-pixel raw
accumulators as diagnostics. C1/C2 may change representation while preserving the
declared values; these diagnostics are not required to match for this settled-pixel
catalogue. C3 must reproduce the entire original immutable PreparedDepth tuple.
If future consumers observe those raw fields, they need a stronger separate contract.

Runtime admission, busy/ready, reset, activation latency and retirement are outside
the settled S2 model. Classify lifecycle equivalence UNSUPPORTED; no inferred RTL
equivalence, hardware scheduling optimization or successful scene activation.

## 4. Frozen corpus and classification

Retain and hash these existing inputs without edits:

- `examples/gpu/t1d_two_triangle.json`
- `examples/gpu/t1d_two_triangle_vertex_b.json`
- `fixtures/gpu_t1d_scene_wire_64b.bin`
- `fixtures/gpu_t1d_scene_reference.json`
- `hardware/rtl/arch/gpu_reciprocal_lut_q15.mem`

Baseline JSON must compile byte-identically to the frozen wire fixture. The wire
fixture is an identity check, not an independent scene or another workload count.
Use exactly seven additional deterministic variants of the baseline JSON:

1. Reverse both windings while retaining each vertex's z association.
2. Set every vertex depth in both triangles to 0.
3. Set every vertex depth in both triangles to 1000.
4. Copy triangle0 vertices to triangle1; retain distinct original RGB values.
5. Copy triangle0 vertices to triangle1, then add 1 to every triangle1 z; retain RGB.
6. Set triangle0 depths to1000 and triangle1 depths to1001.
7. Set all depths to65535.

Total: two maintained scenes plus seven labeled designed scenes, nine scenes.
No claim of statistical representativeness. Separately test malformed types,
truncation, range violations and degeneracy; these are rejection tests, not valid
corpus scenes. Do not tune candidates or corpus after seeing results.

For each candidate/scene record ACCEPTED, REJECTED or UNSUPPORTED with a reason.
No common factor, nonconstant depth or missing duplicate key is UNSUPPORTED
(ineligible), not a failed optimization. An eligible nonidentity application with
any mathematical/device mismatch is REJECTED with its first counterexample.
An eligible application is ACCEPTED for this finite declared domain only after
all640x480 pixels pass and independent plane/coverage identities hold. Rejections
are experimental findings; failing checker integrity stops qualification.
Any missing required observation makes acceptance UNSUPPORTED with its field and
coordinate recorded; unavailable reciprocal diagnostics alone do not prevent C2
depth comparisons. The amendment freezes the proposed observable validation rules.

Each candidate's summary must distinguish mathematical identity, device identity,
eligibility and untested lifecycle dimensions. No rule is promoted as universal
from a corpus PASS. A production rule would need a reviewed sufficient predicate.

## 5. Negative controls, benefit and evidence

Require detected faults: wrong edge factor or sign; incorrect edge-to-z pairing;
one-bit prepared coefficient corruption; reversed equal-depth winner; and a C3
cache key deliberately omitting z that aliases variant5's triangle1 to triangle0
preparation despite their different depths.
The same independent checker must reject known-wrong outputs. Retain counterexamples
and checker exit/status; do not invent a required optimization win.

Report applicability, exact/device comparison counts, first mismatching pixel,
depth/winner/RGB differences, coefficient bit sizes and setup/evaluation operation
vectors. If host timing is later authorized, measure original and reduced paths
including validation, gcd/key/cache/candidate construction and materialization;
separate corpus preparation and oracle checking. Fixed packets remain64 bytes.
No DSP/LUT, GPU cycle, energy, board or hardware-speedup claim follows.

Freeze HEAD/dirty identity, source/model/ROM/fixture/corpus hashes and exact commands
in a fresh child of `build/gpu_reduction_catalogue/`. Preserve rejected candidates.
Guard source hashes before/after execution; refuse output overwrite. No old gate
count, current worktree or previous software PASS qualifies the new experiment.

## 6. Proposed implementation slice and qualification gate

New isolated files only, each runtime module at most150 lines:

```text
software/experiments/gpu_reduction_candidates.py
software/experiments/gpu_reduction_oracle.py
software/experiments/gpu_reduction_catalogue.py
software/tests/test_gpu_reduction_catalogue.py
```

Exact eventual entry points, not executable/authorized until implementation review:

```bash
python3 -B software/tests/test_gpu_reduction_catalogue.py
python3 -B software/experiments/gpu_reduction_catalogue.py --output build/gpu_reduction_catalogue/experiment_01
```

Before execution ratify candidate target APIs, field/observable definitions and
the independent oracle design, then authorize a frozen bounded campaign with exact
runner commands, attempts, per-attempt and cumulative timeouts. Full pixel sweeps
may exceed60 seconds: use the detached runner and end the turn after LAUNCHED.
No experiment or qualification budget is assigned by this preparation contract.

Keep production arithmetic/model/shared verification untouched. Qualification
requirements must be frozen separately; the AGENTS.md offline T1d user-path rule
requires focused S1/S2/S3 checks and any changed preview/edit/inspect commands.
If implementation crosses into arithmetic kernels, RTL, hardware build flows or
shared test infrastructure, the full repository/trace/math/Padé gates apply with
their own authorized allocation. Do not infer an exemption from software-only scope.

Halt on shared expected-result kernels, untracked profile expansion, malformed data
accepted, tie/edge association changes, source drift, vacuous controls or physical
execution. Accepted catalogue entries remain experimental, not a default switch.
