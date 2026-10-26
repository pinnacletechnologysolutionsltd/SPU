# SIM-G2 capability inventory

**Status:** Inventory complete; SIM-G2 implementation not authorized

**Source examined:** standalone `spu-sim` commit `013acd4230442e0e126640604c11176f274962ab`

**Source identity:** clean sibling checkout and the SIM-G1 archived source package

**SIM-G1 evidence:** `build/gpu_evaluation/sim_g1_repro/run_02/replay_manifest.json`

## Current native C++ capabilities

| Area | Implemented in the pinned simulator | Boundary |
|---|---|---|
| SPU software machine | C++17 assembler, bounded `spu13-soft-v1` execution, instruction budget, state snapshots and explicit fault status | The accepted profile has 14 instruction encodings. It is not a general GPU programming environment or cycle-accurate model. |
| T1d rendering | `spu-sim gpu render PACKET --output FRAME [--rom TABLE]`; decodes the fixed 64-byte packet and returns a settled 640×480 RGB8 frame | Exactly two triangle records; uses the reciprocal ROM. No scene JSON, geometry transform, packet generation, retained device state, clock model, or pixel diagnostics are exposed by this command. |
| C++ rendering API | `render_t1d(packet, reciprocal_rom, rgb, error)` is callable through the package library | The caller must already provide the encoded packet and ROM values. |
| Verification | CTest conformance for the pinned SIM-1 profile; SIM-G1 replay matched Python finite-width frames for three frozen packets | Cross-implementation agreement is bounded to the tested profile and scenes. No FPGA equality follows. |

The GPU command is a host-CPU software renderer. It is separate from the SPU
machine instruction loop and does not establish programmable GPU ISA execution.

## Existing geometry-to-packet path outside C++ SIM-1

The Python source provides the preceding stages:

1. `software/spu_gpu_eval/quadray.py` performs exact Quadray normalization,
   coordinate conversion, permutation transforms, rational view projection,
   and ties-to-even pixel/depth quantization.
2. `software/spu_gpu_eval/scene.py` validates the restricted projected-scene
   JSON schema: two nondegenerate triangles, integer screen coordinates,
   16-bit depth, and 4-bit RGB channels.
3. `software/spu_gpu_eval/packet.py` computes oriented edges and encodes the
   64-byte T1d packet.
4. Python reference/device-model paths render or inspect results. The separate
   C++ SIM-1 renderer can consume the resulting packet.

Thus SIM-G1 established packet-to-frame interoperability. It did not establish
a native C++ scene compiler or native Quadray transformation pipeline.

## Missing capabilities relevant to SIM-G2

| Candidate capability | Current status | Consequence |
|---|---|---|
| Parse projected T1d scene data in C++ | Absent | C++ callers need an externally generated 64-byte packet. |
| Encode T1d packets from scene data in C++ | Absent | Packet field validation and edge construction remain in Python or other callers. |
| Apply Quadray transforms and exact projection in C++ | Absent | Exact geometry-to-screen work remains in the Python reference path. |
| More than two triangles or general scene composition | Unsupported by this T1d profile | Requires a separately specified packet/profile change; outside a minimal adapter. |
| Per-pixel coverage/depth/winner diagnostics | Not returned by the C++ CLI | Python workbench remains the inspection path. |
| Programmable GPU execution / compute shaders | Absent | The renderer is a fixed settled-frame software capability. |

The root legacy C++ VM and the C++ Vulkan one-triangle coverage utility are
separate tools. Neither supplies the missing SIM-1 scene-to-packet interface.

## Narrow SIM-G2 candidate

**SIM-G2A — projected-scene-to-T1d adapter (proposal only).** Accept an already
projected scene in a precisely frozen input format, validate it, encode the
existing 64-byte T1d packet, and pass that packet to the existing
`render_t1d` implementation. Keep rasterization, arithmetic, packet layout,
and the current SIM-1 profile unchanged.

This would make native scene submission useful without duplicating the
rasterizer. It would not yet move Quadray transforms or exact projection into
C++; those are a distinct follow-on capability and should be considered only
if SIM-G2A demonstrates a need. The input format and JSON/parser dependency
policy remain open and must be settled in a separate contract.

Proposed evidence for a later SIM-G2A contract:

- Freeze the accepted input schema, field ranges, errors, and output behavior.
- Compare C++-encoded packets byte-for-byte against independently frozen
  Python packet fixtures, including malformed and boundary inputs.
- Feed those packets through the unchanged C++ `render_t1d` path and compare
  complete RGB8 outputs with the existing Python finite-width model.
- Preserve the existing T1d conformance suite and SIM-G1 results; report any
  expanded claim only for explicitly tested inputs.

No implementation, renderer change, ISA/RTL work, FPGA run, or repository
integration is authorized by this inventory. SIM-G2A requires its own reviewed
contract and authorization.
