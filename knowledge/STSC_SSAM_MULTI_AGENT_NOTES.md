# STSC, SSAM, and Multi-Agent Resonance Notes

Recovered conversation notes from the Mac-to-Linux migration loss. This document
captures the intended Spatial Topology Synth-Core (STSC) simulator direction,
Self-Stabilizing Associative Memory (SSAM), multi-agent resonance, Global Nguyen
arbitration, and the Lithic-L microkernel library concept.

At recovery time, the current Linux checkout did not contain the referenced
`software/stsc_dev.sas` or `software/stsc_multi_agent.sas` files. Treat the
execution traces below as recovered milestone notes and reconstruction targets
until they are reverified in this repository.

## Recovered Conversation Outline

1. STSC simulator parity: C++ simulator brought into parity with Python v1.4
   and RTL rules, using exact `Q(sqrt(3))` RationalSurd arithmetic.
2. SSAM: a Self-Stabilizing Associative Memory layer based on vector imprinting,
   topological query, and Henosis relaxation.
3. Multi-agent resonance: two 13-axis sectors bind through shared IVM boundary
   constraints and global Davis stability.
4. Global Nguyen arbitration: a memory manager prioritizes the 26 Tang 25K
   BRAM18 blocks using laminar weight and tension velocity.
5. Track A: define a Lithic-L microkernel/standard library so high-level code
   can emit `IMPRINT`, `RESONATE`, `SNAP`, and global stabilization primitives.

## STSC Simulator Milestone

Recovered implementation summary:

- Exact arithmetic: simulator enforces 32:32 integer RationalSurd pairs in
  `Q(sqrt(3))`; float and double primitives are rejected.
- Native Quadray register file: register file handles 4-axis Quadray
  coordinates `(A, B, C, D)` to match SPU-13 hardware lanes.
- Nguyen weight partitioning: real-time heuristic `W = sum Quadrance` maps hot
  nodes to 1-cycle virtual BRAM18 and cold components to streaming memory.
- Davis Law predicate: stability tracking in the execution loop triggers
  Henosis recovery pulses when a cubic leak is detected.

Recovered stress-test report:

- Script: `software/stsc_dev.sas`
- Test length: 1000 steps
- BRAM hits: 242
- Streaming hits: 256
- Henosis recovery pulses: 177
- Goal: high-level synthetic intelligence prototyping using Nguyen weight
  distribution.

Recovered command:

```text
c++ -std=c++17 -O2 -Wall -o software/vm/spu_vm software/vm/spu_vm.cpp
./software/vm/spu_vm software/stsc_dev.sas
```

## SSAM: Self-Stabilizing Associative Memory

The next layer after STSC parity is an associative lattice memory. Instead of a
floating-point Hopfield-style dense matrix, SSAM stores and recalls patterns as
stable vector configurations inside the IVM.

Core idea:

> A corrupted or incomplete input is treated as a topological deformation. The
> Davis Gate detects the deformation, Henosis relaxation restores the nearest
> stable geometric ground state, and the recovered vector becomes the recalled
> pattern.

### Vector Imprinting

Learning/imprinting maps an input pattern into a 13-axis manifold sector:

1. Compute Nguyen weights for the input.
2. Promote dominant features into BRAM18.
3. Store the pattern as a high-priority geometric state.

### Topological Query

Inference/recall feeds a corrupted or incomplete vector through the manifold:

1. Calculate wedge-fraction routing for active lanes.
2. Let the geometry reveal which sector the signal pulls toward.
3. Avoid statistical classification as the first mechanism; use exact structural
   relaxation.

### Henosis Relaxation

Noisy input breaks IVM symmetry and violates the Davis predicate. The simulator
then applies recovery pulses until the manifold returns to laminar state.

Recovered pseudo-assembly:

```text
; ========================================================
; MODULE: ssam_core.sas
; FUNCTION: ENFORCE_ASSOCIATIVE_CONVERGENCE
; ========================================================

LOAD_NOISY_PATTERN:
    FETCH_SD    QR_REG1, NOISY_INPUT_NODE
    CALL        laminar_weight
    CALL        evaluate_bram_promotion

RELAXATION_LOOP:
    CHECK_DAVIS BR_FLAG, QR_REG1
    BRANCH_SET  BR_FLAG, PATTERN_STABILIZED

    COMPUTE_TAU QR_REG2, QR_REG1
    SUB_QR      QR_REG1, QR_REG1, QR_REG2

    CALL        pell_zoom
    JUMP        RELAXATION_LOOP

PATTERN_STABILIZED:
    STORE_BRAM  QR_REG1, STABLE_MEMORY_SLOT
    RET
```

## SSAM Recovered Benchmark

Recovered status:

- Script: `stsc_ssam.sas`
- Vector imprinting: balanced 13-axis configuration imprinted.
- BRAM tiering: hot axes promoted to roughly 40-43 percent BRAM saturation.
- Noise injection: heavy noise `50 + 20*sqrt(3)` injected into one axis.
- Tension spike: manifold tension rose from `49` to `7316`.
- Relaxation: 9 Henosis pulses systematically reduced tension toward the
  stable ground state.
- Arithmetic: no floating-point operations.

Interpretation:

> SSAM is a geometric pattern recall layer. It handles noise as structural
> deformation, not as probabilistic activation.

## Multi-Agent Resonance

After single-sector SSAM, the next milestone is topological binding across
multiple 13-axis sectors.

Core idea:

> Independent SSAM sectors communicate by shared IVM boundary constraints. A
> resolved state in Sector A acts as an exact rational boundary for Sector B.

### Vector Harmonics

When one sector reaches stability, its out-of-plane Quadray vertices become
boundary constraints for neighboring sectors. Data transmission is a geometric
intersection, not a memory copy.

### Multi-Agent Nguyen Weight Competition

With several active sectors, the 26 BRAM18 blocks become a shared hardware
resource. Allocation should consider:

- `laminar_weight`: static structural importance.
- `d_tau/dt`: tension velocity, or how fast a sector is changing.
- `tau`: current manifold tension.

Active relaxation should get fast memory first.

### Global Henosis Predicate

Instead of isolated relaxation loops, a global monitor checks collective
stability across the network. Global convergence occurs when all interconnected
Davis Gates return laminar state.

Recovered pseudo-assembly:

```text
; ========================================================
; MODULE: stsc_multi_agent.sas
; FUNCTION: DUAL-SECTOR TOPOLOGICAL BINDING TEST
; ========================================================

INIT_RESONANT_PAIR:
    CALL    init_canonical_ivm_s0
    CALL    init_canonical_ivm_s1

INJECT_COGNITIVE_DISSONANCE:
    INJECT_NOISE    S0_REG3, DISTORTION_VECTOR_50_20x3

EXECUTE_RESONANT_RELAXATION:
    CHECK_DAVIS     BR_FLAG_0, S0_REG_FILE
    CHECK_DAVIS     BR_FLAG_1, S1_REG_FILE

    CALL            global_nguyen_arbitration
    RESONATE_S0_S1  S0_REG_FILE, S1_REG_FILE
    SNAP_TRACE

    BRANCH_NOT_BOTH_SET BR_FLAG_0, BR_FLAG_1, EXECUTE_RESONANT_RELAXATION
    RET
```

Recovered dual-sector trace target:

```text
[SIM TRACE - STEP 00] Sector 0 tau: 7316 (BRAM) | Sector 1 tau: 0    (SHIM)
[SIM TRACE - STEP 01] Sector 0 tau: 3658 (BRAM) | Sector 1 tau: 842  (BRAM)
[SIM TRACE - STEP 02] Sector 0 tau: 1829 (BRAM) | Sector 1 tau: 421  (BRAM)
[SIM TRACE - STEP 09] Sector 0 tau: 0    (SHIM) | Sector 1 tau: 0    (SHIM)
```

## Global Nguyen Arbitration

The memory manager should not behave like a heavy software scheduler. It should
model a hardware priority arbitration matrix that can later become a Verilog
priority encoder network.

For every active sector:

```text
priority = laminar_weight + current_tension + 2 * tension_velocity
```

The highest-priority sectors receive BRAM18 slots. Lower-priority sectors fall
back to streaming memory.

Reference C++ sketch:

```cpp
enum class StorageTier {
    BRAM18_FULL,
    STREAMING_COLD
};

struct SectorMetadata {
    uint32_t sector_id;
    uint32_t laminar_weight;
    uint32_t current_tension;
    uint32_t tension_velocity;
    StorageTier assigned_tier;
};

class GlobalNguyenArbitrator {
private:
    static const int MAX_BRAM_SLOTS = 26;

public:
    void arbitrate_hardware_resources(
        std::vector<SectorMetadata>& system_sectors
    ) {
        auto priority = [](const SectorMetadata& s) {
            return s.laminar_weight + s.current_tension
                 + (s.tension_velocity * 2);
        };

        std::sort(system_sectors.begin(), system_sectors.end(),
            [&](const SectorMetadata& a, const SectorMetadata& b) {
                return priority(a) > priority(b);
            });

        int allocated_brams = 0;
        for (auto& sector : system_sectors) {
            if (allocated_brams < MAX_BRAM_SLOTS) {
                sector.assigned_tier = StorageTier::BRAM18_FULL;
                allocated_brams++;
            } else {
                sector.assigned_tier = StorageTier::STREAMING_COLD;
            }
        }
    }
};
```

Verification target:

```cpp
GlobalNguyenArbitrator manager;
std::vector<SectorMetadata> network_fabric;

for (uint32_t i = 0; i < 30; ++i) {
    network_fabric.push_back({i, 100, 0, 0, StorageTier::STREAMING_COLD});
}

network_fabric[28] = {28, 1200, 7316, 3658, StorageTier::STREAMING_COLD};
network_fabric[29] = {29, 850,  4100, 2050, StorageTier::STREAMING_COLD};

manager.arbitrate_hardware_resources(network_fabric);
```

Hardware migration note:

> This should map to a pipelined priority encoder / partial-sort network, not a
> general software sort, when moved into RTL.

## Recovered Multi-Agent v1.5 Benchmark

Recovered status:

- Simulator manages two independent 13-axis sectors.
- Total axes: 26, matching 26 physical BRAM18 blocks on Tang Primer 25K.
- Global Nguyen arbitration evaluates `laminar_weight` and `d_tau/dt`.
- `RESONATE` opcode: `0x32`.
- Sector 0 tension spike: `10832`, later `13332` and `13957` during resonance.
- Sector 1 receives propagated boundary effects.
- Output: synchronized dual-layer heartbeat.

Recovered trace:

```text
[SIM TRACE - STEP 11] Sector 0 tau: 16    | Sector 1 tau: 1
[SIM TRACE - STEP 16] Sector 0 tau: 10832 | Sector 1 tau: 2  <-- Noise Injection
[SIM TRACE - STEP 21] Sector 0 tau: 13332 | Sector 1 tau: 3  <-- Arbitration Shift
[SIM TRACE - STEP 26] Sector 0 tau: 13957 | Sector 1 tau: 4  <-- Resonance Active
```

Interpretation:

> The system scales from a single associative cell into a multicellular
> cognitive fabric by using geometric resonance and competitive BRAM routing.

## What "Kernel" Means Here

The SPU-13 does not run on synthetic intelligence. The intended claim is the
opposite:

> Synthetic intelligence runs natively on SPU-13.

The "kernel" is not a Linux-like operating system. It is a small set of
geometric invariants, opcodes, and Lithic-L macros that let programs operate on
manifold sectors.

Mapping from OS concepts to SPU-13 concepts:

| Conventional OS kernel | SPU-13/STSC equivalent |
| --- | --- |
| memory manager | Nguyen weight plus tension-velocity arbitration |
| process scheduler | Henosis relaxation to stable manifold state |
| IPC | `RESONATE` geometric boundary intersection |
| interrupt/context switch | Davis Gate / SNAP boundary check |
| virtual memory | hot BRAM18 tier plus streaming cold tier |

## `stsc_core.li` Library Direction

The Track A goal is a Lithic-L core library, probably named one of:

- `stsc_core.li`
- `laminar.li`
- `spu13_core.li`

It should abstract raw opcodes into compiler-facing primitives.

Candidate API:

```text
sys_imprint(sector_id)
sys_resonate(sector_a, sector_b)
sys_stabilize_all(active_sector_mask)
sys_snap(sector_id)
sys_global_nguyen_arbitrate()
sys_trace_tau(sector_id)
```

Conceptual high-level use:

```cpp
#include "stsc_core.li"

void execute_synthetic_thought_loop() {
    sys_imprint(0);
    sys_imprint(1);

    sys_resonate(0, 1);

    hydrate_input_signal(0);

    sys_stabilize_all(0b11);
}
```

Compiler mapping targets:

| Library primitive | Lowering target |
| --- | --- |
| `sys_imprint(id)` | initialize canonical IVM sector and register with arbitrator |
| `sys_resonate(a, b)` | emit `RESONATE` / opcode `0x32` |
| `sys_stabilize_all(mask)` | loop over Davis Gates and apply `SNAP`/Henosis |
| `sys_global_nguyen_arbitrate()` | update sector-to-BRAM tier assignment |
| `sys_trace_tau(id)` | emit simulator/telemetry trace row |

Do not implement `stsc_core.li` as C++ inline assembly first. That sketch is
useful as an API shape, but the repo already has a Lithic-L/assembler path.
Prefer a real `.li` or `.lith` macro library that lowers through the existing
assembler/compiler.

## Reconstruction Priorities

1. Recreate `software/programs/stsc_dev.sas` as the minimal STSC parity script.
2. Add a C++ or Python simulator test that verifies exact RationalSurd/Quadray
   RF behavior without floats.
3. Recreate `software/programs/stsc_ssam.sas` and a deterministic noisy-pattern
   recall trace.
4. Recreate `software/programs/stsc_multi_agent.sas` with two sectors and
   `RESONATE` as a symbolic opcode or assembler macro.
5. Add `stsc_core.li`/`laminar.li` as a Lithic-L library layer, then wire the
   compiler lowering for `sys_resonate`, `sys_imprint`, and
   `sys_stabilize_all`.
6. Only after the scripts pass in simulation, translate Global Nguyen
   arbitration into RTL.

