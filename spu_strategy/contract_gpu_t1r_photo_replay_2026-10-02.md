# Engineering Contract: T1r Photographic UART Replay

**Date:** 2026-10-02  
**Contract ID:** `GPU-T1R-PHOTO-REPLAY-2026-10-02`  
**Status:** ACTIVE — single replay consumed; host writes/drains PASS; photos reviewed, visual HOLD; state labels operator-confirmed  
**Owner:** John Curley  
**Spec Author / Halt-and-Flag Implementer / Integration Auditor:** Codex

## 1. Authorization and scope

Record the owner's instruction: "Patterns changed, let's rerun and I'll take a photo." This renews authorization for one A → B → C → return-A sender invocation. Preserve the previous consumed attempt, photo, and visual HOLD. The owner confirms patterns changed in the first sequence, but has not identified individual states or return-A equivalence.

Use the existing powered SRAM configuration documented in `docs/hardware_evidence.md` §3.30. Confirm continued power/configuration and observer readiness before launch. Do not reload, reset, change wiring, or retry this invocation. Freeze one attempt, 60-second per-attempt timeout, 60-second cumulative budget. An invocation consumes its slot on launch for every outcome. Dwell is 15 seconds between packets to allow photos; final return-A remains displayed after the sender exits.

## 2. Frozen inputs

| Input | Value |
|---|---|
| Bitstream | `build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit` |
| Bitstream SHA-256 | `5df8ac43e5e6c10dc8a8a6b6a369ee2c44b7e73df9e11149f2b30e9f044523d7` |
| Sender | `tools/send_gpu_t1r_scaled_visibility.py` |
| Sender SHA-256 | `b53d567e254790da7e35269159752523b8a1226b6b646693d5377291008a77f9` |
| Fixture | `fixtures/gpu_t1i_scene_a_wire_175b.hex` |
| Fixture SHA-256 | `079a14b7fa4565c86e82311d571ab1b70099e96e598eededa7e8bffa5a0f4143` |
| UART | `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` → `/dev/ttyUSB0`, CH341 `1a86:7523`, 115200 8N1 |
| A / return-A packet SHA-256 | `3719a5925da386fbd14e1ad1ca38139e5f4b68defdbce3e22a9fc8a5daa8ab58` |
| B packet SHA-256 | `43dd87f2bdfd0de0aeaaed13693f446099b6c21688c208659992efdbf6a03bd2` |
| C packet SHA-256 | `71c04abf252893262b7eaed6a2649fd1e3a9abe52a6e008eb3d95dfed7e81f37` |
| Evidence | `build/gpu/t1r_palette_pair_20261002/photo_replay_01/` |

## 3. Preflight and one launch

Run the preserved read-only preflight helper in approved host mount namespace `4026531832`:

```bash
python3 build/gpu/t1r_palette_pair_20261002/photo_replay_01/preflight.py
```

Require exact endpoint/USB identity, frozen hashes, exactly one `COMPLETE` reload marker with exit 0, and the scaled-scene oracle/packet dry-run PASS. Require new launch and transcript destinations. Halt on any mismatch before transmission. Record operator power continuity and readiness in `observer_ready.json`.

The operator confirmed "Yes—still powered and ready now" and then "Yes". `observer_ready.json` preserves that confirmation for 15-second dwells. Host preflight PASS at `2026-10-01T21:00:47Z`; `preflight.txt` SHA-256 `92ae1b6c690ccbabff4978fd58dd79d1d780770415a9d0b13c26f132e9bb6971`. The frozen inputs, endpoint identity, successful reload marker/result, and oracle/packet dry-run matched.

Run exactly once in the same host context:

```bash
timeout 60s python3 tools/send_gpu_t1r_scaled_visibility.py --send \
  --port /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 \
  --dwell-seconds 15 \
  --transcript build/gpu/t1r_palette_pair_20261002/photo_replay_01/sequence_01.json
```

The evidence-only `run_sequence.py` helper executes that exact command and preserves launch identity, operator confirmation, complete stdout/stderr, and exit status. It streams each completed write/drain as an observer cue. It refuses overwrite and records consumption before launch. This is foreground interactive observation, expected under 60 seconds.

## 4. Verification and observations

Require exit 0; four ordered full 187-byte writes; four completed `tcdrain` calls; the §2 packet hashes; and identical A/return-A bytes. Record transcript SHA-256. Preserve photos unchanged with their hashes and operator-supplied state attribution. A shows flat lane colors, B their paired alternatives, C the XOR mixture, and return-A should match initial A. Record stationary blocks, blue lines, and flickering snow separately from broad state transitions. Missing or uncertain states make four-state visibility inconclusive. Photos do not establish exact physical pixel equality or byte-level FPGA acceptance.

No RTL, sender, fixture, or bitstream changes are included. Prior functional, repository, Padé, and route gates remain historical evidence; they do not establish this replay's physical result. Update this contract and `docs/hardware_evidence.md` from the durable transcript and operator/photos, then stop. No additional sender, reload, reset, timeout extension, or substitution is authorized after this outcome.

## 5. Sender result and photographic review

The single command exited 0 at `2026-10-01T21:02:04.673081Z`. `sequence_01.json` records four ordered full 187-byte writes and completed drains. Independent checks passed for the exact §2 packet hashes, packet bytes, identical A/return-A bytes, and three 15-second dwells (15.000135, 15.000143, 15.000159 seconds). `transcript_check.json` preserves the checks. Host write/drain PASS; the invocation is consumed.

`sequence_01.json` SHA-256: `1d157de804b0f33a70d7f41f7bd327a3836c2c948dde7b4ae58f30f9d40051b7`. `sender.stdout.log` SHA-256: `8bd972b2cf88e21002060c924009de4a8e7c223e11f56ad4676892d37d20a958`. `sender.stderr.log` is empty, SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. `sender_launch.json`, `sender_result.json`, and `observer_ready.json` preserve provenance and confirmation. Evidence ledger: `docs/hardware_evidence.md` §3.32.

The operator was cued to photograph A, B, C, and return-A as the write/drain notifications arrived. The expected held state after the final packet is return-A. The previous visual HOLD remains unresolved. No additional hardware action was taken.

The owner supplied `A.jpeg`, `B.jpeg`, `C.jpeg`, and `D.jpeg` in the repository root. They are preserved unchanged under `photos/` in the evidence directory; `photos_manifest.sha256` and `photo_review_01.json` record their file hashes, camera timestamps, dimensions, and decoded-pixel hashes. No original was deleted or renamed by the agent.

| Supplied file | File SHA-256 | Camera DateTime | Visual observation |
|---|---|---|---|
| `A.jpeg` | `0cf7988d5a7d7efbc9423c8130c14f05705435d7a5693137f5e1519d549d842c` | `2026:10:02 10:01:23` | Red/green/pale repeated diagonal blocks across the photographed active area |
| `B.jpeg` | `83ffbbff35e24601d7d6e46f1d3f910c2be7c263ecd0f4054f6f64daabdb0c33` | `2026:10:02 10:01:38` | Cyan/magenta bands and repeated dark blocks |
| `C.jpeg` | `f2a00fd358e0ba0e07fe712cb36eba862f7ac9ec709db6bb3c7f5e7c8275a9bc` | `2026:10:02 10:01:53` | Green/pale repeated blocks, fine colored lines, magenta region at lower right |
| `D.jpeg` | `f0460d7f5017a46b90ff8c433536d0721f17b24b4fb33b2178d064559990c48a` | `2026:10:02 10:01:23` | Same photographed pixels as A |

`A.jpeg` and `D.jpeg` have different file-byte hashes but identical decoded RGB pixel hashes (`f1f1f5f40160628acc82641aa2daba9862e4950537920a5ce2825973feb8d690`) and the same camera timestamp. They represent the same photographed pixels, not independent evidence of initial-A versus return-A. Asked about state attribution, the owner clarified: "Initial and return." Record A as initial-A and D as return-A by operator attribution, preserved in `operator_state_attribution.json`. State labels are resolved by that report; the duplicate pixel data still prevents an independent photographic return-A pass.

The three distinct photographs show broad color/pattern changes under the supplied A/B/C labels, with initial/return labels clarified by the operator. They support a display response during the material sequence; they do not establish byte-level FPGA packet acceptance. All retain repeated full-display patterns rather than the expected bounded triangle. `expected_A.png`, `expected_B.png`, and `expected_C.png` were rendered from the frozen geometry and palette/table oracle for visual comparison. These oracle images are expected software output, not physical captures. Classification: visual HOLD; independent four-state/return-A photographic verification inconclusive. The location and cause of the rendering/display fault remain unresolved. The single replay is consumed; stop hardware work under this contract.
