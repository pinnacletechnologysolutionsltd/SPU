# Engineering Contract: SPU Developer Platform SIM-1

**Date:** 2026-10-15
**Contract ID:** `spu_sim_sim1_2026-10-15`
**Status:** CLOSED — ACCEPTANCE PASS (2026-10-15), bounded to the criteria below
**Spec Author:** Codex
**Halt-and-Flag Implementer:** Owner-assigned C++ implementer after authorization
**Integration Auditor:** Owner-assigned reviewer after implementation

## 1. Objective and scoped files

Create a portable C++17 functional simulator for the owner-accepted
`spu13-soft-v1` profile and its separate T1d graphics capability in a new
`spu-sim` repository. This is the owner-accepted implementation contract for
the bounded SIM-1 work. The owner separately authorized SIM-1 on 2026-10-15,
conditional on resolving the identified SIM-0 vector inconsistency. The
approved correction and repin are recorded in
`docs/isa/SPU13_SOFT_V1_SIM0_AMENDMENT_2026-10-15.md`; its semantic replay and
hash checks passed before implementation begins.

**Target files in the future `spu-sim` repository:**

- `CMakeLists.txt`
- `include/spu_sim/` and `src/` for machine state, instruction execution,
  image loading, snapshots, T1d capability, and CLI
- `tests/` for architectural vectors, loader/fault cases, and T1d output
- `fixtures/` for explicitly pinned small inputs and expected results
- `examples/` for one scalar and one Quadray assembly program
- `README.md` for build/run quickstart

Do not edit the existing `SPU` RTL, generated files, VM candidates, GPU model,
or unrelated repository artifacts under SIM-1.

## 2. Frozen inputs and boundaries

Import these inputs into the new repository as immutable, hash-checked
specification and fixture artifacts before implementation:

| Input | Required identity |
|---|---|
| SIM-0 accepted inputs | `docs/isa/SPU13_SOFT_V1_SIM0_ARTIFACTS_2026-10-15.json` |
| ISA reference pin | `docs/isa/SPU13_SOFT_V1_ISA_SOURCE_PIN_2026-10-15.json` and its exact patch |
| Profile review | The hash recorded in the SIM-0 artifact manifest |
| CPU/loader/GPU vectors | The hash recorded in the SIM-0 artifact manifest |
| T1d packet | SHA-256 `aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee` |
| T1d RGB8 expected frame | 921,600 bytes; SHA-256 `96950fa5610063be28056ab0ff9f198a94bbc38ab9aa48949684592d69de7a10` |

Preserve the specified 14 admitted opcodes, image container, register widths,
exact arithmetic, fetch-time instruction validation, fault atomicity, and
snapshot format. Every execution fault must preserve the complete pre-fault
architectural state: scalar and Quadray banks, PC, flags, return stack, memory,
device state, and retirement count. In v1, flags, data memory, and mapped
devices are empty sets. Report the host fault separately.

Expose T1d as `gpu.scene.t1d.two-triangle-v1`, a separate stateless capability;
do not map it into the CPU address space. Invalid packets return an input error
without returning a partial frame.

## 3. Step-by-step implementation instructions

1. Create the new repository only after separate owner authorization. Import
   the frozen inputs above, preserve their hashes, and record their provenance
   in `fixtures/manifest.json`.
2. Implement only the v1 machine state and admitted instruction semantics.
   Use exact integer arithmetic with checked intermediates; do not use
   floating point in architectural results. Reject unsupported opcodes when
   fetched, not during image loading. Keep failed instruction execution
   transactional so no architectural component changes on fault.
3. Implement the strict 16-byte big-endian image header and exact-length
   validation, instruction-boundary JSON snapshots, deterministic run budgets,
   and stable error names from the SIM-0 review.
4. Implement a small textual assembler for the admitted subset and the
   `spu-sim assemble`, `spu-sim run`, and `spu-sim gpu render` CLI commands.
   Assembly output must use the frozen image format. Do not add a compiler or
   source-language frontend.
5. Implement the T1d packet decoder and finite-width settled-frame output to
   the frozen RGB8 byte contract. Do not add animation, display timing, other
   scenes, programmable graphics, or compute execution.
6. Add literal test vectors for every admitted instruction and each defined
   error class. For every fault, compare full state immediately before the
   instruction and after fault. Include load rejection, reached and unreached
   unsupported/malformed words, aliases, control-flow bounds, and counter and
   stack boundaries.
7. Document a fresh Linux x86-64 clone/build/run path that requires only a
   C++17 compiler and CMake. Keep the implementation portable enough for a
   later AArch64 build, but AArch64/ROCK64 qualification is not a SIM-1 gate.

## 4. Required acceptance commands

Run from the root of the new `spu-sim` checkout, in this order:

```bash
cmake -S . -B build/release -DCMAKE_BUILD_TYPE=Release
cmake --build build/release --parallel
ctest --test-dir build/release --output-on-failure
build/release/spu-sim assemble examples/scalar_quadray.sas -o build/scalar_quadray.spusim
build/release/spu-sim run build/scalar_quadray.spusim --snapshot build/scalar_quadray.snapshot.json
build/release/spu-sim gpu render fixtures/gpu_t1d_scene_wire_64b.bin --output build/t1d.rgb8
sha256sum build/t1d.rgb8
```

Acceptance requires a fresh clone to build without Python, FPGA tools, network
access, or external runtime dependencies; the scalar/Quadray example must
produce its literal expected snapshot; all architectural and fault tests must
pass; and the rendered T1d frame must match the frozen byte count, diagnostic
pixels, and SHA-256. At contract issuance, these commands had not yet been run.
The subsequent bounded acceptance record is in Section 7.

## 5. Exclusions and stop conditions

- No Verilator integration, cycle model, RTL changes, FPGA builds, board
  programming, or hardware operations.
- No instruction-set expansion, data memory, flags, MMIO, device plugins,
  dynamic loading, host fallback, compute shaders, SPIR-V, debugger UI, or
  symbolic extensions.
- No performance claim and no AArch64/ROCK64 qualification claim.
- Halt if source pin reconstruction or hash verification fails; if the
  implementation requires changing accepted semantics; if a fault mutates any
  architectural state; or if the T1d frame differs from the frozen output.
  Report the smallest contract amendment needed before proceeding.
- Preserve all unrelated source trees and working-tree changes. Do not stage,
  commit, publish, or tag without separate authorization.

## 6. Authorization record

SIM-0 is owner accepted, including the audited fixture amendment recorded in
`docs/isa/SPU13_SOFT_V1_SIM0_AMENDMENT_2026-10-15.md`. The owner accepted this
bounded SIM-1 contract and authorized implementation on 2026-10-15, conditional
on the amendment passing semantic replay and hash verification. Those checks
passed before implementation begins. Authorization covers only the files,
features, commands, and acceptance conditions in this contract. It does not
authorize staging, committing, publishing, or tagging.

## 7. Acceptance and closure record (2026-10-15)

**Disposition:** PASS — the bounded SIM-1 acceptance criteria in Section 4
passed. This closes the contract within its stated scope; it does not broaden
the supported profile or the claims permitted by Section 5.

### Execution record

| Item | Result |
|---|---|
| Detached outcome | `COMPLETE`, exit code 0; exactly one terminal marker |
| Attempt and timeout | One attempt; 180-second timeout; no retry |
| Detached unit | `spu-sim1_acceptance_rerun_20261015-20261015T040413Z-890507` |
| Evidence directory | `build/sim1_acceptance_rerun_20261015/` in the SPU repository |
| Working directory | `/home/user/Projects/hardware/spu-sim` |
| Build | Release, `-O3 -DNDEBUG -std=c++17`; GCC 16.2.1; CMake 4.4.4 |
| CTest | 3/3 passed: `spu_sim_conformance`, `sim_check_false_fails`, `sim_check_side_effect_once` |
| Hardware operations | None |
| Source commit | None; the accepted interim provenance is the hashed source manifest below |

The exact ordered acceptance commands are Section 4. The detached invocation
is recorded in `build/sim1_acceptance_rerun_20261015/command.txt`; its stdout,
stderr, terminal marker, result, exit status, tool versions, and launch metadata
are preserved alongside it.

### Frozen identity and outputs

| Artifact | SHA-256 / result |
|---|---|
| 40-file source and fixture provenance manifest at `../spu-sim/build/release/sim1_source_manifest.json` | `74411bd87c51149e717ada9e64c8580d40dd1e6122eb1824289316dc2c92365c` |
| Imported fixture manifest `../spu-sim/fixtures/manifest.json` | `dc26d3fed6577aa9b7b2cb41cdbe2346a6416be43e513e1224ec26b1f4828d4c` |
| Corrected test harness `../spu-sim/tests/test_sim.cpp` | `c82200775a77e2b9d5f3941e1c743c5d4770bc1d102325fbfc21819a822c0f3b` |
| Test registration `../spu-sim/CMakeLists.txt` | `f1ad88fc4c82696d8e23cc3b2cc4aaa3981cd57242daa19d0d7e8a7f0827abd1` |
| Scalar/Quadray expected snapshot | SHA-256 `35d8f0c08bf76eca673b44077a9c899f6214a0044d6bcb55d95cfc415b6a14da` — byte-exact match |
| Assembled scalar/Quadray image | SHA-256 `3f12eee89da4a5801019a7c5be446eac9b2aee627aa9bb71f3e81379084f8d41` |
| T1d RGB8 framebuffer | 921,600 bytes; SHA-256 `96950fa5610063be28056ab0ff9f198a94bbc38ab9aa48949684592d69de7a10` — match |

The acceptance preflight revalidated all 40 source-manifest entries and all 12
imported fixture hashes. The Release executable contained the always-active
`SIM_CHECK` failure diagnostic; the intentional-failure and exactly-once
side-effect probes passed. The full conformance suite and both probes then
passed in the acceptance CTest run.

### Scope of this PASS

This record establishes the accepted `spu13-soft-v1` functional simulator
checks, the frozen scalar/Quadray snapshot, and the frozen T1d framebuffer for
the recorded x86-64 Release environment. It does not establish complete
SPU-13 ISA compatibility, programmable GPU or compute-shader support, cycle
accuracy, FPGA equivalence across all operations, performance, or AArch64 /
ROCK64 portability. It authorizes no commit, publication, or hardware work.
