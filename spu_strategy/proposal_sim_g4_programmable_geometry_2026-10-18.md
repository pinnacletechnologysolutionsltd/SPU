# SIM-G4: bounded programmable affine geometry

Date: 2026-10-18. Status: DESIGN ONLY; implementation and campaigns NOT AUTHORIZED.
Roles: Spec Author drafts; Implementer halts on ambiguity; Auditor checks claims separately.

## 1. Preserve baselines and establish the implementation gate

Run these read-only commands before preparing an implementation contract:

```bash
git -C /home/user/Projects/hardware/spu-sim rev-parse HEAD
git -C /home/user/Projects/hardware/spu-sim status --short
sha256sum research/sim_g3/{__init__.py,handoff.py,__main__.py,test_handoff.py,test_staging.py,README.md}
cat build/sim_g3/qualification_r1_job_20261018_01/closeout.json
cat /home/user/Projects/hardware/spu-sim/include/spu_sim/t1d_scene.hpp
```

Pin the qualified SIM-G2A base plus its exact qualified overlay, executable,
fixtures and ROM; HEAD alone does not identify that dirty baseline. Preserve
SG-0 and both SIM-G3 events. Create no branch, snapshot or build in this design
stage. Freeze fixture bytes, expected outputs, command implementation and final
path inventory in a later reviewed implementation contract before execution.

## 2. Demonstrate one new execution interface

Accept an input-described rational affine transformation sequence and four
Cartesian rational vertices; produce the existing projected two-triangle scene.
Keep topology at two triangles so the existing 64-byte encoder remains usable.
Programmability means changing the input transformation sequence, not changing
an instruction set or executing arbitrary code. No general mesh engine, camera
language, shader, solver, symbolic deduction or animation scheduler is proposed.

Propose a separate native utility, `spu-geometry`, linked to the existing core:

```bash
build/sim-g4/spu-geometry materialize fixtures/sim_g4/rotation.json --output build/sim_g4/attempt_01/rotation.scene.json
build/sim-g4/spu-sim gpu encode-scene build/sim_g4/attempt_01/rotation.scene.json --output build/sim_g4/attempt_01/rotation.packet
build/sim-g4/spu-sim gpu render build/sim_g4/attempt_01/rotation.packet --output build/sim_g4/attempt_01/rotation.rgb8 --rom hardware/rtl/arch/gpu_reciprocal_lut_q15.mem
```

These are proposed post-implementation commands, not currently executable APIs.
The ROM path above assumes the SPU repository as working directory and absolute
simulator executable paths in the eventual runner. Do not change `src/main.cpp`,
`t1d_scene.cpp`, renderer, parser, machine, ISA, RTL or FPGA flows. Proposed sibling
repository edits: new `include/spu_sim/geometry_*.hpp`, `src/geometry_*.cpp`,
`src/geometry_main.cpp`, `tests/test_geometry*.cpp`, `fixtures/sim_g4/`, and additive
CMake target/test registration only. Bound production work to eight new modules,
each at most 150 lines. Halt if that budget cannot express the reviewed scope.

## 3. Freeze exact semantics before implementation

Use versioned JSON with four 3D vertices, two index triples, two existing-profile
colour triples and zero through eight affine steps. A step is a 3-by-3 rational
matrix plus rational translation. Apply steps in listed order to column vectors;
the empty sequence is identity. Reject unknown fields, duplicate keys, invalid
indices and non-integer JSON numeric tokens. Represent rationals as numerator /
positive-denominator integer pairs; canonicalize by gcd with zero as 0/1.
No floating-point path, external expressions, imports or executable payloads.

Proposed input limits: 64 KiB JSON, absolute numerators at most 32767,
denominators 1 through 4096. Use checked signed-64-bit exact rational operations;
reduce fractions and check every intermediate multiplication/addition before
evaluation. Overflow is RESOURCE_EXHAUSTED, never wrapping, rounding or a claim
of geometric inconsistency. No arbitrary-precision native dependency is assumed.

Freeze projection against `software/spu_gpu_eval/quadray.py`: its declared view
matrix, scale 80, depth scale 1000, centres 639/2 and 479/2, depth offset 32768,
and signed ties-to-even rounding. Compare Cartesian direct evaluation against
the existing Cartesian-to-zero-sum-Quadray-to-projection reference route.
Range-check only after declared quantization; reject out-of-range or degenerate
triangles through the unchanged encoder validation. Do not clip or repair them.
All outputs use exclusive creation; parse/resource/geometry failure publishes no
scene. Keep malformed input, resource exhaustion and encoder rejection distinct.

## 4. Acceptance and negative controls

Freeze identity and 3/5,4/5 rotation from SG-0 plus one translated patch and one
two-step noncommuting sequence. Supply independently computed Python Fraction
reference coordinates and projected scenes. Compare exact stepwise versus
composed evaluation where both remain within the declared arithmetic bounds.
Use 32 seeded bounded affine cases for coordinate/projection comparisons; record
resource rejections separately instead of dropping them from a correctness total.

Require SG-0 identity/rotation projected geometry, packets and raw RGB8 to match
their frozen references exactly. Require all four positive fixtures to match
Python-generated projected scenes, packets and frames using the existing encoder
and renderer. Freeze oracle provenance; this is not an independent rasterizer.
Record exact rational coordinates separately from quantized vertices and images.

Negative controls: duplicate/unknown fields, zero/negative denominator, invalid
index, ninth step, excessive input, checked arithmetic overflow, signed half-ties,
range failure, quantized degeneracy and pre-existing output. Include an ordering
control where reversing two transforms changes the expected geometry. Preserve
qualified baseline tests unchanged. No depth, silicon or performance superiority
claim follows from packet/RGB agreement.

## 5. Proposed budgets, evidence and stop conditions

Prepare two independently authorized stages: interface/fixture freeze first,
implementation qualification second. Propose one detached qualification attempt,
600 seconds cumulative, with each component command capped at 60 seconds and no
automatic retries. Review exact build/test/oracle commands and a fresh evidence
directory before authorizing that attempt; do not launch from this proposal.
Record pre/post two-repository identities, compiler/build configuration, commands,
exact coordinates, scenes, packets, RGB hashes, rejection results and baseline
test results. Rendering and compiler reproducibility are separate claims.

Stop on source drift, mismatch, timeout, output collision, unhandled rational
case, module-budget excess or a required baseline edit. Preserve partial evidence
and seek a separate amendment. Do not weaken limits to accommodate a fixture.
SSM-4 remains parked independently; this proposal does not repair its guard,
consume an SSM-4 attempt or modify its frozen execution inputs. INF-1 is deferred.
