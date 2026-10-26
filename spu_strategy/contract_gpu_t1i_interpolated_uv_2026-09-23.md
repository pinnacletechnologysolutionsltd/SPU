# Engineering Contract: T1i Interpolated Material Coordinates

**Date:** 2026-09-23<br>
**Contract ID:** `GPU-T1I-INTERPOLATED-UV-2026-09-23`<br>
**Revision:** 0<br>
**Status:** `Q0–Q2 PASS; Q3 FULL REPOSITORY GATE FAILED ON UNRELATED TIMEOUT`<br>
**Owner:** John Curley

## 1. Objective

Answer the question:

> Can the prepared four-primitive raster path carry two independent affine
> fragment coordinates `(u,v)` through dynamic A/B/C/A scene replacement,
> with both values selected by the existing depth winner?

T1i extends T1h's scalar interpolation mechanism to two unsigned 16-bit
coordinates. It has no texture memory, coordinate normalization, fragment
shader, or RGB visualization. T1j will use the qualified `(u,v)` values for a
procedural material. T1i is simulation-qualified; it has no physical H1 and
requires no logic-analyzer capture.

T1h's purple vertex-edge artifact remains documented as unresolved. Per the
owner's direction, the T1h artifact investigation is stopped as inconclusive;
that issue does not block this simulation-only T1i tranche and is not claimed
as resolved by T1i.

## 2. Scope and frozen profile

Add one compile-time T1i profile:

```text
T1I_UV_SCENE=0|1, default 0
legal value 1: PREPARED_SCENE=1 and FOUR_PRIMITIVE_SCENE=1
T1H_SCALAR_SCENE and T1I_UV_SCENE are mutually exclusive
```

With the selector at zero, T1f, T1g and T1h profiles, packet lengths,
fixtures, and elaboration remain unchanged. T1i is a separate profile and
does not append coordinates to the T1h scalar record.

Each T1i primitive record is 348 bits:

| Bits | Field |
|---:|---|
| 0–251 | Existing canonical geometry and depth record |
| 252–267 | `u0`, unsigned 16-bit sample at vertex 0 |
| 268–283 | `v0`, unsigned 16-bit sample at vertex 0 |
| 284–299 | `u1` |
| 300–315 | `v1` |
| 316–331 | `u2` |
| 332–347 | `v2` |

Four records form a 1392-bit (174-byte) payload. The complete transaction is
175 wire bytes: the unchanged `A5` start byte plus the payload. Byte order
remains little-endian, matching `spu_scene_loader`. The widened 8-bit loader
counter represents payload indices 0 through 173; termination remains the
compile-time `PAYLOAD_BYTES-1` comparison. No runtime packet-length inference,
UART protocol change, or queue is authorized.

## 3. Frozen coordinate semantics and scenes

`u` and `v` are independent raw unsigned 16-bit vertex samples. They use the
same signed 56-bit affine coefficient, accumulator and arithmetic-right-shift
semantics as T1h. There is no normalization, rounding, clamping, wrap, or
conversion to a smaller value. A covered pixel's `u` and `v` both come from
the primitive selected by the existing four-way depth comparator. An
uncovered pixel has `valid=0`, `u=0`, and `v=0`.

Use the frozen T1h A/B/C geometry and depth records without modification.
For each row below, the three coordinate pairs correspond to geometry
vertices 0, 1, and 2. Scene B adds `(2048,1024)` to every A coordinate pair;
scene C adds `(1024,4096)` to every A coordinate pair. These offsets are
applied independently to both coordinates and do not wrap.

| Primitive | Scene A vertex `(u,v)` values |
|---:|---|
| 0 | `(0,0)`, `(8192,1024)`, `(1024,8192)` |
| 1 | `(12288,4096)`, `(20480,5120)`, `(13312,12288)` |
| 2 | `(24576,12288)`, `(32768,13312)`, `(25600,20480)` |
| 3 | `(36864,20480)`, `(45056,21504)`, `(37888,28672)` |

All six fields vary over each primitive, lane ranges are distinct, and B/C
produce different fields from A. Fixture generation is authorized only after
the Q0 source/profile checks below pass. Do not modify T1h or T1g fixtures.

## 4. Invariants and hard constraints

* `u` and `v` each have independent candidate coefficients, fractional shift,
  readiness, active state, and four per-lane accumulators.
* Both coordinate sets are prepared for the same candidate scene generation.
  Activation waits for depth, U and V readiness. Geometry, depth, U and V
  activate together on the first eligible `frame_start`.
* The U and V outputs use the same depth winner ID and valid bit. No losing
  primitive may contribute either coordinate.
* The outgoing scene remains active during receipt and preparation. While
  `commit_pending=1`, incoming UART bytes remain unaccepted.
* No top-level port changes. Test visibility is internal and hierarchical.
* No floating-point arithmetic, division, framebuffer, additional render
  clock, runtime packet inference, FIFO, or unrelated refactor.
* No physical capture, FPGA programming, or H1 claim is in this tranche.

## 5. Q0 — Source and profile review

The following read-only review was completed before implementation:

```bash
sed -n '1,180p' hardware/rtl/gpu/spu_scene_profile_unpack.v
sed -n '1,180p' hardware/rtl/gpu/spu_prepared_scalar_attribute4.v
sed -n '1,150p' hardware/rtl/gpu/spu_scene_loader.v
sed -n '190,275p' hardware/rtl/gpu/spu_gpu_top.v
rg -n "T1H_SCALAR|SCENE_BITS|PAYLOAD_BYTES" hardware/boards/artix7/build_a7.sh
```

Q0 source findings:

* The loader is compile-time parameterized by scene width and payload byte
  count. Its 8-bit counter and `PAYLOAD_BYTES-1` termination can represent the
  T1i 174-byte payload while retaining existing profile lengths.
* The profile unpacker currently supports the 252-bit legacy record and the
  300-bit T1h record. A 348-bit T1i record can be isolated with its own
  compile-time generate branch and per-lane stride.
* `spu_prepared_scalar_attribute4` provides a complete four-lane setup,
  generation-ready join, active/candidate coefficient handoff and winner-ID
  selection for one scalar. Two independently instantiated paths can carry U
  and V; their ready vectors must both join the existing scene controller.
* The Artix build currently has a T1h selector and guards. T1i requires an
  isolated selector and artifact tag; legacy and T1h build combinations must
  remain unchanged.

**Q0 result:** PASS. Q1 may implement the isolated T1i profile. If source
changes reveal that independent U/V paths cannot share the existing timing,
winner identity, or activation boundary, HALT and amend this contract before
changing the architecture.

## 6.1 Q1 implementation record

**Status:** PASS. Implemented the isolated `T1I_UV_SCENE` profile through the
GPU top, Artix wrapper, and compile-time build selector. T1i uses 1392-bit
scenes and 174 payload bytes; byte 173 is the one-under boundary and byte 174
completes the packet. T1h and legacy profiles retain their prior selectors and
packet lengths. The two attribute paths use the same candidate preparation,
depth winner ID, frame-start activation edge, and pixel validity.

Generated fixtures from this contract's frozen table:

| Artifact | Wire transaction SHA-256 | Hex file SHA-256 | Decoded payload SHA-256 |
|---|---|---|---|
| Generator `tools/generate_gpu_t1i_uv_scenes.py` | — | `cace478d1cba6be6bd3e10d52ee4661297d70404054725c2bcfe4c23eea6dd92` | — |
| Scene A | `8077acb3efbb92756fdee4c137500417e32f6f3664784c3b21f150c398d0dae9` | `079a14b7fa4565c86e82311d571ab1b70099e96e598eededa7e8bffa5a0f4143` | `25a21419cffd7055d8cbdd9730fba8bd1e5b210215ce87047b33ad39ac0c4ae2` |
| Scene B | `f71ec97d18c37cdae7067accbc3b0100bad3689d4fcbc856f55efc11207525d1` | `49484804bf798a4de6c4389c615eacfc3b42115d67a3b5d60c311b0c432d9fc9` | `016191716775c000020fa03c802e7001af19b30f6d9b1f2fecccf0569ae35716` |
| Scene C | `604fea47bee07549e28212b87bb5da18dbe6b72d32412ed57bddb6decb8cb89d` | `628f1efd61c1c23f52d72d6908d4ccbacc27289687b8c18c6ab5c01d91b5ccba` | `aa8b607e5504f823c2dae97092d12a21fae1bf4d13487616355ee6b3c0ff229e` |

The generator also printed wire-transaction and decoded-payload hashes when it
created each fixture. The fixture files are generated outputs; do not edit
them by hand.

## 7. Q1 — Profile, interpolation paths, and fixtures

1. Add `T1I_UV_SCENE=0|1`, default zero, to `spu_gpu_top`, the Artix wrapper,
   and build script. Reject illegal prepared/four-lane combinations and
   simultaneous T1h/T1i selection at elaboration/build time.
2. Add the 348-bit record unpacking and 1392-bit scene width. Preserve all
   existing profile branches and packets when the selector is zero.
3. Instantiate two independent four-lane interpolation paths from the frozen
   `u0/u1/u2` and `v0/v1/v2` fields. Join depth, U and V readiness before
   candidate activation. Select both outputs with the same depth winner ID.
4. Add a T1i fixture generator from the frozen A/B/C table. Record source,
   wire-fixture and decoded-payload SHA-256 hashes. Do not edit fixture files
   by hand.
5. Extend the loader boundary regression to prove exact completion and
   one-under/one-over behavior for 63, 126, 150 and 174 payload bytes. Byte 173
   must not commit T1i; byte 174 must commit it.
6. Add assertions for atomic U/V candidate state, readiness, activation,
   winner identity and invalid-pixel zeroing. Keep the T1h scalar profile
   behavior and H1 classification unchanged.

## 8. Q2 — Independent interpolation and transition oracle

Run `A→B→C→A` through the T1i loader in simulation. For every active pixel in
the first complete frame after activation, independently derive the U and V
planes from fixture vertex samples and frozen geometry, then compare both
results and validity against the existing depth winner.

The oracle must not consume RTL coefficients, accumulator values, or winner
signals to form expected results. Check every active pixel (at least 8,000 per
frame in the small-frame harness) and include samples from all four lanes,
overlaps, uncovered boundaries, the lower vertex and the row below it.

Required results:

```text
U result matches independent oracle: PASS
V result matches independent oracle: PASS
uncovered U/V are invalid and zero: PASS
both coordinates belong to the same depth winner: PASS
candidate U/V remain hidden until activation: PASS
geometry/depth/U/V activate as one generation: PASS
mixed-generation pixels in A/B/C/A frames: 0
```

**Q2 result (2026-09-23): PASS.** The independent Python oracle checked all
32,000 active pixels across first post-activation A/B/C/A frames (8,000 per
frame). Both coordinates matched the oracle, including overlap winner changes
and uncovered pixels. The RTL test also confirmed that active scene state
stays fixed across each checked frame, candidate state does not replace the
outgoing scene during UART receipt, U/V readiness agrees at activation, and
depth/U/V coefficients and fractional widths commit together. Illegal profile
selection and simultaneous T1h/T1i selection both fail elaboration as required.
The loader profile bench passed exact, one-under, and one-over byte boundaries
for 63, 126, 150, and 174-byte payloads.

**Q3 full gate result:** `FAILED` (exit 1, 822 seconds), unit
`spu-gpu_t1i_interpolated_uv_20260923_q3_02-20260923T103545Z-371155`,
evidence directory
`build/gpu_t1i_interpolated_uv_20260923_q3_02`. The only reported full-suite
failure was a timeout in unrelated `spu_t1d_board_transaction_tb.v`; no T1i
oracle or loader failure was reported. `run_all_tests.py` counted that timeout
both in `failed` and again in `timeouts`, producing a headline total of two
failures for the one timed-out test. The full repository gate is not PASS.

## 9. Q3 — Verification and stop conditions

Run in this order:

```bash
python3 software/tests/test_gpu_t1i_uv.py
TB_FILTER=spu_gpu_t1i_uv python3 run_all_tests.py
git diff --check
```

Then launch the repository gate as a detached job in a new directory under
`build/`, using `tools/run_detached_job.sh --output <new-build-directory>
--timeout 3600 --notify-desktop -- bash tools/verify_repo.sh`. Record its
unit and evidence directory. End the agent turn after `LAUNCHED`; interpret a
result only when exactly one `COMPLETE`, `FAILED`, or `TIMEOUT` marker exists.

* On any loader-boundary, oracle, readiness, winner or mixed-generation
  failure, HALT. Do not build or program an FPGA image.
* If the second setup path prevents timing closure or requires a new transport
  or render architecture, HALT and propose a narrow contract amendment.
* Do not add a checkerboard, stripes, fragment function, RGB diagnostic,
  texture memory or hardware capture in T1i. Those belong to T1j or a separate
  observability tranche.
* T1h's ghost vertex-line remains unresolved and T1h H1 remains HOLD. T1i
  simulation success shall not be used to upgrade that result.
