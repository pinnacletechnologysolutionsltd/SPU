# Engineering Contract: SSM-4 certified geometric state

Date: 2026-10-18

Status: RATIFIED FOR BOUNDED IMPLEMENTATION — campaign launch requires separate authorization

Spec author: current agent. Implementer: current agent under owner ratification.
Auditor: deterministic independent replay and detached runner after authorization.

## 1. Verify the preparation and predecessor boundary first

Run from the repository root:

```bash
sha256sum -c research/sg0_baseline_20261018/artifacts.sha256
sha256sum -c spu_strategy/ssm4_preparation_2026-10-18/SHA256SUMS
python3 -m research.ssm3.verify_artifact spu_strategy/ssm4_preparation_2026-10-18/correlated.proof.json
python3 -m research.ssm3.verify_artifact spu_strategy/ssm4_preparation_2026-10-18/mirror.proof.json
python3 -m research.ssm3.verify_artifact spu_strategy/ssm4_preparation_2026-10-18/point.proof.json
python3 -m research.ssm3.verify_artifact spu_strategy/ssm4_preparation_2026-10-18/resolved.proof.json
python3 -m research.ssm3.verify_artifact spu_strategy/ssm4_preparation_2026-10-18/contradiction.proof.json
python3 -m research.ssm3.verify_artifact spu_strategy/ssm4_preparation_2026-10-18/exhausted.proof.json
```

Require SG-0's original unique terminal marker COMPLETE and exit 0 at
`build/sg0/certified_geometry_20261018_01/`. Its 240-second focused campaign
qualified two scenes, 31 byte-identical bundle files and entry/exit source checks.
It did not execute the full repository suite. Preserve its exact 159-file
prelaunch archive, manifests and outputs through the
[local baseline](../research/sg0_baseline_20261018/README.md).

The preparation pack contains six proofs generated/replayed with unchanged
SSM-3 and four rational recipe vectors. These establish candidate mathematical
inputs, not SSM-4 implementation or qualification. Do not replace expected values
to accommodate an implementation discrepancy.

## 2. Objective, scoped files and exclusions

After separate ratification, implement only `research/ssm4/` with single-purpose
modules of at most 150 lines, focused tests, CLI, capture/verifier and runner.
Add its own versioned fixture copies and user documentation. Keep the preparation
pack immutable after ratification. Use existing public Family/linear and SSM-3
proof APIs, plus SG-0's conversion/scene/packet helpers; do not modify predecessors.

Demonstrate that an unresolved parameter family can produce uniquely determined
requested vertices, while the unresolved latent directions remain persistent
state. Demonstrate that a different recipe can expose those directions.

No edits to SG-0, SSM-0–3, existing registered scenes/catalogue, GPU renderer/viewer,
C++ simulator, ISA, RTL, shared runner or arithmetic kernels. No symbolic GPU,
general mesh solver, nonlinear/Gram constraints, surds, SOM, Soul or SSM-5.
No framebuffer rerender is required: exact scene/packet equality to qualified
SG-0 artifacts is the handoff acceptance target, not a new rendering qualification.

## 3. Freeze the mathematical representation and outcomes

Parameter domain: Q3, order [A,B,C]. A nonempty canonical Family stores origin
theta0 and basis vectors as ROWS, as defined by S2-P:

```
theta = theta0 + sum(lambda_j * basis_row_j)
vertex_i(theta) = M_i * theta + b_i
direction_image_ij = M_i * basis_row_j
```

Do not feed row-basis storage into a column-basis product without transposing it.
For a nonempty family, requested vertex i is unique iff every direction image is
exactly zero. Equivalently, when B has those basis vectors as columns, M_i B=0.
Its unique value is M_i theta0+b_i. The origin is not an admissible arbitrary
witness when any direction image is nonzero.

Return an exact affine image Family for each requested vertex, including its
dimension. Do not combine separate vertex images as independent marginals to
claim preservation of correlations; retain the original common parameter family
and recipes as the joint representation.

Classify in this order:

1. `RESOURCE_EXHAUSTED`: unfinished predecessor proof or declared budget exceeded;
   no completed geometric conclusion.
2. `EMPTY`: verified empty parameter family; no vertices, including for zero maps.
3. `UNRESOLVED`: nonempty family, at least one requested image has nonzero dimension;
   retain exact images and latent state, emit no requested concrete geometry/scene.
4. `EXACT`: nonempty family and every requested image is unique; emit only requested
   coordinates while retaining the original family, including unresolved directions.

Invalid proof/domain/shape/handle/schema is `REJECTED`, not EMPTY. T1d conversion
failure is `CONVERSION_REJECTED`, separate from exact geometric resolution.
An empty vertex request is rejected, never vacuous EXACT. All four concrete
vertices are required for a scene; a unique requested subset is not a complete mesh.

## 4. Freeze the examples and falsifiers

Use the preparation pack's exact matrices, offsets, topology, colors and proofs.
The main family is A+B=0, C=1/2, with theta=(t,-t,1/2). Its canonical basis
orientation is determined by Family, not by a manually chosen parameter sign.

`correlation_visible` has each M=((1,1,0),(0,0,0),(0,0,1)) and
b_i=(1/2+dx_i,-1/2+dy_i,0), where offsets (dx,dy) cycle
(-1,-1),(1,-1),(1,1),(-1,1). Every M annihilates the family direction;
the four exact vertices equal SG-0's identity vertices despite unresolved t.

`latent_visible` has M=I3 and b_i=(dx_i,dy_i,0). On the same family every vertex
is unresolved. Observing A=1/2 resolves the parameters and reproduces SG-0's patch.

`latent_hidden` has M=((0,0,0),(0,0,0),(0,0,1)) and the centered offsets above.
Both A+B=0,C=1/2 and A-B=0,C=1/2 produce the same patch, but remain different
latent families. Selecting `correlation_visible` subsequently yields EXACT for
the first and UNRESOLVED for the second. Equal visible geometry must not merge
these states or discard their differing proofs/constraints.

`mixed_request` uses `correlation_visible` for vertex 0 and `latent_visible` for
vertices 1–3. Request {0}: EXACT; request {0,1}: UNRESOLVED; no scene in either case.

Required additional controls:

- The point proof A=B=0,C=1/2 is distinct from the unresolved main family even
  when the correlation-visible images coincide.
- The resolved proof has A=1/2,B=-1/2,C=1/2 and produces SG-0's exact coordinates.
- Contradictory observations A=B=1/2 with A+B=0 produce EMPTY.
- Exhausted proof produces RESOURCE_EXHAUSTED; zero maps cannot turn it into EXACT.
- One altered matrix coefficient that exposes t causes UNRESOLVED, not a sample.
- Wrong recipe/parameter ordering, proof/certificate, family, state lineage,
  transform, scene, packet or receipt is rejected by reconstruction.
- Quantization ties, rounded-range rejection and collapsed triangles retain the
  SG-0 behavior and cannot change an EXACT result into a proof of raster equality.

## 5. Immutable state and bounded operations

Create a separate semantic schema `SSM4_GEOMETRIC_STATE_V1`; do not alter SSM0_V1
or allocate binary registers/opcodes. State retains original equations/observations,
replayable proof bytes/digest, canonical parameter Family, parameter order, recipe
identity, exact spatial transformation history and predecessor state identities.
Use immutable records/content identities; do not build another generic expression
store or unify the existing SSM machines in this tranche.

Expose only these bounded operations:

- Admit a supported proof and one of the four frozen recipes.
- Select another frozen recipe, preserving latent family and lineage.
- Append spatial R or r=R-transpose from the pack, compose exactly and simplify
  adjacent inverse pairs; empty history is identity. These act on vertex space,
  not on parameter equations. Transform M,b as (R M,R b).
- Append an explicit scalar parameter observation, rerun the existing SSM-3
  executor and independently replay the new proof; retain the original inputs and
  added observation lineage. Observations are declared assumptions, not deductions
  or certified sensor truth. No hidden equation transport is implied.
- Query requested vertex image families; materialize unique requested geometry;
  convert a complete exact patch through the unchanged SG-0 finite-width boundary.

Compare composed R/r histories to explicit stepping. Verify inverse/orthogonality
identities and annihilation tests independently; do not trust stored pass flags.
Bound to 3 parameters, 4 vertices, 4 recipes, 16 state records per artifact,
8 history operations per lineage, and 4096 bits per completed rational coefficient.
Inherit at most 6 original rows, 64 proof messages and 64 proof operations per
proof. These do not imply bounds on host parsing/temporary arithmetic or performance.
On rejected/exhausted updates retain the input state and publish no partial success.

## 6. Materialization receipts and SG-0 handoff

Use sorted compact JSON, exactly one newline and reduced decimal-string rational
pairs. Freeze `SSM4_MATERIALIZATION_V1` with state/proof/recipe/history digests,
requested indices, exact origin/basis/images, outcome and per-vertex direction
products. Include original proof/input lineage needed for independent reconstruction.
The verifier rebuilds proofs/families/maps and classifications; a stored annihilator
table or image-family equality is insufficient evidence by itself.

For the main correlation-visible family and identity/R histories, all four exact
vertices, zero-sum Quadray values, conversion values, scene bytes and packets must
equal SG-0's frozen identity/rational_rotation artifacts. Record the matching
qualified predecessor hashes and distinct SSM-4 parameter/proof provenance.
Do not pass unresolved parameters into SG-0's public `generate` admission or
change its unique-proof requirement. Reuse its public conversion and scene/packet
helpers only after SSM-4 independently establishes exact requested coordinates.
Keep exact receipts and finite-width conversion receipts separate. Mark all
artifacts software-only, physical_observation=false.

Future CLI (not implemented or runnable yet):

```bash
PYTHONHASHSEED=17 python3 -m research.ssm4 capture --out build/ssm4/certified_state_20261018_01/cases
PYTHONHASHSEED=17 python3 -m research.ssm4 verify build/ssm4/certified_state_20261018_01/cases
```

Use new output paths, owned staging and final rename. Refuse existing/partial
outputs. Repeat in a fresh process/hash seed; compare semantic artifacts bytewise.
Do not add a workbench entry or render scenes again to satisfy this contract.

## 7. Proposed campaign — requires separate execution authorization

The detached launcher creates the fresh campaign directory before invoking the
script. The script must require that existing runner-owned directory and its
command/unit metadata, refuse terminal markers and pre-existing `cases` or
`cases_repeat`, then create its own new `verification/` evidence directory before
capture. It must not create/reuse a campaign root to bypass the detached launcher.
Each capture independently refuses an existing output. Focused preparation uses
a different path, never either reserved campaign capture path.

Emit separate evidence claims: proof replay; affine-image uniqueness; exact vertex
and spatial-transform reconstruction; SG-0 scene/packet equality (or explicit
NOT_APPLICABLE for nonmatching/partial/unresolved requests); and cross-seed
deterministic artifact comparison. Never replace these with one aggregate PASS.

Capture source hashes/archive before launch, including predecessor sources,
proof/recipe inputs, all tests, gate entry points and qualified SG-0 handoff bytes.
Verify at entry and exit, preserving source identity on a failed run too.
Propose exactly one attempt, 1800-second timeout, cumulative budget 1800 seconds.
Do not launch, retry or extend on the authority of this draft.

The future `research/ssm4/check_repo.sh` must run in this order:

```bash
python3 -m unittest discover -s research/ssm4 -p 'test_*.py' -v
PYTHONHASHSEED=17 python3 -m research.ssm4 capture --out build/ssm4/certified_state_20261018_01/cases
PYTHONHASHSEED=17 python3 -m research.ssm4 verify build/ssm4/certified_state_20261018_01/cases
PYTHONHASHSEED=271 python3 -m research.ssm4 capture --out build/ssm4/certified_state_20261018_01/cases_repeat
PYTHONHASHSEED=271 python3 -m research.ssm4 verify build/ssm4/certified_state_20261018_01/cases_repeat
python3 -m unittest discover -s research/sg0 -p 'test_*.py' -v
python3 -m unittest discover -s research/ssm3 -p 'test_*.py' -v
python3 -m unittest discover -s research/symbolic_projection -p 'test_*.py' -v
python3 software/tests/test_gpu_scene_compiler_s1.py
python3 software/tests/test_gpu_device_model_s2.py
python3 software/tests/test_gpu_pixel_inspect_s3.py
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py
bash tools/verify_repo.sh
```

The capture/verifier must compare the two semantic artifact sets byte-for-byte,
recording a failed comparison before entering regression gates.
No synthesis is proposed: hardware/RTL/build flows are unchanged. A requested
hardware or shared-kernel modification requires a new scope review first.
Record actual suite totals; do not assume the historical 244 count remains current.

Proposed detached launch after prerequisites and owner authorization:

```bash
tools/run_detached_job.sh --output build/ssm4/certified_state_20261018_01 --timeout 1800 --notify-desktop -- bash research/ssm4/check_repo.sh
```

End turn at LAUNCHED. Interpret only exactly one terminal marker later. Stop on
the first failed control, pin drift, predecessor mutation, resource violation,
independent replay discrepancy or scope expansion. Preserve failures; no retry,
new renderer, relaxed expected hash, arbitrary witness or timeout substitution.

## 8. Evidence and disposition

Demonstrated now: SG-0 focused qualification and local preservation; six prepared
SSM-3 proofs replayed; main affine annihilation and frozen vertex expectations
checked using existing exact operations. SSM-4 state/operations/replay, C++ parity,
performance, hardware realization and silicon observation: NOT RUN.

The owner ratified the mathematical interface and bounded implementation with
the two runner/evidence clarifications on 2026-10-18. Campaign authorization is
withheld until focused results, frozen source identities and the exact runner
are available for review. No SOM integration or new symbolic generation is
authorized. Local preservation grants no deletion or independent-storage claim.

## 9. Corrective preparation and runner review — 2026-10-18

The [separate corrective amendment](amendment_ssm4_initial_recipe_2026-10-18.md)
authorized one executable line: add `'minus_exposed': 'latent_hidden'` to the
initial-recipe override map. The before-image diff confirms no other recorded
source/fixture changed. The original failure remains unchanged. Its absent raw
log is disclosed, with a labelled transcript excerpt retained. One fresh focused
pass with fail-fast and a 60-second bound passed all 18 methods (exit 0).
Evidence: `build/ssm4/corrective_preparation_20261018_02/`.

Review the exact future `research/ssm4/check_repo.sh`: it checks frozen sources,
sets exit hash guards, requires runner-created command/unit metadata, refuses
existing captures and creates fresh verification evidence before capture. It
then runs focused tests, both fresh hash-seed captures/verifiers, byte comparison
and the specified predecessor/GPU/trace/math/full-repository gates. It stops on a
failed command and has no retry/extension or launch code.

Focused tests establish proof replay, affine-image uniqueness, vertex/transform
reconstruction and SG-0 scene/packet equality for their named cases. Fresh-process
cross-seed qualification and repository regression remain NOT RUN. The source
manifest/archive must identify the final reviewed code; freeze is not execution
evidence. The reserved campaign root remains absent and zero attempts consumed.

Runner review identified a source-identity hold: `research/ssm4/sources.py` does
not capture seven entry points executed by the frozen runner: both ROTC/IROTC
trace tests, rational robotics/SOM, Lucas MAC, Pade batch inversion, and
`run_all_tests.py`. Evidence is `runner_review.json` in the corrective preparation
directory. No extra executable correction was applied under the one-line
amendment. Source freezing and campaign authorization remain pending closure.
