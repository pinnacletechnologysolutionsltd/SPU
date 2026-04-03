# SPU-13 vs. SPU-4: Architectural Comparison

The Sovereign Processing Unit (SPU) ecosystem is built on a "Mother-Satellite" relationship, where geometric integrity scales from 4-dimensional Euclidean quadrays to 13-dimensional recursive manifolds.

## 1. Core Architecture

| Feature | SPU-4 (Satellite) | SPU-13 (Cortex/Mother) |
| :--- | :--- | :--- |
| **Axis Dimensionality** | 4-Axis Quadray ($4\text{D}\pm$) | 13-Axis Collective Manifold ($13\text{D}$) |
| **Word Size** | 64-bit State (4 x 16-bit Q8.8) | 832-bit State (13 x 64-bit RationalSurd) |
| **Logic Field** | $\mathbb{Q}(\sqrt{3})$ (Rational Trig) | $\mathbb{Q}(\sqrt{3}, \Phi)$ (Golden Ratio Manifolds) |
| **Primary ALU** | Folded Euclidean (Circulant Matrix) | Recursive Berry Gate & Janus Mirror |
| **Goal** | Local Bio-Resonant Sensing | Global Collective Integrity |

## 2. Instruction Sets (ISA)

### SPU-4 (Euclidean ISA)
- **Format**: 24-bit fixed (8-bit Op, 8-bit Dest, 8-bit Src/Imm).
- **Philisophy**: Minimalist and deterministic to fit in low-gate iCE40 FPGAs.
- **Key Op**: `QROT` (Rational Rotation) - maintains magnitude with zero drift.

### SPU-13 (Sovereign ISA)
- **Format**: Variable-length VLIW (Very Long Instruction Word).
- **Philosophy**: Orchestrates the "Bloom" of the entire manifold cluster.
- **Key Op**: `JPER` (Janus Permutation) - flips the manifold state across the IVM lattice.

## 3. How Intrinsics Work

Intrinsics are C/C++ wrappers around specialized SPU machine code instructions. They allow developers to use "Bunker-Hardened" logic without writing raw assembly.

### The Mechanism:
1. **Type Safety**: The compiler treats `q4_vector` (SPU-4) and `m13_manifold` (SPU-13) as native types.
2. **Inline Assembly**: The header file uses `__asm__ volatile` blocks to map the function call directly to a single SPU instruction word.
3. **Register Constraints**: The compiler handles moving C-variables into the SPU's register file (R0-R7 for SPU-4, Collective Banks for SPU-13).

### Example (SPU-4):
```c
static inline q4_vector spu_qrot(q4_vector v) {
    q4_vector result;
    // Map to SPU-4 opcode 0x45 (QROT)
    __asm__ ("qrot %0, %1" : "=r"(result) : "r"(v));
    return result;
}
```

## 4. Does SPU-13 have intrinsics?

**Yes.** The SPU-13 intrinsics are significantly more powerful. While SPU-4 intrinsics handle simple 4D math, SPU-13 intrinsics (defined in `spu13_intrinsics.h`) manage high-level topological operations:
- `spu13_bloom()`: Triggers the Fibonacci-stepped power-up sequence.
- `spu13_mirror()`: Synchronizes the "Janus Mirror" state with the satellite cluster.
- `spu13_snap_all()`: Asserts a global 15-Sigma Snap across all 13 axes.

This "Geometric SDK" ensures that a developer writing code for the "Bunker" doesn't need to understand the underlying circulant matrix math—they just need to call the appropriate geometric intrinsic.
