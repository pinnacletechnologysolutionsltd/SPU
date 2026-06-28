# SOM + Temporal Opcodes: Bidirectional Phase-Lock Classification

## Current SOM (Serial Scan)

The existing `spu_som_bmu.v` scans 7 nodes sequentially:

```
IDLE → READ_ADDR → READ_WAIT → START_ACC → WAIT_ACC → EVAL → NEXT_NODE × 7 → DONE
= ~35+ cycles per classification
```

Each node computes weighted quadrance, tracks best/second, then outputs BMU.

## New Approach: Wheeler-Feynman SOM

Map each SOM cluster to an RPLU material entry. The centroid vector is stored as
material parameters. Classification becomes a boundary-value resolve:

```
OFFR  R1, [RPLU, input_addr]    ; Load input vector → R1.O (Offer wave)
CNFM  R1, [RPLU, cluster_addr]  ; Load cluster centroid → R1.C (Confirmation)
PHSLK R2, R1, R0                ; Resolve: does input belong to this cluster?
JC    #clustered                 ; Coherent → classification match!
INVJ  R2, R2                     ; Not coherent → try conjugate domain
```

### Why This Works

The RPLU material table already stores 64-bit parameter records per material.
A SOM cluster centroid is a 64-bit vector (4 features × 16-bit Q12.4).
The RPLU `ratio_cmp` cross-multiplier already computes Offer vs Confirmation
coherence.

Result: **classification in 3-4 cycles** instead of 35+.

### New Opcode: SOM_CLASSIFY

```
Mnemonic: SOM_CLASSIFY Rd, Rs, addr
Format:   R (register)
Encoding: 0x2A (same opcode as existing SOM, now maps to temporal pipeline)

Operation:
  1. Read R[Rs].O as input feature vector (Offer)
  2. Read RPLU material[addr] as cluster centroid (Confirmation)
  3. RAU computes PHSLK cross-multiplication
  4. If coherent: Rd = cluster label, FLAGS.C=1
  5. If not coherent: Rd = nearest mismatch, FLAGS.C=0
```

### HW Integration (Updated for RPLU v2)

| Component | Change |
|-----------|--------|
| `spu_rau.v` | Add PHSLK path (already exists) |
| `spu13_fp4_inverter.v` | Conjugate reduction tower for F_{p^4} denominator inversion |
| `rplu_thimble_pade.v` | [4/4] Padé rational approximant over F_{p^4} via Horner + inverter |
| `spu_som_node_array.v` | Parallel 7-node array with WTA tree (replaces serial scan) |
| `spu13_btu_core_top.v` | BTU spatial→F_{p^4} transmutation (4-lane BRAM) |
| `spu_btu_collision_resolver.v` | Multi-saddle collision priority encoder + bubble insertion |
| `spu_isa_decoder.v` | SOM (0x2A) → node array start; SOM_TRAIN (0x2B) → weight update |

### Assembler Syntax

```asm
; Load input feature vector
LOAD    R1, [R0, #input_addr]

; Classify against cluster 3 (stored in RPLU material 3)
; Uses parallel 7-node array → WTA → BTU → Padé pipeline
SOM     R2, R1, 3
JC      #match
; Not classified → handle unknown
JMP     #done
match:
; R2 contains cluster label
; FLAGS.V=1 if singularity encountered (zero-norm in Padé denominator)
done:
```

### Performance Comparison

| Approach | Cycles | Type |
|----------|--------|------|
| Current BMU scan (7 nodes) | 35+ | Serial search |
| **New parallel node array** | **5** | Parallel quadrance + WTA (3-stage pipeline) |
| Full Thimble-Padé pipeline | ~120 | SOM + BTU + Padé evaluate + F_{p^4} invert + multiply |
| Temporal PHSLK classify | 3-4 | Boundary resolve |
| Speedup (vs serial scan) | ~10× | — |

The temporal path doesn't replace SOM_TRAIN — the existing training engine still
updates weights. The innovation is in how classification is done: not by scanning
all nodes, but by evaluating all 7 nodes in parallel through the 3-stage quadrance
pipeline, then selecting the winner via combinational WTA tree in a single cycle.

For applications requiring field inversion (Padé denominator evaluation), the
full Thimble-Padé pipeline adds the conjugate reduction tower (~76 cycles) plus
the final F_{p^4} multiply, for ~120 cycles total. The zero-norm singularity
guard (FLAGS.V) prevents silent corruption when the classification lands on a
geometric boundary.