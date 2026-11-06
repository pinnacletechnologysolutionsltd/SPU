# SPU-13 Documentation Index

Date: 2026-07-05

This directory contains current source-of-truth documents, paper drafts,
hardware evidence logs, and older tactical roadmaps. Prefer updating current
documents instead of deleting historical logs; many older files preserve useful
bring-up context.

## Proposed future directions

- [v0.2 master roadmap](../spu_strategy/SPU_V02_MASTER_ROADMAP.md): proposed programmable platform, demonstrations and release milestones.
- [Post-v0.2 contract architecture](../spu_strategy/POST_V02_STATE_MACHINE_CONTRACT_ARCHITECTURE.md): proposed bounded agent autonomy and evidence-based state transitions.
- [SOUL-AI conceptual research](../spu_strategy/SOUL_AI_CONCEPTUAL_RESEARCH_DIRECTION.md): prospective adaptive intelligence and mathematical claim boundaries.

## Current Source Of Truth

[Public research identity and maturity vocabulary](RESEARCH_IDENTITY.md): shared
definitions for demonstrated results, experimental implementations and exploratory
hypotheses, with comparative utility and evidence boundaries.

[QSG research stages](QSG_RESEARCH_ROADMAP.md): QSG-0–2 bounded software results
and QSG-3 relational machine specification; hardware
adoption remains conditional on separate comparative evidence and authorization.

[Vivado source reconciliation](VIVADO_SOURCE_RECONCILIATION_2026-10-19.md):
historical/current source identities, completed static include inventory and
remaining vendor-elaboration boundary; no implementation run.

Newcomer path: [guided tour](NEWCOMER_TOUR.md) →
[explanation and current claim table](START_HERE.md) →
[supported demos](SUPPORTED_DEMOS.md) →
[project status](PROJECT_STATUS_2026-10-17.md) →
[development status](CURRENT_STATUS.md) → [archived research evidence](archive/bench_sessions/).

| File | Purpose |
|---|---|
| [Newcomer explanation and claim table](START_HERE.md) | Public entry point; selected evidence archive and detailed logs below the explanation |
| [Guided newcomer tour](NEWCOMER_TOUR.md) | Umbrella onboarding path across browser lessons, exact Python checks, and standalone SIM-1; SIM-1's own README remains its component build guide |
| `SUPPORTED_DEMOS.md` | Newcomer path for software, Quadray/Golden Core, and Wukong T1G demonstrations, with claim limits |
| [Project status and release milestone](PROJECT_STATUS_2026-10-17.md) | One page for Golden Core, public demos, CPU deployment, and simulator release status |
| [Symbolic state-machine architecture](SSM_ARCHITECTURE_2026-10-18.md) | Qualified SSM-0–3 software operations, proof semantics, limits, evidence and reuse path |
| [Golden Core research snapshot](GOLDEN_CORE_RESEARCH_SNAPSHOT_2026-10-17.md) | GC-2A through GC-6 results, fixtures, interpretations, limitations, and reproduction commands |
| `CURRENT_STATUS.md` | Short current board status, proof level, and priority list |
| `hardware_evidence.md` | Detailed silicon/RTL evidence ledger |
| `build_and_bringup_guide.md` | Commands, wiring, and board bring-up procedures |
| `GPU_BRINGUP_RUNBOOK.md` | Frozen T1G Wukong recovery procedure and A/B/C observation path |
| `../spu_strategy/gpu_campaign_template.md` | Reusable bounded GPU hardware campaign template |
| `fpga_board_scaling_strategy.md` | Board acquisition and scaling ladder |
| `../spu_strategy/GPU_EVALUATION_ROADMAP_2026-10-03.md` | Versioned GPU software evaluation milestones and development sequence |
| `gpu_scene_preview.md` | T1d user path for previewing and editing a scene, comparing ideal and device-model output, inspecting pixels, and saving a reproducible run |
| `SPU13_IDENTITY_AND_BOUNDARIES.md` | Claim boundaries and public language |
| `ZPHI_KARATSUBA_MULTIPLIER.md` | Three-product Z[phi] multiplier contract and current proof-candidate evidence |
| `ZPHI_KARATSUBA_INTEGRATION_PLAN.md` | Active phased integration, A/B P&R gates, rollback rules, and agent handoff |
| [Surd CPU Lorentz research milestone](SURD_LORENTZ_RESEARCH_MILESTONE_2026-10-11.md) | Focused instruction-executing RTL simulation, application invariants, model counterexample and preserved evidence |

## Proposed Research Contracts

| Review | Status |
|---|---|
| [SG-0 symbolic-to-GPU interface](SG0_SYMBOLIC_GPU_INTERFACE_DESIGN_2026-10-18.md) | Focused software PASS; [qualified local baseline](../research/sg0_baseline_20261018/README.md) preserves source/evidence; full repository suite not run |
| [SSM-4 certified geometric state](SSM4_CERTIFIED_GEOMETRIC_STATE_DESIGN_2026-10-18.md) | Implemented in software; recovery qualification UNAVAILABLE because its terminal marker is absent; [current evidence boundaries](SSM_SG0_CONTINUATION_2026-10-19.md) |
| [Selective observation fixture](../research/selective_observation/README.md) | Experimental software result: five test groups PASS; immutable request/receipt binding, deferred subsets, correlation retention and guarded conversion; shared replay dependencies, no performance or SSM-4 qualification claim |
| [SSM-5 composition and observation fixtures](../research/ssm5/FINDINGS.md) | Preliminary Class A results: two composition and two incremental-observation groups PASS; exact dependency reuse reduces counted kernel work with higher metadata cost; no overall efficiency or architecture qualification claim |
| [SSM-6 certified reuse fixture](../research/ssm6/FINDINGS.md) | Preliminary Class A result: five groups PASS; explicit assumptions, complete dependencies and child-bound certificates; full source checks remain, with no reduced-validation or combined-machine qualification claim |
| [SOM–symbolic interface design](SOM_SYMBOLIC_INTERFACE_DESIGN_2026-10-18.md) | DESIGN ONLY; adaptive candidate ranking separated from exact admission and proof replay; no bridge implementation or campaign |
| [Algebraic–geometric machine direction](ALGEBRAIC_GEOMETRIC_MACHINE_RESEARCH_DIRECTION.md) | PROPOSED AOR/SGN synthesis; five research gates, representation boundaries and end-to-end falsifiers; no unified-machine or RTL execution authorized |
| [SGN-1 research specification](SGN1_RESEARCH_SPECIFICATION.md) | Frozen Phase A definitions and software qualification history; later status in the closeout review |
| [SGN-1 Phase A closeout review](SGN1_PHASE_A_CLOSEOUT_REVIEW_2026-10-13.md) | Mesh/cost qualification COMPLETE/PASS; seven bounded software gates supported; owner closeout decision pending; physical claims excluded |
| [SGN-1 owner decision record](SGN1_PHASE_A_OWNER_DECISION_RECORD_2026-10-13.md) | Original evidence and supplemental diagnostics kept distinct; Phase B deferred until Surd CPU backend legality, integrated routing and 25 MHz qualification |
| [D4/E8 mathematical preparation](D4_E8_MATHEMATICAL_PREPARATION_2026-10-13.md) | Read-only AOR-S1 integration audit, independent exact roots, finite preparation checks and comparative workload plan; no qualification campaign or hardware execution |
| [AOR compact symbolic processor roadmap](../spu_strategy/AOR_SYMBOLIC_PROCESSOR_ROADMAP_2026-10-13.md) | OPEN research programme; qualified Phase A evidence preserved; future symbolic-state tranches PROPOSED, implementation and hardware promotion gated |
| [AOR-S1 canonical product-fragment draft](../spu_strategy/contract_aor_s1_product_fragment_2026-10-13.md) | Exact canonical equality, one-adjustment local rebalance proof and bounded oracle obligations; implementation and execution gated |
| [AOR-S3 workload preparation draft](../spu_strategy/contract_aor_s3_workload_preparation_2026-10-13.md) | Four exact baselines, longitudinal/transverse state and proof-cost accounting; ranges, budgets and acceptance criteria pending |
| [AOR-1 Phase A draft review](AOR1_PHASE_A_DRAFT_REVIEW_2026-10-11.md) | Historical pre-implementation review; consult the roadmap for the subsequent software closeout and continuing research direction |
| [GPU reduction catalogue GCR-1](../spu_strategy/contract_gpu_reduction_catalogue_gcr1_2026-10-12.md) | PROPOSED; three T1d host-model reductions, independent exact/device comparisons and negative controls; execution budget pending |
| [GCR-1 ratification amendment](../spu_strategy/contract_gpu_reduction_gcr1_ratification_amendment_2026-10-12.md) | PROPOSED; C2 adapter, mandatory observable fields, C3 cache rules and staged 6,300-second budget; no code or launch authorization |

| [Padé service-state PSS-1](PADE_SERVICE_STATE_PSS1_REVIEW_2026-10-12.md) | DRAFT; A31 evaluator lifecycle audit and independent software-oracle plan; source-description conflict flagged, execution pending |
| [PSS-1 ratification preparation](../spu_strategy/contract_pade_service_state_pss1_ratification_2026-10-12.md) | HOLD; reviewed source identities confirmed, consumer validity rule and 80-case scenario plan; code and budget not authorized |

## Active Paper Drafts

| File | Purpose |
|---|---|
| `spu13_central_paper.tex` | Foundation SPU-13 architecture paper |
| `rplu_paper.tex` | RPLU v2 paper draft |
| `LUCAS_MAC_PAPER.md` / `LUCAS_MAC_PAPER.tex` | Lucas phinary MAC paper |
| `SU3_COPROCESSOR_PAPER.md` | SU3 coprocessor paper |
| `SU3_PAPER_OUTLINE.md` | SU3 paper outline |

## Current Board / Target Docs

These six now live under `docs/archive/ecp5/`, not at the docs root — paths
below are relative to `docs/`.

| File | Status |
|---|---|
| `archive/ecp5/COLORLIGHT_I9_PINOUT_VERIFIED.md` | Current i9 pinout audit; open-flow P&R passes, hardware smoke pending |
| `archive/ecp5/COLORLIGHT_I9_SETUP_SUMMARY.md` | i9 setup summary with measured RPLU2 synthesis/P&R/bitstream results |
| `archive/ecp5/colorlight_i9_feasibility.md` | i9 feasibility decision; build proof yes, hardware proof no |
| `archive/ecp5/ecp5_vs_artix7_gap_analysis.md` | Missing ECP5 southbridge/result wiring versus Artix |
| `archive/ecp5/ecp5_85k_curated_source_strategy.md` | Curated-source approach for ECP5-85F synthesis/P&R |
| `archive/ecp5/ecp5_evaluator_ee_handoff.md` | EE handoff for future custom ECP5 evaluator |
| `oshwa_application.md` | Pre-certification draft only; not ready to submit |

## Historical / Planning Docs

These are useful but not current sources of truth:

| File | Note |
|---|---|
| `SD_HYDRATION_AUDIT_JUNE28_2026.md` | Point-in-time SD/RP2350/Tang audit |
| `PUBLICATION_REDACTIONS.md` | Exclusions, redactions and retained provenance in this public release |
| `archive/tang25k/tang25k_replacement_bringup_plan.md` | Closed-regression ladder; useful for retest order |
| `rp_mcu_bringup_plan.md` | RP2040/RP2350 bring-up history |

## Parked Research Roadmaps

These documents are non-authorizing. Each requires a new owner-ratified
execution contract before tests, model work, RTL, synthesis, or hardware work.

| File | Status |
|---|---|
| `POST_GPU_LATTICE_RESEARCH_ROADMAP_2026-09-15.md` | GPU-first A3/D4, software SOM allocator, lattice-quantization, reflection-layer, and isolated-hardware decision ladder; the prior SOM tranche remains closed |
| `EXACT_LEARNED_GROUP_PROGRAMS_RESEARCH_NOTE.md` | Non-authorizing E8 finite-word, affine-translation, and bounded-E10 research hypothesis with an initial compilation falsifier |
| `EXACT_GEOMETRIC_COMPUTATION_PRIMER.md` | Non-authorizing overview of exact geometric state, Weyl programs, finite quotients, holonomy, Davis-style cache/gating, and Stage E8-0 |
| `../spu_strategy/contract_spu_d4_root_reflection_probe_2026-09-14.md` | Parked fixed-root D4 hardware probe; no opcode or E8 implementation authorized |

## Update Rules

1. Keep paper, grant, and public claims aligned with `CURRENT_STATUS.md` and
   `hardware_evidence.md`.
2. Mark old tactical plans as historical instead of silently editing the record.
3. Do not claim OSHWA certification until certification is actually granted.
4. Do not quote speed, power, energy, or cost advantages without measured data.
5. When a board target changes, update `CURRENT_STATUS.md`,
   `build_and_bringup_guide.md`, and `fpga_board_scaling_strategy.md` together.
