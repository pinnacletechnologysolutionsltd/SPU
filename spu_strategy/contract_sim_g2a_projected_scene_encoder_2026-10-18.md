# Engineering Contract: SIM-G2A Projected Scene Encoder

**Date:** 2026-10-18

**Contract ID:** `sim_g2a_projected_scene_encoder_2026-10-18`

**Status:** TECHNICAL DESIGN APPROVED — EXECUTION BUDGET AWAITING OWNER AUTHORIZATION

**Spec Author:** Codex

**Halt-and-Flag Implementer:** Owner-assigned C++ implementer after authorization

**Integration Auditor:** Owner-assigned reviewer after implementation

## 1. Objective and scope

Add one native C++ front end to the standalone `spu-sim` package. It accepts an
already projected T1d scene, validates the narrow schema below, and encodes the
existing 64-byte packet. The resulting packet is consumed by the existing
`spu-sim gpu render` command and unchanged `render_t1d` implementation.

This is a scene-ingestion feature. It does not perform Quadray transforms,
projection, pixel quantization, rasterization changes, ISA execution, or FPGA
work.

### Target files after separate implementation authorization

- `../spu-sim/src/t1d_scene.cpp` and `../spu-sim/include/spu_sim/t1d_scene.hpp`
- `../spu-sim/src/main.cpp` for one new CLI command
- `../spu-sim/tests/` for parser and encoder conformance tests
- `../spu-sim/fixtures/sim_g2a/` for the schema fixtures and provenance manifest
- `../spu-sim/CMakeLists.txt` and `../spu-sim/README.md`

Do not edit the 14-instruction machine semantics, `src/t1d.cpp`, the T1d packet
decoder, the reciprocal ROM, Python rendering semantics, ISA-A, RTL, FPGA flows,
or unrelated files. Do not stage, commit, publish, or tag.

## 2. Frozen source and expected results

Implement against standalone SIM-1 commit
`013acd4230442e0e126640604c11176f274962ab`, verified clean in the sibling
checkout and reproduced in SIM-G1. Record the exact implementation source tree,
compiler, CMake version, and fixture hashes when authorized execution begins.

Use the three SIM-G1 projected views as packet and frame regressions. Preserve
their source JSON and licensing metadata; adapt only the schema discriminator
and field layout needed by this contract. Store each adapted JSON fixture and
the corresponding expected 64-byte packet from
`build/gpu_evaluation/sim_g1_repro/run_02/output/<scene>/scene_packet.bin` in
`fixtures/sim_g2a/`. Record source path, provenance, license, and SHA-256 for
both in `fixtures/sim_g2a/manifest.json`. Expected packet and RGB8 hashes are:

| Scene | Packet SHA-256 | RGB8 SHA-256 |
|---|---|---|
| `identity` | `e2ef44e4087e7c8a2d1a67c3ef24abde1e2542d9b8f5a74c11753762dad43942` | `434e6b5525fcfc75ddb8e5888a1e6cda0c4e877c5d08518af90a5aa01ba90691` |
| `rotate_bcd` | `8d829ce865a2053578e5369b437ec9b603023cbf624e6a6d573f112af7ee7b37` | `f8a6afbfeb929e5079b800893acf5fb15623c0e9a09807d61bac1d4d66baaad4` |
| `reflect_bc` | `c0c439c1955a43f86793fa439aa2d1617a4a671a8237850c5acde802f63b772d` | `ad7415db404a5189012b1dfcd30bd096317420d631f4555a7cf3b4459e162c7e` |

Each expected frame is 921,600 RGB8 bytes. These fixtures establish bounded
cross-implementation consistency, not independent mathematical correctness or
FPGA equivalence.

## 3. Input schema: `spu-t1d-projected-scene-v1`

Accept only this root object, with exactly these keys and types:

```json
{
  "format": "spu-t1d-projected-scene-v1",
  "profile": "gpu.scene.t1d.two-triangle-v1",
  "width": 640,
  "height": 480,
  "triangles": [
    {"vertices": [[x0, y0, z0], [x1, y1, z1], [x2, y2, z2]], "rgb": [r, g, b]},
    {"vertices": [[x0, y0, z0], [x1, y1, z1], [x2, y2, z2]], "rgb": [r, g, b]}
  ]
}
```

The six vertex triples and two RGB triples shown above are placeholders for
integer values. The schema contains screen-space coordinates only. It carries
no object identifiers, source geometry, transformations, materials, labels,
additional primitives, or extension fields.

### 3.1 Field constraints

- `format` and `profile` must equal the literals shown above.
- `width` and `height` must be the integers `640` and `480`.
- `triangles` must contain exactly two objects.
- Each triangle object must contain exactly `vertices` and `rgb`.
- `vertices` must contain exactly three triples `[x,y,z]`.
- `x` is an integer in `0..639`; `y` is an integer in `0..479`;
  `z` is an integer in `0..65535`.
- `rgb` contains exactly three integers in `0..15`.
- Each projected triangle must have nonzero signed twice-area, evaluated with
  checked integer intermediates. Reject degenerate triangles.
- Compute edge coefficients with checked signed 64-bit intermediates, then
  independently verify that `a`, `b`, and `c` fit their signed 16-, 16-, and
  32-bit packet fields before serialization.
- Reject any unknown/missing key, wrong JSON type, duplicate key, out-of-range
  value, overflow, malformed input, invalid UTF-8, or trailing non-whitespace
  data. Never wrap, clamp, saturate, or coerce values.

### 3.2 Parser policy

The pinned SIM-1 package has no JSON parser dependency. Implement a small,
schema-specific parser in the new T1d scene module using C++17 standard
library facilities only; do not add a third-party dependency or general JSON
framework in this tranche.

The accepted lexical subset is ASCII JSON with standard JSON whitespace,
objects, arrays, unescaped ASCII strings for the fixed keys and literals, and
nonnegative base-10 integer tokens. Reject string escapes, non-ASCII bytes,
negative numbers, leading-zero multi-digit integers, fractions, exponents,
booleans, and `null`. Reject duplicate keys. Parse integers with checked
conversion such as `std::from_chars`; do not use floating point. Cap the input
file at 4,096 bytes and reject larger files before parsing. The parser is only
for this versioned schema and must not be advertised as a general JSON parser.

Use these stable diagnostic names: `SCENE_TOO_LARGE`, `SCENE_ENCODING`,
`SCENE_SYNTAX`, `SCENE_DUPLICATE_KEY`, `SCENE_SCHEMA`, `SCENE_RANGE`,
`SCENE_DEGENERATE`, `PACKET_FIELD_RANGE`, `OUTPUT_EXISTS`, and `IO_ERROR`.
Diagnostics may append a field name or byte offset; tests must assert the
stable name rather than message prose.

## 4. Packet encoding and CLI contract

Add this command:

```text
spu-sim gpu encode-scene SCENE.json --output PACKET.bin
```

It parses and validates the entire input and constructs the complete packet in
memory before opening the destination. On success it writes exactly 64 bytes
and reports the packet SHA-256. Input or validation failure returns a nonzero
status, a stable named diagnostic, and no packet output. Host I/O failures
must be reported separately from input errors.

Create the destination exclusively (for example, with an equivalent of
`fopen(..., "wbx")`); do not use check-then-open. If the destination already
exists, return `OUTPUT_EXISTS` and leave it byte-for-byte unchanged. Do not
fall back to a truncating open if exclusive creation is unavailable. Check the
write, flush, and close results; report success only after all succeed. If a
write fails after creating the destination, close it and attempt to remove the
partial file created by this invocation. Return `IO_ERROR` regardless of
cleanup success, and include the residual path in the diagnostic if cleanup
fails.

Encode each triangle using the existing Python T1d packet contract:

1. For each directed edge `(p,q)` in vertex order `(v0,v1)`, `(v1,v2)`,
   `(v2,v0)`, compute `a=q.y-p.y`, `b=p.x-q.x`, and
   `c=-(a*p.x+b*p.y)`.
2. Evaluate each edge at its opposite vertex. If all three values are
   negative, negate all three edge triples. Require all three values to be
   strictly positive after orientation; otherwise reject.
3. Encode each edge as signed `a:16`, `b:16`, `c:32`, in edge order; encode
   `rgb` as three unsigned 4-bit channels; encode depth as unsigned 16-bit
   values in order `(v2.z, v0.z, v1.z)`.
4. Each triangle record is 252 bits. Place triangle 0 at payload bit offset 0
   and triangle 1 at offset 252. Prefix the 63-byte little-endian payload with
   `0xA5`. The complete packet is exactly 64 bytes.

Use an explicit bounded bit writer over a zero-initialized 64-byte packet.
Every write must check that its payload bit offset and width lie within the
504-bit payload and that the source value fits the declared field. Serialize
the marker and fields explicitly; do not use C++ bitfields, packed structs,
host-endian object copies, or shifts by the machine word width.

The packet has no reserved bytes or bits: the marker occupies byte 0 and both
records consume all 504 payload bits in bytes 1 through 63. The conformance
tests must assert the marker, record boundary, and field boundaries below;
they must not invent a reserved region or silently ignore packet bits.

| Record bit range | Field |
|---:|---|
| 0–63 | Edge 0: signed `a:16`, `b:16`, `c:32` |
| 64–127 | Edge 1: signed `a:16`, `b:16`, `c:32` |
| 128–191 | Edge 2: signed `a:16`, `b:16`, `c:32` |
| 192–203 | RGB nibbles in `r,g,b` order |
| 204–219 | `v2.z`, unsigned 16-bit |
| 220–235 | `v0.z`, unsigned 16-bit |
| 236–251 | `v1.z`, unsigned 16-bit |

Within each record, the least-significant field bit is serialized first.
Triangle 1 starts at payload bit 252, in the middle of a byte; tests must cover
this cross-byte record boundary.

### 4.1 Coefficient bounds and field-width controls

The coordinate limits imply these per-edge coefficient bounds before packet
encoding:

- `a = q.y - p.y` lies in `[-479, 479]`.
- `b = p.x - q.x` lies in `[-639, 639]`.
- `c = q.x*p.y - p.x*q.y` lies in `[-306081, 306081]`, since each product
  lies in `[0, 639*479]`.

Therefore valid schema inputs cannot approach the signed 16-bit limits for
`a`/`b` or the signed 32-bit limits for `c`. Do not claim that a valid
screen-space triangle exercises those packet-field limits. Add this explicit
boundary-coordinate input as `fixtures/sim_g2a/input_boundaries.json`:

```json
{"format":"spu-t1d-projected-scene-v1","profile":"gpu.scene.t1d.two-triangle-v1","width":640,"height":480,"triangles":[{"vertices":[[0,0,0],[639,0,65535],[0,479,32768]],"rgb":[0,15,8]},{"vertices":[[639,0,65535],[0,479,0],[639,479,479]],"rgb":[15,0,15]}]}
```

This fixture reaches each coordinate and color endpoint and includes
nondegenerate triangles with edge coefficient `c` at both `-306081` and
`306081`. Before implementation begins, encode it with the established Python
reference, independently decode all fields, and freeze the expected 64-byte
packet and SHA-256 in the fixture manifest. Separately unit-test the bounded
bit writer with synthetic signed-field values at each encoded width's minimum
and maximum, plus one value outside each limit; out-of-range values must be
rejected before bits are written. These private writer tests do not expand the
public scene schema. Exercise the output failure cleanup path through a
test-only injected short-write/failure seam; verify it reports `IO_ERROR` and
does not report success or leave a partial packet behind.

### 4.2 Independent packet qualification

Packet correctness is tested before rendering. The encoder unit test calls the
scene-to-packet function directly and compares all 64 bytes with the pinned
Python-produced packet fixture for each of the three frozen scenes. It must not
call `render_t1d` to obtain its packet acceptance result. Also independently
decode the expected fixture packets in test code and assert every field against
the scene values, including both records, signed edge coefficients, RGB nibble
order, depth order, and the cross-byte record boundary. Compare the packet
SHA-256 with the fixed table above as a secondary identity check.

The existing command remains the renderer entry point:

```text
spu-sim gpu render PACKET.bin --output FRAME.rgb8 [--rom TABLE.mem]
```

Do not refactor or change its semantics. The normal workflow is `encode-scene`
followed by the existing `gpu render` command.

## 5. Verification and acceptance

From the root of the standalone `spu-sim` checkout, execute each command under
`timeout 60s`; stop on the first nonzero exit or timeout. The complete command
campaign must remain within the proposed 300-second cumulative command budget.

```bash
cmake -S . -B build/sim-g2a -DCMAKE_BUILD_TYPE=Release
cmake --build build/sim-g2a --parallel 2
ctest --test-dir build/sim-g2a --output-on-failure
build/sim-g2a/spu-sim gpu encode-scene fixtures/sim_g2a/identity.json --output build/sim-g2a/identity.packet
build/sim-g2a/spu-sim gpu render build/sim-g2a/identity.packet --output build/sim-g2a/identity.rgb8 --rom hardware/rtl/arch/gpu_reciprocal_lut_q15.mem
sha256sum build/sim-g2a/identity.packet build/sim-g2a/identity.rgb8
```

Repeat the two `encode-scene` and `gpu render` commands for `rotate_bcd` and
`reflect_bc` using these distinct new output paths. Also replay the existing
SIM-1 fixture with the unchanged renderer.

```bash
build/sim-g2a/spu-sim gpu encode-scene fixtures/sim_g2a/rotate_bcd.json --output build/sim-g2a/rotate_bcd.packet
build/sim-g2a/spu-sim gpu render build/sim-g2a/rotate_bcd.packet --output build/sim-g2a/rotate_bcd.rgb8 --rom hardware/rtl/arch/gpu_reciprocal_lut_q15.mem
build/sim-g2a/spu-sim gpu encode-scene fixtures/sim_g2a/reflect_bc.json --output build/sim-g2a/reflect_bc.packet
build/sim-g2a/spu-sim gpu render build/sim-g2a/reflect_bc.packet --output build/sim-g2a/reflect_bc.rgb8 --rom hardware/rtl/arch/gpu_reciprocal_lut_q15.mem
build/sim-g2a/spu-sim gpu render fixtures/gpu_t1d_scene_wire_64b.bin --output build/sim-g2a/baseline.rgb8 --rom hardware/rtl/arch/gpu_reciprocal_lut_q15.mem
sha256sum build/sim-g2a/{identity,rotate_bcd,reflect_bc}.packet build/sim-g2a/{identity,rotate_bcd,reflect_bc}.rgb8 build/sim-g2a/baseline.rgb8
```

Acceptance requires:

- Existing SIM-1 CTest suite passes unchanged.
- A packet-stage conformance test compares the C++ encoder's complete output
  against each frozen 64-byte packet fixture before any render call.
- Packet tests independently check byte 0, each field boundary, both records,
  and the record boundary at payload bit 252. There are no reserved bytes or
  bits in this packet profile.
- Parser tests cover every field constraint, exact boundaries, duplicate,
  missing and extra keys, wrong triangle count, wrong tuple arity, malformed
  syntax, invalid UTF-8, forbidden numeric forms, degenerate triangles,
  oversize input, and existing-output refusal.
- Each C++ encoded packet matches the corresponding frozen Python packet bytes
  exactly and has the expected SHA-256 above.
- Rendering each generated packet with the unchanged C++ T1d renderer returns
  921,600 bytes matching the frozen historical frame hash above.
- The original SIM-1 fixture still yields its accepted 921,600-byte frame and
  hash `96950fa5610063be28056ab0ff9f198a94bbc38ab9aa48949684592d69de7a10`.
- No ISA, CPU machine-state, packet-decoder, rasterizer, ROM, Python semantic,
  RTL, or FPGA-flow changes are present.

Report parser/encoder correctness against these fixtures separately from
renderer correctness. Matching packet bytes and frames do not establish an
independent mathematical proof.

## 6. Halt conditions and authorization boundary

Halt before implementation if the schema cannot be parsed unambiguously, if
the Python packet encoder and this contract disagree on any field or byte
ordering, if any frozen packet identity is unavailable, or if preserving the
renderer requires changing `render_t1d` semantics. Submit the smallest
specification amendment for review.

This document records approval of the technical design only. It does not
authorize source changes, implementation, builds, tests, dependency downloads,
commits, publication, RTL/ISA changes, FPGA operation, or hardware
qualification. Execution requires the separate owner authorization described
in Section 7.

## 7. Proposed bounded execution budget (awaiting separate authorization)

The technical design is approved for bounded implementation, but execution
has not been authorized. The owner must authorize this budget separately
before source edits or verification begin.

- One implementation pass in the pinned SIM-1 checkout; no automatic retry.
- One verification campaign, with a maximum of 300 seconds cumulative command
  wall time and a maximum of 60 seconds for any individual command.
- The campaign begins by producing and validating the
  `input_boundaries.json` expected packet through the already-established
  Python reference. Then it includes the C++ build, existing CTest suite,
  focused parser and packet-encoder tests, the four packet/frame regressions
  (`identity`, `rotate_bcd`, `reflect_bc`, and `input_boundaries`), and the
  unchanged SIM-1 baseline render. Stop on the first failed prerequisite,
  mismatch, or timeout. Preserve all partial evidence; do not retry or extend
  a timeout without renewed authorization.
- Record the exact command, elapsed time, exit status, compiler/CMake versions,
  source revision and dirty status, fixture hashes, packet hashes, frame hashes,
  and test output in a new evidence directory under `build/`.
- No dependency download, commit, publication, ISA/RTL edit, FPGA operation, or
  unrelated repository gate is included.

After budget authorization, execute only the frozen commands and tests from
the implementation contract. Any need to exceed the attempt count, per-command
limit, or cumulative budget requires renewed owner authorization.
