# Engineering Contract: GPU Evaluation Profile Audit Q0

**Date:** 2026-10-03

**Contract ID:** `gpu_evaluation_profile_audit_q0_2026-10-03`

**Status:** DRAFT — first recommended implementation-preparation task.

**Spec Author:** Codex

**Halt-and-Flag Implementer:** Next assigned implementer

**Integration Auditor:** Repository gates and owner review

## 1. Commands and scoped output

Run from the repository root:

```bash
git status --short
python3 tools/doc_audit.py --json
sed -n '1,200p' fixtures/gpu_t1d_scene_reference.json
sed -n '1,200p' software/tests/test_gpu_t1e_prepared_scene_oracle.py
sed -n '1,180p' hardware/rtl/gpu/spu_scene_profile_unpack.v
sed -n '1,180p' hardware/rtl/gpu/spu_scene_unpack.v
sed -n '1,180p' hardware/rtl/gpu/spu_scene_loader.v
sed -n '1,180p' hardware/rtl/gpu/spu_prepared_scene_control.v
sed -n '1,200p' software/lib/gpu_depth_v2_oracle.py
sed -n '1,180p' software/lib/gpu_raster_oracle.py
sed -n '1,180p' tools/send_gpu_t1d_scene.py
```

Read dependencies identified by those sources. Produce exactly one new report:
`spu_strategy/GPU_EVALUATION_PROFILE_AUDIT_2026-10-03.md`.
Identify the source revision and hashes of every fixture/source used.
Keep machine inventories/logs under a new child of `build/gpu_evaluation/`.

## 2. Objective

Select the existing two-triangle T1d packet as the initial software-pilot
candidate. Identify enough behavior to draft a bounded scene encoder/preview
contract. Do not infer hardware support from this software selection.

## 3. Invariants and scope

- Read existing RTL, host tools, tests, fixtures and documentation.
- Preserve immutable/generated fixtures; no RTL, generator, protocol or ISA edits.
- Do not run serial/JTAG commands, load bitstreams, change wiring or power-cycle.
- Do not fix discrepancies by choosing a new geometry convention silently.
- Treat mathematical correctness, hardware-semantic agreement and physical
  observation as separate claims. Cite [hardware_evidence.md](../docs/hardware_evidence.md)
  only for its recorded artifact/scope.
- State reciprocal approximation and truncation explicitly. No new claim that
  arbitrary depth decisions are exact, or that coverage implements unverified
  half-open boundary ownership.
- Preserve existing user changes. Do not archive/move files in Q0.

## 4. Required inventory

| Item | Required report fields |
|---|---|
| Packet | Start byte, payload length, byte/bit order, profile selection and all field widths. |
| Geometry | Edge orientation, winding, vertex-to-edge depth association, coefficient ranges and zero-area handling. |
| Coverage | Sample positions, edge inclusion, signed overflow behavior and actual shared-edge rule. |
| Depth | Reciprocal normalization, truncation, fixed-point scaling, saturation/wrap and tie policy. |
| Scene lifecycle | Inactive writes, preparation, activation, ignored bytes, reset and incomplete-packet behavior. |
| Outputs | Internal RGB widths, selected physical RGB output and timing-alignment scope. |
| Reference code | Reusable exact/oracle functions, dependencies and missing behavior; separate independent math from RTL-shaped algorithms. |
| User path | Exact software-only command candidates, dependencies, expected files/output and manual editing points. |
| Evidence | Source/test names and scope; historical versus current physical acceptance. |

## 5. Implementation order

1. Compare packet fixtures, sender checks and RTL unpacking before choosing
   public field names or a scene schema.
2. Trace the selected GPU parameters and preparation/control/depth chain.
3. Reconcile edge/depth conventions across existing tests and references.
4. Identify finite-width behavior missing from current teaching scripts.
5. Record confirmed behavior, discrepancies and unknowns in separate rows.
6. Specify the minimal S1 files and acceptance vectors in the report; do not
   implement them. Include changed geometry, overlap, a depth tie, an invalid
   input and one approximation-sensitive case where justified by the inventory.
7. Link the report to [the evaluation roadmap](GPU_EVALUATION_ROADMAP_2026-10-03.md).

## 6. Verification and evidence

Q0 is a source/evidence review, not a fresh RTL or silicon qualification.
Inspect new Markdown links and run a scoped whitespace check:

```bash
git diff --check -- spu_strategy
python3 tools/doc_audit.py --check links
```

The audit tool scans tracked Markdown only. Inspect the new report's relative
links explicitly; an untracked report is not covered by that tool.
Before completion/commit execute all mandatory gates in
[AGENTS.md](../AGENTS.md), using a detached job for long-running commands.
Record actual gate outcomes; leave unrun dimensions `NOT RUN`.

## 7. Stop conditions

- Flag conflicting packet order, vertex/depth correspondence or arithmetic
  semantics with source locations and the smallest proposed correction.
- Do not resolve the conflict by rewriting RTL or a golden vector in Q0.
- If no existing profile can support the software pilot without changing
  hardware semantics, return the identified blocker and a separate contract.
- Stop after the report and gate interpretation; no hardware action or S1
  implementation follows implicitly from this draft.
