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

### HW Integration (Minimal Delta)

| Component | Change |
|-----------|--------|
| `spu_rau.v` | Add PHSLK path (already exists) |
| `spu_rplu_exp.v` | Route `ratio_cmp` to RAU for SOM coherence check |
| `spu_isa_decoder.v` | SOM_CLASSIFY → RAU start + RPLU read (already maps 0x2A) |
| `spu_som_bmu.v` | Keep for training (SOM_TRAIN); classify via temporal path |

### Assembler Syntax

```asm
; Load input feature vector
LOAD    R1, [R0, #input_addr]

; Classify against cluster 3 (stored in RPLU material 3)
SOM_CLASSIFY R2, R1, 3
JC      #match
; Not classified → handle unknown
JMP     #done
match:
; R2 contains cluster label
done:
```

### Performance Comparison

| Approach | Cycles | Type |
|----------|--------|------|
| Current BMU scan (7 nodes) | 35+ | Serial search |
| Temporal PHSLK classify | 3-4 | Boundary resolve |
| Speedup | ~10× | — |

The temporal path doesn't replace SOM_TRAIN — the existing training engine still
updates RPLU material entries. The innovation is in how classification is done:
not by scanning all nodes, but by checking phase coherence against the target
cluster in a single cycle.
