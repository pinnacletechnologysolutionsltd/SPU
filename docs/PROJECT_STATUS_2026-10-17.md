# SPU project status — 2026-10-17

This page joins five deliverables into one review path. **Demonstrated** means
the linked finite software or build result exists; **pending** means a named
release or gate is incomplete; **proposed** means no implementation is implied.
Hardware timing and board claims remain governed by the [hardware evidence
ledger](hardware_evidence.md).

## Five release deliverables

| Deliverable | Status | Current evidence and completion gap |
|---|---|---|
| [Golden Core research snapshot](GOLDEN_CORE_RESEARCH_SNAPSHOT_2026-10-17.md) | **Demonstrated, bounded** | GC-2A through GC-6 results, fixtures, limitations, and reproduction paths are indexed. GC-2A remains proposed/unratified; its qualification scripts are still in local `/tmp`, so its result cannot be rerun from a clean checkout yet. |
| [Public demonstration path](SUPPORTED_DEMOS.md#quadray-to-golden-core) | **Demonstrated; public review pending** | Browser lessons progress from Quadray to the golden icosahedron to GC-5B dynamics. Python runs the exact Golden Core checks; the optional T1d simulator path is separately identified. No newcomer trial is claimed. |
| [GPU paths](#gpu-paths) | **Physical baseline preserved; software scene demonstrated; clean-checkout review pending** | T1G and T1H images, transport tools, evidence and recovery instructions are retained. T1G bounded visual switching passed; T1H switching passed but H1 remains HOLD. Three Quadray tetrahedron views compile exact geometry into frozen T1d packets and Python/SIM-1 complete frames match byte-for-byte. The newcomer workflow is packaged; independent clean-checkout review awaits immutable source revisions for both repositories. |
| CPU deployment milestone | **Software arithmetic and placement demonstrated; route/FASM pending; timing HOLD** | Surd Register S0 is accepted for its tested software scope. Preserved OpenXC7 placement passed the independent saved-placement audit: 52,090 cells, 80 DSPs, 15,964 LUT mapping checks, and 1,091 adjacent carry links. Both small-fixture preparation attempts failed at ambiguous native PIP adjacency ([failure record](../build/spu_surd_register/backend_compatibility_20261012/openxc7_route_fasm_preparation_20261017/prerequisites_02/fixture/capture_failure.json)); launch gates remain pending, so the authorized full route attempt has not been consumed. No FASM or bitstream is qualified. Timing remains separately unqualified. See [OpenXC7 preparation review](../build/spu_surd_register/backend_compatibility_20261012/openxc7_route_fasm_preparation_20261017/REVIEW.md) and its [packet](../build/spu_surd_register/backend_compatibility_20261012/openxc7_route_fasm_preparation_20261017/packet.json). |
| Simulator release | **Integrated release packaging pending; standalone SIM-1 bounded acceptance passed** | The Python `spu_toolkit-0.2.0` wheel remains a legacy VM candidate with documented example failures. Root-checkout `software/vm/spu_vm` is a separate partial C++ VM with no T1d interface. The standalone C++17 [`spu-sim` SIM-1 repository](../../spu-sim/README.md) implements the accepted bounded `spu13-soft-v1` profile and T1d frozen-scene renderer. Its accepted baseline remains the release conformance scope; the three Golden Core frame comparisons are additional bounded evidence. Release integration and newcomer packaging review remain pending. See [SIM-1 contract and acceptance record](../spu_strategy/contract_spu_sim_sim1_2026-10-15.md), [SIM-0 review](isa/SPU13_SOFT_V1_SIM0_REVIEW_2026-10-15.md), and [platform audit](SPU_PLATFORM_LIBRARY_AUDIT_2026-10-15.md). |

## Immediate release priorities

1. **Complete the clean-checkout demonstration review.** A newcomer should
   obtain both repositories at pinned commits, build SIM-1 using its documented
   CMake commands, run the one-command scene workflow, inspect the PPM, and
   confirm the full-frame comparison. The local workflow passes, but the SPU
   changes are not committed and the SIM-1 checkout has no configured remote;
   a fetchable pair of immutable revisions is not available yet.
2. **Improve graphics usability.** After the newcomer run, prioritize a simple
   output viewer with scene selection and pixel inspection, clear errors for
   unsupported scene features, and one shared packet workflow for Python,
   SIM-1, and any later FPGA replay. A viewer displays outputs; it does not
   replace either renderer.
3. **Select one demonstration-driven capability.** Write its scene contract,
   independent expected results, and simulator checks before considering RTL.
   Do not add a compute backend unless a measured workload calls for it.

As a planning guide, allocate roughly two-thirds of available software effort
to onboarding/release integration and one-third to graphics tooling until the
clean-checkout demonstration is reviewed. CPU route/FASM and timing repairs
remain on their separate track.

## Onboarding entry point

The main SPU repository is the project-wide onboarding gateway. Its
[guided newcomer tour](NEWCOMER_TOUR.md) connects browser lessons, exact Python
checks, and the bounded Python-to-SIM-1 graphics workflow. The standalone
[SIM-1 README](../../spu-sim/README.md) remains the authoritative build and
command guide for SIM-1 itself; it does not cover the wider SPU project. The
clean-checkout review remains pending until both source repositories have
fetchable pinned revisions.

## Public walkthrough: Quadray to Golden Core

1. **Quadray in the browser:** open [`baby_quadray_covariance.html`](../examples/gpu/baby_quadray_covariance.html). The controls expose four coordinates, common-offset gauge equivalence, and labelled orientation changes. Browser JavaScript drives this lesson; it is not the exact Python oracle or an FPGA run. The accompanying [GPU lesson guide](../examples/gpu/README_golden_core_quadray.md) explains exact transforms and the raster boundary.
2. **Golden icosahedron in the browser:** open [`icosahedron_phi.html`](../examples/golden_core/icosahedron_phi.html). The exact coordinate/incidence data and symmetry catalog are frozen from Python, while the camera and pixels use approximate JavaScript projection.
3. **Edge dynamics in the browser:** open [`gc5b_seed_dynamics.html`](../examples/golden_core/gc5b_seed_dynamics.html). It presents the four seeds side by side and reads a frozen exact fixture. The exact evolution runs in Python via `python3 software/tests/test_golden_core_gc5b.py`; the browser is a viewer, not a simulator.

Optional GPU software path: the T1d Python simulator can preview and inspect the
Quadray scene using the commands in the [GPU lesson guide](../examples/gpu/README_golden_core_quadray.md).
This is a finite-width software model; it does not imply that the Golden Core
operator runs on the SPU GPU. No physical GPU result is needed for the Golden
Core demonstrations.

## Simulator release candidate and capability boundary

The current candidate identifier is **`spu_toolkit-0.2.0`**. It is a wheel
identity, not an accepted stable simulator profile. The review records the
clean-snapshot commands and outcomes, but the exact source overlay used for
that snapshot is not packaged as a clean-clone release input. The
[C++ VM release review](isa/CPP_VM_RELEASE_REVIEW_2026-10-15.md) preserves the
source hashes and candidate wheel identity.

| Surface | Demonstrated capability | Unsupported or unqualified |
|---|---|---|
| Python `spu-sim` in `spu_toolkit-0.2.0` | Wheel built and installed in an isolated target. | It remains the legacy Python VM; Quadray Orbit printed raw object representations and Davis Equilibrium exited after SNAP failures in the clean package trial. No stable conformance profile. |
| C++ `software/vm/spu_vm` | Checked instruction subset, build smoke checks, and two examples halt normally. | Separate binary and implementation; incomplete ISA coverage and known width/semantic differences from Python and RTL. |
| Standalone SIM-1 `spu-sim` | Separate C++17 repository implements the owner-accepted bounded `spu13-soft-v1` profile, including a stateless T1d `gpu render` capability; its accepted build, tests and baseline frozen-frame output are recorded in the [SIM-1 contract](../spu_strategy/contract_spu_sim_sim1_2026-10-15.md). | Keep separate from the root-checkout legacy `software/vm/spu_vm` and Python `spu-sim` entry point. The three Golden Core frame matches are additional bounded evidence, not a replacement for the accepted baseline conformance fixture. |
| T1d software capability | Host-CPU scene compiler, exact reference rasterizer, and finite-width software model of the T1d datapath. | No compute-shader execution backend; not a general GPU API, not Golden Core hardware execution, and not physical GPU qualification. |

Standalone SIM-1 has a bounded clean-checkout build/run path for its accepted
profile and T1d baseline. The consolidated project release still needs an
integrated newcomer path that identifies this separate repository alongside
the legacy Python and C++ VMs. Golden Core arithmetic remains an independent
Python research library; the T1d renderer consumes already-compiled scene
packets and does not execute Golden Core evolution.

## CPU deployment gates

Preserve the placed OpenXC7 candidate and use its recorded no-place route/FASM
packet. The current blocker is route-capture correspondence on small fixtures;
do not infer a route/FASM result from the successful placement or from the
native router's exit. The existing budget permits one bounded route attempt
only after all technical preparation gates pass. Timing qualification is a
separate decision and remains **HOLD** regardless of a future FASM result.

Older deployment plans and unsuccessful attempts remain in their dated
`build/` evidence directories and `spu_strategy/` history. This newcomer path
links the current reviewed record and keeps superseded planning material out of
the walkthrough.

## GPU paths

The project has separate physical and software GPU paths. Their evidence is
not interchangeable.

| Path | Demonstrated | Status and next bounded work |
|---|---|---|
| Physical FPGA GPU | Retained Wukong T1G image passed the bounded two-cycle A/B/C visual switching replay. The retained T1H scalar-diagnostic image passed bounded A/B/C/A visual switching. Images, hashes, UART transport tools, campaign records, and recovery steps are retained in the [GPU bring-up runbook](GPU_BRINGUP_RUNBOOK.md). | **T1H H1 remains HOLD.** The historical edge-fringe cause and pixel-level identity are unresolved. Do not infer FPGA packet receipt from host writes. Select any next feature under a separate bounded hardware contract; no hardware action is authorized here. Evidence: [T1G §3.37](hardware_evidence.md#337--t1g-two-cycle-visual-acceptance-retry-2026-10-07) and [T1H §3.38](hardware_evidence.md#338--t1h-scalar-diagnostic-visual-replay-2026-10-07). |
| Software GPU and demonstrations | The frozen T1d scene packet, exact reference renderer, finite-width Python device model, preview/inspect tools, and focused S1/S2/S3 regressions are documented in the [T1d guide](gpu_scene_preview.md). Browser Quadray/icosahedron/GC-5B pages are separate visual demonstrations. Three Quadray views pass exact transforms, rational projection, ties-to-even quantization and T1d packet encoding. Python host-CPU and standalone SIM-1 C++ frames match byte-for-byte for all three. | Reproduce the Python tests and previews using the [Quadray GPU guide](../examples/gpu/README_golden_core_quadray.md); reproduce the C++ comparison using the [SIM-1 frame report](GOLDEN_CORE_T1D_SIM1_COMPARISON_2026-10-17.md). This is software evidence, not physical GPU evidence. T1d supports exactly two triangles, so each frame rasterizes labelled faces ABC and ADC; it is not a closed tetrahedron render. |

The new scene closes a small end-to-end software path, not a general geometry
interface: exact Quadray coordinates and S4 maps → explicit rational view →
ties-to-even pixel/depth quantization → two T1d triangles → frozen packet and
pixel outcomes. The independent test implementation checks projected vertices
against the fixture, then both Python render paths against frozen pixel
expectations. The newcomer runner also compares complete Python and SIM-1 RGB8
frames byte-for-byte for the identity view. The three-view report records
cross-language consistency; matching implementations do not establish
independent correctness or FPGA pixel equality.

| Tool identity | Role in this workflow |
|---|---|
| Python T1d renderer/model | Host-CPU exact reference and finite-width simulation of T1d datapath behavior; does not execute compute shaders. |
| Standalone SIM-1 C++ renderer | Separate C++17 `spu-sim gpu render` T1d packet-to-RGB8 implementation. |
| Root legacy C++ VM | Accepts SAS or VM binary input; has no T1d scene interface. |
| C++ Vulkan utility | Checks one triangle's coverage only; no T1d depth, color, or complete frames. |

The browser Quadray page is a separate interactive visualization. Ordinary
image viewers and graphics APIs can display the saved frame without moving
Golden Core evolution or the T1d software simulation to a compute backend.

## What “GPU support” means here

There are two distinct software meanings. **Simulating the SPU GPU** means
running the bounded T1d rasterizer model on the host CPU: Python provides the
reference and finite-width model, and standalone SIM-1 provides a separate C++
implementation for the frozen packet profile. That path is demonstrated by
the [newcomer workflow](SUPPORTED_DEMOS.md#first-graphics-run-matching-python-and-sim-1-frames).
**Using the computer's GPU to accelerate simulation** means a Metal, Vulkan,
WebGPU, or other compute backend; none is implemented, and the current small
scenes do not require one. A browser or ordinary graphics API may display the
saved images without running the simulation on a GPU. The physical FPGA GPU
path remains separate, with T1H H1 still on HOLD.

The current checkout comparison is not the requested clean-checkout review.
The runner supports expected commit IDs and `--require-clean-checkouts`, but
SPU is dirty (HEAD `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`; an `origin`
is configured) and the separate SIM-1 checkout is clean (HEAD
`013acd4230442e0e126640604c11176f274962ab`) but has no configured remote.
The review remains pending until a newcomer can fetch immutable source
revisions for both repositories and run the pinned command from clean trees.

Keep three C++ identities separate. The root-checkout legacy VM
`software/vm/spu_vm` accepts SAS or VM binary and has no T1d packet/frame
interface. The C++ Vulkan utility `software/gpu_vulkan/gpu_raster_compute.cpp`
accepts one triangle's edge coefficients and reports covered pixels; it does
not model T1d depth, primitive color, or complete frames. The standalone SIM-1
package in `../spu-sim` does expose `gpu render` for the frozen two-triangle
T1d packet profile. On 17 October, its 921,600-byte RGB8 frames matched the
Python finite-width device-model frames byte-for-byte for identity, BCD
rotation, and BC reflection. See the [comparison report](GOLDEN_CORE_T1D_SIM1_COMPARISON_2026-10-17.md).

The exact Python reference and Python finite-width device model both run on the
host CPU; the latter models T1d datapath behavior and does not execute compute
shaders. This comparison is software evidence only. Graphics or browser APIs
can display rendered frames without moving Golden Core evolution or scene
simulation to a compute backend.
