# SPU-13 Experimental Wheeler–Feynman Adapter ISA v1.0

> **Status: experimental architecture study; not the canonical silicon ISA.**
>
> This profile specifies a twin-register adapter with OFFR/CNFM/PHSLK/INVJ
> opcodes. Its Python and C++ models and isolated RTL blocks have focused test
> coverage, but the profile is not dispatched by the active `spu13_core.v`
> images used for the Tang and Wukong silicon proofs. “Offer,” “Confirmation,”
> and “Wheeler–Feynman” are names for paired boundary-data slots and their
> algebraic comparison; they do not assert physical retrocausality.
>
> **Canonical ISA:** [`knowledge/isa_reference.md`](../knowledge/isa_reference.md),
> implemented by `software/spu_vm.py`, the default mode of
> `software/tools/spu13_asm.py`, and the active core RTL. No deprecation or
> replacement decision has been made.
>
> The opcode values in this experimental profile match
> `hardware/rtl/arch/spu_isa_defines.vh` and `software/spu13_arch_sim.py`.
> They form a separate encoding from the canonical ISA.

## 1. Architecture Overview

The SPU-13 is a **Deterministic Geometric Computer** based on four pillars:

1. **Quadray coordinates** (a,b,c,d) — 4D barycentric basis spanning 3D space without sqrt or trig
2. **Rational arithmetic** — all values are exact integer fractions (numerator/denominator), no IEEE-754 floats
3. **Twin-register file** — each logical register holds an Offer wave (`R[n].O`) and a Confirmation wave (`R[n].C`)
4. **Paired-boundary phase-lock** — an experimental dataflow model compares
   independently supplied Offer and Confirmation slots using exact arithmetic

### 1.1 Scalability

| Variant | Axes | Registers | Manifold | Target |
|---------|------|-----------|----------|--------|
| SPU-13  | 13   | 32        | 832 bits | Large FPGA (GW5A, ECP5-85) |
| SPU-4   | 4    | 8         | 256 bits | Sentinel/monitor (GW1N, iCE40) |

The ISA is identical across variants; SPU-4 uses a subset of registers (R0-R7) and axes (0-3). Software compiled for SPU-13 runs on SPU-4 when restricted to the subset.

---

## 2. Data Formats

### 2.1 Quadray Coordinate (64-bit)

```
63:48   47:32   31:16   15:0
  a       b       c       d
```

Each component is **signed Q12.4** (12 integer bits + 4 fractional bits = 16-bit signed, range ±2048.9375).

The four coordinates satisfy: `a + b + c + d = 0` (tetrahedral constraint).

### 2.2 Rational Quadrance (64-bit)

```
63:32        31:0
Numerator    Denominator
```

Unsigned 32-bit integer pair representing `Q = num / den`. Zero denominator is reserved (treated as infinite).

### 2.3 Rational Spread (8-bit)

```
7:0
Spread index (0-255)
```

Spread `s = n/256` where `n` is an integer 0-256. Represented as 8-bit index into a 257-entry rational spread LUT. This replaces angles and trigonometric functions entirely.

### 2.4 Chord / Instruction Word (64-bit)

The chord is the fundamental instruction word, matching `SPU_LINK_CHORD_BYTES = 8`:

```
63:56      55:51   50:46   45:41   40:0
[Opcode]   [Dest]  [SrcA]  [SrcB]  [Immediate / Reserved]
```

See Section 4 for format details.

---

## 3. Register File

### 3.1 Twin-Register Architecture

Each of the 32 logical registers `R0`–`R31` contains two physical 64-bit slots:

| Slot | Accessor | Role |
|------|----------|------|
| `R[n].O` | OFFR | Offer wave — forward-propagating past constraints |
| `R[n].C` | CNFM | Confirmation wave — backward-propagating future constraints |

### 3.2 Special Registers

| Register | Name | Purpose |
|----------|------|---------|
| R0  | ZERO | Always reads as zero; writes discarded |
| R1  | PC | Program counter (readable, writable for jump) |
| R2  | FLAGS | Status flags: Z=bit0, C=bit1 (coherent), S=bit2 (scale overflow) |
| R3  | MANIFOLD_PTR | Current manifold read pointer (4-13 axes) |
| R4  | SCALE_PTR | Current scale table index |
| R5  | CHORD_IN | Incoming chord from SPI slave (read-only) |
| R6  | CHORD_OUT | Outgoing chord to SPI master (write-only) |
| R7  | QUAD_OUT | Quadrance output register (read-only) |
| R8–R31 | GP | General-purpose twin-registers |

### 3.3 SPU-4 Subset

In SPU-4 sentinel mode, only R0–R7 are active. The decoder treats R8–R31 as R0 (writes discarded, reads return zero). Implementation may power-gate the upper registers.

---

## 4. Instruction Formats

All instructions are **64 bits** wide. Six formats are defined:

### 4.1 Format R — Register 3-Operand (Arithmetic / Geometric)

```
63:56    55:51   50:46   45:41   40:0
Opcode   Dest    SrcA    SrcB    Reserved (41 bits)
```

Used by: QADD, QSUB, QMUL, QDIV, SPRD, ROTR, CROSS, DOT, TNSR, PHSLK, CMP, MOV

The operation reads from `SrcA` and `SrcB` twin-registers, writes result to `Dest` twin-register. Which slot(s) are read/written depends on the opcode:
- Arithmetic ops (QADD/QSUB/QMUL/QDIV): read `R[SrcA].O` + `R[SrcB].O`, write `R[Dest].O`
- Geometric ops (SPRD/ROTR): read both `.O` and `.C` as coordinate pairs
- Phase-lock (PHSLK): reads `R[SrcA].O` + `R[SrcB].C` (bidirectional), writes `R[Dest].O` (locked result)

### 4.2 Format L — Load/Store with Offset

```
63:56    55:51   50:46   45:36    35:0
Opcode   Dest    Base    Offset   Reserved (36 bits)
```

Signed 10-bit offset (±512) from base register. Base=0 → absolute address in range [0, 1023].

Used by: LOAD, STORE, LDO, LDC, OFFR, CNFM

### 4.3 Format I — Immediate Load

```
63:56    55:51   50:0
Opcode   Dest    Immediate (51-bit unsigned)
```

51-bit immediate — sufficient to load any rational numerator or quadray component in one instruction.

Used by: MOVI, RCFG

### 4.4 Format U — Unary / Conditional

```
63:56    55:51   50:46   45:44    43:0
Opcode   Dest    Src     Cond     Reserved (44 bits)
```

Condition field:
- `00` = always execute
- `01` = execute if phase-lock coherent (FLAGS.C=1)
- `10` = execute if phase-lock not coherent (FLAGS.C=0)
- `11` = reserved

Used by: QNORM, INVJ, RREAD, PHSTA

### 4.5 Format B — Branch

```
63:56    55:51   50:0
Opcode   Flags   Branch offset (51-bit signed)
```

51-bit signed offset from current PC. Range: ±2^50 instructions.

Used by: JMP, JZ, JNZ, JC, JNC, CALL

### 4.6 Format X — System / No Operand

```
63:56    55:0
Opcode   Reserved (56 bits)
```

Used by: NOP, HALT, SYNC, RET, MFOLD, STAT, SCALE, QR, HEX

---

## 5. Opcode Map

### 5.1 System & Control (0x00–0x0F)

| Opcode | Mnemonic | Format | Description |
|--------|----------|--------|-------------|
| 0x00 | NOP | X | No operation |
| 0x01 | HALT | X | Halt execution until reset |
| 0x02 | SYNC | X | Wait for all pending phase-locks to resolve |
| 0x03–0x0F | — | — | Reserved |

### 5.2 Data Movement (0x10–0x1F)

| Opcode | Mnemonic | Format | Description |
|--------|----------|--------|-------------|
| 0x10 | LOAD | L | Load memory[Base+Offset] → R[Dest].O |
| 0x11 | STORE | L | Store R[Dest].O → memory[Base+Offset] |
| 0x12 | MOV | R | Copy R[SrcA].O → R[Dest].O |
| 0x13 | MOVI | I | Load immediate → R[Dest].O |
| 0x14 | LDO | L | Load memory → R[Dest].O (explicit Offer) |
| 0x15 | LDC | L | Load memory → R[Dest].C (explicit Confirmation) |
| 0x16 | MOV_O | R | Copy R[SrcA].O → R[Dest].O |
| 0x17 | MOV_C | R | Copy R[SrcA].C → R[Dest].O |
| 0x18–0x1F | — | — | Reserved |

### 5.3 Quadrance Arithmetic (0x20–0x2F)

| Opcode | Mnemonic | Format | Description |
|--------|----------|--------|-------------|
| 0x20 | QADD | R | Rational add: R[Dest].O = R[SrcA].O + R[SrcB].O |
| 0x21 | QSUB | R | Rational subtract: R[Dest].O = R[SrcA].O − R[SrcB].O |
| 0x22 | QMUL | R | Rational multiply: R[Dest].O = R[SrcA].O × R[SrcB].O |
| 0x23 | QDIV | R | Rational divide: R[Dest].O = R[SrcA].O ÷ R[SrcB].O |
| 0x24 | QNORM | U | Normalize R[Src].O to reduced fraction → R[Dest].O |
| 0x25 | QCMP | R | Compare quadrances: set FLAGS.Z/FLAGS.C per R[SrcA].O − R[SrcB].O |
| 0x26–0x2F | — | — | Reserved |

### 5.4 Geometric Operations (0x30–0x3F)

| Opcode | Mnemonic | Format | Description |
|--------|----------|--------|-------------|
| 0x30 | SPRD | R | Calculate spread between quadrays R[SrcA] and R[SrcB] → R[Dest].O |
| 0x31 | ROTR | R | Apply spread-rotor: rotate R[SrcB] by spread in R[SrcA] → R[Dest].O |
| 0x32 | CROSS | R | Quadray cross product: R[SrcA] × R[SrcB] → R[Dest].O |
| 0x33 | DOT | R | Quadray dot product → rational quadrance in R[Dest].O |
| 0x34 | TNSR | R | Apply metric tensor M=4I−J to R[SrcA] → R[Dest].O |
| 0x35 | PROJ | R | Project R[SrcB] onto R[SrcA] → rational spread in R[Dest].O |
| 0x36–0x3F | — | — | Reserved |

### 5.5 Bidirectional / Temporal Operations (0x40–0x4F)

| Opcode | Mnemonic | Format | Description |
|--------|----------|--------|-------------|
| 0x40 | OFFR | L | Load memory → R[Dest].O (Offer wave from past constraints) |
| 0x41 | CNFM | L | Load memory → R[Dest].C (Confirmation wave from future boundary) |
| 0x42 | PHSLK | R | Phase-lock: solve R[SrcA].O ∩ R[SrcB].C → R[Dest].O |
| 0x43 | INVJ | U | Invert through Janus point: negate all quadray components of R[Src] → R[Dest] |
| 0x44 | PHSTA | U | Read PHSLK status: 0=pending, 1=locked, 2=failed → R[Dest].O |
| 0x45 | PHCLR | U | Clear phase-lock status for R[Src] |
| 0x46–0x47 | — | — | Reserved |
| 0x48 | JSCR | R | Janus screw: tetrahedral six-edge topology permutation |
| 0x49–0x4B | — | — | Reserved |
| 0x4C | NSA_DQADD | R | Dual-number add over $A_{31}[\epsilon]$ |
| 0x4D | NSA_DQMUL | R | Dual-number multiply over $A_{31}[\epsilon]$ |
| 0x4E–0x4F | — | — | Reserved |

#### 5.5.1 PHSLK Hardware Mechanics

The isolated adapter model defines PHSLK as follows:

1. The RAU loads `R[SrcA].O` (forward Offer) and `R[SrcB].C` (backward Confirmation)
2. The hardware performs rational comparison: does `Offer × Confirmation⁻¹` reduce to unity?
3. If yes: result is written to `R[Dest].O`, hardware sets FLAGS.C=1
4. If no: FLAGS.C=0; any correction or branch is an explicit later operation

This is a functional model contract. The profile does not currently specify a
silicon-proven variable-latency refinement loop or an integrated-core cycle
count.

#### 5.5.2 JSCR Edge-Topology Mechanics

`JSCR` is a topology operation, not a spread rotor or matrix multiply.  It
acts on the six tetrahedral line buses in edge order `AB, AC, AD, BC, BD, CD`.
The low mode bits select straight pass-through, clockwise screw,
counter-clockwise screw, or opposite-edge dual inversion.

The standalone RTL primitive is `spu13_janus_screw_lines.v`.  It is
combinational and does not consume DSPs.  The architectural state target is the
six-line topology register path implemented by `spu13_topology6_state.v`.
Projection back into Quadray `A,B,C,D` coordinates is a separate conversion
step and is not part of the inverse pathway.

`spu13_janus_dual_mode.v` wraps this primitive for paired positive/negative
tetrahedra.  It exposes three tested boundary modes:

| Mode | Hardware behavior |
|------|-------------------|
| PISTON | Positive tetrahedron passes through unchanged; negative boundary strobe applies the screw permutation one-sided. |
| SEESAW | Positive and negative boundary strobes must arrive on the same cycle; outputs are cross-coupled after screw permutation. A one-sided strobe reports phase mismatch. |
| INDEPENDENT | Each side may screw on its own boundary strobe. `phase_offset` checks the expected cycle separation between the two boundary events. |

Boundary arrival is an explicit algebraic predicate from PHSLK/RPLU logic
(`pos_boundary`, `neg_boundary`).  The hardware does not infer a boundary from
real-valued sign, volume, or continuous zero-crossing language.

`spu13_topology6_state.v` stores paired positive/negative tetrahedra as thirteen
lanes of six-line state.  `JSCR` dispatch should read a source topology lane,
apply the selected PISTON/SEESAW/INDEPENDENT mode through the Janus dual-mode
wrapper, and commit the result into a destination topology lane.  This preserves
the inverse edge-connectivity path across Janus transitions.

In the current `spu13_core.v` integration, `QLDI` also hydrates the matching
topology shadow lane by deriving pairwise positive edges from the loaded
`A,B,C,D` coordinates and reverse edges for the negative dual copy.

### 5.6 RPLU Configuration (0x50–0x5F)

| Opcode | Mnemonic | Format | Description |
|--------|----------|--------|-------------|
| 0x50 | RCFG | I | Write RPLU config: packed{sel, material, addr, data64} → RPLU table |
| 0x51 | RREAD | U | Read RPLU config at R[Src].O address → R[Dest].O |
| 0x52 | RLOAD | I | Load RPLU table from memory region (burst) |
| 0x53 | RDISSOC | U | Read RPLU dissociation table → R[Dest].O |
| 0x54–0x5F | — | — | Reserved |

### 5.7 Flow Control (0x60–0x6F)

| Opcode | Mnemonic | Format | Description |
|--------|----------|--------|-------------|
| 0x60 | CMP | R | Compare R[SrcA].O to R[SrcB].O, set FLAGS{Z,C} |
| 0x61 | JMP | B | Unconditional jump |
| 0x62 | JZ | B | Jump if FLAGS.Z=1 |
| 0x63 | JNZ | B | Jump if FLAGS.Z=0 |
| 0x64 | JC | B | Jump if FLAGS.C=1 (phase-lock coherent) |
| 0x65 | JNC | B | Jump if FLAGS.C=0 (phase-lock not coherent) |
| 0x66 | CALL | B | Call: push PC+1 to return stack, jump |
| 0x67 | RET | X | Return: pop return stack → PC |
| 0x68 | IRET | X | Return from interrupt |
| 0x69–0x6F | — | — | Reserved |

### 5.8 Classification / SOM (0x2A–0x2B)

> **Adapter-model semantics only.** This subsection does not describe the
> active canonical SOM implementation. Canonical opcode `0x2A` launches the
> writable, exact-order seven-node BMU (fixed 434-clock latency), while the
> parallel node array described below is archived and superseded.

| Opcode | Mnemonic | Format | Description |
|--------|----------|--------|-------------|
| 0x2A | SOM | R | SOM classify: PHSLK input against RPLU cluster material |
| 0x2B | SOM_TRAIN | R | SOM train: update RPLU material weights from input |

In the adapter study, the SOM opcodes were intended to use the temporal
pipeline for classification: SOM would load an input as Offer and a prototype
as Confirmation, then PHSLK would check coherence. That proposal never became
the active core datapath, and one coherence comparison is not a complete
nearest-prototype search contract.

**Historical RTL experiment:** A SOM layer was implemented as a parallel
7-node array (`spu_som_node_array.v`) with a combinational winner-take-all
comparator tree and is now archived.
Each node (`spu_som_node.v`) runs a 3-stage parallel quadrance pipeline
(subtract → square → accumulate) over A31. The BTU (`spu13_btu_core_top.v`)
routes activation lines through a 4-lane BRAM lookup into A31 coordinates.
Multi-saddle collisions are resolved by the priority encoder in
`spu_btu_collision_resolver.v`. These blocks belong to the broader RPLU2
research pipeline and do not replace the SOM v1 product contract.

**Proposed Thimble-Padé integration:** The study has SOM classification feed saddle-point
coordinates into `rplu_thimble_pade.v` which evaluates the [4/4] Padé rational
approximant over A31 using Horner evaluation + conjugate reduction tower
inversion (`spu13_fp4_inverter.v`). The RPLU2 pipeline is silicon-proven on
Artix-7, but this adapter-specific SOM composition is not a product or silicon
claim.

```
SOM   R2, R1, R3    ; Classify R1.O against RPLU material[R3] → label in R2
                     ; FLAGS.C=1 if classified, 0 if unknown
SOM_TRAIN R1, R2, R3 ; Train: update RPLU material[R3] with R1.O weights
```

### 5.9 Telemetry / Output (0x70–0x7F)

| Opcode | Mnemonic | Format | Description |
|--------|----------|--------|-------------|
| 0x70 | MFOLD | X | Emit manifold state (4 axes × 64-bit) to SPI output bus |
| 0x71 | STAT | X | Emit status{dissonance, flags} to SPI output bus |
| 0x72 | SCALE | X | Emit scale table + overflow to SPI output bus |
| 0x73 | QR | X | Emit QR commit{A,B,C,D} to SPI output bus |
| 0x74 | HEX | X | Emit hex{q,r} to SPI output bus |
| 0x75 | SENT | X | Emit sentinel telemetry burst (64 bytes) |
| 0x76 | CHRDOUT | I | Output 51-bit immediate as chord to SPI master |
| 0x77–0x7F | — | — | Reserved |

### 5.9 Extension Space (0x80–0xFF)

128 opcodes reserved for:
- Microcode expansion (SPU-13 microcode ROM)
- User-defined custom accelerators
- Future ISA versions

---

## 6. Pipeline

### 6.1 Geometric Pipeline Structure: 1 + 3 + 3 = 7 Stages

The proposed adapter pipeline uses a Wheeler–Feynman-inspired geometric
metaphor for paired dataflow. The diagram is an architecture model, not evidence
of a currently integrated silicon datapath or a claim of physical
retrocausality. Two conceptual tetrahedra meet at a single Janus point:

```
          ┌──────────────── Tetrahedron A (Offer) ────────────────┐
          │                                                       │
          │  Stage 1          Stage 2            Stage 3          │
          │  Decode           ReadReg / RPLU     RAU              │
          │  (intention set)  (past constraints) (forward prop)   │
          │      ●─────────────────●─────────────────●            │
          │                       / \                             │
          │                      /   \                            │
          │                     /     \                           │
          │                    /       \                          │
          │          Stage 0  /         \                         │
          │        (Janus)  ●───────────●                         │
          │                    Origin    \                        │
          │                               \                       │
          │                                \                      │
          │                                 \                     │
          │           ●─────────────────●─────────────────●       │
          │  Stage 4          Stage 5            Stage 6          │
          │  Load Confirm     PhaseLock Solve    WriteReg + Tel   │
          │  (future bounds)  (handshake check)  (commit result)  │
          │                                                       │
          └──────────────── Tetrahedron B (Confirmation) ─────────┘
```

#### Stage 0 — Janus Point (Origin / Zero / Instruction Fetch)
- The unified field from which both wave paths emerge.
- 64-bit instruction word fetched from chord input or microcode ROM.
- Both future and past are undifferentiated at this point.
- Duration: 1 cycle.

#### Stages 1-3 — Tetrahedron A (Forward Offer Wave)
Propagates the Offer wave outward from past constraints toward the future boundary.

| Stage | Name | Vertex | Operation |
|-------|------|--------|-----------|
| **1** | **Decode** | Intention | Opcode decode, operand extraction, format detection. The wave's purpose is set. |
| **2** | **ReadReg / RPLU** | Past Boundary | Read twin-register file (O and C slots in parallel). OFFR loads material parameters from RPLU ROM. The past constraint edge is established. |
| **3** | **RAU** | Forward Wave | Rational Arithmetic Unit: Q(√3) integer cross-multiply, Pell orbit rotation. The Offer wave propagates outward via the DSP. |

- Design target: 3 cycles; not measured on an integrated silicon image.

#### Stages 4-6 — Tetrahedron B (Backward Confirmation Wave)
Returns the Confirmation wave backward from the future boundary toward the past.

| Stage | Name | Vertex | Operation |
|-------|------|--------|-----------|
| **4** | **Load Confirmation** | Future Boundary | CNFM loads future boundary condition from RPLU ROM into twin-register `.C` slot. The inverse vertex is set. |
| **5** | **PhaseLock Solve** | Handshake Edge | RATIO_CMP performs cross-multiplication: `acc_num × q2 vs acc_den × p2`. Zero tolerance → FLAGS.C=1 (coherent). May iterate 1-3 cycles on boundary mismatch. The handshake edge is the interference pattern. |
| **6** | **WriteReg / Telemetry** | Resolved Transaction | Write resolved state to destination twin-register and conditionally emit manifold/status to the output bus. |

- Total: 3 cycles.

The seven-stage diagram is structural design intent. No integrated-image
throughput claim is made from it.

### 6.2 SPU-4 Lite Pipeline (4 stages)

```
Fetch → Decode → RAU → WriteReg
```

No PhaseLock stage; temporal opcodes (PHSLK, INVJ) are reduced to register
moves in this proposed subset. This behavior belongs to the experimental
profile and is not the silicon-proven SPU-4 Sentinel ISA contract.

### 6.3 SOM, BTU, and Padé status boundary

The original adapter study sketched a four-stage SOM → BTU → Padé composition.
That composition is not the current product classification path and its former
worked-example constants and aggregate latency estimates were not generated by
a checked oracle. They are therefore not normative.

The implemented blocks have separate contracts:

| Block | Current evidence boundary |
|---|---|
| SOM v1 | Writable seven-node, exact-order BMU; fixed 434 clocks; cross-vendor silicon evidence |
| BTU collision resolver | RTL subsystem with its own tests; not part of the SOM1 inference ABI |
| Thimble–Padé | Deterministic RPLU2 pipeline, silicon-proven on Wukong Artix-7 |
| PHSLK adapter | Isolated experimental-model semantics; not active core dispatch |

An integrated future composition must publish generated vectors and measure its
own end-to-end latency. Latencies from the independent blocks must not be added
as though the proposed control schedule already exists.

---

## 7. Twin-Register Timing Diagram

```
Clock:     _|‑|_|‑|_|‑|_|‑|_|‑|_|‑|_|‑|_
                     │
OFFR R1, [ADDR]  →   │  R[1].O = MEM[ADDR]
CNFM R1, [ADDR]  →   │  R[1].C = MEM[ADDR]
                     │
PHSLK R3, R1, R2  →  │  RAU: (R[1].O) ∩ (R[2].C) → R[3].O
                     │
INVJ R4, R3       →  │  R[4].O = negate(R[3].O)
```

---

## 8. Memory Map

| Address Range | Region | Access |
|---------------|--------|--------|
| 0x000–0x1FF | RPLU config table (512 entries × 64-bit) | R/W |
| 0x200–0x2FF | Scale table (256 entries spread LUT + 1 overflow) | R/W |
| 0x300–0x3FF | Microcode ROM (256 instructions) | R |
| 0x400–0x4FF | Pell coefficient cache | R/W |
| 0x500–0x5FF | Boot parameter block | R/W |
| 0x600–0x7FF | Reserved |
| 0x800–0xFFF | General-purpose scratch (2K) | R/W |
| 0x1000–0x1FFF | SPI slave mailbox (incoming chords) | R |
| 0x2000–0x2FFF | SPI master mailbox (outgoing telemetry) | W |

---

## 9. SPI Command Mapping

The SPI commands (`spu_spi_slave.v`) map directly to the telemetry opcodes:

| SPI CMD | Opcode | Response Size | Description |
|---------|--------|---------------|-------------|
| 0xA0 | MFOLD | 32 bytes | Read 4-axis manifold |
| 0xAC | STAT | 4 bytes | Read status (dissonance + flags) |
| 0xAD | SCALE | 9 bytes | Read scale table + overflow |
| 0xAE | QR | 34 bytes | Read QR commit registers |
| 0xAF | HEX | 5 bytes | Read hex (q, r) |
| 0xB0 | SENT | 64 bytes | Read sentinel telemetry burst |
| 0xB1 | CHORD | — | Write 8-byte instruction chord |
| 0xA5 | RCFG | — | Write RPLU config record (HEADER + DATA) |

---

## 10. Assembly Syntax

```asm
; ── System ──
NOP
HALT
SYNC

; ── Data movement ──
LOAD    R1, [R2, #4]       ; Load from mem[R2+4] → R1.O
STORE   R1, [R2, #4]       ; Store R1.O → mem[R2+4]
MOV     R3, R1             ; R3.O = R1.O
MOVI    R3, #0x123456789   ; R3.O = immediate

; ── Quadrance arithmetic ──
QADD    R3, R1, R2         ; R3.O = R1.O + R2.O  (rational)
QMUL    R3, R1, R2         ; R3.O = R1.O × R2.O
QNORM   R3, R1             ; Normalize R1.O → R3.O

; ── Geometric ──
SPRD    R3, R1, R2         ; Spread between quadrays R1, R2
ROTR    R3, R1, R2         ; Rotate R2 by spread/rotor in R1
TNSR    R3, R1             ; Apply M=4I-J tensor to R1

; ── Temporal ──
OFFR    R1, [R0, #PAST]    ; Load Offer wave from address PAST
CNFM    R1, [R0, #FUTURE]  ; Load Confirmation from address FUTURE
PHSLK   R3, R1, R2         ; Phase-lock Offer(R1) ∩ Confirm(R2)
INVJ    R4, R3             ; Invert R3 through Janus point

; ── Flow control ──
CMP     R1, R2             ; Compare, set flags
JZ      #target            ; Jump if zero
JC      #locked            ; Jump if coherent

; ── Telemetry ──
MFOLD                       ; Emit manifold to SPI output
STAT                        ; Emit status to SPI output
```

---

## 11. SPU-13 vs SPU-4 Feature Matrix

| Feature | SPU-13 | SPU-4 |
|---------|--------|-------|
| Registers | 32 twin | 8 twin |
| Axes | 13 | 4 |
| RAU width | 64-bit | 32-bit |
| PhaseLock stage | Yes | No (reduced to MOV) |
| Microcode ROM | 256 entry | None |
| RPLU config | Full (512 entries) | None |
| Telemetry | All commands | STAT, MFOLD only |
| Max clock | 6.25 MHz | 12.5 MHz |
| LUT estimate | ~15-25K | ~2-4K |

---

*Experimental Wheeler–Feynman adapter ISA v1.0 — architecture study*
