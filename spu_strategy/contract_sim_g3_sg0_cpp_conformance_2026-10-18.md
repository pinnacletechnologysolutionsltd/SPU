# SIM-G3: SG-0 projected scenes through the native C++ T1d path

**Date:** 2026-10-18

**Contract ID:** `sim_g3_sg0_cpp_conformance_2026-10-18`

**Status:** RATIFIED — ONE HARNESS IMPLEMENTATION PASS AUTHORIZED; QUALIFICATION CAMPAIGN PENDING SEPARATE AUTHORIZATION

**Disposition:** No implementation or execution authorized by this draft.
**Scope:** Two frozen SG-0 projected scenes, the existing SIM-G2A encoder, and the unchanged SIM-1 T1d renderer.

## 1. Objective

Check that the two qualified SG-0 projected scenes can cross the existing C++ SIM-G2A packet encoder and SIM-1 renderer with the same packet bytes and RGB8 framebuffer payloads as the frozen Python SG-0 results.

This is a cross-implementation conformance experiment for two fixed scenes. It does not run the symbolic solver in C++, re-derive the geometry in C++, qualify arbitrary scene conversion, or establish FPGA equivalence.

## 2. Provenance and frozen inputs

The following evidence identifies the source baselines available at draft preparation. Before any future run, verify every listed identity and stop if one differs.

### SG-0

- Qualified local baseline: `research/sg0_baseline_20261018/README.md`.
- SG-0 terminal result: `build/sg0/certified_geometry_20261018_01/COMPLETE`; detached result is `COMPLETE`, exit 0, duration 240 seconds.
- Focused scope: 12 SG-0 tests, 14 SSM-3 tests, GPU S1/S2/S3 and W1/W1-C passed. Full repository suite and hardware qualification were not run.
- Frozen source archive: `research/sg0/provenance/sources.tar.gz`, SHA-256 `0595219d7b474437ecb983fe3621629915ae3bec36a24d2e91165e097af2d7cb`.
- Source manifest: `research/sg0/provenance/sources.json`, SHA-256 `02a5d23ab70d62324c4c41ca7bbe3ba6433df00276acf9f70e83bebce5d56f7b`.
- Frozen SG-0 inputs: `fixtures/sg0_v1/inputs.json`, SHA-256 `308e68d5bce183883caa86b093d9a4fcbb7dfd830c5098dd816f0f8b312b82ed`.
- Proof: `fixtures/sg0_v1/unique_cycle.proof.json`, SHA-256 `bea32a0564eebfa9f5e9693aedc656ddbc365d943d714aa3eea4f2363731f418`.
- Qualified generated bundle: `build/gpu_evaluation/sg0/qualification_20261018_01/`; manifest SHA-256 `4ea8b6081f9aa292a25ad0284b1d3aa57339236573c2e2d59f7d2258be8781b7`.
- The `identity` and `rational_rotation` scene, packet and image artifacts are listed in §3. The repeated bundle `qualification_20261018_01_repeat` is available for determinism cross-checks.

### SIM-G2A / SIM-1

- Base source commit: `013acd4230442e0e126640604c11176f274962ab`.
- Qualification record: `/home/user/Projects/hardware/spu-sim/docs/SIM_G2A_QUALIFICATION_2026-10-18.md`.
- Qualified executable: `/home/user/Projects/hardware/spu-sim/build/sim-g2a/spu-sim`, SHA-256 `ca524aaedd5a61c6bb469d5fcdf57552c4044a15c4ddf6317b9428911b4ac847`.
- The encoder implementation is an uncommitted source overlay on the pinned base commit. At draft preparation its recorded hashes are:

| Path relative to `spu-sim` | SHA-256 |
|---|---|
| `CMakeLists.txt` | `679a5facabad7ca855afe443a39b90553336c557f758db15b717fed629688f8e` |
| `README.md` | `20e24f0f1983e29eca7911c57ec98525a88b47f250d9ee483838ec66c7fb8bc6` |
| `src/main.cpp` | `f2f6d287539ae0ec1cff463be1890c41182f9f4a0b2ed4b3c3a7276070754d11` |
| `src/t1d_scene.cpp` | `058c8fe028f32aa2ccb62242c88dbd3d5c2d7ac8acba8f38387417c73eeef5ad` |
| `include/spu_sim/t1d_scene.hpp` | `46ecbdc8dc989626c13ccde979a4216784a4a846076ba2c479c8770581ac058f` |
| `tests/test_t1d_scene.cpp` (R2) | `7c63717179a96327b1bc62b8898410bb9fd73c5f8f3b1dd30c4fa93b9e793552` |
| `docs/SIM_G2A_QUALIFICATION_2026-10-18.md` | `e672f35a4b677144c2874ed589202bc1fef56af9615fb34e126aeb160a46e03f` |
| `fixtures/sim_g2a/identity.json` | `fe22438bcad82c75936c8716ba6f2c3cf1c2a3cbe98eeaa7c31ab7e3b781cc3c` |
| `fixtures/sim_g2a/identity.packet` | `e2ef44e4087e7c8a2d1a67c3ef24abde1e2542d9b8f5a74c11753762dad43942` |
| `fixtures/sim_g2a/identity.packet.sha256` | `8e52008eb2af3c72d509470c8e0074c01373ef9cde2e83ba9b1c7a07575f6f5b` |
| `fixtures/sim_g2a/input_boundaries.json` | `de65878b3f745bcc5d31bb8efd7789d56d0cce77d68fec0d814595a2bb1a61ec` |
| `fixtures/sim_g2a/input_boundaries.packet` | `feb1279ebb543192adc135212cadbcc3283b836e050bf54aecaf45f0d80117c4` |
| `fixtures/sim_g2a/input_boundaries.packet.sha256` | `4c6ca7988865d417e8fe35e52cdb6871285abd8a077cd24c104078740ca5749d` |
| `fixtures/sim_g2a/manifest.json` | `a7b2c21074856a249b46fd0403445d6b723148aef1089b9163b223cf45db65e9` |
| `fixtures/sim_g2a/reflect_bc.json` | `9225eca55b24514b230da2e0df0f3c1d4aace80cc94d33a8129b5b7de6b6b6f9` |
| `fixtures/sim_g2a/reflect_bc.packet` | `c0c439c1955a43f86793fa439aa2d1617a4a671a8237850c5acde802f63b772d` |
| `fixtures/sim_g2a/reflect_bc.packet.sha256` | `2001d84c065b9d1abea6c85d732e65189a2cf7b68c424916c8024e164978a8f0` |
| `fixtures/sim_g2a/rotate_bcd.json` | `8216ed2fafd4623061783ae02e284a1e1796510596f18b860aec5e4da4e0f348` |
| `fixtures/sim_g2a/rotate_bcd.packet` | `8d829ce865a2053578e5369b437ec9b603023cbf624e6a6d573f112af7ee7b37` |
| `fixtures/sim_g2a/rotate_bcd.packet.sha256` | `912e4e8821539670fe48f299e80fbe3d7e5d07e376bdbd57bea5cb2fb246b950` |

The completed R2 test source is also preserved at `build/sim-g2a-r2_20261018/test_t1d_scene.cpp` with the same hash. The R2 record states the production executable hash did not change. SIM-G2A source and executable are not represented by a clean commit. A future execution must create and hash a source-overlay archive before invoking the executable; these hashes are preflight pins, not a substitute for that archive.

### T1d reciprocal table

Use `hardware/rtl/arch/gpu_reciprocal_lut_q15.mem`, SHA-256 `a64327c1bc0c8c74a4fb8c849a922a1f8b3d6a6e2e3bb58951d11f2012bb5248`.

## 3. Frozen scene and output identities

All packet files are exactly 64 bytes. Each raw RGB8 frame is 640 × 480 × 3 = 921,600 bytes.

| SG-0 variant | Scene SHA-256 | Packet SHA-256 | Python ideal PPM SHA-256 | Python device PPM SHA-256 | RGB8 payload SHA-256 |
|---|---|---|---|---|---|
| `identity` | `e7d13326a973be5bc142073c031fea2cb5fb71722fa7102f845ba59a9c3bb59f` | `35a976682ecfbbf17684e6738cf463f7462841ef995b852fe5ff4140674beeaf` | `e90865ea0de24c4b524034ecae3819da3245bb207f22f233953f04c13a4f9a4c` | `e90865ea0de24c4b524034ecae3819da3245bb207f22f233953f04c13a4f9a4c` | `d408eec2cd55285f3c5f11f576d3f009c0799501a607cca58fbfc6f3360e70c4` |
| `rational_rotation` | `b690c3a536dbcb14ae7e1affc3594af6f98c38ca1300f17079c1ba8fb9853ceb` | `c05801cc609499e6da33b28e420c7c198aa8c17a95a31375a2f3955059f533b7` | `594c08ebb5448a9cc9da3f5d7cfce0e5820fce63f2900749ba40b48b2cef2576` | `594c08ebb5448a9cc9da3f5d7cfce0e5820fce63f2900749ba40b48b2cef2576` | `fe481871ffefa93f533628abde477c2c0db8f8b4c21beef685b4744f6f35ac03` |

The SG-0 PPM files have the P6 header `P6\n640 480\n255\n` followed by the 921,600-byte RGB8 payload. Compare C++ raw RGB8 output against that payload, not against the PPM header bytes.

The SG-0 full-frame reports record equal coverage, covered-triangle sets, winners, and RGB for all 307,200 pixels in both variants. Finite-width depth differs from ideal depth at 19,845 `identity` pixels and 19,878 `rational_rotation` pixels. Preserve those measurements as SG-0 evidence. SIM-G3's C++ renderer emits RGB8 only; it cannot establish per-pixel depth agreement.

## 4. Schema handoff and semantic boundary

The exact SG-0 scene JSON cannot be passed byte-for-byte to the current SIM-G2A parser: the schemas use different `format` and `profile` identifiers. Their geometry payloads use the same `width`, `height`, `triangles`, `vertices`, and `rgb` fields, but the identifiers are:

| Field | SG-0 | SIM-G2A |
|---|---|---|
| `format` | `spu_gpu_scene_v1` | `spu-t1d-projected-scene-v1` |
| `profile` | `t1d-two-triangle-v1` | `gpu.scene.t1d.two-triangle-v1` |

The integration harness shall create a derived C++ input JSON by changing exactly these two schema identifier strings. It shall use strict JSON loading that rejects duplicate keys and require exact key sets at the root and triangle levels. It shall prove by structured comparison that the complete objects are identical after removing only `format` and `profile`, and that the dimensions, triangle count and order, every vertex coordinate, and every RGB channel are identical to the original SG-0 scene. It shall record both source and derived JSON hashes. The original SG-0 scene and all qualified SG-0 files remain read-only. Unexpected keys or any required non-metadata conversion are a harness failure and stop condition.

This metadata-only adapter is a SIM-G3 integration step, not an expansion or modification of either schema. If the C++ parser requires any other field/value change, halt for contract review.

## 5. Implementation scope after separate ratification

Allowed new files:

- `research/sim_g3/` — a small deterministic harness, fixed-input tests and README.
- `docs/SIM_G3_QUALIFICATION_2026-10-18.md` — terminal evidence record after a separately authorized campaign.
- A new output directory under `build/sim_g3/` for the source overlay archive, staged executable and ROM, adapted inputs, C++ outputs, comparisons and manifests.

No edits to SG-0, SSM-3, SIM-G2A, `spu-sim`, the Python renderer/device model, the T1d packet format, the reciprocal ROM, ISA, RTL, FPGA flows, scene catalogues or existing qualification evidence. Do not commit, tag, publish, or alter original source/evidence under this draft.

The harness may call the existing SG-0 verifier and the existing C++ executable. It may parse P6 PPM headers for the frozen dimensions and compare payloads. It must not implement a rasterizer, packet encoder, geometry conversion, or new arithmetic path.

### Preflight and write ordering

The `run` command must perform all read-only checks before creating the output directory: SG-0 terminal/bundle/source pins; C++ base commit and every pinned overlay/fixture hash; executable and reciprocal-table hashes; input scene schema/key validation; and output-path nonexistence. A failed preflight must leave no output directory or archive. After successful preflight, create the new output directory, write a deterministic manifest and exact SIM-G2A overlay archive, copy the pinned executable and reciprocal table into the evidence directory, verify each copy's hash, then invoke the staged executable. Never run from the mutable source path after staging.

The source overlay archive must identify base commit `013acd4230442e0e126640604c11176f274962ab`, preserve the exact changed source files, R2 test amendment, SIM-G2A fixture files and qualification record, and include a path-to-SHA-256 manifest. Exclude build outputs. The staged executable and reciprocal table are separate evidence artifacts. This is an evidence snapshot of the qualified local overlay; it does not claim a clean Git commit or a reproducible rebuild unless a rebuild is separately performed and qualified.

## 6. Required checks and acceptance criteria

1. Verify SG-0 baseline result marker, bundle manifest, source archive and all referenced hashes. Run `python3 -m research.sg0 verify build/gpu_evaluation/sg0/qualification_20261018_01` only as a read-only integrity check; do not regenerate or publish fixtures.
2. Verify SIM-G2A base commit, every overlay source hash, executable hash, fixture manifest, and reciprocal table hash. If any pin differs, stop before creating output.
3. For each of the two scenes, create the metadata-only adapted JSON and assert the strict key and structured-object equality defined in §4.
4. Run the existing executable's `gpu encode-scene` command on each adapted scene. Each output must be exactly 64 bytes and byte-for-byte equal to the corresponding SG-0 `scene_packet.bin`; also verify the tabled SHA-256.
5. Render each packet with the same existing executable and pinned reciprocal table. Each output must be exactly 921,600 bytes and byte-for-byte equal to the RGB8 payload extracted from both the SG-0 device PPM and ideal PPM. Verify the tabled payload SHA-256.
6. Report packet equality, framebuffer RGB equality, and SG-0 depth-difference counts as separate outcomes. Do not infer C++ depth equality from RGB equality.
7. Preserve source identities, exact commands, toolchain versions, stdout/stderr, exit status, adapted JSON hashes, packet/frame hashes and comparison results. Originals remain unchanged.

Acceptance requires every pin to match, both packet comparisons to pass, both RGB8 payload comparisons to pass, and all generated evidence to bind to the frozen source identities. Any command failure, mismatch, timeout or missing evidence halts the campaign; do not retry under the same allocation.

### Failure classification

- **Harness/preflight failure:** missing or changed input/source/artifact, malformed or unexpected schema key, inability to construct the metadata-only adaptation, output-path refusal, archive/copy/hash failure, or missing command output. No conformance conclusion follows.
- **Packet-conformance failure:** the adapter passed all checks and the C++ encoder returned a packet, but packet length, bytes or SHA-256 differs from the SG-0 reference.
- **Renderer-conformance failure:** packet bytes match, but the C++ renderer fails or its RGB8 output length/bytes/hash differs from the frozen SG-0 image payload.

Preserve partial evidence and the first terminal classification. Do not repair implementation, expectations, or artifacts during this campaign.

## 7. Focused tests and separately gated campaign

Run the focused handoff tests from the repository root:

```bash
python3 -m unittest research.sim_g3.test_handoff -v
```

Before requesting qualification authorization, freeze the harness file hashes and show that this focused test passes. The runner enforces one 300-second cumulative campaign deadline and a 60-second maximum per subprocess command.

The harness interface proposed for implementation is:

```bash
python3 -m research.sim_g3 run --out build/sim_g3/qualification_20261018_01
python3 -m research.sim_g3 verify build/sim_g3/qualification_20261018_01
```

`run` performs SG-0 bundle verification, constructs the metadata-only adapters, archives the pinned SIM-G2A overlay, stages the pinned executable and ROM, then encodes and renders both scenes. `verify` checks the preserved campaign record and generated artifacts without invoking the simulator. The runner must refuse an existing output directory and must stop before writing if any source/fixture preflight fails.

Proposed execution limits, subject to separate owner authorization:

| Limit | Proposal |
|---|---:|
| Implementation | One harness-only pass |
| Qualification campaign | One attempt |
| Per-command timeout | 60 seconds |
| Cumulative campaign budget | 300 seconds |
| Automatic retry/extension | None |
| Source changes | `research/sim_g3/` and final evidence record only |
| SIM-G2A, SG-0, renderer, ISA, RTL, FPGA changes | Prohibited |

This ratification authorizes one harness implementation pass and its focused handoff tests only. It does not authorize the 300-second qualification campaign, a repository-wide regression, a SIM-G2A/SG-0 source change, or any physical hardware work. Before requesting campaign authorization, freeze harness source hashes, run the focused tests, and present the exact command and evidence paths.

## 8. Evidence interpretation

### Harness implementation pass record

The single authorized harness pass is complete. The focused handoff test command
`python3 -m unittest research.sim_g3.test_handoff -v` passed **6/6**. The CLI
help command `python3 -m research.sim_g3 --help` passed. The bounded SG-0/C++
replay has not been launched.

| Harness file | SHA-256 |
|---|---|
| `research/sim_g3/__init__.py` | `731be69431a2ab0370efa0b1b2d8fcb51fcbf37c109f3de00fd678bbfd9fa173` |
| `research/sim_g3/handoff.py` | `e68a8c69cac32e26578701c6b59d9bd7edb49ed082f785b0d4d2fc8bc34c0f40` |
| `research/sim_g3/__main__.py` | `587c47596cefe58208d8ef1988c89946d4fe2c44cb47ae36ed575953baa42c42` |
| `research/sim_g3/test_handoff.py` | `85a0565b0c6e842af66a9d9cf4ece4c3edfa457bd84ac47a3495b08bae041131` |
| `research/sim_g3/README.md` | `cd6dade9ee88ef7c059a333667873991af2597c4581880fd070a328fcae1bc47` |

The qualification request must use the frozen command and fresh output path in
§7. Any harness-file change after these hashes requires a reviewed contract
amendment and a new focused test result before campaign authorization.

A PASS would show that, for these two frozen SG-0 scenes, the field-preserving schema adapter supplies inputs that the qualified C++ encoder maps to the same T1d packet bytes, and the unchanged C++ T1d renderer produces the same RGB8 payload as SG-0's Python ideal and finite-width software outputs.

It would not show that C++ independently verifies the symbolic proof, reconstructs Quadray geometry, performs exact projection, has depth diagnostics equivalent to Python, executes a programmable GPU ISA, or matches FPGA output. The existing SG-0 depth discrepancies remain visible and are not erased by equal RGB frames.
