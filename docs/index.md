# SPU documentation

SPU is an experimental computing architecture exploring how exact algebraic
arithmetic, geometric representations and deterministic transformations can
support useful native computational primitives.

The [research identity and maturity vocabulary](RESEARCH_IDENTITY.md) distinguish
demonstrated results, experimental implementations and exploratory hypotheses.
Utility can include exactness, determinism, verification, energy or system
complexity as well as speed; each requires an appropriate baseline.

## Current results

Status at 15 October 2026. These are separate experiments and configurations.

| Work | Established result | Remaining boundary |
| --- | --- | --- |
| AOR-S1 | Software qualification complete | Finite coverage; no hardware, silicon, speedup or energy claim |
| Padé | Build complete; 34.80 MHz tool-reported estimate | Timing qualification pending model coverage/provenance review |
| Surd CPU Packet 06 | Route integrity PASS (independent all-net audit) | Timing HOLD; 40.886 MHz is an unqualified tool estimate; no board result |

## Start here

- [Short introduction and current claim table](START_HERE.md) — the ideas, a worked example and their limits.
- [Capability matrix](CAPABILITY_MATRIX.md) — what is backed by math, host software, RTL simulation, FPGA synthesis or physical hardware, and the **known limitations**.
- [Software quickstart](NEWCOMER_SOFTWARE_QUICKSTART.md) — the reproducible, software-only first run (no board, standard library only).
- [Release readiness](PUBLIC_RELEASE_READINESS.md) — validation record, publication blockers and the recommended release sequence.
- [Contributing](../CONTRIBUTING.md#ways-to-help) — what you can reproduce, review or build; [licensing map](../LICENSING.md); [attribution](ATTRIBUTION.md).
- [About and contact](ABOUT.md) — the project, company and ways to get in touch.

The selected evidence package and detailed logs are linked from the introduction's
[evidence section](START_HERE.md#inspect-the-evidence). The [17 October project status](PROJECT_STATUS_2026-10-17.md)
keeps demonstrated, pending and proposed claims for the then-current workstreams separate. Historical documents
retain their original dates and evidence boundaries.

## Simulator and software

- [Software guide](software_guide.md) — VM, assembler, installed tools and the C++ VM.
- [Your first hour](FIRST_HOUR.md) — programs and simulation.
- [Simulator integration policy](SIMULATOR_INTEGRATION_POLICY.md) — how qualified behavior reaches the reference simulator.
- [ISA conformance report](isa/ISA_CONFORMANCE_2026-10-10.md) and [ISA reference](../knowledge/isa_reference.md).
- [SPU platform library audit](SPU_PLATFORM_LIBRARY_AUDIT_2026-10-15.md) — provenance, maturity and build boundaries.

## Architecture and mathematics

- [What is SPU-13](WHAT_IS_SPU13.md) and [identity and claim boundaries](SPU13_IDENTITY_AND_BOUNDARIES.md).
- [Mathematical foundations](../knowledge/MATHEMATICAL_FOUNDATIONS.md), [lexicon](../knowledge/SPU_LEXICON.md), [ROTC tables](../knowledge/rotc_tables.md).
- [SPU-13 ISA specification](spu13_isa_spec.md), [IROTC specification](IROTC_SPEC.md), [Lucas/Z[φ] oracle](CYCLOTOMIC_FIBONACCI_ORACLE.md).
- [Surd Register paper draft and papers](papers/) — working manuscripts; related-work and timing provenance review remain open.

## Geometry research (experimental)

- [Quadray for programmers](QUADRAY_FOR_PROGRAMMERS.md) and the [guided newcomer tour](NEWCOMER_TOUR.md).
- [Golden Core research snapshot](GOLDEN_CORE_RESEARCH_SNAPSHOT_2026-10-17.md) — bounded exact geometry, symmetry, dynamics, reversibility.
- [QSG research stages](QSG_RESEARCH_ROADMAP.md) — rectangle, intrinsic-constraint and PH-curve results; no native hardware adoption is inferred.
- Relational and hexagonal geometry experiments, each with its test command and limits:
  [PHY-R1](../research/phy_r1/FINDINGS.md) metric-state tensegrity, [PHY-R2](../research/phy_r2/FINDINGS.md) exact cable actuation,
  [PHY-R3](../research/phy_r3/FINDINGS.md) tangent stability, [REL-1](../research/rel1/FINDINGS.md) relational state execution,
  [HEX-C1](../research/hex_c1/FINDINGS.md) certified hexagonal hierarchy, [GEO-I1](../research/geo_i1/FINDINGS.md) integration,
  [NGW-H1](../research/ngw_h1/FINDINGS.md) memory layout (negative result).

## GPU

- [GPU evaluation quickstart (T1d)](gpu_scene_preview.md) and [supported demonstrations](SUPPORTED_DEMOS.md).
- [GPU bring-up runbook](GPU_BRINGUP_RUNBOOK.md) — physical path; T1H H1 is on hold, see the [ledger](hardware_evidence.md#338--t1h-scalar-diagnostic-visual-replay-2026-10-07).

## CPU

- [Surd CPU kernel analysis](SURD_CPU_KERNEL_ANALYSIS_2026-10-07.md) and [oracle review](SURD_CPU_ORACLE_REVIEW_2026-10-07.md).
- Routing status: [Packet 06 audit](hardware_evidence.md#339--packet-06-routed-cpu-integrity-audit-2026-10-15) (timing unqualified),
  [router-policy study](../research/route_alg3/FINDINGS.md) (negative), [Vivado readiness](VIVADO_ENVIRONMENT_READINESS_2026-10-19.md).

## SOM (classification)

- [SOM v1 product contract](SOM_V1_PRODUCT_CONTRACT.md), [result frame](SOM1_RESULT_FRAME.md), [sidecar quickstart](SOM_SIDECAR_QUICKSTART.md),
  [CSV trainer](SOM_CSV_TRAINER.md), [sensor replay](SOM_SENSOR_REPLAY.md).
- [Exact full-domain C99 BMU (SOM-RP0a)](../research/som_rp0/FINDINGS.md), the original [width audit](../research/som_rp0/HALT_RECORD.md)
  and the [RTL repair backlog](../research/som_rp0/RTL_REPAIR_BACKLOG.md).

## Hardware and roadmap

- [Hardware evidence ledger](hardware_evidence.md) — the only place physical claims are recorded.
- [Build and bring-up guide](build_and_bringup_guide.md), [toolchain setup](toolchain_setup.md), [FPGA board scaling strategy](fpga_board_scaling_strategy.md),
  [spin catalog](SPIN_CATALOG.md), [SPU-4 product claims](SPU4_PRODUCT_CLAIMS.md).
- [Current status](CURRENT_STATUS.md) — dated engineering status; the [repository map](REPOSITORY_MAP.md) lists directories.
