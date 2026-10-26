# SG-0: certified affine patch to the existing T1d workbench

Date: 2026-10-18
Status: RATIFIED — bounded implementation and one 1800-second software campaign authorized by owner; qualification pending
Roles: current agent: implementer and integration auditor under the ratified contract.
Scope: one Python integration experiment, two frozen scenes, no SSM-4 implementation.

## 1. Command-first scope and immutable inputs

Preparation commands executed now:

```bash
sha256sum -c fixtures/sg0_v1/SHA256SUMS
python3 -m research.ssm3.verify_artifact fixtures/sg0_v1/unique_cycle.proof.json
python3 fixtures/sg0_v1/test_catalogue_serialization.py
```

Serialization amendment verification (2026-10-18): two focused tests pass,
including three input field orders. The complete catalogue matches the unchanged
expected SHA-256 `dbea34a85dbe6c672ec23718d596f162af022e634bc6028028d2a4fedbe736ad`.
The original base serialization, four pinned data files and copied proof replay
pass. No catalogue publication, bridge implementation or campaign was performed.

Control inputs are in `fixtures/sg0_v1/inputs.json`; all data-file digests are
pinned by `SHA256SUMS`. Frozen inputs.json SHA-256:
`308e68d5bce183883caa86b093d9a4fcbb7dfd830c5098dd816f0f8b312b82ed`.
The base catalogue SHA-256 is
`0ff4d2eaef0898b95a6109d0a658f6f4a365c37f38506492a5e5607197d3ec23`;
expected generated catalogue SHA-256 is
`dbea34a85dbe6c672ec23718d596f162af022e634bc6028028d2a4fedbe736ad`. Copied original proof SHA-256:
`bea32a0564eebfa9f5e9693aedc656ddbc365d943d714aa3eea4f2363731f418`.
It has schema SSM3_PROOF_RESEARCH_V1 and certifies the frozen canonical inputs
A+B=0, A+C=1, B+C=0. Require exact input identity, not just a coincidentally equal
final answer. Parameter order is exactly [A,B,C], domain Q3, unique theta=(1/2,-1/2,1/2).

Future implementation may create/modify only:

- `research/sg0/`: input/proof admission, affine materialization, conversion receipts,
  bundle generation/verification, fixture publisher, focused tests, CLI and runner.
- Generated `examples/gpu/sg0/identity.json` and `rational_rotation.json`.
- `fixtures/gpu_workbench_w1_scene_catalog.json`: append the two frozen entries only.
- `software/tests/test_gpu_workbench_w1.py` and `test_gpu_workbench_w1c.py`:
  explicitly retain the original 11 entries and extend expected count to 13;
  add checks for the two generated scenes without weakening existing controls.
- User documentation for SG-0, navigation and this contract's execution record.

Keep SSM-0–3, their historical manifests/baselines, evaluator/renderer/viewer
implementations, C++ simulator, GPU RTL/ISA and hardware flows unchanged.
The frozen GPU core-file hashes in inputs must still match before implementation
and at qualification. If concurrent work changes them or the base catalogue,
halt for a reviewed rebase rather than overwriting its changes.

## 2. Exact scene recipes and transformations

Use three latent parameters, four vertices and two faces. Every vertex matrix
M_i is I3 and offsets are (-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0), respectively.
Thus v_i=M_i*theta+b_i. Faces are (0,1,2),(0,2,3), colors (15,2,1),(1,8,15).

The two frozen variants share this recipe:

- `identity`: I3.
- `rational_rotation`: ((3/5,-4/5,0),(4/5,3/5,0),(0,0,1)), the existing G3 R.

Apply the selected transform after the affine recipe. Verify exact inverse and
orthogonality identities for these matrices; no angle evaluation is used.
Check exact Cartesian expected vertices, planarity, nonzero face area and common
edge identity. These are separate checked properties; the parameter proof alone
does not certify topology, recipe correctness or every rendered property.

## 3. Cartesian/Quadray/projection interface

Map (x,y,z) to q=(x+y+z,x-y-z,-x+y-z,-x-y+z)/4. Verify sum(q)=0 and exact
Cartesian bridge recovery. This is a redundant spatial representation, not an
independent four-dimensional hidden state. Never pass it through a different
algebraic domain implicitly.

Reuse the existing `project_to_t1d` implementation and pinned view matrix:

```
((1/9,8/9,4/9),(8/9,1/9,-4/9),(-4/9,4/9,-7/9))
sx = 639/2 + 80*u
sy = 479/2 - 80*v
sz = 32768 + 1000*depth
```

Freeze nearest-integer ties-to-even for each coordinate. Admit only resulting
integers x in 0..639, y in 0..479, z in 0..65535, matching the existing projector.
Raw rational values are recorded; admissibility is tested after rounding, not
by undocumented raw-coordinate clipping. No saturation/wraparound or topology
repair. Require absolute rounding error <=1/2 per component. Reject zero signed
screen area after rounding through the unchanged strict scene parser.

Expected screen/depth vertices:

| Variant | v0 | v1 | v2 | v3 |
|---|---|---|---|---|
| identity | (226,306,31935) | (244,164,31046) | (386,146,31935) | (368,288,32824) |
| rational_rotation | (253,205,31401) | (377,105,31579) | (448,208,32824) | (324,308,32646) |

Exact intermediate rationals, packet bytes/hashes and selected ideal pixel
expectations are frozen in inputs.json. Future tests must independently recompute
recipe/bridge/rounding identities, not simply compare a value with itself.

## 4. Output bundle, schemas and reproducibility

CLI form below is frozen for future implementation, not runnable yet:

```bash
python3 -m research.sg0 generate --out build/gpu_evaluation/sg0/qualification_20261018_01
python3 -m research.sg0 verify build/gpu_evaluation/sg0/qualification_20261018_01
```

`generate` always emits both variants, admits the pinned proof/inputs only and
refuses an existing output. Require a new child of build/gpu_evaluation. Validate
proof, recipe, numeric budgets and both scenes before publishing a bundle.
Use owned temporary staging and a final rename; failed generation must not
publish a success manifest or mutate pre-existing data. No arbitrary file imports,
model fitting, network service or hardware access.

Root bundle: copied original proof, frozen inputs, source/proof/input identities
and canonical `sg0_bundle_v1` manifest. Each variant contains:

- `geometry.json`: verified theta, exact Cartesian/Quadray vertices, recipe and
  transform identities, checked geometric properties (schema sg0_geometry_v1).
- `conversion.json`: exact screen/depth rationals, ties-to-even integers, errors,
  range/area checks and profile identity (sg0_conversion_v1).
- `scene.json`: strict spu_gpu_scene_v1/t1d-two-triangle-v1, exactly two triangles.
- `scene_packet.bin`: exact existing 64-byte T1d wire encoding.
- `ideal/` and `device/`: unmodified existing preview output sets/manifests.
- `inspection.json`: named frozen diagnostic pixels and separate ideal/device
  coverage, depth, winner and RGB equality fields (sg0_inspection_v1).

Semantic SG-0 JSON uses sorted keys, compact separators, one trailing newline,
and reduced decimal-string numerator/positive-denominator pairs for rationals.
Use integer fields only where the scene/packet schemas require them. Record
logical relative paths, not temporary staging addresses, in semantic receipts.
A receipt binds its predecessor artifact digests; final verify reconstructs from
the copied original inputs/proof and checks every scene/packet stage, not just
existing hashes. Editing a mesh or swapping a proof cannot retain certification.

Compare two fresh subprocess runs with fixed sources/inputs and different hash
seeds: exact semantic JSON, scene/packet and image bytes must agree. Record
runtime/environment/source metadata separately from semantic equivalence.
Mark physical_observation=false and distinguish ideal-reference images from
finite-width software-device images. Neither is an FPGA output.

## 5. Workbench registration: generated and hash-pinned

Names/paths/group are frozen in inputs.json:
`sg0_identity` -> examples/gpu/sg0/identity.json;
`sg0_rational_rotation` -> examples/gpu/sg0/rational_rotation.json; group `sg0`.
Append in that order to the exact 11-entry base catalogue preserved in
`catalogue_before.json`. Serialize each new catalogue entry with insertion-ordered
keys `id`, `path`, `sha256`, `group`, independently of its input dictionary order.
Preserve the existing 11 entries' field order, entry order and values; do not
rebuild or reorder those entries. Emit JSON with `indent=2`, separators
`(',', ': ')`, `sort_keys=False` and exactly one trailing newline. The complete
13-entry catalogue must match the frozen expected SHA-256 in inputs.json; halt
on disagreement rather than updating that expectation.
Run the preparation regression before ratification:

```bash
python3 fixtures/sg0_v1/test_catalogue_serialization.py
```

It must construct the two appended entries from different initial key orders,
produce byte-identical catalogues, verify the unchanged base serialization and
match the frozen complete-catalogue hash. This is a contract-vector check, not
the SG-0 publisher implementation.
Do not loosen catalogue validation or add arbitrary-path loading.

Future publication command:

```bash
python3 -m research.sg0 publish-fixtures
```

The generator owns both scenes and catalogue pins. Verify the proof/inputs,
core-file hashes, exact base catalogue hash and new-path absence before any
publication. Precompute/validate all bytes, stage the new examples directory,
and atomically publish the catalogue last as the commit point. On any pre-commit
failure, remove only newly created owned staging/assets; retain the original
catalogue and pre-existing paths. Do not hand-edit generated scenes to pass.
If the exact expected post-publication catalogue and both scene files already
exist, this command is an idempotent verification with no writes; any mixed or
unexpected state is a rejection, never an automatic overwrite/rebase.

Extend W1/W1-C tests intentionally: require the original 11 entries unchanged,
the two exact new pins and 13 total. Exercise both new IDs through existing render
and inspect routes, including HTTP frame/pixel paths with orderly server shutdown.
No evaluator/server/viewer arithmetic or network-interface change is authorized.

## 6. Negative controls and distinct outcomes

Require rejection of altered/unpinned proof, invalid certificate, changed original
equations or parameter ordering, wrong domain, recipe/transform pin mismatch,
existing output and edited receipt/scene/packet. A different valid proof with the
same numerical answer does not satisfy this frozen-input contract.

Unit-test internal admission/materialization/conversion helpers with empty,
family and BUDGET_EXHAUSTED results, wrong dimensions, coefficient overflow,
out-of-range rounded vertices/depth, and quantization-collapse controls. Public
CLI still admits only frozen inputs. Do not broaden the production contract to
arbitrary scenes to exercise helper negative tests.

Resource errors, unsupported inputs and contradictory original equations are not
interchangeable results. No renderable success bundle may be emitted for any
unresolved, empty or unfinished parameter state. No arbitrary witness selection.

Require independent packet decode/field comparison and exact diagnostic pixel
expectations. Compare full ideal/device RGB and coverage/depth/winner outcomes,
reporting discrepancies rather than requiring universal equality. Exact symbolic
constraints need not survive quantization or approximate depth arithmetic.

## 7. Budget and verification gates

Freeze: three latent rational parameters, four vertices, two variants/faces per
scene, 4096-bit completed rational coefficients, and inherited proof limits.
No new register width, arithmetic domain, mesh generality or hardware claim.

After implementation ratification, run fast SG-0 proof/recipe/publisher/refusal
checks before expensive rendering, preserving old source manifests. Publish
fixtures only through the generator, then capture final source hashes/archive
including the 13-entry catalogue, scene fixtures, changed W1 tests, SG-0 code,
inputs and proof. Freeze all executable source changes before the campaign.

Proposed command sequence for the future check script:

```bash
python3 -m unittest discover -s research/sg0 -p 'test_*.py' -v
python3 -m unittest discover -s research/ssm3 -p 'test_*.py' -v
python3 software/tests/test_gpu_scene_compiler_s1.py
python3 software/tests/test_gpu_device_model_s2.py
python3 software/tests/test_gpu_pixel_inspect_s3.py
python3 software/tests/test_gpu_workbench_w1.py
python3 software/tests/test_gpu_workbench_w1c.py
SKIP_TESTS=1 bash tools/verify_repo.sh
```

Also execute the frozen generate/verify command, two-run comparison, workbench
list/render/inspect for both IDs and preview/device-preview/inspect on both
emitted scenes. Exercise the documented edit path on an owned working scene copy;
never edit the published generated fixtures. Record exact commands and results.
The capture/runner must use fresh paths under this campaign, never overwrite
historical SSM/GPU outputs or call their fixed-output check scripts blindly.

Scope rationale: this is the offline T1d user path plus an unchanged qualified
proof consumer and fixture registration. Apply AGENTS.md section 4.1 focused
S1/S2/S3 gates and workbench tests, plus hygiene/citation checks explicitly using
SKIP_TESTS=1. Do not claim a new full 244-test repository qualification, run
unrelated ROTC/math campaigns or synthesize FPGA hardware. If implementation
needs RTL, arithmetic-kernel or shared-runner changes, halt for a scope amendment.

Freeze exactly one detached attempt, external timeout 1800 seconds, no retry or
extension. This budget covers the complete focused software qualification,
full-frame comparisons, workbench endpoint checks and evidence capture. No separate expensive
rendering campaign is authorized. Check prerequisite terminal evidence, source
pins and shared-regression conditions before launch; run entry/exit hash checks.

```bash
tools/run_detached_job.sh \
  --output build/sg0/certified_geometry_20261018_01 \
  --timeout 1800 --notify-desktop \
  -- bash research/sg0/check_repo.sh
```

Record unit/evidence and end turn at LAUNCHED. Interpret exactly one terminal
marker later. Refuse existing output; exhaustion/failure does not authorize a
substitute method, longer budget or another attempt.

## 8. Preparation disposition and gate ownership

Frozen here: exact proof/inputs, two recipes/transforms, projection/rounding,
output schemas and paths, rejection rules, catalogue entries/ownership and the
single-attempt budget. Initial preparation checked inputs with existing
proof/projector/scene/packet/pixel APIs before implementation.

Owner ratified the interface and authorized bounded implementation plus the
single 1800-second campaign on 2026-10-18. The earlier SG-0 design's interface is
now frozen by this contract. SSM-4 stays design-only; ratifying this interface permits a separate
SSM-4 authorization decision, not automatic implementation or promotion to C++
or FPGA. SOM–SSM remains follow-on. No new archive storage or pruning authority.

Halt on pin drift, lost original catalogue entries, proof/receipt inconsistency,
raw-versus-quantized conflation, mutation of predecessors, failed controls or
scope expansion. Report the minimal correction; do not silently change targets.

## 9. Implementation preparation record — 2026-10-18

The bounded bridge is implemented under `research/sg0/`; 12 fast focused tests
pass. Rendering is mocked only in the fast bundle trust-boundary tests; real
image generation/reconstruction and full-frame diagnostics remain campaign gates.
The generator published both scenes and the complete catalogue with the unchanged
frozen hashes. The focused W1 catalogue admission test and two preparation
serialization tests pass. All four frozen input hashes and all 16 GPU core pins
match. The 72 predecessor research-source pins in SSM-3's qualification manifest
remain unchanged, and its terminal record is COMPLETE/exit 0.

The implementation retains the original W1/W1-C controls and adds both SG-0
IDs to render/inspect and HTTP frame/pixel checks. The detached script freezes
source identity at entry/exit, saves the prelaunch source archive, runs the
specified focused gates and user paths, and stops on first failure. Qualification
is pending; no full 244-test rerun or hardware qualification is claimed.

Prelaunch shared-job inspection found Router-F1 running an independent routing
experiment; its command does not run a shared repository regression. SG-0's
single attempt retains the frozen 1800-second limit and output directory in §7.
No SSM-4 implementation is included.
