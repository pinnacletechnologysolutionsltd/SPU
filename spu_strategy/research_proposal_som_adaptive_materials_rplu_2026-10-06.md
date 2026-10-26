# Research Proposal: SOM-Assisted Adaptive Materials with RPLU

Date: 2026-10-06 (Pacific/Auckland)  
Status: **PARKED — research concept only; no implementation or execution is authorized.**

## Purpose

Investigate whether workload classification can choose validated material implementations more efficiently than fixed dispatch or simple rules, while preserving explicitly defined rendering semantics. Reuse existing SPU procedural-material references and SOM/RPLU components where appropriate.

This proposal does not address the current FPGA display/readback fault and does not supersede active GPU contracts.

## Hypothesis

A SOM may identify workload regions where an eligible material implementation costs less. A deterministic eligibility validator and reference fallback can preserve correctness when classification is ambiguous or a proposed variant is unsuitable. Selection must save more than feature extraction, classification, validation, and switching costs.

A successful result would establish a measured application benefit, not general shader synthesis or a failure-proof GPU.

## Proposed architecture

1. Extract a small, frozen feature vector from material parameters and workload properties.
2. Use a fixed SOM to propose a variant ID with winner and runner-up distances and their gap.
3. Use a deterministic validator to check the variant's declared domain, arithmetic limits, and coefficient-table identity.
4. Dispatch a prevalidated implementation; otherwise use the reference implementation.
5. Record selections, fallback reasons, output comparisons, and complete execution cost.

Initially classify at material or batch boundaries, not per pixel. Freeze weights during evaluation. Specify deterministic ties and hysteresis for any later stateful switching. Treat the distance gap as an ambiguity indicator, not a calibrated probability or correctness certificate. Specify out-of-domain rejection separately.

## RPLU role and boundaries

The uploaded `rplu_paper.tex` describes SOM/BMU metadata, deterministic BTU dispatch, an M31 Padé evaluator with unit/non-unit detection, and separately qualified jet arithmetic. These are potential building blocks, not evidence for an integrated adaptive shader.

Initial software selection need not use modular arithmetic. If RPLU arithmetic is evaluated later, specify signed/range encoding, denominator-unit requirements, wraparound, quantization, and output-to-colour mapping. The split finite algebra A₃₁ is not the real Surd field. Exact modular evaluation does not guarantee real-valued accuracy or ordinary distance ordering. Prove metric ordering within a bounded feature domain, or retain an independently validated integer metric.

An explicit non-unit fault may trigger fallback. It does not protect against arbitrary RTL defects, hangs, electrical faults, or corrupt configuration. Recovery and bounded execution require separate mechanisms.

Jets may later supply derivative information for filtering or level-of-detail selection. That extension needs a distinct derivative convention, reference, and cost experiment; it is outside the first study.

## First study: software-only dispatch oracle

Choose one existing procedural material with two independently validated, semantically equivalent implementations. Prefer a material whose Boolean U/V logic admits an identifiable simplification. If no useful second implementation exists, record that result rather than manufacture a performance win.

Freeze the material equation, input domain, edge behaviour, integer widths, and colour mapping. Candidate eligibility can depend on parameters, but every eligible candidate must agree with the independent reference on its declared domain. For a finite, manageable domain, test exhaustively. Otherwise combine algebraic reasoning, boundary tests, and a retained adversarial corpus, and state coverage limits.

Compare:

- Reference/fixed dispatch.
- A simple deterministic rule selector.
- SOM-assisted selection with deterministic validation and fallback.
- Always choosing each candidate where eligible, to expose actual cost differences.

Use separate training and evaluation inputs and retain their hashes. Distinguish synthetic cases from maintained scenes. Report wrong eligibility proposals, fallback rate, ties, unfamiliar inputs, output mismatches, and timing variability. Include corrupted IDs/tables, empty selections, singular denominators where relevant, and rapidly changing workloads as negative or stress controls.

Correctness comes first. Measure selector and material costs separately and end to end, including preprocessing, validation, and switch costs. No speedup is required. If simple rules are equally effective or cheaper, prefer them.

## Deferred functionality generation

The SOM does not infer unspecified shader semantics. A future compiler may compose missing operations from supported primitives only after the requested function, domain, and error policy are explicit. Independently validate generated candidates before making them eligible. Approximate neural materials need a separate quality/error contract; they are not interchangeable with exact procedural materials.

## Evidence and decision criteria

Produce a reproducible software packet with frozen code, inputs, weights, references, complete timings, and limitations. Distinguish correctness, measured benefit, and architectural feasibility.

Proceed beyond software only if a useful advantage exceeds selector overhead across retained evaluation workloads, deterministic fallback is verified, and arithmetic-domain mapping is justified. Reject or archive the approach if rules suffice, workloads are too small, classification costs dominate, or approximate outputs violate the material contract.

Python measurements establish no native throughput, register, ISA, resource-fit, or silicon claim. Hardware integration requires a new reviewed contract and an established GPU baseline. Do not add FPGA synthesis figures from separate images into an integration estimate.

## Activation prerequisites

1. Finish current GPU diagnosis and obtain a reproducible demonstration baseline.
2. Complete relevant software-kernel reviews before adding a maintained subsystem.
3. Inventory existing SOM/material tooling to avoid duplicate frameworks.
4. When priority and evidence justify the study, freeze a bounded execution contract with exact commands, limits, and repair budget.

At activation, identify and hash current repository sources. This proposal remains parked until separately activated.

## Context sources

- Uploaded RPLU manuscript: `rplu_paper.tex`, reviewed 2026-10-06. Its evidence statements have not been independently reproduced here.
- Existing SPU procedural-material and SOM references: identify and hash current repository sources at activation.
- Stanford shader-specialization research: [thesis PDF](https://graphics.stanford.edu/~katokop1/thesis.pdf).
- NVIDIA neural shading implementation (adjacent work, not a SOM equivalence claim): [RTX Neural Shaders](https://github.com/NVIDIA-RTX/RTXNS).
- Khronos robustness boundaries: [Vulkan robustness guide](https://docs.vulkan.org/guide/latest/robustness.html).

These sources motivate investigation; novelty and patent clearance are not established by this proposal.

## Separate C1 software result and promotion gate

The C1 follow-on review reports a production-wrapper-compatible Python candidate with lower same-machine elapsed time on the retained robotics fixtures. Thirteen of 32 retained vector inputs have nonzero Surd coefficients; 19 are rational-only, and all retained joints are rational. The workload therefore exercises Surd-by-rational operations but does not time multiplication where both operands have nonzero Surd coefficients. The simpler unshared boundary-normalized path performed similarly to or better than shared-scale paths. This result is separate from the parked materials proposal and provides no register, ISA, or hardware evidence.

The next C1 step is an implementation review followed by one opt-in robotics integration using the simpler unshared kernel while retaining the original implementation as reference. Promotion is blocked until the repository verification gaps recorded in the C1 closeout are resolved. Do not reopen or rewrite frozen C1 evidence as part of this proposal.
