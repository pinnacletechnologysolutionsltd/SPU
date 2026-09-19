# Wukong GPU Checkpoint

Date: 2026-09-11
Status: T1c CLOSED T1c-A; synthesis/P&R not authorized

## T1a completion update

The separately authorized standalone UART scene-loader tranche completed
**T1a-A — PASS** on 2026-09-11. Its two-bank 504-bit control-plane semantics
passed P1/P2 and N1-N6 (966 checks), followed by the mandatory repository gate
at 228 PASS / 0 FAIL. This is simulation-only and establishes neither GPU
integration nor rendered-scene atomicity.

At T1a closure, T1b was still unauthorized. Its unresolved question was how
candidate coverage state and multi-cycle derived depth coefficients could both
be fully prepared before one atomic rendered-scene activation.

### T1b architecture update

The owner subsequently authorized static T1b inspection. It closed **B1 —
Prepared-State Banking**. The minimum boundary is an immutable inactive raw
scene plus tagged `ready0` and `ready1` derived-depth results. The existing
shared dispatcher/arithmetic can be reused; approximately 350 bits of retained
active derived-depth state plus small readiness/generation control are required.

Two integration hazards are frozen for any future contract: active depth must
retain `frac_bits` rather than consume candidate dispatcher output directly,
and the activation edge requires candidate-data bypass because a nonblocking
raw-bank selector change exposes the new bank too late for same-edge setup.
No implementation, synthesis, or physical work is authorized.

## Preserved baseline

- The Wukong Artix-7 100T display path has two recorded silicon observations
  of the depth-resolved two-triangle scene, including one after a confirmed
  power cycle and harness reseat (`docs/hardware_evidence.md` §3.10).
- That image used hardcoded 2D edge/depth coefficients: no runtime geometry,
  transform, projection, shading, framebuffer, or general scene residency.
- Resource evidence for that spin was 7,896 LUTs, 2,419 FFs, 2 DSP48E1s, and
  no BRAM, with 41.36 MHz post-route Fmax against 25 MHz.
- UART receive on F3 is separately silicon-verified by a 20/20 byte echo and a
  zero-stray-byte negative control (`docs/hardware_evidence.md` §3.11).
- `spu_strategy/contract_gpu_pipeline_tranche_2026-09-06.md` remains DRAFT rev
  5 and explicitly halts implementation until its newest changes are reviewed.
- `docs/IVM_GPU_FRONTIER_2026-09-08.md` is a software research finding, not a
  ratified RTL contract. It does not establish an IVM-exclusive or measured
  FPGA advantage.

## Next smallest question

T1a-T1c have answered the control-plane and prepared-state atomicity questions
in simulation. The next smallest question is now:

> What resource and timing cost does prepared-state banking add to the Wukong
> GPU, and does the result still meet the frozen 25 MHz target?

That question requires a separate synthesis/P&R contract. It is not authorized
by this checkpoint.

## Required next gate

Before any build, owner-authorize a bounded synthesis/P&R contract that freezes
the existing Wukong target, 25 MHz timing requirement, baseline comparison,
resource accounting, timeout, and terminal classifications. Bitstream loading,
physical UART, VGA observation, and further features remain separately gated.

## Deferred material research

Procedural, hierarchical/fractal, hybrid residual, and conventional sampled
material backends are recorded as a future research direction in
`docs/WUKONG_GPU_PROCEDURAL_MATERIALS_NOTE_2026-09-11.md`. The smallest proposed
experiment is a deterministic two-colour procedural checker evaluated from
surface coordinates. This work is explicitly outside T1c and remains
unauthorized.

## Post-renderer SOM/GPU division

After the ordinary streaming renderer and prepared-scene path are physically
validated, an SOM processor may serve as the scene and scheduling host while
the FPGA remains responsible for pixel-local work. The SOM (for example an
RP2350) would handle sensor and robotics inputs, scene updates, compact
geometry/material descriptors, and scheduling/control. The FPGA GPU would
handle tile binning, tile-local depth and coverage, interpolation, procedural
material evaluation, and video output.

The intended interface is:

```text
SOM sensor/control data
        ↓
compact scene packets
        ↓
GPU scene banks
        ↓
tile binning and deferred rasterization
        ↓
display or vision output
```

This keeps per-pixel traffic off the SOM link; the SOM sends small scene
descriptions and the GPU expands them locally. Tile-local storage could make
external-memory traffic more predictable and allow updates to touch only
changed objects or material parameters. This is a post-renderer research
direction, not an implementation authorization. The current framebuffer-less
streaming renderer must be benchmarked first; TBDR earns its complexity only
if tile reuse and bandwidth reduction are measurable.

## Prepared-state cost campaign terminal update — 2026-09-13

The owner-authorized matched PS0/PS1 synthesis/P&R campaign stopped **D — TOOL
FAILURE** before synthesis. Its detached repository gate completed at 230 PASS
/ 0 FAIL. PS0 then exited 1 after one second: the GPUVGA synthesis manifest's
premature hierarchy pass removed the unparameterized `spu_gpu_top`, so the
later PS0 board-top `chparam` re-derivation could not resolve that instance.

No PS0 resource or timing result exists, PS1 was not launched, and no packing,
hardware operation, or silicon claim occurred. The unused third campaign slot
does not authorize a repair or replacement run. The minimal proposed flow
correction and evidence pointer are recorded in
`spu_strategy/contract_wukong_gpu_prepared_cost_2026-09-13.md`; any retry
requires a new owner authorization and frozen budget.

## T1c terminal update

T1c Revision 2 implemented the prepared-state banking path and its scoped
simulations passed: loader 968 checks, controller negatives 9 checks, and
integrated P1-P4/N1-N10 876 checks. Existing frame and depth anchor simulations
also passed.

T1c nevertheless closed **T1c-E** because its mandatory detached repository
gate ended at 229 PASS / 1 FAIL. The independent GPU-top integration script has
an explicit RTL source list that omits the three new modules instantiated by
`spu_gpu_top`, so compilation stopped before a new simulation binary was
produced. No prepared-state semantic failure was observed, but T1c-A is not
licensed. Updating that manifest and rerunning verification requires a new
owner gate. No synthesis or physical work occurred.

On 2026-09-12 the owner separately authorized the exact manifest repair and
one independent GPU-top integration run. Adding the three missing T1c source
paths made that test pass across 115,198 pixels with 0 mismatches.

A second detached repository gate then completed at 230 PASS / 0 FAIL,
including GPU Top Integration PASS. The owner explicitly authorized
retrospective use of that run as final mandatory T1c evidence and bounded
reclassification.

**T1c is CLOSED T1c-A — PASS.** The original T1c-E remains preserved as the
historical first terminal result, along with the manifest omission, bounded
correction, focused PASS, and successful second gate. No synthesis or physical

## Prepared-state cost retry reconciliation — 2026-09-19

The separately authorized retry contract
`spu_strategy/contract_wukong_gpu_prepared_cost_2026-09-19.md` supersedes
neither the original D/tool-flow failure nor the T1c result. It records a new
matched PS0/PS1 campaign after the corrected elaboration ordering:

- repository gate: 230 PASS / 0 FAIL;
- PS0: 9,306 cells, 7,900 routed LUTs, 2,428 routed FFs, 45.46 MHz pixel Fmax;
- PS1: 15,941 cells, 12,903 routed LUTs, 3,799 routed FFs, 43.44 MHz pixel Fmax;
- both builds passed the 25 MHz target and PS1 retained the T1c prepared-scene
  hierarchy.

Classification: **A — PASS**, synthesis/P&R evidence only. No bitstream was
loaded and no silicon claim is made. No synthesis or physical
work occurred.
