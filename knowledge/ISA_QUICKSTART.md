# SPU-13 ISA Quickstart

**Sovereign Assembly Source (.sas) — instruction set reference for the SPU-13 soft-CPU and hardware core.**

Programs are assembled and simulated via:
```bash
python3 software/spu_forge.py simulate software/programs/your_program.sas
```

Direct assembler (v3.1 — three-pass: label resolve → constant-fold → encode):
```bash
python3 software/tools/spu13_asm.py --hex software/programs/your_program.sas
python3 software/tools/spu13_asm.py --no-fold --hex ...   # disable constant-folding
```
The constant-folding pass pre-evaluates known-constant Q(√3) arithmetic at
assemble time (ADD/SUB/MUL/ROT/JINV on literal-initialised registers) and
eliminates dead stores.  Loop bodies are never folded — known state is cleared
at every labelled position.

---

## Registers

### Scalar registers — `R0`–`R25`

Each holds a Q(√3) surd: `(P, Q)` where the real value is `P + Q·√3`.
Packed in hardware as a 32-bit word: `[31:16] = P (signed)`, `[15:0] = Q (signed)`.

```
R0  general purpose / accumulator
R1–R12  general purpose (13 total scalar slots mirror the 13 IVM axes)
R13–R25 extended / scratch
```

### Quadray registers — `QR0`–`QR12`

Each holds a 4-component Quadray vector `(a, b, c, d)` over Q(√3).
Quadray coordinates use a tetrahedral basis — four non-negative components,
sum invariant. No negative coordinates needed to describe 3-D space.

---

## Instruction Format

All instructions are 64-bit words:

```
[63:56]  opcode  (8-bit)
[55:48]  r1      (dest / first operand register index)
[47:40]  r2      (second operand register index)
[39:24]  p1_a    (immediate P component, signed 16-bit)
[23: 8]  p1_b    (immediate Q component, signed 16-bit)
[ 7: 0]  (reserved)
```

Assembly syntax is case-insensitive. Comments begin with `;`.

---

## Instruction Reference

### Scalar Arithmetic

| Mnemonic | Opcode | Syntax | Operation |
|----------|--------|--------|-----------|
| `LD` | 0x00 | `LD Rd, P, Q` | `Rd ← (P + Q·√3)` |
| `ADD` | 0x01 | `ADD Rd, Rs` | `Rd ← Rd + Rs` |
| `SUB` | 0x02 | `SUB Rd, Rs` | `Rd ← Rd − Rs` |
| `MUL` | 0x03 | `MUL Rd, Rs` | `Rd ← Rd × Rs` via `(ac+3bd, ad+bc)` |
| `ROT` | 0x04 | `ROT Rn` | `Rn ← Rn × (2+√3)` — Pell rotor, Q-preserving |
| `LOG` | 0x05 | `LOG Rn` | Print `Rn` to stdout (debug only) |

**Note on MUL:** `(a+b√3)(c+d√3) = (ac+3bd) + (ad+bc)√3` — no division, stays in Q(√3).

**Note on ROT:** The Pell rotor satisfies `P²−3Q²=1`. Repeated ROT never drifts — the
norm Q is preserved exactly through all rotations.

---

### Control Flow

| Mnemonic | Opcode | Syntax | Operation |
|----------|--------|--------|-----------|
| `JMP` | 0x06 | `JMP LABEL` | Unconditional jump |
| `COND` | 0x20 | `COND Rn, LABEL` | Jump if `Q(Rn) > 0` (laminar); fall through if `Q ≤ 0` |
| `CALL` | 0x21 | `CALL LABEL` | Push return address, jump |
| `RET` | 0x22 | `RET` | Pop and jump to return address |
| `SNAP` | 0x07 | `SNAP` | Assert all non-zero scalar registers have `Q = 1`; exit 2 on failure |
| `HALT` | 0x08 | `HALT` | Stop execution |
| `NOP` | 0xFF | `NOP` | No operation |

**COND semantics:** `Q(Rn) > 0` means the register is laminar (on the unit manifold).
`Q(Rn) ≤ 0` signals cubic leak — control falls through for manual recovery.
This is how the Davis Law Gasket works in software: no branches, only field tests.

**SNAP note:** SNAP causes `spu_forge simulate` to exit with code 2 if any register
fails the Q=1 test. Use SNAP for positive verification (pure Pell orbit programs).
Use `COND`+`JMP` when demonstrating or handling failure paths.

---

### Quadray IVM Operations

| Mnemonic | Opcode | Syntax | Operation |
|----------|--------|--------|-----------|
| `QLOAD` | 0x13 | `QLOAD QRn, Rb` | Pack R[Rb]..R[Rb+3] into QRn (4 consecutive scalar registers → 1 Quadray) |
| `QADD` | 0x10 | `QADD QRd, QRs` | `QRd ← QRd + QRs` (component-wise) |
| `QROT` | 0x11 | `QROT QRn` | Apply IVM rotation: `(a,b,c,d)→(b,c,d,a)` — preserves 60° geometry |
| `QNORM` | 0x12 | `QNORM QRd, QRs` | Quadrance (squared length) into `QRd` |
| `QLOG` | 0x14 | `QLOG QRn` | Print Quadray register (debug) |

**Why Quadray?** In a tetrahedral (IVM) basis four non-negative coordinates `(a,b,c,d)`
with `a+b+c+d = constant` describe every point in 3-D space without negative values.
Volumes of Platonic solids relative to a unit tetrahedron are whole numbers.
The transformation that breaks this: switching to a cubic (XYZ) basis.

---

### Geometry Output

| Mnemonic | Opcode | Syntax | Operation |
|----------|--------|--------|-----------|
| `SPREAD` | 0x15 | `SPREAD Rd, QRa, QRb` | Spread between two Quadrays: `s = 1 − (p·q)²/(p·p)(q·q)`. Stores `(numer, denom)` in `Rd`, `Rd+1` — never divides |
| `HEX` | 0x16 | `HEX Rn` | Render register as hex surd on output stream |

**Why Spread instead of angle?** `SPREAD` computes `numer = denom − (pq)²` using only
multiply and subtract. Geometric questions answered by integer comparison:
- Perpendicular? → `numer == denom` (spread = 1)
- 60° IVM angle? → `4×numer == 3×denom` (spread = 3/4)
- Parallel? → `numer == 0` (spread = 0)
No arcsin, no π, no rounding.

---

### Vector Equilibrium & Janus Layer

| Mnemonic | Opcode | Syntax | Operation |
|----------|--------|--------|-----------|
| `EQUIL` | 0x17 | `EQUIL Rd` | Check Vector Equilibrium state; write tension to `Rd` |
| `IDNT` | 0x18 | `IDNT Rd, Rs` | Identity Monad: `Rd ← Rs` with provenance tag |
| `JINV` | 0x19 | `JINV Rn` | Janus Inversion: `Rn ← (P, −Q)` — negate surd (b) component only; single XOR in hardware |
| `ANNE` | 0x1A | `ANNE Rd, Rs` | Anneal: smooth manifold tension between `Rd` and `Rs` |

---

## Program Structure

```asm
; fibonacci_demo.sas
; Compute first 8 Fibonacci steps in Q(√3)

        LD   R0, 1, 0      ; R0 = (1 + 0·√3) = 1
        LD   R1, 1, 1      ; R1 = (1 + 1·√3)
LOOP:
        LOG  R0
        ADD  R0, R1        ; R0 = R0 + R1
        LOG  R1
        ADD  R1, R0        ; R1 = R1 + R0
        JMP  LOOP          ; (use COND + counter to terminate)
```

Labels are identifiers followed by `:`. They are resolved in a two-pass assembly.
Immediates are signed 16-bit decimal integers.

---

## Running All Demos

```bash
# Individual programs
python3 software/spu_forge.py simulate software/programs/poiseuille_flow.sas
python3 software/spu_forge.py simulate software/programs/kinematic_chain.sas
python3 software/spu_forge.py simulate software/programs/laminar_vs_cubic.sas
python3 software/spu_forge.py simulate software/programs/jitterbug.sas
python3 software/spu_forge.py simulate software/programs/fibonacci_pulse.sas
python3 software/spu_forge.py simulate software/programs/equilibrium_test.sas

# Run all tests (Verilog)
python3 run_all_tests.py
```

---

## Key Algebraic Identities

```
Field:     Q(√3) = { a + b·√3 | a,b ∈ ℤ }
Pell norm: P² − 3Q² = N  (N=1 for unit manifold, N=−1 for half-step)
Rotor:     r = 2 + √3,  r⁻¹ = 2 − √3,  r·r⁻¹ = 1
Spread:    s(P,Q) = 1 − (P·Q)²/((P·P)(Q·Q))   — in integer arithmetic: numer/denom
Davis Law: ΣABCD = 0  ↔  manifold is stable (no cubic leak)
```

The processor never computes `1/x`. The field is closed under `+`, `−`, `×`.
Ratios are stored as `(numerator, denominator)` and compared by cross-multiplication.

---

## Common Patterns

### Load a surd constant
```asm
LD R0, 2, 1     ; R0 = 2 + √3  (Pell rotor seed)
```

### Pell orbit (unit manifold walk)
```asm
LD   R0, 1, 0   ; start at 1
ROT  R0          ; R0 = (2+√3)
ROT  R0          ; R0 = (7+4√3)
ROT  R0          ; R0 = (26+15√3)  — P²−3Q² = 1 all the way
```

### Detect cubic leak (not SNAP)
```asm
        COND R1, LAMINAR   ; jump if laminar
        LOG  R1             ; print the leak value
        JMP  DONE
LAMINAR:
        SNAP               ; now safe — all registers are laminar
DONE:
```

### IVM 60° spread check
```asm
; Load two unit Quadray axes via scalar registers R0..R3
LD R0, 1, 0 \ LD R1, 0, 0 \ LD R2, 0, 0 \ LD R3, 0, 0
QLOAD QR0, R0           ; QR0 = (1,0,0,0)
LD R0, 0, 0 \ LD R1, 1, 0
QLOAD QR1, R0           ; QR1 = (0,1,0,0)
SPREAD R4, QR0, QR1     ; R4=numer, R5=denom
; Check 4×R4 == 3×R5  →  spread = 3/4  →  60°
```

---

*See [`knowledge/MATHEMATICAL_FOUNDATIONS.md`](MATHEMATICAL_FOUNDATIONS.md) for the full theoretical derivation.*
