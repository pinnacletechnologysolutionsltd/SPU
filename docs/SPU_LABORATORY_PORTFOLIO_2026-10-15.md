# SPU Laboratory Portfolio and Priorities

**Date:** 2026-10-15
**Status:** Reviewed planning guidance; locally checked, pending inclusion in the repository documentation audit. This document authorizes no implementation or hardware execution.

## Purpose

The SPU laboratory now spans deterministic arithmetic, symbolic representations,
geometry, graphics, adaptive systems, and hardware architecture. This portfolio
groups work by readiness for independent testing and use. The tiers do not rank
scientific importance.

The immediate risk is spreading limited engineering time across too many
unmatured directions. Prioritize a usable software platform, retain a bounded
physical demonstration path, and make speculative architecture earn promotion
through reproducible comparisons.

## Portfolio tiers

| Tier | Research and engineering areas | Near-term objective |
|---|---|---|
| **Platform engineering** | C++ simulator/SDK, SAS and Lithic-L target profiles, exact arithmetic runtime, deterministic GPU capability, packaging and documentation | Make a pinned, testable SPU software target independently buildable and understandable. |
| **Applied research** | Surd/Quadray kernels, GPU workloads, RPLU/Padé and jets, Soul/SOM, sensor replay and bounded hardware demonstrations | Establish useful workloads, exact baselines, costs, and reproducible evidence. |
| **Fundamental research** | Symbolic-state execution, D4/E8/E9 and higher symmetry, new algebraic structures, architecture hypotheses | Develop independent mathematical/software experiments; promote only when a measured advantage or useful capability appears. |

Audio, robotics, and wearables are demonstrator domains that may use capabilities
from more than one tier. They are not separate architecture commitments.

## Priority order

1. **The developer platform** is the immediate engineering priority. SIM-0's
   `spu13-soft-v1` profile is owner-accepted and pinned. SIM-1 is the next
   principal engineering milestone under its separate owner-accepted,
   bounded implementation contract. The [platform library audit](SPU_PLATFORM_LIBRARY_AUDIT_2026-10-15.md)
   records the source maturity and gaps that motivated this scope.
2. **Deterministic algebraic computing** is the technical foundation. Preserve
   exact, finite-width and domain-specific semantics; benchmark complete
   workloads against conventional implementations before claiming an
   advantage.
3. **The deterministic GPU** is the leading public-facing hardware direction.
   Keep the accepted T1d software capability bounded to its frozen fixture;
   treat later graphics and compute work as separately versioned extensions.
4. **RPLU/Padé and exact algebra** should be evaluated through a small number of
   meaningful end-to-end kernels. Specify representation, scaling,
   reconstruction, singularity behavior, and error budgets at measurement
   boundaries.
5. **Soul/SOM** remains an independent applied software track. First establish
   portable state, checkpoint/replay, and useful prediction or adaptation
   against simple baselines. Do not conflate a classifier, persistent model,
   physical sensor loop, and claims about subjective experience.
6. **Symbolic-state execution** is the highest-upside architectural hypothesis,
   not an established processor advantage. Compare optimized numerical,
   exact SPU, and bounded symbolic/selective-materialization implementations on
   identical workloads, with representation, storage, scheduling, and
   materialization costs included.
7. **Symmetry and higher algebra** remain fundamental research. Keep exact
   oracles and software experiments active; do not require every result to
   become an instruction or FPGA sidecar.

## Promotion rule

Move a capability toward hardware only when it has passed the applicable stages:

1. Mathematical or architectural definition.
2. Independent software oracle and reproducible tests.
3. A useful workload and fair baseline comparison.
4. Standalone RTL and resource/timing qualification under a separate contract.
5. Integrated hardware and public demonstration with evidence appropriate to
   the claim.

A capability may stop at any stage. A library or theoretical result can be a
   successful outcome without hardware implementation.

For a public software-platform release, internal tests alone are insufficient.
An unfamiliar developer must be able to obtain the release inputs, build it,
run a documented example, and inspect the specified results without access to
the research checkout or specialist FPGA tools. The release must identify its
profile, dependencies, fixtures, and expected outputs so that this result can
be reproduced independently.

## Decision register

Update this register at each tranche review. A position summarizes readiness;
the next decision is a gate, not implied authorization to perform the work.

| Workstream | Current position | Next decision |
|---|---|---|
| SIM-1 | Owner-accepted bounded implementation contract; implementation authorized after SIM-0 amendment verification | Deliver the contract's portable `spu13-soft-v1` C++17 simulator and conformance evidence |
| SPU-FABRIC-0 | Phase 1B closed; evaluator integrity PASS; C2 throughput gate FAIL | Defer C3/C4 and physical sharing studies; preserve the [negative result](../spu_strategy/result_spu_fabric_0_phase1b_2026-10-15.md) |
| GPU | Bounded software and hardware demonstrations exist | Choose the scope and evidence gate for the next physical qualification |
| Soul | Synthetic persistent-state experiment; no qualified physical sensor loop | Define a portability experiment with a reproducible checkpoint/replay target |
| RPLU audio | Software sample model and RTL I²S transmitter identified; no Padé-to-PCM contract or PCM5102 board result | Specify the typed signal-generation and PCM conversion boundary |

## Work allocation and gates

Use the proposed planning split as a flexible attention guide, not a measured
resource commitment: 45% platform/software, 30% GPU and bounded FPGA
demonstrations, 15% symbolic processor/shared-fabric research, and 10% Soul,
symmetry, and exploratory mathematics. Include documentation and sustainability
work within platform/software effort. Revisit the split when a tranche closes.

Keep repository boundaries intact until source ownership, build dependencies,
and conformance interfaces are stable. Do not extract a new repository based on
the inventory alone. Continue physical work only under its own accepted scope
and evidence gates.

SPU-FABRIC-0 Phase 1B completed as a software scheduling comparison. Candidate
C2 failed its predeclared SOM throughput gate; the result does not establish
physical resource savings or timing. No fabric follow-up is authorized by this
portfolio. SIM-1 implementation authority and boundaries are recorded in the
separate [SIM-1 contract](../spu_strategy/contract_spu_sim_sim1_2026-10-15.md);
this portfolio records priorities and does not expand that contract.

## Review cadence

At each tranche review, record the deliverable, independent evidence, remaining
gates, and whether the capability should advance, remain in research, or pause.
Update the decision register above and distinguish internal verification from
external reproduction. Prefer closing one useful, externally reviewable
platform increment before opening another major architecture campaign. Existing
documentation warnings remain a separate cleanup backlog; resolving all orphaned
documents is not a prerequisite for SIM-1.
