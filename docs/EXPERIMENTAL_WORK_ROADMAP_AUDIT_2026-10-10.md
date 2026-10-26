# Experimental and unstarted work: audit and proposed roadmap

Date: 2026-10-10 (Pacific/Auckland). Status: reviewable planning proposal.

This audit reads the current dirty engineering checkout, contracts, implementation
sources and selected retained evidence. It does not authorize a build campaign,
hardware operation, publication, default switch or reopening a closed experiment.
“Implemented” below means code exists; qualification is stated separately.
Historical plans are discovery aids, not the current execution queue.

## Audit findings

| Work | Reconciled status and source | Next useful deliverable |
|---|---|---|
| Exact-digital REGEN backend | Digital pass-through semantics already specified in [Stage A](../spu_strategy/contract_regen_stageA_2026-08-20.md), implemented in [DigitalSurdBackend](../software/tests/regen_emulator.py). Active core instead instantiates the fixed-point reference chain and recovery backend. A selectable lean digital integration is a new proposal. | Reviewed backend-selection contract, exact supported operation subset, block-count/status/commit tests and resource baseline. |
| Scalar/Quadray ISA conformance | Focused repairs qualified; remaining arithmetic, register, status and addressing policies conflict or remain unverified. See [conformance audit](isa/ISA_CONFORMANCE_2026-10-10.md) and [independent-review disposition](isa/ISA_CONFORMANCE_REVIEW_DISPOSITION_2026-10-10.md). | One policy decision table followed by small literal-word and rejection repairs. |
| CPU Surd 0x70–0x77 | Experimental opt-in RTL and assembler exist. Both VMs reject it. Directed qualification covers failures, aliases and injected engine faults; reset cancellation and staging retry remain unverified. | Reset/retry directed fixtures; retain the frozen tuple/zero/status semantics. VM execution is a separate optional contract. |
| Integrated Surd CPU image | Latest inspected selective-REGEN attempt has exactly one TIMEOUT marker, exit 124, 7,200 seconds. Synthesis: 234 DSPs; no route/timing result. [Attempt evidence](../build/spu_surd_register/main_cpu_integration_20261007/selective_regen/integrated_build_04_attempt_01/result.json). | After backend review, a fresh frozen resource/route campaign with explicit attempt and cumulative budgets. |
| Surd lane sharing | Standalone one/two/five-lane comparison and exact normalizer already exist under the [multiply contract](../spu_strategy/contract_surd_mul_unit_arch_compare_2026-10-07.md). CPU uses five wide products. | Matched CPU throughput/resource study only if lean-backend results still leave a concrete capacity or latency problem. |
| SPU-4 Surd portability | Isolated W=16, LANES=1 mapping job has exactly one COMPLETE marker, exit 0; [evidence](../build/spu_surd_register/spu4_portability_20261007/gw5a_w16_lanes1_01/result.json). No SPU-4 product integration follows. | Interpret retained mapping reports before proposing a product ABI or integration. Do not rerun the screen as unstarted work. |
| Unshared robotics kernel | Opt-in software exists; [end-to-end benchmark](../build/spu_lossless_reduction/c1_surd_batch_20261006/followup_benchmark_02/closeout.md) is COMPLETE. Retained workload and synthetic Surd inputs are distinct. | Maintained API review or a separately scoped native implementation comparison, with conversion costs included. |
| Lossless CPU/batch/register studies | Experimental sources and retained results exist; contract headers often still say ACTIVE. C0 original gate is FAILED; later C1 records resolve that history. [C1 contract](../spu_strategy/contract_spu_surd_batch_c1_2026-10-06.md). | Evidence/status reconciliation before proposing promotion. Host timing does not establish device speedup. |
| Lossless scene storage | [R1](../spu_strategy/contract_spu_lossless_storage_r1_2026-10-05.md) is COMPLETE for software scope; device equivalence untested. | Bounded compiler-reduction study against ideal and finite-width models; retain current packets. |
| GPU S1 compiler / S2 model / S3 inspector | S1 and S2 CLOSED; S3 code exists despite ACTIVE header. [S1](../spu_strategy/contract_gpu_scene_compiler_preview_s1_2026-10-04.md), [S2](../spu_strategy/contract_gpu_device_model_s2_2026-10-04.md), [S3](../spu_strategy/contract_gpu_pixel_inspector_s3_2026-10-05.md). Full-top S2 parity remains unverified after its frozen timeout. | Reconcile S3 closure evidence; qualify a selected release profile rather than rebuild these tools from scratch. |
| GPU loading diagnostics and release | [Evaluation roadmap](../spu_strategy/GPU_EVALUATION_ROADMAP_2026-10-03.md) H2/R1 remain release objectives. T1G replay passed within its visual scope; T1H and T1r acceptance gaps remain. [Current status](CURRENT_STATUS.md). | Sent/accepted/rejected/activated diagnostic contract, profile-specific recovery, matched software/image manifest and external-user walkthrough. |
| GPU display/UV diagnostics | Existing implementation and visual results are mixed; signal cause remains unresolved. [Signal diagnostic](../spu_strategy/contract_gpu_t1r_vgafix_signal_diagnostic_2026-10-02.md) is deferred. | One frozen discriminating signal/readback experiment; keep operator observation, host writes and FPGA acceptance separate. |
| CPU-to-GPU execution, texture/mesh import, shader compilation, Vulkan/Metal models | Explicit later work in [GPU roadmap §7](../spu_strategy/GPU_EVALUATION_ROADMAP_2026-10-03.md). | Named user workload and interface/profile contract after baseline release acceptance. |
| Sparse Jet MAC | Explicitly RTL not started; dense RTL and software oracles exist. [Sparse contract](SPARSE_JET_MAC.md). | Review A31 algebra wording and trusted-tag provenance, then dense-equivalence plus issued-multiply-count tests for bounded jet orders. |
| ROTC extended-angle hardware qualification | Catalog and trace surfaces exist; angles 6–35 have no cited silicon qualification in [current status](CURRENT_STATUS.md). Tagged and TDM implementations are separate representations. | Select representation and finite-width policy before an extended-angle board probe. |
| Typestate harness extensions | [ROTC roadmap Phase 4](ROTC_CANONIZATION_ROADMAP.md) and [methods paper](papers/THEOREM_LICENSED_TYPESTATE_PAPER.md) distinguish complete harnesses from planned SOM/BTU/Padé work. | One falsifiable harness on a chosen service with reachable fault, hold and recovery paths. |
| Service composition | Policy says oracle trace outstanding, but [trace source](../software/tests/test_composition_trace.py), retained trace artifact and RTL policy module exist. Broader integration remains unverified. | Reconcile source, retained trace and integration evidence; do not infer permission for shared arithmetic from a stale status line. |
| D4 canonical noisy-input decision P1b | P0/P1 exact synthetic experiments passed. [P1b](../spu_strategy/contract_d4_canonical_decision_p1b_2026-09-29.md) is DRAFT, software execution unstarted by its contract. | Frozen noisy/off-lattice corpus, quantization/tie oracle and matched conventional baseline. |
| D4 root-reflection hardware probe | P0/P1 passed; P2 halted on XDC error. Corrected retry budget pending in [contract](../spu_strategy/contract_spu_d4_root_reflection_probe_2026-09-14.md). | Review corrected constraints and existing attempt accounting before any renewed mapping campaign. |
| D4 structured-head retrieval/fusion | Frozen construction CLOSED; retrieval utility not established. [Fusion closeout](../spu_strategy/contract_d4_structured_head_fusion_p1_2026-09-28.md). | Retain the negative result. A different hypothesis needs a new task and baseline. |
| Learned group programs, latent coupling, adaptive materials | Parked concepts: [group programs](EXACT_LEARNED_GROUP_PROGRAMS_RESEARCH_NOTE.md), [lattice roadmap](archive/bench_sessions/POST_GPU_LATTICE_RESEARCH_ROADMAP_2026-09-15.md), [adaptive materials](../spu_strategy/research_proposal_som_adaptive_materials_rplu_2026-10-06.md). | Optional software falsifier only after naming a useful workload; simple rules and signed permutations are required controls where applicable. |
| SOM coarse monitoring / INA226 | Capture tooling exists; physical task validation pending in [current status](CURRENT_STATUS.md). Previous SOM research closed; hydraulic-pump application gate failed. | Qualified acquisition and frozen physical capture if this application is reprioritized; no post-data gate tuning. |
| Tensegrity active balancing | Proposed primitive FALSIFIED; [active-control contract](../spu_strategy/contract_tensegrity_active_control_2026-09-04.md) BLOCKED. Admission and table transport are separate completed work. | A physically valid actuation/control model and independent oracle before reconsidering RTL. |
| Photonics and WF adapter | Simulation research and experimental adapter remain separate. Old photonic indexes conflict about Model B completion; later bounded studies include completed and negative results. [Compilation boundary](PHOTONIC_REGEN_COMPILATION_CONTRACT.md), [WF study](spu13_isa_spec.md). | Reconcile research status if resumed; no photonic machinery dependency for exact digital CPU qualification. |
| Cyclotomic Fibonacci / jet-ring photonics | [Cyclotomic oracle](CYCLOTOMIC_FIBONACCI_ORACLE.md) COMPLETE, no RTL authorized; [photonic jet ring](PHOTONIC_JET_RING_NOTES.md) shelved. | Named bounded hardware workload before any new implementation. |
| Laminar parser and editor extension | Explicitly planned in [language specification §9](../knowledge/LITHIC_L_LANGUAGE_SPEC.md); its hardware and test-count rows are historical. | Small grammar and canonical assembler lowering contract; syntax tooling can follow. |
| DDR3, cluster, PIO, PCIe and additional boards | DDR bridge planned, Mega top stub in [hardware manifest](../knowledge/HARDWARE_MANIFEST_SPU13.md); board roles and transport sequence in [current status](CURRENT_STATUS.md). | Selected-board requirements, pin/clock/tool support and isolated bring-up plan. Full integration and transports remain separate tranches. |
| Bench carrier / custom ECP5 carrier | Rev A bench PCB must not be fabricated; [Rev B spec](../hardware/pcb/bench_adapter/bench_adapter_spec.md) requires reconciliation and interlock/footprint checks. [Custom carrier](ee_handoff.md) is EE/funding dependent. | Reviewed schematic/BOM/footprints/ERC/DRC and interlock evidence before fabrication. |
| Release provenance and publication | Clean newcomer proposal tested; default-branch publication pending. Artifact catalogue and durable release packages proposed in [artifact plan](REPOSITORY_SETUP_AND_ARTIFACT_PLAN_2026-10-08.md). | Reviewable source slices and immutable profile-specific source/tool/image/evidence manifests. |

## False backlog entries and status debt

The boot FSM is implemented in the active core and documented as end-to-end
implemented in [BOOT_SEQUENCE_FSM.md](BOOT_SEQUENCE_FSM.md); the “RTL is not
started” paragraph in [STATE_MACHINE_HARNESS.md](STATE_MACHINE_HARNESS.md) is stale.
The [Z[phi] integration plan](ZPHI_KARATSUBA_INTEGRATION_PLAN.md) explicitly closes
all phases; do not schedule its older first-phase instructions as new work.
The service-composition trace exists despite “outstanding” wording. S3 and
several completed experiments need evidence-linked closure rather than another
implementation. Historical photonic index pages disagree about both status and
the recovery formula; do not use either as an executable repair specification.

These are documentation findings. This audit does not rewrite their source
documents or certify all retained artifacts against current source hashes.

## Proposed tranches

| Order | Tranche | First reviewable deliverable | Exit condition / dependency |
|---|---|---|---|
| 0 | Status and provenance reconciliation | Evidence-linked status matrix for CPU, GPU and research; identify source snapshots and consumed attempt budgets. | Each selected item names supported scope, authoritative contract and qualification state. Can begin immediately. |
| 1A | Exact-digital CPU backend | Command-first contract for backend selection, supported exact operations, REGEN block/status semantics and fault preservation. | Reviewed contract precedes RTL. Preserve the reference backend as selectable. No guarantee that legacy rounded operations become exact. |
| 1B | ISA policy and rejection | Separate decision sheets for operand/index validation, scalar overflow, rotor representations, status/reset and addressing. Implement the smallest agreed encoding/rejection slice first. | Literal encodings and malformed-input rejection agree across the named supported subsets. No opcode-only migration of ambiguous words. Can proceed alongside 1A planning. |
| 1C | Surd reset/staging qualification | Directed reset-during-load/arithmetic/normalize cases, retry after failure and completion/write-pulse checks. | No stale commit; documented staging lifetime and exactly one completion per accepted operation. Freeze reset policy first. |
| 1D | GPU diagnostics and reproducible release | Choose one profile; inventory existing software/physical evidence; specify loading observations and recovery. | Matched software/image provenance and independent acceptance/activation evidence. Hardware campaign remains separately budgeted. |
| 2A | Lean CPU physical qualification | Fresh matched synthesis/route reports after 1A–1C, then a separately contracted board probe. | Measured DSP/LUT/FF/BRAM and timing for the exact configuration; exact result and fault readback on hardware before silicon claims. |
| 2B | Software workload comparison | Native opt-in robotics/Surd baseline or bounded host compiler reduction, with maintained references. | Exact outputs and total conversion/preparation/execution costs; report neutral or negative outcomes. No encoding changes by implication. |
| 2C | Sparse Jet MAC | Reviewed small-order tag schedule and dense-equivalence/counting testbench. | Value/status equivalence, valid tag provenance and measured issued products; integration only after standalone verification. |
| 3 | Optional research | D4 P1b first; typestate expansion, extended rotor probes or adaptive material selection only for a named need. | Frozen comparator, corpus and falsifier; no architecture promotion based solely on a synthetic PASS. |
| Later | Larger-board integration and transports | Selected Kintex board bring-up/constraints plan; isolated PCIe/DDR tests before service integration. | Known hardware/toolchain and qualified interfaces. Retain working Artix/Tang profiles and rollback artifacts. |

Recommended active portfolio: 1A and 1B as CPU foundations, 1C as qualification,
and 1D as the graphics release track. Keep at most one optional research tranche
active. Sparse Jet MAC is the clearest genuinely new arithmetic RTL candidate,
but it does not resolve the current CPU image bottleneck.

In the inspected CPU synthesis, the reference chain accounts for 130 DSPs,
selected REGEN recovery for 24, and Surd products for 80. Removing the reference
backend could remove the 154-DSP allocation, but a fresh synthesis must establish
the resulting total. Sharing Surd lanes should follow an explicit throughput
requirement and this measurement. Kintex planning can proceed independently;
procurement and integrated timing are not established by this audit.

Every implementation tranche needs a command-first contract, supported subset,
negative controls, required scoped/repository gates and an evidence directory.
Expensive campaigns additionally need frozen maximum attempts, per-attempt
timeouts and cumulative budgets under AGENTS.md. No prior exhausted budget is
renewed by this roadmap.

## Audit validation

Documentation-only validation uses:

```bash
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/EXPERIMENTAL_WORK_ROADMAP_AUDIT_2026-10-10.md
```

The supplied historical count is the documentation gate argument required by
AGENTS.md, not a new regression total. No implementation tests, synthesis,
hardware operations or research experiments are launched by this audit.
