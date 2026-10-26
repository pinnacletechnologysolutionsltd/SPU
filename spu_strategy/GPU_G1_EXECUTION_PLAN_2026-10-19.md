# GPU-G1 — Reproducible Graphics Execution and Physical Evidence

Run from the SPU repository root. These are **offline** reproduction commands, executed during preparation; use a fresh output directory for a later reproduction.

```bash
timeout 60s python3 -B -m software.spu_gpu_eval.cli preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/gpu_g1_preparation_20261019_01/ideal_01
timeout 60s python3 -B -m software.spu_gpu_eval.cli device-preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/gpu_g1_preparation_20261019_01/device_01
timeout 10s python3 -B -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle.json --x 320 --y 0
```

**Disposition:** preparation complete; physical execution NOT AUTHORIZED by this plan. No board access, flashing, synthesis, routing, analyzer capture or installed-tool change. Route-D1 I4 continues independently: no edits or execution against its source/backend, no resource reservations or changes to its campaign. SSM-6 is complete within its bounded research scope; RET-4 remains closed; QSG-3 and SIM-CAP1 are separate next work.

## Authoritative checkpoint and reconciled identities

Use the [bring-up runbook](../docs/GPU_BRINGUP_RUNBOOK.md), [physical ledger §§3.37–3.38](../docs/hardware_evidence.md#337--t1g-two-cycle-visual-acceptance-retry-2026-10-07) and [retained provenance](../docs/GPU_RETAINED_ARTIFACT_PROVENANCE_2026-10-14.md). The [portfolio](SPU_PORTFOLIO_REVIEW_2026-10-19.md) provides context; the owner's current tranche ordering supersedes its earlier suggested action order.

| Boundary | Verified or recorded status | Limit |
|---|---|---|
| T1d software scene | `examples/gpu/t1d_two_triangle.json`, SHA-256 `fbe44dd9f21e05a51e544ef88c0cee47c060fd36b7eeb309e38b846bab0566ef`; profile `t1d-two-triangle-v1` | Two triangles, 640×480, RGB444 and bounded depths; host execution |
| T1d packet/frame reproduction, this preparation | Both commands exit 0; generated 64-byte packets equal `fixtures/gpu_t1d_scene_wire_64b.bin`, SHA-256 `aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee`; ideal/device RGB agree at all 307,200 pixels | Not equality of all depths: at (320,0), ideal=2000 and device=1999, both red/primitive 0. No FPGA result |
| T1G operational rollback image | `build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit`; 3,825,930 bytes; SHA-256 `e16dc6992c60de99d9f5d9a5cc10c3aff99a245b5f5da6035887f2c92cb68fa5`, rechecked | Wukong `xc7a100tfgg676-1`, recorded IDCODE `0x3631093`; target pixel clock 25 MHz. No new timing qualification |
| T1G retained source | `build/t1f_clean_qualification_20260922`, commit `a64d87c7ae0d96b44d8178c20f2421376a975ac0`; HEAD rechecked and status empty | Tracked-source identity does not establish full external build-input closure |
| T1G physical checkpoint | October 7 attempt 08: PASS for two operator-confirmed A/B/C cycles, stable VGA lock and six completed 127-byte host writes/drains | Visual switching only; independent packet receipt, internal activation and exact output pixels NOT MEASURED |
| T1H diagnostic | SHA-256 `ec600abe73e847f0846bff5429813cc6913a343b235e215cab5298ebb5d126dd`, rechecked; bounded A/B/C/A visual replay PASS | H1 HOLD; historical dirty source closure incomplete; fringe cause unresolved; 151-byte format. Retain diagnostic, do not select it as GPU-G1 baseline |
| Build/tool reconstruction | Historical T1G build command retained; selected XDC hash recorded in provenance | Actual historical PNR binary hash, chipdb and packing dependency identities unresolved. Launcher version strings are insufficient; rebuild acceptance NOT RUN |

Preparation evidence: [identity and result summary](../build/gpu_evaluation/gpu_g1_preparation_20261019_01/preparation.json), [ideal manifest](../build/gpu_evaluation/gpu_g1_preparation_20261019_01/ideal_01/manifest.json), [device manifest](../build/gpu_evaluation/gpu_g1_preparation_20261019_01/device_01/manifest.json), [pixel inspection](../build/gpu_evaluation/gpu_g1_preparation_20261019_01/pixel_320_0.json). Source/tool identities in these manifests describe this software run; they do not replace missing historical build identities. The read-only identity summary was collected after rendering, not as a prelaunch freeze of the entire dirty repository.

Frozen T1G transactions, rechecked from hex fixture bytes:

| Scene | Fixture under `fixtures/` | Decoded wire SHA-256 |
|---|---|---|
| A | `gpu_t1f_scene_wire_127b.hex` | `78820c1f6da055a3c51eb9ec3709fe027cd1b0a2772093c6e8618a5c300dbe5f` |
| B | `gpu_t1f_coverage_scene_wire_127b.hex` | `861783056fa024a9ac232184c493fc20e2d432f94bff80d0dc14d957ccdfee97` |
| C | `gpu_t1g_scene_c_wire_127b.hex` | `863585de89f3a827e25d12ba262f35dafab93ba05440377fd56cc0f255a3ef7b` |

Each is A5 followed by 126 payload bytes: four 252-bit prepared primitive records, little endian. Source text hashes and current loader/sender/runner hashes are in the preparation summary. Keep packets immutable. Scene C's generator translates A's edge equations by (8,8); do not regenerate in place during preparation. A/B are sufficient for the first discriminating question; C remains available as historical baseline evidence.

## Halt-and-flag finding: the missing correspondence

**Do not send a T1d packet to T1G.** The accepted T1d compiler emits 64 bytes for two primitives; the frozen T1G image consumes 127 bytes for four. T1H adds scalar data and consumes 151 bytes. These are compile-time profiles, not runtime packet-length variants. The [T1f contract](contract_gpu_t1f_family_a_four_primitive_2026-09-22.md) preserves this distinction and does not add a packet CRC. Do not invent a CRC-acceptance claim.

Minimal correction: keep T1d's validated software workflow intact and attach a **T1G-specific offline reference to the already frozen A/B wire records** before claiming correspondence to physical T1G. Do not silently pad, convert or relabel the T1d scene. If a shared high-level scene is later desired, it needs an explicit checked lowering to each profile.

Existing [T1G pacing test](../software/tests/test_gpu_t1g_pacing.py) checks activation and pixels at 80×100 against the current checkout. Its pixel oracle captures derived depth coefficients from the DUT. It is useful regression evidence, but is neither a full 640×480 independent arithmetic reference nor evidence tied automatically to the historical T1G image. Preserve that limitation when reusing it.

## Smallest useful next execution step: offline T1G correspondence

**Proposed bounded implementation scope:** one scene/profile reference slice; no RTL, ISA, transport, fixture or build-flow edits. Use the retained T1G source as read-only authority. A small host-only decoder/reference may reuse existing prepared-scene/depth mathematics where semantics match, but may not change the accepted T1d evaluator.

1. Decode the exact A/B wire records into signed edge equations, colors and depth inputs; retain raw byte identity. Treat prepared records as authoritative inputs; do not claim an unrecorded original vertex scene was recovered.
2. Independently establish expected depth preparation, fixed-width evaluation, tie rule and output projection from the frozen source. Expected values must not come solely from DUT internal coefficient reads. Include background, single-primitive, overlap, tie and A/B-discriminating samples; identify which cases the frozen A/B scenes actually exercise. Any missing case remains NOT COVERED rather than changing the wire fixtures.
3. Produce named reference RGB444 samples and the actual board expectation `R=rgb.r[3], G=rgb.g[3], B=rgb.b[3]`. The physical interface exposes only **RGB111**. It cannot verify the discarded nine color bits or internal depth.
4. Record exact coordinate, frame phase/pipeline alignment and expected output for one A/B-discriminating sample, plus an interior and background control. Select the points from the independently evaluated frozen records, not by guessing from a photograph.
5. Bind results to source, fixture, oracle and ROM hashes in a fresh GPU-only output directory. Negative controls must reject a changed packet byte, wrong primitive order/tie handling and wrong channel projection where the fixture distinguishes them. Keep unexercised controls explicit.

**Acceptance:** unchanged T1d packet/frame/inspection behavior; unchanged frozen T1G hashes; independent expected sample values; exact RGB444→RGB111 projection; explicit source/ROM identity and coverage limits. Hardware equivalence remains NOT RUN. No timing or performance target. Use short foreground software invocations with explicit limits; any job expected to exceed 60 seconds requires the existing detached runner and its governing budget. Coordinate resource availability before running simulation alongside I4.

This preparation request authorizes the plan and completed offline reproduction. The new decoder/reference implementation and its exact commands are a subsequent concrete engineering step, not an implementation claimed by this document. No runnable command for a nonexistent reference tool is supplied.

## Next physical question and measurement decision

**Smallest unresolved physical acceptance question:** after sending frozen B then A to the frozen T1G image, does a settled, sync-aligned output sample that distinguishes them change to the independently predicted A RGB111 value, with the control samples and sync intact?

That would establish sampled physical output correspondence and a scene-dependent change. It would **not** independently prove all packet bytes were accepted, identify an internal bank/generation, or establish every frame pixel. A photograph remains visual evidence only. This is a streaming raster output; do not presume a readable framebuffer exists.

| Desired claim | Additional observation needed | GPU-G1 decision |
|---|---|---|
| Host transmission | Existing sender's exact bytes, positive short-write accounting, drain and pacing transcript | Reuse existing transport unchanged after separate board authorization |
| FPGA receipt/internal activation | Independent decoded acceptance/active-state telemetry or a qualified state readback with freshness and packet/generation binding | Frozen T1G has `GPU_T1D_DIAG=0`; no exposed acceptance channel was established. New instrumented image/readback qualification is separate, not included by assumption |
| Selected exact physical output samples | Qualified observation of R/G/B and HSYNC/VSYNC with sufficient sampling, verified coordinate/phase reconstruction, raw capture and uncertainty criteria | Preferred first physical extension because it can retain the exact T1G image; instrument/readiness and method still need selection and authorization |
| Complete output frame | Lossless, qualified active-pixel capture and independent full-frame RGB111 comparison | Deferred; selected samples cannot establish this |
| Internal RGB444/depth equivalence | Suitable internal instrumentation and independent expected state | Outside the frozen board's RGB111 evidence boundary |

The historical FX2 sustained-stream limitation and the owner's stop on further analyzer captures remain in force. No analyzer probing or replacement capture method is authorized here. A monitor capture/converter with resampling, scaling or color processing cannot be assumed bit-exact. If no qualified output measurement is available, stop at the offline result; do not repeat visual replay and label the gap closed.

## Physical execution gate, acceptance and authorization

The [runbook](../docs/GPU_BRINGUP_RUNBOOK.md) already contains exact loader/demo commands and first-failure rules; they are **inactive reference procedures** after their closed campaigns. Preserve T1G rollback bytes and the existing UART by-id path, 115200 8N1, positive-short-write suffix continuation, bounded drain, 20 ms post-drain delay, ≥31.1 ms start interval and observation pacing. Do not run the old A/B/C demo under a new name to imply fresh authority.

Before any physical attempt, a separate authorization must name: the verified instrument and pins, connection/loading constraints, exact capture/decoder and transport commands, a fresh output path, sample coordinates/alignment, operator readiness, maximum attempts/loads/transactions/captures, per-attempt and cumulative elapsed limits, and rollback/stop actions. No numeric campaign budget is proposed as already granted. Any analyzer use must explicitly resolve the existing owner stop. Any diagnostic image needs separately approved build/verification scope and its own immutable identity.

Physical PASS requires the authorized frozen-image load evidence, exact host byte transcript, valid sync/sample alignment, matching predetermined RGB111 samples for the specified A/B observation, preserved raw measurements and a unique terminal result. Mark internal receipt/activation NOT MEASURED unless independently measured. A mismatch, invalid/ambiguous capture, loss of lock, identity change, timeout or exhausted budget stops the attempt; preserve the failure and do not substitute another image, instrument, packet or retry. Full-frame equality and full rebuild reproducibility remain separate unrun claims.

**Current blocker:** no independent T1G full-resolution reference-to-output correspondence or authorized qualified physical measurement for the frozen image. **Next useful step:** the narrow offline A/B reference slice above. **Authorization:** preparation and software reproduction completed; new physical operations/builds/campaigns are not authorized. No CPU routing campaign, SSM tranche, RET-4 cleanup or generic qualification framework is opened.
