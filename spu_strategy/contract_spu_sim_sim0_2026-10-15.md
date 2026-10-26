# Engineering Contract: SPU Developer Platform SIM-0

**Date:** 2026-10-15
**Contract ID:** `spu_sim_sim0_2026-10-15`
**Status:** COMPLETE — owner accepted 2026-10-15; SIM-1 contract preparation only
**Spec Author:** Codex
**Halt-and-Flag Implementer:** Assigned reviewer before SIM-1
**Integration Auditor:** Repository documentation gates and owner review

## 1. Commands and scoped output

Run from the SPU repository root:

```bash
git status --short
sed -n '1,180p' knowledge/isa_reference.md
sed -n '1,180p' docs/isa/ISA_CONFORMANCE_2026-10-10.md
sed -n '1,180p' docs/isa/ISA_SOFTWARE_SEMANTICS_2026-10-10.md
sed -n '1,180p' docs/isa/ISA_IMPLEMENTATION_MATRIX.md
sed -n '1,160p' docs/isa/ISA_PROFILE_PROVENANCE.md
sed -n '1,160p' software/vm/spu_vm.cpp
sed -n '1,200p' fixtures/gpu_t1d_scene_reference.json
sed -n '1,220p' software/spu_gpu_eval/scene.py
sed -n '1,220p' software/spu_gpu_eval/device_model.py
sed -n '1,180p' spu_strategy/contract_gpu_evaluation_profile_audit_q0_2026-10-03.md
rg -n "SPU_SIM|SIM-0|SIM-1|conformance|profile" docs knowledge software/vm software/spu_gpu_eval spu_strategy
```

SIM-0 review outputs are the versioned profile review at
`docs/isa/SPU13_SOFT_V1_SIM0_REVIEW_2026-10-15.md` and its machine-readable
vectors at `fixtures/spu13_soft_v1_sim0_vectors.json`. Update these artifacts
and this contract only during review. Do not create a second repository, copy
code, modify RTL, alter generated files, or implement simulator features under
this contract.

## 2. Objective

Freeze the first portable software-machine profile against the existing
canonical ISA-A reference. Define observable architectural state, supported
instruction behavior, program loading, memory and fault behavior, GPU Level 1
compatibility, host requirements, and the conformance evidence required before
SIM-1 implementation begins.

The first public deliverable is a native C++ functional simulator for an
explicitly named subset. It is not a cycle model and does not claim unrestricted
equivalence with RTL or physical hardware. Verilator RTL/cycle execution is a
separate hardware-development mode and is outside SIM-0 implementation scope.

## 3. Initial profile boundary

Use the canonical ISA-A encoding in `knowledge/isa_reference.md` as the
instruction authority. Name the initial software capability profile
`spu13-soft-v1`; keep ISA-B/Wheeler–Feynman and experimental ISA-C separate.
The profile name identifies a versioned software contract, not a claim that all
canonical instructions execute in every implementation.

Admit an instruction to the initial profile only when SIM-0 records its exact
encoding, operand interpretation, state changes, fault behavior, and an
existing or newly specified discriminating conformance vector. An assembler's
ability to emit a word does not establish execution support.

Use the current C++ VM execution surface as the candidate minimum:

| Family | Candidate scope | SIM-0 disposition |
|---|---|---|
| Scalar and control | `LD ADD SUB MUL ROT LOG JMP SNAP HALT CALL RET NOP` | Freeze per-instruction semantics and limits; retain C++ checked-width behavior as an explicit capability boundary. |
| Quadray and exact geometry | `QADD QROT QNORM QLOAD QLOG QSUB QLDI DELTA QREAD` | Freeze operand widths, ordered normalization, aliases, and exact supported domains. |
| Canonical math/geometry extensions | `ROTC SPREAD HEX EQUIL IDNT JINV ANNE` | Freeze only the exact C++-supported subset and record known VM/RTL conflicts as deferred. |
| Unsupported ISA-A operations | `MIN4 REGEN IROTC LOAD2X SCALE2 PHADD PHCFG SOM SOM_TRAIN RATIO_CMP POLY_STEP`, Surd opcodes, and all other unimplemented operations | Require a defined unsupported-operation diagnostic with no partial architectural commit. Do not allocate encodings. |
| GPU Level 1 | Existing T1d two-triangle scene profile | Specify the existing packet and finite-width pixel decisions as a separately versioned device capability; C++ implementation remains SIM-1 work. |

The table is a review starting point. Do not ratify rows that lack source-backed
semantics or a falsifiable vector. In particular, retain the documented
conflicts for scalar overflow domains, ROT/QROT metadata and operand behavior,
ROTC rounding/range, FLAGS/SNAP, SPREAD/JINV operands, reset versus reload,
invalid register indices, and hardware execution support. Resolve each conflict
by excluding the affected operation or by recording an explicit versioned
choice and its compatibility cost. Do not silently change canonical ISA-A.

## 4. Required machine contract

Record all of the following in the SIM-0 reviewed revision:

1. **Identity:** profile name, specification version, binary word width and
   field layout, byte order, assembler/loader format, and compatibility policy.
2. **CPU state:** register counts and widths, reset values, PC and retirement
   rules, flags, stack/call behavior, and snapshot representation.
3. **Arithmetic:** integer coefficient widths, intermediate widths, exact
   operations, overflow outcomes, division/rounding rules, and allowed domains.
   Prohibit floating-point dependencies in architectural results.
4. **Memory and loading:** address width, mapped regions, read/write behavior,
   alignment, program bounds, initial memory contents, load/reset distinction,
   and behavior at invalid or out-of-program fetches.
5. **Errors:** stable error categories for malformed images, unsupported
   instructions, invalid operands/addresses, arithmetic overflow, and device
   errors. Separate container framing validation from instruction validation;
   define whether unsupported instructions fault at load or fetch. Define
   whether each error retires and preserve all pre-instruction
   architectural state on an execution fault: destination and source
   registers, PC, flags, stack, memory, and device state. The terminal host
   diagnostic is outside architectural state.
6. **Determinism:** define the inputs captured by a replay record, state
   snapshot contents, event ordering, and the guarantee that a replay from the
   same profile and initial state produces identical architectural outputs.
7. **GPU Level 1:** identify the T1d scene packet/profile version, accepted
   fields, sample coordinates, coverage and depth rules, finite-width behavior,
   RGB channel representation, framebuffer byte order, and reference vectors.
   Treat timing/display output separately from settled-frame results.
8. **Conformance:** specify vector formats and independent authorities for
   instruction results, errors, memory transactions, state transitions, and
   complete GPU framebuffer hashes. Identify tests as software-only,
   RTL-simulation, synthesis, or physical evidence; do not merge these claims.
9. **Host targets:** require standard C++17 and CMake on Linux x86-64 and
   AArch64 as build targets. Treat ROCK64 execution as a later platform check;
   do not claim it is qualified by desktop compilation.
10. **Capability reporting:** require each runtime target to report the
    profile version and supported capability identifiers. Distinguish native
    execution, host fallback, and unsupported behavior in output and
    benchmarks. SIM-0 specifies static capability registration only; dynamic
    loading is deferred.

## 5. Evidence and decisions

Use these labels in the contract and later conformance reports:

| Label | Meaning |
|---|---|
| `specified` | Versioned behavior is written and internally consistent. |
| `software-tested` | A named software implementation passed named vectors. |
| `rtl-simulation-tested` | A named RTL revision passed a named simulation. |
| `synthesis-tested` | A named build completed for a stated target and constraints. |
| `silicon-observed` | A specific programmed artifact and observation are recorded in `docs/hardware_evidence.md`. |
| `unsupported` | The implementation must return its defined unsupported result. |
| `unresolved` | Evidence or semantics do not establish a stable contract. |

Do not promote Python-oracle agreement with C++ into independent verification
when both implementations share algorithm structure. Preserve the Python
oracle as an independent source only where its derivation is independent; add
literal vectors and mathematical checks for the selected profile. Bind every
fixture to its specification version and source provenance. Do not use the
repository's build archive as a runtime dependency or as an unversioned fixture
source.

## 6. SIM-0 review sequence

1. Re-read the sources listed in Section 1 at the revision used for review.
2. Produce an instruction-by-instruction candidate matrix for
   `spu13-soft-v1`; record encodings, semantics, C++ support, Python support,
   RTL support, tests, and every discrepancy.
3. Trace the T1d profile from packet fixture through parser, finite-width
   device model, mathematical oracle, RTL tests, and hardware evidence ledger.
4. Separate settled-frame GPU behavior from raster/display timing and physical
   output behavior.
5. Write exact state-transition and fault-preservation vectors for the admitted
   CPU subset. Mark unsupported and unresolved behavior explicitly.
6. Freeze binary/container and memory semantics only where existing evidence
   or a deliberate new software-version choice supports them. Mark other
   fields unresolved; do not infer them from a partial VM.
7. Record C++ reuse candidates with file paths, dependencies, license headers,
   and required isolation work. Do not copy or edit those components in SIM-0.
8. Submit the matrix and decisions for halt-and-flag review before opening
   SIM-1 implementation.

## 7. SIM-1 entry criteria

SIM-1 may begin only after the owner accepts the reviewed SIM-0 decisions and
all of these items are present:

- A versioned `spu13-soft-v1` specification with no unresolved behavior in
  its claimed subset.
- An accepted clean source commit or an owner-accepted source hash and diff
  manifest for the canonical ISA reference.
- An explicit list of supported and unsupported instructions and devices.
- A loader/image definition, memory map, deterministic error contract, and
  state snapshot format.
- Frozen CPU conformance vectors with independent expected results and
  negative cases for each defined error class.
- Frozen T1d scene inputs and complete-frame expected hashes, with finite-width
  and tie behavior stated.
- Use the named 64-byte T1d fixture and its 921,600-byte RGB8 hash as the
  initial GPU Level 1 conformance target.
- For every execution-fault class, compare complete pre-instruction and
  post-fault architectural state, including registers, PC, flags, stack,
  memory, device state, and retirement count. Keep host diagnostics outside the
  state equality.
- A C++17/CMake build plan for Linux x86-64 and AArch64, with no Python or FPGA
  tool requirement in the end-user path.
- A source reuse inventory and fixture manifest that excludes build archives.

SIM-1 success is a newcomer building a native C++ simulator, running a program
from the specified image format, rendering a frozen T1d scene, and reproducing
its specified architectural state and framebuffer output on a supported Linux
host. This is a target acceptance statement, not a result claimed by SIM-0.

## 8. Scope boundaries

- Do not add instructions, opcodes, architectural registers, or speculative
  extensions in SIM-0.
- Do not promise unrestricted one-to-one behavior across RTL, cycle timing,
  analog I/O, DDR, FPGA routing, power, or physical boards.
- Do not implement Verilator integration, debugger UI, dynamic plugins,
  programmable graphics, compute shaders, SPIR-V translation, or hardware
  fallback dispatch.
- Do not claim C++ GPU support: current T1d scene parsing and device behavior
  are Python components; their transfer to C++ requires a later implementation
  and conformance review.
- Do not claim ROCK64, FPGA, ASIC, or silicon support from host-side tests.
- Preserve the incoming working tree. Do not stage, commit, move, or clean up
  unrelated files.

## 9. Verification

For this documentation-only contract, run:

```bash
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_spu_sim_sim0_2026-10-15.md
```

The repository-wide, RTL, arithmetic, and synthesis gates are not SIM-0
documentation gates. Run them only if a later change crosses the scopes defined
in `AGENTS.md` §4.1. Owner acceptance recorded in
`docs/isa/SPU13_SOFT_V1_SIM0_REVIEW_2026-10-15.md` closes SIM-0 and authorizes
preparation of a separate SIM-1 contract. It does not authorize SIM-1
implementation. Implementation requires separate owner authorization after
review of that contract.

## 10. Halt conditions

- Halt if the canonical ISA authority, implementation matrix, and existing
  tests give different encodings or observable results for a candidate
  instruction.
- Halt if T1d fixture, oracle, finite-width model, RTL simulation, and recorded
  physical evidence cannot be reconciled for a behavior claimed by the profile.
- Halt if an error case can partially commit architectural state and its
  preservation rule is not specified. Atomicity includes registers, PC, flags,
  stack, memory, and device state.
- Halt if a proposed profile choice would silently reinterpret existing
  canonical words or claim unsupported hardware behavior.
- Report the conflicting sources, exact affected behavior, and the smallest
  decision needed to proceed. Do not patch implementation or evidence under
  this contract.
