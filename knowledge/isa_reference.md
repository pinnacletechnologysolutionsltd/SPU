# SPU-13 Sovereign ISA Reference

Version 3.2 — 26 opcodes

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
| **0x1C** | **ROTC** | QRd, QRs, θ | Thomson circulant rotation (F,G,H) |
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

| Opcode | Mnemonic | Operands | Description |
|--------|----------|----------|-------------|
| 0x60 | POLY_STEP | Rd,Rx | Horner step via RPLU |
| 0x61 | RATIO_CMP | Rd,Rs | Rational comparison |

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
