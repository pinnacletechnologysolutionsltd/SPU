# SPU-13 Sovereign ISA Reference — LEGACY v3.2

> **⚠ LEGACY ARCHITECTURE — Linear Forward-Flowing Execution**
>
> This ISA (v3.2) is the currently-silicon-proven architecture, running on Tang Primer 25K hardware.
> It is **slated for deprecation** in favor of the Wheeler-Feynman Next-Gen ISA (v1.0).
>
> **Migration path:**
> - New development should target `docs/spu13_isa_spec.md` (Wheeler-Feynman v1.0)
> - RPLU v2 Thimble-Padé pipeline (`rplu_thimble_pade.v` + `spu13_fp4_inverter.v`) targets v1.0
> - SOM classification uses parallel 7-node array (`spu_som_node_array.v`) with v1.0 opcodes 0x2A/0x2B
> - Use `spu13_asm.py --arch linear` to assemble programs for this legacy ISA
> - Use `spu13_asm.py --arch wf` (default) for the next-gen ISA
> - The `spu_vm.py` emulator supports v3.2; `spu13_arch_sim.py` supports v1.0

## Instruction Encoding

```
[63:56] [55:48] [47:40] [39:24] [23:8]
  Op      R1       R2      P1_A    P1_B
```

- **Op** (8 bits): Opcode
- **R1** (8 bits): Destination register (scalar R0–R25 or QR0–QR12)
- **R2** (8 bits): Source register / second operand
- **P1_A** (16 bits): Immediate field A (spread numerator, angle, byte values)
- **P1_B** (16 bits): Immediate field B (steps, configuration)

## Opcode Table

### Scalar Q(√3) Arithmetic

| Opcode | Mnemonic | Operands | Description |
|--------|----------|----------|-------------|
| 0x00 | LD | Rd, imm | Load RationalSurd into R |
| 0x01 | ADD | Rd, Rs | R[d] += R[s] |
| 0x02 | SUB | Rd, Rs | R[d] -= R[s] |
| 0x03 | MUL | Rd, Rs | R[d] ×= R[s] |
| 0x04 | ROT | Rd, Rs, n | Pell rotor step: R[d] = R[s] × rⁿ |
| 0x05 | LOG | Rd | Print R[d] to UART |
| 0x30 | PHADD | Rd, Rs | Phinary-packed addition |
| 0x31 | PHCFG | Rd, val | Phinary configuration |

### Control Flow

| Opcode | Mnemonic | Operands | Description |
|--------|----------|----------|-------------|
| 0x06 | JMP | addr | Unconditional jump |
| 0x07 | SNAP | — | Davis Gate stability check |
| 0x17 | EQUIL | — | Vector Equilibrium check |
| 0x20 | CALL | addr | Push PC, jump to subroutine |
| 0x21 | RET | — | Pop return stack, return |
| 0x08 | HALT | — | Halt execution |
| 0xFF | NOP | — | No operation |

### Quadray IVM Operations

| Opcode | Mnemonic | Operands | Description |
|--------|----------|----------|-------------|
| 0x10 | QADD | QRd, QRs | QR[d] += QR[s] |
| 0x11 | QROT | Rd, Rs, n | Pell rotor: R[d] = R[s] × (2+√3)ⁿ |
| 0x12 | QNORM | QRd | Normalize QR by subtracting min component |
| 0x13 | QLOAD | QRd | Load QR from manifold lane |
| 0x14 | QLOG | QRd | Print QR to UART (quadrance + components) |
| **0x1B** | **QSUB** | QRd, QRa, QRb | QR[d] = QR[a] - QR[b] |
| **0x1C** | **ROTC** | QRd, QRs, θ | Thomson circulant / permutation / octahedral rotation. θ = 0-35 verified (0-5 circulant A-invariant; 6-14 thirds conjugates about B/C/D; 15-23 A₄ pure permutations; 24-35 octahedral S₄, integer 3×3 on BCD with A recomputed from zero-sum). θ ≥ 36 faults (`rotc_debug_status[15]` / `RotcUnverifiedAngleError`), manifold untouched. Silicon: 0-5 on Artix-7; 6-35 testbench/trace-verified. Full catalog: `AGENTS.md` |
| **0xD6** | **IROTC** | QRd, QRs, sel | Icosahedral A₅ rotation on the φ-plane (Z[φ] pairs overlay QR components). sel[5:0] = catalog index 0-59, sel[6] = conjugate catalog. Typestate-guarded at dispatch (BADIDX/UNTAGGED/CATMIX), destination untouched on fault. Requires `ENABLE_IROTC`. Spec: `docs/IROTC_SPEC.md` v0.2 |
| **0xD7** | **LOAD2X** | QRd, A,B,C,D | QLDI-format immediates loaded doubled (<<1); sets φ-plane tag FRESH |
| **0xD8** | **SCALE2** | QRd, QRs | QR[d] = 2·QR[s] componentwise; sets tag FRESH (catalog-switch re-conditioning) |
| **0x1D** | **QLDI** | QRd, A,B,C,D | Load immediate Quadray vector |
| **0x1E** | **DELTA** | QRd, Q1,Q2,k | Triple quadrance parameterization |
| **0x1F** | **MIN4** | QRd | Normalize: subtract min(A,B,C,D) |
| **0x22** | **QREAD** | QRd, QRs | QR[d] = QR[s] (copy) |

### Geometry Output

| Opcode | Mnemonic | Operands | Description |
|--------|----------|----------|-------------|
| 0x15 | SPREAD | QRd, Q1,Q2,Q3 | Spread from three quadrances |
| 0x16 | HEX | Rd, QRs | Project QR[s] → hex (q,r) in R[d], R[d+1] |

### Vector Equilibrium / Janus

| Opcode | Mnemonic | Operands | Description |
|--------|----------|----------|-------------|
| 0x18 | IDNT | QRd | Load identity vector (1,0,0,0) |
| 0x19 | JINV | QRd | Janus inversion |
| 0x1A | ANNE | QRd | Annealer trigger |

### RPLU / Polynomial Extensions

> **RPLU v2 (Next-Gen ISA v1.0):** The legacy POLY_STEP/RATIO_CMP opcodes are
> superseded by the Thimble-Padé pipeline (`rplu_thimble_pade.v`) which evaluates
> [4/4] Padé rational approximants over A₃₁ (M31) using Horner + conjugate
> reduction tower inversion. See `docs/spu13_isa_spec.md` §5.5–5.8 for the
> OFFR/CNFM/PHSLK/SOM opcode chain.

| Opcode | Mnemonic | Operands | Description |
|--------|----------|----------|-------------|
| 0x60 | POLY_STEP | Rd,Rx | Horner step via RPLU (legacy Morse potential) |
| 0x61 | RATIO_CMP | Rd,Rs | Rational comparison (legacy) |

### Classification / SOM (v1.0 ISA only)

| Opcode | Mnemonic | Format | Description |
|--------|----------|--------|-------------|
| 0x2A | SOM | R | Classify via parallel 7-node array + WTA tree |
| 0x2B | SOM_TRAIN | R | Update node weights via 36-bit widened multiply |

## Wildberger Library (SPI Flash Primitives)

These are multi-instruction subroutines — not opcodes. Stored on SPI flash,
called via `CALL`:

| Address | Primitive | Input | Output | Instructions |
|---------|-----------|-------|--------|-------------|
| 0x010000 | quadrance_between | QR0,QR1 | Q in R0 | QSUB + QLOG |
| 0x010100 | spread_from_quadrances | Q1,Q2,Q3 | num,den | DELTA + QSUB |
| 0x010200 | is_right_angle | Q1,Q2,Q3 | bool | DELTA + compare |
| 0x010300 | is_collinear | Q1,Q2,Q3 | bool | DELTA×2 + compare |
| 0x010400 | spread_polynomial | n,s | R | Pell loop |
| 0x010500 | tangent_slope | QR,polynum | rational | QLDI + QSUB |
| 0x010600 | rational_area | polynum,x | rational | Faulhaber sum |
| 0x010700 | cross_matrix_2subspace | P,R matrices | C, c, s | DELTA + arithmetic |
| 0x010800 | diagonal_rule_verify | P,R,T subspaces | bool | cross + compare |

## Usage Examples

```lisp
;; Difference between two vectors
QLDI QR0, -1,  0,  0,  1    ; v1
QLDI QR1,  0, -1,  1,  0    ; v2
QSUB QR2, QR0, QR1          ; QR2 = v1 - v2
MIN4 QR2                     ; normalize result

;; Spread via DELTA
delta Q1=3 Q2=4 steps=4 dest=QR3
QLOG QR3                     ; shows q_sum=7, rhs²=0

;; Subroutine call
CALL .quad_identity
ROTC QR1, QR0, 1            ; rotate by 60°
RET
```

## Hardware Status

| Category | Count | Hardware Verified |
|----------|-------|------------------|
| Scalar ops | 8 | 4 |
| Control flow | 7 | 4 (JMP/CALL/RET/NOP) |
| Quadray ops | 12 | 8 |
| Output | 2 | 2 (HEX/QLOG) |
| VE/Janus | 3 | 1 (IDNT) |
| RPLU | 2 | 0 |
| **Total** | **26** | **19** |

20 of 26 opcodes have RTL implementations. The remaining 6 are software sequences
or require RPLU/SPI flash integration.

## FLAGS Register

The FLAGS register is a 6-bit status word read via the `SNAP` opcode (0x07)
and updated by arithmetic/geometry operations. Bits are sticky within an
instruction but cleared at the start of the next.

| Bit | Name | Set by | Meaning |
|-----|------|--------|---------|
| 0 | Z | Arithmetic | Result is zero |
| 1 | C | Arithmetic | Carry/overflow |
| 2 | V | A₃₁ inverter | Zero-norm detected (non-unit element) |
| **3** | **MISALIGNED** | **ROTC tagged** | **B/C/D exponents differ — ALIGN required before ROTATE** |
| **4** | **OVERFLOW** | **ROTC tagged** | **Exponent would exceed MAX_EXPONENT — REDUCE required** |
| **5** | **INEXACT** | **ROTC tagged** | **REDUCE failed: value not divisible by 3^exponent — true value is non-integer** |

Bits 3–5 are implemented in `spu13_rotor_core_tagged.v` (deferred-reduction
ROTC, `docs/ROTC_EXPONENT_STATE_MACHINE.md`). The legacy TDM rotor core
(`spu13_rotor_core_tdm.v`) does not assert these flags — its `div3` silently
truncates. The tagged core is the documented fix; see Davis Gate entry in
`knowledge/SPU_LEXICON.md` for the correctness analysis.

## Golden Vectors — Tagged ROTC Representation

The existing six-step ROTC closure golden vectors (VM-vs-RTL trace equivalence,
`software/tests/test_rotc_vm_rtl_trace.py`) were verified against the TDM core
with `div3`. Re-verification under the tagged representation is defined as:

1. The tagged core's ROTATE(angle) must produce the integer-coefficient output
   (3× the TDM golden value) at exponent 1 for thirds angles (1, 3, 4).
2. REDUCE on that output must recover the TDM golden value exactly at exponent 0.
3. Angles 0 (identity), 2 (P5 forward), and 5 (P5 inverse) must produce
   identical output to the TDM core (bypass path, no exponent change).

**Status:** RTL testbench verified (7/7 tests,
`hardware/tests/spu13/spu13_rotor_core_tagged_tb.v`). Silicon re-verification
pending — probe target: `spu13_tang25k_rotc_tagged_probe.v`, awaiting board run.
The existing six-step silicon evidence (`docs/hardware_evidence.md`)
was obtained with the TDM core and remains the silicon baseline.
