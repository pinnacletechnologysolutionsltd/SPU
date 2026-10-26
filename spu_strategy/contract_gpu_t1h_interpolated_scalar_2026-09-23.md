# Engineering Contract: T1h Generic Interpolated Scalar Attribute

**Date:** 2026-09-23<br>
**Contract ID:** `GPU-T1H-INTERPOLATED-SCALAR-2026-09-23`<br>
**Revision:** 2<br>
**Status:** `Q0–Q3 PASS; diagnostic B1 PASS; H1 HOLD — edge artifact audit`<br>
**Owner:** John Curley

## 1. Objective

Answer the question:

> Can the prepared four-primitive raster path interpolate one non-depth
> fragment scalar deterministically through dynamic scene replacement?

T1h adds one unsigned 16-bit scalar sample at each primitive vertex and
interpolates that scalar over covered pixels, independently of depth. It
qualifies attribute setup, per-pixel stepping, winner selection, and
active/candidate activation coherence. It does not add texture memory, UV
coordinates, fragment shading, or a framebuffer. Two-coordinate interpolation
is reserved for T1i; procedural material functions are reserved for T1j.

The original T1h image keeps the selected scalar internal for simulation and
does not visualize it. Physical H1 therefore uses the isolated compile-time
`T1H_SCALAR_DIAG=1` mode: after the existing depth winner selects the scalar,
bits `[14:11]` drive all three RGB channels as grayscale. The Wukong VGA top
exports each channel's most significant bit, so the physical black/white
threshold is scalar bit 14 (16384). This mode does not feed back into
interpolation, depth selection, or scene activation. It is legal only with
`T1H_SCALAR_SCENE=1`; the default is `0`.

The existing T1f/T1g 252-bit primitive record and 1008-bit scene remain
unchanged. T1h uses a separate compile-time prepared-scene profile with a
300-bit record: the existing 252 bits followed by `attr0`, `attr1`, and
`attr2`, each an unsigned 16-bit per-vertex scalar. Four records form a
1200-bit (150-byte) payload and a complete transaction is 151 wire bytes
including the unchanged `A5` start byte. The profile selector is
`T1H_SCALAR_SCENE=0|1`, default `0`. Value `1` is legal only with
`PREPARED_SCENE=1` and `FOUR_PRIMITIVE_SCENE=1`; all other combinations must
fail elaboration. Value `0` preserves the existing T1f/T1g elaboration and
packet interpretation. No legacy packet is reinterpreted.

## 2. Scope and authorized files

Expected implementation and evidence files:

* `hardware/rtl/gpu/spu_scene_unpack.v` or a separate T1h unpacker.
* `hardware/rtl/gpu/spu_scene_profile_unpack.v` and
  `hardware/rtl/gpu/spu_prepared_scalar_attribute4.v`.
* `hardware/rtl/gpu/spu_gpu_top.v` and the prepared-scene attribute path.
* `hardware/boards/artix7/spu_a7_gpu_vga_top.v` and
  `hardware/boards/artix7/build_a7.sh` for compile-time profile selection.
* A T1h-specific attribute setup/dispatch module if source review shows the
  existing depth setup cannot be reused without changing depth semantics.
* `hardware/tests/common/spu_gpu_t1h_attribute_tb.v`.
* `software/tests/test_gpu_t1h_attribute.py` and deterministic T1h fixtures
  generated only after Q0 freezes their semantic values.
* `hardware/tests/common/spu_scene_loader_profiles_tb.v` and
  `run_all_tests.py` for payload boundary regression integration.
* `spu_strategy/contract_gpu_t1h_interpolated_scalar_2026-09-23.md`.

Existing T1f/T1g profiles, fixtures, wire format, depth ordering, and scene
activation behavior are immutable under this contract. Existing top-level
ports may not change. Any new selection is compile-time/profile scoped.
`T1H_SCALAR_DIAG=0|1`, default `0`, is legal only with
`T1H_SCALAR_SCENE=1`. It maps selected scalar bits `[14:11]` to grayscale
after depth winner selection; legacy RGB behavior is unchanged by default.

## 3. Frozen invariants

* `attr0/attr1/attr2` are unsigned 16-bit vertex samples, distinct from
  `z0/z1/z2`; all four primitive lanes carry independent values.
* Attribute interpolation uses the primitive's existing edge geometry and the
  same deterministic fixed-point affine-plane convention as the depth setup
  path. Attribute setup state, including coefficients, fractional shift,
  ready/valid state, and candidate generation, belongs to the same scene
  generation as the geometry and depth state.
* Attribute coefficients and accumulators are signed 56-bit values. The
  unsigned 16-bit vertex samples feed the existing depth-plane setup math as
  its `z0/z1/z2` operands, using the same signed geometry coefficients; this
  setup is a separate attribute calculation and does not alter depth setup.
  The 7-bit `frac_bits` is applied with the existing signed arithmetic right
  shift. Discarded fractional bits are not rounded; negative values follow
  arithmetic-shift semantics. The interpolated result remains signed 56-bit:
  it is not clamped or reduced to 16 bits. Values outside 0..65535 retain
  their signed 56-bit result; fixtures will keep checked covered samples
  within 0..65535. Coverage validity, not numeric range, controls whether a
  fragment attribute is valid.
* At a pixel covered by multiple primitives, the scalar output belongs to the
  primitive selected by the existing depth comparison and tie rule. At an
  uncovered pixel, the scalar output is zero and marked invalid.
* The old active scene remains visible while a T1h candidate is received and
  prepared. Geometry, depth, and attribute state activate together at the
  first `frame_start` after every required result for that candidate generation
  is ready.
* `commit_pending=1` continues to reject incoming UART bytes. T1h makes no
  arbitrary back-to-back delivery claim. Any host pacing used by a physical
  follow-on must be measured against the enlarged payload and complete
  attribute preparation path.
* No floating point, RTL division, framebuffer, new render clock, or
  unrequested FIFO/queue is permitted.

## 4. Q0 — Source review and semantic freeze

Before editing RTL or creating fixtures, execute:

```bash
sed -n '1,220p' hardware/rtl/gpu/spu_scene_loader.v
sed -n '1,180p' hardware/rtl/gpu/spu_scene_unpack.v
sed -n '1,240p' hardware/rtl/gpu/spu_depth_math.v
sed -n '1,220p' hardware/rtl/gpu/spu_depth_dispatch4.v
sed -n '560,700p' hardware/rtl/gpu/spu_gpu_top.v
```

Record the exact loader payload parameterization, generation/readiness
controls, accumulator readout semantics, and whether depth setup can be
instantiated for attribute samples without modifying its depth behavior.
Confirm that the added attribute result can be selected by the same winning
primitive ID as color and depth. Test observability shall use an internal
hierarchical simulation signal; no external FPGA/top-level output port may be
added. Do not alter source, fixtures, or generated artifacts in Q0.

Freeze semantic values for scenes A/B/C using the immutable T1g geometry and
depth fixtures. Each row lists `attr0, attr1, attr2` for primitive IDs 0..3:

| Scene | Primitive 0 | Primitive 1 | Primitive 2 | Primitive 3 |
|---|---|---|---|---|
| A | 1000, 2000, 4000 | 6000, 9000, 12000 | 14000, 16000, 20000 | 24000, 28000, 32000 |
| B | 1500, 3000, 4500 | 6500, 10000, 13500 | 14500, 18000, 21500 | 24500, 29000, 33500 |
| C | 2000, 4000, 6000 | 7000, 11000, 15000 | 15000, 19000, 23000 | 25000, 30000, 35000 |

The values are unsigned 16-bit, distinct at the three vertices of every
primitive, and nonconstant in each scene. Their disjoint lane ranges make
overlap samples distinguish the existing depth winner from losing primitives.
Q2 computes expected scalar results for every active pixel using the frozen
edge coefficients, the software integer reciprocal/setup oracle, signed
56-bit affine coefficients, arithmetic right shift, and the existing depth
winner rule. Expected values are independent of RTL setup and accumulator
outputs. Fixture generation remains deferred to Q1.

Q0 must demonstrate from source that the 1200-bit payload is accepted by a
profile-scoped loader/unpacker path without changing T1f/T1g behavior. If the
loader, activation controller, or resource/timing architecture cannot support
this isolated profile within the frozen invariants, HALT and report the
smallest required contract amendment. Do not silently change the packet format
or introduce a transport queue.

### Q0 source-audit result

The source review confirms:

* `spu_scene_loader` is parameterized by `SCENE_BITS` and `PAYLOAD_BYTES`,
  and uses the `A5` start byte. It has no T1h profile selector today.
* The loader's `payload_count` is only 7 bits. It can represent the T1f/T1g
  126-byte payload count but cannot reach 149 for the proposed 150-byte T1h
  payload. Therefore the current loader cannot complete a T1h packet.
* `spu_depth_math` accepts unsigned 16-bit `z0/z1/z2`, emits signed 56-bit
  affine coefficients and a 7-bit fractional shift, and uses the shared
  reciprocal/multiplier setup path. It can calculate an attribute plane from
  the three unsigned scalar samples using the same geometry without changing
  the depth calculation. The separate setup workload and resource/timing
  impact remain to be characterized in Q1.
* `spu_attr_stepper` accumulates signed 56-bit values and exposes
  `acc >>> frac_bits`; it neither clamps nor reduces to 16 bits.
* The current top-level has no internal attribute result or T1h selector yet.
  T1h shall expose its selected scalar only to hierarchical simulation
  observation, not through an external port.

Q0 initially halted because the current loader counter cannot accept 150
payload bytes. The owner has amended the implementation boundary to authorize
`T1H_SCALAR_SCENE=0|1` and the minimum parameterized loader change. An 8-bit
counter is sufficient to represent payload byte indices 0 through 149. Its
termination comparison remains `PAYLOAD_BYTES-1`, preserving exact 63-byte
and 126-byte completion semantics for T1f/T1g. No runtime length inference,
UART protocol change, external port, or duplicate loader is authorized.

Q0 is now **PASS WITH AMENDMENT**. Q1 is authorized to implement this narrow
profile/loader change and continue into scalar setup, stepping, activation,
fixtures, and simulation qualification. The loader boundary regression shall
prove exact completion and one-under/one-over behavior at 63, 126, and 150
payload bytes.

## 5. Q1 — Attribute path and fixture generation

After Q0 passes:

1. Add the profile-scoped 300-bit record unpacking and 1200-bit scene path.
2. Prepare one scalar plane for each primitive from its three vertex samples,
   retaining the output coefficients and fractional shift per lane.
3. Add one scalar accumulator per primitive using the existing pixel and row
   stepping coordinates. Keep attribute validity and generation identity
   aligned with the corresponding scene candidate.
4. Route the attribute for the depth-selected primitive to an internal scalar
   signal that the testbench observes hierarchically. Do not add an external
   top-level port or modify RGB with the scalar in T1h.
5. Generate immutable A/B/C T1h fixtures from the Q0 semantic specification.
   Record source and decoded-payload SHA-256 hashes.
6. Add assertions that fail if any lane exposes coefficients, fractional
   shift, validity, or generation from a different candidate scene.

### Q1 implementation record

The implementation adds the compile-time `T1H_SCALAR_SCENE` selector to
`spu_gpu_top` and the Artix-7 wrapper/build path. The selector defaults to
zero, and elaboration rejects value one unless both prepared-scene and
four-primitive profiles are enabled. T1h records append the scalar samples at
bits 252..299. The loader uses a widened 8-bit counter and remains terminated
by its configured `PAYLOAD_BYTES-1` comparison.

`spu_scene_profile_unpack` separates the T1h record extension from the
legacy geometry slices. `spu_prepared_scalar_attribute4` owns the parallel
four-lane attribute setup, generation-aligned readiness, active scalar state,
four incremental accumulators, and winner-selected internal output.
`spu_depth_math` is instantiated as a parallel four-lane attribute setup
dispatch using the same edge geometry and the three scalar vertex samples.
Depth and scalar result pulses are required to align before the existing
four-lane generation controller can activate. Four signed 56-bit accumulators
use the shared pixel/row steps. `spu_depth_compare4` exposes the selected
primitive identity and valid bit internally; the selected scalar is an
internal hierarchical simulation signal only.

The T1h fixtures were generated only after freezing the A/B/C vertex-value
table above:

```text
python3 tools/generate_gpu_t1h_scalar_scenes.py
```

| Fixture | Wire SHA-256 | Hex-file SHA-256 |
|---|---|---|
| `gpu_t1h_scene_a_wire_151b.hex` | `656e4583753bd86d37b9fe0480cf6fa493e4f475232fb89271ae4bf5559ad3e3` | `93a4baf336ec166e69c802ecaeee43383810ad48b5597940229f83eff81db062` |
| `gpu_t1h_scene_b_wire_151b.hex` | `3858256dd7999634cf997afdf40318c16bf4d87a731b340148b31d1c49aed70a` | `6f913e4715f458d4caf70865649f7aff466520b46fc7366c2589c0a4e256dca5` |
| `gpu_t1h_scene_c_wire_151b.hex` | `f9415dcf3143604e25fa4591e49646d9cb446e28e81f87a1f3d771869cfb27d9` | `df43e881a888ff96df09aab448f7c686d0367209ffcc6ae8e3d3060de573ee74` |

The loader boundary bench passed exact, one-under, and one-over checks for
63-, 126-, and 150-byte payload configurations. The 150-byte profile remained
uncommitted through byte 149 and committed only after byte 150. Results were
also checked for byte ordering and ignored post-completion input.

## 6. Q2 — Deterministic interpolation and transition qualification

Run scene transitions A→B→C→A through the prepared-scene path. For every
active pixel in the first complete frame after each activation, compare the
hardware scalar and validity against an independent integer oracle using the
frozen geometry, per-vertex scalar samples, and existing depth winner rule.
Check the old scene throughout candidate receipt/preparation and assert that
no frame contains mixed geometry/depth/attribute generations.

Required results:

```text
all four lanes have distinct, nonconstant scalar planes: PASS
all selected-pixel scalar values match the oracle: PASS
all uncovered pixels report invalid and zero: PASS
candidate attributes remain invisible before activation: PASS
geometry/depth/attribute activate on one frame boundary: PASS
mixed-generation pixels across all checked frames: 0
```

Use at least 8,000 active pixels per first post-activation frame for the
small-frame profile. The oracle must not reuse the RTL accumulator output or
the RTL depth-setup result as its expected scalar value.

### Q2 result

The first complete post-activation frames for A, B, C, and A were compared
pixel-by-pixel with the independent integer setup/raster oracle:

```text
scene A: 8,000 pixels PASS
scene B: 8,000 pixels PASS
scene C: 8,000 pixels PASS
scene A: 8,000 pixels PASS
mixed-generation pixels: 0
scalar/depth setup-ready pulse alignment: PASS
active scalar tuple held through candidate receipt/preparation: PASS
illegal T1h profile elaboration: rejected as required
```

Command and result:

```text
python3 software/tests/test_gpu_t1h_attribute.py
PASS: T1h scalar interpolation, depth winner, and A/B/C/A activation (32,000 pixels)
```

Measured from final payload byte acceptance in the small-frame simulation,
all four scalar and depth results were generation-ready in 96 `clk_pixel`
cycles. Depending on final-byte frame phase, activation followed 8,458 to
8,726 additional cycles in this 8,858-cycle frame profile. The scalar setup
does not extend the depth setup critical path because both setup dispatchers
run in parallel and their per-lane result pulses aligned. Reuse the T1g
20 ms host delay after the final payload byte: T1g measured a 420,095-cycle
worst-case busy interval at 25 MHz, while T1h adds only one measured setup
cycle and does not serialize the new attribute setup. The resulting bounded
busy interval is 420,096 cycles (16.80384 ms), leaving 3.19616 ms margin.
The 151-byte UART transaction takes 13.10764 ms at 115200 baud, giving a
minimum scene start-to-start spacing of 33.10764 ms. This remains a paced
replacement path, not arbitrary streaming. The T1g phase characterization is
recorded in `contract_gpu_t1g_temporal_scene_replacement_2026-09-23.md` §5.
Artix resource/timing remains for B1.

## 7. Verification commands

After Q1 adds the named tests, execute these commands in order:

```bash
python3 software/tests/test_gpu_t1h_attribute.py
TB_FILTER=spu_gpu_t1h_attribute python3 run_all_tests.py
bash tools/verify_repo.sh
```

Because production RTL changed, B1 must build and qualify the T1h Artix-7
image using the same frozen source revision and evidence discipline as T1g.
The non-diagnostic T1h B1 image does not provide a physical scalar observable.
H1 must use a fresh `T1H_DIAG_B1_S1` image built with
`T1H_SCALAR_DIAG=1`, then establish baseline RGB and send the frozen T1h
fixtures at the characterized 151-byte pacing. H1 must verify predetermined
dark/bright regions against the scalar oracle; merely seeing a rendered scene
does not qualify scalar interpolation. Simulation results alone do not
support a silicon claim. Any physical host delay must be characterized for
the 151-byte wire transaction and added setup work before scene sequencing.

H1 used the diagnostic bitstream and frozen A/B/C/A fixtures. The operator
confirmed the black/white scalar pattern changed for B and C and returned to
the A pattern. For A, the oracle-predicted sample at `(28,44)` is 15499
(black, scalar bit 14 clear), while `(44,44)` is 27716 (white, scalar bit 14
set). The photo shows the expected broad threshold split, but also a purple
line extending along the left vertex edge. The operator reports that it
follows the scene geometry. This edge artifact is not accepted as camera noise
or harmless output skew without further evidence. H1 remains on hold pending
resolution of the physical edge artifact. The focused simulation audit covers
572 samples around the lower vertex across A/B/C/A: all twelve lane edge
accumulators match the independent edge equations, coverage and winner
selection match the scalar/depth oracle, and invalid pixels drive black through
the final VGA output. This does not explain or dismiss the physical purple
shimmer. Existing evidence and the audit result are recorded in
`docs/hardware_evidence.md` §3.13.

The independent depth oracle also shows that Scene A's four primitives have
identical coverage and an internal depth-winner seam. Across the seam at
`(40,41)`, lanes 2 and 3 tie at depth 58; deterministic lower-ID priority
selects lane 2, while its immediate left and right neighbors select lanes 2
and 3. All four lanes tie at `(40,40)`, where lane 0 wins. A repeated complete
A frame matches the oracle, so simulation shows a stable seam rather than
frame-to-frame depth winner oscillation. This makes the visible black/white
boundary a plausible source of the physical purple fringe, but does not
identify the downstream color artifact. The owner has stopped further logic
captures; H1 remains on hold with the purple fringe unresolved.

## 8. Stop conditions

* If Q0 cannot preserve legacy profile behavior or identify generation-matched
  activation for scalar state, HALT and propose a minimal amendment.
* If source review shows attribute interpolation requires changing depth
  winner behavior, HALT.
* If any mixed-generation scalar, oracle mismatch, or tear is observed, HALT
  qualification and fix the localized defect before proceeding.
* Do not add `(u,v)`, procedural shading, texture storage, FIFO/queueing,
  altered UART handshaking, or unrelated renderer refactors under T1h.
* Do not claim physical qualification without a fresh T1h bitstream and an
  entry in `docs/hardware_evidence.md`.
