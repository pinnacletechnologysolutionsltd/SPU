# GCR-1 ratification amendment: adapter, observables and staged execution

**Date:** 2026-10-12

**Status:** PROPOSED FOR REVIEW. No code implementation, numerical experiment,
qualification launch or physical operation is authorized.

Read the source boundary and parent contract:

```bash
sed -n '1,130p' software/spu_gpu_eval/device_model.py
sed -n '1,240p' spu_strategy/contract_gpu_reduction_catalogue_gcr1_2026-10-12.md
```

## 1. Private experimental adapter

Use two explicit modes per triangle, ORIGINAL and CONSTANT_BYPASS. Do not edit
the production PreparedDepth, PreparedScene, packet encoder or device evaluator.

| Mode | Evaluator input | Diagnostic metadata |
|---|---|---|
| ORIGINAL | Existing immutable PreparedDepth from frozen prepare_depth | Its actual denominator, mantissa, normalization_shift, reciprocal_y and rom_index |
| CONSTANT_BYPASS | Private immutable four-field record: a_z=0,b_z=0,c_z=z,frac_bits=0 | reciprocal_metadata=null, reason=NOT_COMPUTED_CONSTANT_BYPASS |

An immutable experimental scene view exposes the existing decoded scene and an
ordered pair of depth records. Its required attributes are exactly those read
by the frozen settled evaluator; use its same pixel_decision and _depth_value
paths for original and reduced preparations. This is an explicitly private
structural adapter, not a supported public PreparedScene API or new wire format.
Mode/provenance/metadata remain separate from the arithmetic input record.

Source review establishes that _depth_value reads only a_z,b_z,c_z,frac_bits;
pixel_decision reads the decoded triangles and those depth fields. Reciprocal
metadata is not used in this path. Confirm this against frozen sources and an
adapter compatibility test before full comparison. If future source identities
introduce another required field, halt preparation and review the dependency.
Do not populate fake reciprocal zeros or label synthetic records as RTL output.

Both modes must undergo the unchanged signed56 affine accumulation, arithmetic
right shift and signed56 final conversion. No direct return-z evaluation shortcut,
alternate coverage rule or candidate-specific depth evaluator is permitted.
Validate the three associated depths are equal, uint16 and non-Boolean integers;
validate signed56 coefficients and the uint7 shift range before evaluation.

C1 retains ORIGINAL mode with actual preparation metadata for its transformed
edge coefficients. C3 reuses an actual immutable ORIGINAL record and must match
all nine PreparedDepth fields exactly. Mixed eligible/ineligible triangles retain
their own modes and slots without changing original RGB/ownership.

## 2. Mandatory settled-pixel observations

At every checked coordinate require: coverage; ordered covered_by; one identified
shifted finite-width depth value for every covered triangle; selected triangle
(including None for background); and final RGB. Validate field presence/types,
triangle identities, ordering and consistency before comparing values.

An absent required observation cannot yield ACCEPTED: classify the application
UNSUPPORTED with MISSING_REQUIRED_OBSERVABLE, identifying coordinate and field.
Stop treating that application as acceptance-capable; retain evaluated counts and
missing-field evidence. An empty depth list for background is valid, not missing.
Do not compare only RGB or silently omit a covered triangle's depth.

Raw coefficients, raw accumulators and reciprocal metadata remain diagnostics.
Unavailable CONSTANT_BYPASS reciprocal metadata does not make a required depth
observation unavailable. C1/C2 diagnostic differences are recorded, not required
to match. C3 must also preserve the entire immutable original preparation tuple.
Lifecycle behavior remains UNSUPPORTED: busy/ready, reset, scene activation,
latency, service ownership and retirement are not modeled or qualified here.

## 3. C3 validation and cache lifetime

Validate complete scene/triangle structure, integer types, every field range,
nondegeneracy and edge/depth association before cache-key construction or lookup.
Use a fresh empty cache per case; no cross-case warm state or result carryover.
Key: ordered nine edge fields, ordered three associated z fields, profile identity,
reciprocal ROM SHA256 and preparation source/dependency identity.

Cache values contain immutable preparation data only. Exclude RGB, triangle slot,
ownership, instruction state, completion flags and mutable diagnostic structures.
Keep RGB/slot in the uncached scene. Count validation and key/lookup cost; a hit
never bypasses admission checks. Require a malformed-input test with an already
populated cache, and an omitted-z-key negative control on variant5's two triangles.

## 4. Proposed budgets — ceilings, not authorization

| Stage | Attempts | Per-attempt/cumulative stage ceiling | Required prior evidence |
|---|---:|---:|---|
| A: independent oracle, adapter and negative controls | 1 | 900 seconds | Reviewed immutable execution packet |
| B: nine-scene catalogue, full-frame comparisons | 1 | 3,600 seconds | A has unique COMPLETE, exit0 and durable stage PASS |
| C: focused S1/S2/S3 regressions | 1 | 1,800 seconds | B has unique COMPLETE, exit0 and durable integrity PASS |
| Total | 3 | 6,300 seconds | One slot per named stage; no transfer or retry |

Launch consumes a stage slot regardless of outcome. Failed, timed-out or unavailable
prior evidence blocks successors. Exactly one COMPLETE/FAILED/TIMEOUT marker is
required to interpret a stage; COMPLETE means exit0, not automatically qualification.
TIMEOUT is infrastructure evidence, not a reduction rejection. No timeout extension,
automatic retry, substitute method or borrowing unused time between stages.

Stage B PASS means checker integrity, complete applicable comparisons, immutable
inputs and valid outcome accounting. Device-inequivalent but mathematically
equivalent candidates are legitimate REJECTED findings. An undetected poison,
source drift, mislabeled identity or incomplete claimed acceptance fails the stage.
Missing observations never count as a partial PASS. Record each stage verdict and
each candidate verdict separately.

## 5. Execution packet required before authorization

Freeze source/model/transitive import identities; ROM and fixture hashes; HEAD/dirty
state; Python, Icarus/vvp versions and executable hashes; contract and command
identities. Generate, validate and hash all nine deterministic scene descriptions
before evaluating any candidate. Retain candidate-independent corpus construction.
Do not invoke reductions or conduct a numerical trial during review-only preparation.

Store an immutable preparation manifest and exclusive stage budget ledger in a
new child of build/gpu_reduction_catalogue/. Recheck frozen hashes immediately
before each launch and at worker entry/exit. Refuse changed files, overwritten
outputs, exhausted slots or ambiguous/failed predecessors. Freeze exact scripts
and commands after implementation review; the planned commands below do not
authorize creation or execution of their currently absent targets.

```bash
tools/run_detached_job.sh --output build/gpu_reduction_catalogue/gcr1_01/stage_a --timeout 900 --notify-desktop -- python3 -B build/gpu_reduction_catalogue/gcr1_01/preparation/run_stage.py --stage A
tools/run_detached_job.sh --output build/gpu_reduction_catalogue/gcr1_01/stage_b --timeout 3600 --notify-desktop -- python3 -B build/gpu_reduction_catalogue/gcr1_01/preparation/run_stage.py --stage B
tools/run_detached_job.sh --output build/gpu_reduction_catalogue/gcr1_01/stage_c --timeout 1800 --notify-desktop -- python3 -B build/gpu_reduction_catalogue/gcr1_01/preparation/run_stage.py --stage C
```

These are worker invocations only. A reviewed launch guard must enforce frozen
owner authorization, stage reservation and predecessor checks before calling the
runner; direct invocation cannot bypass those requirements. After LAUNCHED record
unit/evidence and end the turn. A later invocation reviews the durable result
before launching a successor. Notification is neither PASS evidence nor launch
authorization. No deterministic waiting or automatic campaign chaining by agents.

Stage C runs these unchanged focused scripts in order; no compiler/user-path
changes are proposed, so no new preview/edit/inspect command is introduced:

```bash
python3 -B software/tests/test_gpu_scene_compiler_s1.py
python3 -B software/tests/test_gpu_device_model_s2.py
python3 -B software/tests/test_gpu_pixel_inspect_s3.py
```

Production-kernel, shared-runner or RTL scope expansion requires another reviewed
contract and the full applicable AGENTS.md gates; this budget does not cover them.

## 6. Counts, counterexamples and falsification

One full active frame is307,200 pixels; nine original frames total2,764,800 pixels.
At most27 candidate/scene applications produce8,294,400 pixel-pair comparisons,
and at most16,588,800 per-triangle depth pairs. Eligibility changes actual totals.
Record per-application planned/evaluated/missing/mismatching counts and covered
triangle depth counts; unsupported applications contribute no invented comparisons.
Sweep every eligible application in y-major,x-minor order, retaining its first
counterexample and total mismatches. ACCEPTED requires all307,200 observations.

Retain original/candidate coefficients, modes, hashes, metadata availability,
independent exact decisions and both finite decisions with every counterexample.
Prevent output-size explosion: aggregate counts and retain one first mismatch
per application plus the fixed negative-control cases, not millions of rows.

Stage A poisons edge sign/factor, depth association, one prepared coefficient bit,
tie ownership and C3 key identity; each must provoke nonacceptance in the intended
independent checker. Also delete one required field to verify UNSUPPORTED rather
than ACCEPTED. Use inputs where the injection changes a checked observation;
invisible poisons or pure representation changes are not valid negative controls.
Record invoked checker, input/output hashes and detected reason. Lack of detection
is a qualification failure, irrespective of a later catalogue's visual agreement.

No hardware result, universal compiler proof, GPU setup-cycle reduction, energy
or device equivalence is established by approving this proposal. Artix-7, AOR,
Padé and existing closed tranches remain independent.
