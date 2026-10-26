# SPU Graphics Evaluation Roadmap

**Date:** 2026-10-03

**Status:** Decision record and sequenced backlog; implementation contracts remain separate.

**Owner:** John

**Source:** Owner discussion on GPU focus, evaluation software, documentation and bench PCB.

**2026-10-19 public identity:** Adopt the shared
[research identity and maturity vocabulary](../docs/RESEARCH_IDENTITY.md).
Label scoped results Demonstrated, implementations with unresolved utility or
qualification Experimental, and unimplemented hypotheses Exploratory. Keep
correctness, comparative utility and hardware qualification separate. Utility
may concern determinism, exact invariants, verification, energy or total system
complexity as well as speed, with a baseline appropriate to each claim.
Mathematical elegance motivates experiments; independent evidence determines
architectural adoption. These labels change no release gate or campaign budget.

**2026-10-19 research boundary:** [QSG-0: Generative Geometry Research](../docs/QSG0_GENERATIVE_GEOMETRY_RESEARCH.md)
records a frozen software-first scope for SPU-G2: Algebraic Geometry and Dynamics.
Gen 1 qualification and integration remain primary. QSG-0 reserves no hardware
budget and changes no Gen 1 RTL, ISA, pipeline or timing constraints; its
experimental research gate remains 0/5 verified.

The [proposed QSG-0 through QSG-4 stage map](../docs/QSG_RESEARCH_ROADMAP.md)
keeps QSG-0 frozen pending designated review. The owner's revised instruction
authorized QSG-1's reviewed bounded software tranche independently of that
decision; its fixture now passes. Later stages remain research possibilities,
not delivery commitments or Gen 1 dependencies. See the separate
[Vivado reference preparation](../docs/VIVADO_REFERENCE_PREPARATION_2026-10-19.md)
for an independent hardware-tool comparison; implementation budget approval,
tool availability and matched source identity remain prerequisites.

## 1. Start with the offline profile audit

Run from the repository root:

```bash
git status --short
python3 tools/doc_audit.py --json
sed -n '1,200p' fixtures/gpu_t1d_scene_reference.json
sed -n '1,200p' software/tests/test_gpu_t1e_prepared_scene_oracle.py
sed -n '1,200p' software/lib/gpu_depth_v2_oracle.py
sed -n '1,180p' hardware/rtl/gpu/spu_scene_loader.v
```

Execute the read-only scope in
[the Q0 profile audit contract](contract_gpu_evaluation_profile_audit_q0_2026-10-03.md).
Produce its profile/evidence inventory before drafting the scene compiler or
functional simulator implementation contract. Do not launch hardware operations.

## 2. Record the product boundary

| Decision | Required result |
|---|---|
| Focus development on graphics | Every first-release task supports loading, rendering, inspecting or reproducing a GPU experiment. |
| Use deterministic spatial computing as the broader positioning | State workload, arithmetic domain and evidence level for each claim. |
| Release a standalone renderer first | Freeze one GPU profile; CPU and unrelated sidecars are separate targets. |
| Support one FPGA board first | Wukong Artix-7 100T is the candidate; exact revision, pinout, programmer and image need qualification. |
| Start scene loading with the existing UART path | Keep scene preparation independent of transport; qualify a Pico southbridge adapter separately. |
| Treat the scene interface and CPU ISA separately | GPU packets are not SPU instructions. Keep the CPU VM/assembler discoverable without making them graphics prerequisites. |
| Start with a portable software implementation | Add Vulkan or Metal execution backends only after correctness, user need and a measured software bottleneck. |
| Publish open source with a curated release | Users receive matched tools, examples, documentation and qualified hardware artifacts. |

This record updates the product/integration sequence in
[the earlier graphics-first strategy](contract_graphics_first_priority_2026-09-04.md).
Do not apply its full-core coexistence resource threshold as a new requirement
for the standalone evaluation image. Preserve historical measurements,
falsifiers and operational contracts unchanged. This roadmap does not renew
exhausted hardware or expensive verification campaign budgets.

## 3. Preserve the evidence boundaries

Read [the hardware evidence ledger](../docs/hardware_evidence.md), especially
sections 3.31–3.34, before selecting a hardware release artifact. At this record's
date, the latest recorded configuration is UNKNOWN after the programming/startup
anomaly; display acceptance is unresolved. Earlier results retain their stated
artifact and scope. Successful host writes do not establish device acceptance.

Read [the depth-v2 oracle](../software/lib/gpu_depth_v2_oracle.py): reciprocal
normalization includes truncation and reciprocal approximation. Model the
specified finite-width behavior separately from an exact mathematical reference.
Do not describe the whole graphics pipeline as approximation-free.

Read [the repository map](../docs/REPOSITORY_MAP.md) before cleanup. The short
scripts under `software/graphics/` are teaching examples, not complete GPU
models. The existing Vulkan shader covers triangle coverage; it does not model
the complete processor, loader, depth/material paths or display timing.

Report repeatability, cross-build/device agreement, mathematical-reference
agreement and measured cost independently. Do not claim a unique computational
capability, competitive GPU performance, market demand or an energy advantage
without evidence for the named comparison.

## 4. Execute the release sequence

| Stage | Deliverable | Exit criterion |
|---|---|---|
| Q0 — profile audit | One profile/evidence inventory and identified semantic gaps | Fields, ranges, tie rules, truncation, activation and reference dependencies identified from source. |
| S1 — software pilot | One editable two-triangle scene, scene encoder, CPU preview and short tutorial | A changed vertex produces changed validated data and output; independent references discriminate coverage/depth mistakes. |
| S2 — functional device model | Selected-profile packet decoding, arithmetic, materials and scene-update model | Declared finite-width behavior matches scoped RTL observations; ideal-reference differences are reported. |
| H1 — hardware baseline | Known programmed artifact, startup result and stable display | Independent programming/startup, interface and display evidence for the exact supported configuration. |
| H2 — loading diagnostics | Versioned scene transport and diagnostic behavior | Distinguish sent, accepted, rejected and activated states; document recovery from incomplete input. |
| R1 — evaluation release | Tagged source, tools, examples, docs and prebuilt image | An external user previews, edits, loads and diagnoses the supported example without live coaching. |
| R2 — comparison | Optimized conventional baselines with equal correctness requirements | Report resource/latency/throughput and conversion costs; measure energy only with qualified acquisition. |

S1 and H1 can proceed independently. R1 depends on both software and hardware
acceptance. Freeze primitive count, widths, material operations, transport,
resolution and physical colour output before advertising R1.

Send scene descriptions rather than pixel frames. Compile supported vertices,
depth and attributes to coefficients/packets; the FPGA retains scene state and
streams display pixels. Runtime scene changes do not require rebuilding the
FPGA image. Reject unsupported input explicitly; do not silently drop primitives.

## 5. Build the user-facing software and documentation

| Component | Required behavior |
|---|---|
| Scene library/compiler | Validate the selected profile, encode/decode packets, retain source-to-packet identity and conversion rules. |
| Independent reference | Compute named ideal geometric decisions without reusing the device's preparation algorithm. |
| Functional model/viewer | Reproduce device arithmetic; show images and inspect coverage, depth and winner/material decisions. |
| Thin CLI | Preview, inspect, load, capture, compare and report; label unavailable device observations explicitly. |
| RTL simulation launcher | Use Verilog sources for cycle/timing verification; keep it optional for basic preview. |
| Experiment directory | Save input, profile/software/source identity, packet hashes, expected output, observations and separate result dimensions. |
| Examples | Two-triangle overlap, boundary/depth ties, scene replacement and qualified material behavior. |
| Tutorial path | Preview an example, edit a vertex, understand the change, load hardware, collect a diagnostic. |

Keep documentation source in Git and use the existing MkDocs/Pages workflow.
Use the company website for product explanation, demonstrations, downloads and
support links. A company documentation subdomain can serve the same generated
site; do not maintain duplicate technical manuals. Review narrative and diagrams
by hand; test commands and derive interface tables from authoritative sources.

Publish getting-started, capabilities/limits, scene/API, hardware, build,
troubleshooting and evaluation pages with release-specific instructions.
Record tested host environments and dependencies. Keep historical evidence
accessible through the engineering references rather than the introductory path.

### 5.1 Research compile-time reduction before representation changes

**Follow-up research direction (2026-10-05):** explore algebraic reduction and
lossless representation at the host compiler boundary first. This is a research
note, not an implementation contract. Keep the T1d packet, RTL and finite-width
device behavior unchanged until a separate model study and versioned contract
authorize a change.

The scene compiler runs on the host CPU, where more expensive preparation can
be done once. That does not make CPU and GPU transformations interchangeable:
prove each transformation against the semantics of the layer that consumes it.

| Technique | Host CPU/compiler or future CPU/SPU software | GPU path and boundary |
|---|---|---|
| GCD cancellation | Canonicalize rational values and reduce numerator/denominator widths | Reduce geometric coefficients only with the scale retained and interpolation semantics checked. |
| Common-factor extraction | Share a factor across coefficients or a block | The representation must carry the factor and restore its meaning at use. |
| Common-subexpression elimination | Compute repeated preparation or execution expressions once | Count real reuse and include storage/routing cost. |
| Incremental evaluation | Replace repeated evaluation with additions | Edge and depth stepping already exist; prove accumulator width and overflow bounds. |
| Symmetry reduction | Store a representative plus a reversible transform | Use only for supported scene symmetries with exact reconstruction. |
| Lossless packing | Compress stored integers/surd coefficients when the format permits | It saves packet bits only when the wire format encodes the narrower values. |
| Variable-width execution | Could select narrower supported operations; SPU ISA changes are separate work | Could trade lane width against throughput/resources; changing GPU execution widths is a separate hardware experiment. |

For an edge function `f(x,y)=a*x+b*y+c`, dividing all three coefficients of
that edge by a positive common factor preserves its coverage test
`f(x,y) >= 0`. If edge values also act as barycentric numerators, independently
scaling the three edges changes their relative weights. Scaling all three edge
functions of a triangle by the same positive factor preserves ideal normalized
barycentric weights. The T1d depth-v2 path also has finite-width reciprocal
normalization and truncation, so even this shared scaling can change device
results. Check it in the finite-width model before proposing any packet change.

Incremental stepping is already part of the current renderer: edge values
advance by `a` per x step and `b` per y step, and depth uses an affine
accumulator. Treat that as the baseline to measure, not as a new optimization
to claim. For Hyper-Surd values, reduce with `(sqrt(3))^2 = 3` to retain the
two-coefficient form `a + b*sqrt(3)`; a common divisor can be removed only if
its scale is retained.

The first bounded experiment should analyze common factors and repeated
expressions using the existing host-side scene compiler and representative
scenes. Report exact-output preservation, factor/GCD preparation cost, reuse,
coefficient signed widths, accumulator bounds and estimated operation counts.
The current fixed-width T1d packet remains 64 bytes, so smaller coefficients
alone do not reduce its packet size. Compare ideal-reference results and
finite-width device-model results separately, including reciprocal-sensitive
cases. Any encoding or arithmetic change requires its own versioned profile
and acceptance contract. Variable-width execution inside either processor is
a separate hardware experiment.

## 6. Carry out bounded parallel preparation

| Work | Next action | Boundary |
|---|---|---|
| Documentation | Review audit findings and test the graphics onboarding path in a clean environment. | Preserve evidence; do not replace historical results with current totals. |
| Repository hygiene | Inventory callers, tests, generators and evidence before moving anything. | Surgical changes; no broad RTL/ISA refactor or deletion by age. |
| Licensing/contributions | Reconcile directory/file notices and contribution instructions into an explicit component map. | Do not relicense third-party or existing work as incidental cleanup. |
| KiCad learning | Complete a small tutorial, then inspect a working copy of the bench carrier. | Practice does not authorize fabrication or connection to an FPGA. |
| Bench carrier | Reconcile spec/schematic/BOM, qualify the interlock, verify physical footprints, then layout and review. | Existing Rev A board is not orderable; UART is qualified separately from SPI. |
| Community | Publish interface/version rules, compatibility vectors and contributor guidance. | Reuse does not imply automatic support for every board or fork. |

Retain [the carrier handoff](../hardware/pcb/bench_adapter/bench_adapter_spec.md)
and its acceptance evidence. Produce a tested carrier/target adapter only when
it supports the selected graphics setup; it is not a dependency of S1.

## 7. Keep later work out of the first release

Keep CPU-to-GPU execution, full sidecar integration, SU(3), sensing, robotics,
texture/mesh import, general shader compilation, new FPGA boards and Vulkan/Metal
device models in separate later contracts. Maintain existing evidence and code.
Add a feature when it serves a demonstrated graphics use case.

Offer tested kits, training, support, ports and custom integration after R1.
Use external pilots and paid work to validate demand; community uptake is not
itself a revenue result. Keep the free path sufficient to reproduce the example.

## 8. Apply the repository gates

Execute the mandatory commands in [AGENTS.md](../AGENTS.md) before declaring
an implementation complete or committing it. Use the detached runner for work
over 60 seconds; interpret only one durable terminal marker in a later turn.
Hardware diagnosis retains its own owner-authorized contracts and attempt limits.
