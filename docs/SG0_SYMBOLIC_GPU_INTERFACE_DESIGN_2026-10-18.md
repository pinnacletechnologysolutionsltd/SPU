# SG-0 design: certified parameters to a T1d procedural patch

Status: interface ratified under the [frozen implementation contract](../spu_strategy/contract_sg0_certified_geometry_2026-10-18.md), 2026-10-18. Bounded software implementation and one 1800-second
campaign are authorized; qualification remains pending. See the
[bridge implementation](../research/sg0/README.md) for commands and evidence boundaries.
It precedes SSM-4 implementation and does not depend on SIM-G2A or Router-F1 closure.

## One visible result, within current limits

Use SSM-3's frozen unique cycle A+B=0, B+C=0, C+A=1. Independently replay its
proof, obtaining theta=(A,B,C)=(1/2,-1/2,1/2). Treat these as three latent geometric
parameters, not twelve independent vertex unknowns. Generate four exact vertices:

```
v0 = (A-1,B-1,C)     v1 = (A+1,B-1,C)
v2 = (A+1,B+1,C)     v3 = (A-1,B+1,C)
faces = ((0,1,2),(0,2,3))
colors = ((15,2,1),(1,8,15))
```

This affine recipe defines one planar patch. Render two frozen variants: identity
and the existing G3 rational rotation R=((3/5,-4/5,0),(4/5,3/5,0),(0,0,1)).
It is a procedural two-triangle demonstration, not a general mesh engine.

The proof certifies parameter equations relative to admitted inputs. SG-0 must
separately check the recipe, transformation and conversion. Do not call all
geometry properties proof-certified merely because a parameter proof exists.
Freeze the recipe and exact expected vertices; independently check shared edges,
planarity/nondegeneracy for this case and transformation/inverse identities.

## Exact handoff and finite-width boundary

Stages are explicit:

1. Verify the original SSM-3 artifact, inputs, certificate and active-system replay.
2. Require a unique parameter family. Empty, unresolved or exhausted results do
   not produce a scene; no arbitrary representative or default zero is permitted.
3. Evaluate the frozen affine recipe and exact rational transform in Python.
4. Inject Cartesian (x,y,z) into zero-sum Quadray coordinates:
   q=(x+y+z,x-y-z,-x+y-z,-x-y+z)/4. Check sum(q)=0 and the existing Cartesian
   bridge returns exactly (x,y,z). These are redundant spatial coordinates,
   not independent hidden Q4 state.
5. Reuse `software.spu_gpu_eval.quadray.project_to_t1d`, with its existing view
   matrix, scale=80 and depth_scale=1000. Record exact pre-rounded screen/depth
   coordinates and ties-to-even integer results.
6. Reject out-of-range values and zero-area quantized triangles. No clipping,
   wraparound, saturation or silent topology repair is introduced.
7. Emit strict `spu_gpu_scene_v1`, profile `t1d-two-triangle-v1`, and pass it through
   the existing scene parser/packet compiler and ideal/device preview paths.

Current scene limits are exactly two triangles, 640x480 active coordinates,
unsigned 16-bit vertex depth and RGB444 flat colors. The packet, quantization
receipt and frame are different artifacts. The T1d finite-width device model
uses approximate depth arithmetic and may disagree with the ideal reference;
measure and explain those differences instead of claiming proof preservation
through rasterization or making all pixels agree by assumption.

Preparation-only projected integer vertices, computed with the existing projector:

| Variant | v0 | v1 | v2 | v3 |
|---|---|---|---|---|
| Identity | (226,306,31935) | (244,164,31046) | (386,146,31935) | (368,288,32824) |
| Rational rotation | (253,205,31401) | (377,105,31579) | (448,208,32824) | (324,308,32646) |

Bounds and nonzero projected areas were checked during design preparation. These
are candidate fixtures, not rendered output, independent oracle qualification
or an SG-0 acceptance result. Freeze them under the implementation contract.

## Workbench integration point

The arbitrary-file evaluator already consumes the scene schema via
`software.spu_gpu_eval.cli`. The browser workbench instead uses a hash-checked
allowlist in `fixtures/gpu_workbench_w1_scene_catalog.json`; generating arbitrary
scene JSON does not automatically make it a selectable workbench scene.

The future SG-0 contract must cover both steps:

- Generate the two scenes and proof/conversion bundles in a fresh output directory,
  then exercise existing preview, device-preview and pixel inspection APIs.
- Register only reviewed, hash-pinned frozen generated scenes in the existing
  catalogue through its declared fixture workflow. Preserve all existing entries;
  no permissive arbitrary-path import or viewer/core rewrite is needed.

Output-scene generator ownership, fixture locations and catalogue update paths
must be frozen before implementation. No checked-in scene/catalogue is modified
by this design. Viewer presentation remains a software observation, not FPGA output.

## Proposed bundle and refusal behavior

Retain source/proof/recipe/transform identities, original inputs, verified parameter
family, exact Cartesian/Quadray vertices, rational screen/depth values, rounding
errors, quantized vertices, scene/packet hashes and ideal/device diagnostics.
Mark `physical_observation=false`. Independent replay must bind every stage to
its predecessor digest so a stale proof or edited mesh cannot inherit certification.

Require errors for altered proof/certificate, changed parameter ordering, recipe
or transform mismatch, wrong domain, unresolved/empty family, resource overflow,
out-of-frame vertices, depth overflow, quantization collapse and existing output
refusal. A well-formed image is not evidence of any preceding proof property.

## Implementation and qualification gates

Prepare a separately ratified bounded SG-0 contract before coding. Preserve
SSM-0–3 and their manifests. Use Python and existing GPU evaluator/workbench APIs;
no GPU RTL, ISA, C++ simulator or FPGA changes. Keep three latent variables,
four derived vertices, two faces and existing rational coefficient guards.

Freeze the input/proof/recipe/projection/scene schemas and finite-width rules first.
Then run SSM proof checks, focused SG-0 tests and the existing S1/S2/S3 evaluator
tests, documented preview/device/edit/inspect commands and workbench regression
controls for any added catalogue entries. Inspect source and artifact reproducibility.
Select the necessary union of repository gates under AGENTS.md and freeze its
single-attempt timeout before launch; this design grants no campaign budget.

Interface freeze means the handoff schemas, recipe ownership, materialization
policy, conversion failure rules and acceptance fixtures are owner-reviewed and
versioned. It does not mean all rendering or hardware claims have passed.
That concrete freeze enables [SSM-4 implementation planning](SSM4_CERTIFIED_GEOMETRIC_STATE_DESIGN_2026-10-18.md);
SSM-4 still needs its own implementation authorization and independent qualification.


## Frozen implementation preparation

The [implementation contract](../spu_strategy/contract_sg0_certified_geometry_2026-10-18.md)
and [versioned input pack](../fixtures/sg0_v1/README.md) now pin the proof, exact
intermediates, two scene/packet hashes, diagnostic pixels, catalogue publication
and focused 1800-second single-attempt budget. This supersedes the earlier open
choices in this design. The owner has ratified the interface and authorized its
bounded implementation/campaign; rendering qualification remains pending.
SSM-4 implementation requires its own authorization.
