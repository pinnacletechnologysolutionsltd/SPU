# Lithic-L: A Formally Closed Programming Language for Q(√3) Geometry

**Version 1.0 — SPU-13 Sovereign Engine Language Specification**

*Authors: SPU-13 Project / CC0 1.0 Universal*

---

## Abstract

Lithic-L is the native programming language of the SPU-13 Sovereign Processing Unit.
It is not an assembly language in the conventional sense, and it is not a high-level
language in the C/Java sense. It occupies a new category: a **field-native language**
whose atomic type is an element of the algebraic number field Q(√3), not a bit.

The central thesis is this:

> **Standard processors operate on bits — syntactic tokens with no algebraic structure.
> The SPU-13 operates on field elements — entities that are closed under addition,
> subtraction, and multiplication, with no approximation and no rounding. The
> "word size" is not 64 bits. It is the field itself.**

This document defines:
1. The algebraic type system (§2)
2. The three-layer language stack (§3)
3. The Laminar Lang source language with formal EBNF grammar (§4)
4. The compilation model — including the MUX polynomial transform (§5)
5. The SPU-13 machine ISA (64-bit .sas format) (§6)
6. The Chord compact encoding for the SPU-4 Sentinel (§7)
7. Comparison with von Neumann languages (§8)

---

## 1. Motivation: The Wrong Basis Problem

Every floating-point number is an approximation. The IEEE 754 standard encodes numbers
as `± m × 2^e` — a mantissa and exponent in base 2. This basis is convenient for
electronics (two voltage levels), but it is **geometrically incommensurate** with the
structure of 3-dimensional space.

The consequence: algorithms that are algebraically exact (fluid dynamics, rigid body
kinematics, geodesic routing) accumulate rounding error at every step. The programmer
workarounds — epsilon comparisons, Kahan summation, double-precision casts — are
engineering responses to a fundamental mismatch between the number system and the
geometry being computed.

The SPU-13 chooses a different basis. The algebraic number field Q(√3) is the
**minimal closed field** containing the IVM (Isotropic Vector Matrix) basis vectors.
Within this field:

- Addition is exact: `(a+b√3) + (c+d√3) = (a+c) + (b+d)√3`
- Multiplication is exact: `(a+b√3)(c+d√3) = (ac+3bd) + (ad+bc)√3`
- The Pell norm `P² − 3Q²` is an integer invariant — never drifts
- The 60° tetrahedral spread `s = 3/4` is representable exactly as the fraction (3,4)

Floating-point arithmetic is a **workaround for the wrong choice of basis**. Lithic-L
is what programming looks like when you choose the right one.

---

## 2. The Type System

### 2.1 The Atomic Type: `Surd`

```
type Surd = (P: ℤ, Q: ℤ)
```

A `Surd` represents the exact rational surd `P + Q·√3` where P and Q are integers.

Hardware encoding (32-bit packed):
```
[31:16]  P  (signed 16-bit integer, rational component)
[15: 0]  Q  (signed 16-bit integer, surd coefficient)
```

Arithmetic is closed — no escape from the type:

| Operation | Rule | Notes |
|-----------|------|-------|
| `a + b` | `(Pa+Pb, Qa+Qb)` | Component-wise addition |
| `a - b` | `(Pa-Pb, Qa-Qb)` | Component-wise subtraction |
| `a * b` | `(PaPb+3QaQb, PaQb+QaPb)` | √3·√3 = 3 keeps result in field |
| `-a` | `(-Pa, -Qa)` | Negation |

**Division is not defined as a primitive.** Ratios are held as `(numerator: Surd, denominator: Surd)` 
and compared by cross-multiplication. This is not a limitation — it is the discovery that
most geometric questions (Is this angle 60°? Are these vectors perpendicular? Is this
system stable?) do not require evaluating a ratio; they require comparing two products.

### 2.2 The Pell Invariant (Unit Manifold)

A `Surd` is said to be **laminar** (on the unit manifold) when:

```
P² − 3Q² = 1
```

The Pell equation. All powers of the rotor `r = (2, 1)` = `2 + √3` satisfy this.
This is the algebraic analogue of a unit vector in Euclidean space — but exact.

The hardware Davis Gate checks this condition every cycle. If any manifold element
violates it (`P² − 3Q² ≠ 1`), it triggers Henosis (soft recovery). In software,
the `SNAP` instruction performs the same test across all active scalar registers.

### 2.3 Compound Types

```
type Quadrant  = (a: Surd, b: Surd, c: Surd, d: Surd)   -- 4-axis IVM coordinate
type Chord     = (a: Surd, b: Surd, c: Surd, d: Surd)   -- alias for Quadrant (semantic: instruction)
type Manifold  = Quadrant[13]                             -- full 13-axis SPU-13 state
type Spread    = (numer: Surd, denom: Surd)              -- rational ratio, never evaluated
```

**Quadrant coordinates** use a tetrahedral (IVM) basis. Four non-negative components
`(a, b, c, d)` with `a+b+c+d = constant` describe every point in 3-D space without
negative values. This is the Quadray coordinate system (Urner, 1994), extended to
Q(√3) field elements.

**Why four coordinates for three dimensions?** The overcomplete basis is not redundant —
it is the natural basis for a tetrahedral geometry. The XYZ Cartesian basis has three
coordinates and is overcomplete in a different way: it cannot represent 60° angles
rationally. Quadray can. The price is one extra component; the gain is closure.

### 2.4 The Spread Type (No Division)

The spread between two vectors P and Q is:

```
s(P, Q) = 1 − (P·Q)² / ((P·P)(Q·Q))
```

In Lithic-L this is **never evaluated as a decimal**. It is stored as:

```
numer = (P·P)(Q·Q) − (P·Q)²
denom = (P·P)(Q·Q)
```

Both are computed using only multiplication and subtraction. Geometric questions
become integer comparisons:

```
s = 0      ↔  numer = 0           (parallel vectors)
s = 1      ↔  numer = denom       (perpendicular, 90°)
s = 3/4    ↔  4·numer = 3·denom  (IVM 60° — the natural angle)
s = 1/2    ↔  2·numer = denom    (45°)
```

This is the foundation of Wildberger's Rational Trigonometry (2005): the geometric
question is answered by an integer polynomial identity, not by evaluating arcsin(√(3/4)).

### 2.5 Weighted Manifold Types (Sovereign Memory)

The Lithic-L type system treats **Nguyen weight as a first-class citizen**. This is the
key distinction from every Von Neumann language: you can tell the compiler (and the
hardware) *which data matters more*, and it will place that data in faster memory
automatically.

#### Static vs Dynamic weighting — both, layered

| Tier | Mechanism | When evaluated | Effect |
|------|-----------|---------------|--------|
| **Static** | Nguyen W(v) tree, `weight` attribute | Compile time / boot | BRAM18 placement oracle |
| **Dynamic** | `pressure` field, runtime impact | Every gasket tick | Runtime BRAM promotion |

They compose: `effective_weight = static_weight + pressure`. The Davis Gasket uses
`effective_weight` to decide the BRAM tier each cycle.

#### The `manifold` declaration (Laminar Lang syntax)

```lam
-- Define a 13D structural node with weight-awareness
manifold SimplexNode {
    weight 8;            -- static Nguyen weight (floor, compile-time)
    vector13 position;   -- 13-axis Synergetic coordinate
    u8 pressure;         -- runtime weight modifier (impact accumulator)
}
```

The compiler pre-calculates `W(v) = self_quad + Σ W(children)` (Nguyen Eq 2.1)
during the build phase and emits a **Weight-Map** that the SPU-13 inhales at boot.
This tells the hardware which registers to assign to BRAM18 vs SDRAM vs PSRAM before
the first instruction executes.

#### `sum_weight` — a built-in operator

```lam
let total_w : Surd = sum_weight(root_node);   -- Nguyen Eq 2.1 recursive sum
```

`sum_weight` is not a library function — it is a **compiler intrinsic** that folds
the weight tree at compile time when all weights are statically known. For dynamic
trees (runtime-constructed), it emits a `QROT`+`QADD` loop bounded by manifold depth.

#### Pressure-driven BRAM promotion ("Heave")

```lam
on_impact(wall, impact_quadrance) {
    wall.pressure += impact_quadrance;   -- dynamic weight spike
    -- Lithic-L compiler emits: wm_pressure_add() + bram_promote() check
    -- Hardware: if tier promoted → DMA copy to faster memory this tick
}
```

The `pressure` field decays at the phi_8 gate (every 8 cycles) by halving — the
same ANNE mechanic as Henosis. A high-pressure node stays in BRAM18 as long as
impacts keep arriving; it gracefully falls back to SDRAM/PSRAM when pressure drains.

#### `jitterbug` keyword

```lam
jitterbug(my_manifold, TO_OCTAHEDRON);
```

Compiles to a single `QROT` sequence stepping the Pell Invariants to the named
phase target. No trigonometry, no loop — one hardware command, executed at 60°
native speed. Named phases: `TO_VE`, `TO_ICOSAHEDRON`, `TO_OCTAHEDRON`, `TO_RETURN`.

#### Arlinghaus Central-Place Routing

High-weight functions ("hub" nodes in the call graph) are assigned dedicated
832-bit registers by the compiler. Low-weight functions ("spoke" nodes) share
a register pool. This is the hardware equivalent of Arlinghaus's hex-hierarchy
central place theory: gravity flows through the hubs, not the spokes.

```lam
-- Mark this function as a hub (will get dedicated register allocation)
@hub weight 25
fn physics_step(m: manifold) -> manifold { ... }
```

Implementation status: `spu_manifold_types.h` provides the C++ runtime layer:
`WNode`, `sum_weight()`, `WeightedManifold`, `wm_tier()`, `wm_pressure_add()`,
`bram_promote()`, `jitterbug_to()`, `wm_tick()`. Laminar Lang syntax is planned.

---

## 3. The Three-Layer Language Stack

Lithic-L is not a single language — it is a **layered stack** where each layer is
a faithful, surjective map onto the layer below:

```
Layer 3 │ Laminar Lang (.lam)    — domain language for scientists/engineers
         │      ↓  Lark parser → AST → type check → code gen
Layer 2 │ SAS (.sas)            — symbolic assembly (24 opcodes, 64-bit words)
         │      ↓  spu13_asm.py
Layer 1 │ Binary (.bin / .mem)  — 64-bit instruction words loaded into hardware
         │      ↓  BRAM or SPI flash
Layer 0 │ RTL                   — SPU-13 hardware executing at 61.44 kHz
```

Additionally, a **compact encoding** exists for the SPU-4 Sentinel:

```
Layer 3 │ Chord notation (a,b,c,d)  — 4-bit per axis, 16-bit total
         │      ↓
Layer 1 │ 16-bit Chord word         — direct hardware input to SPU-4 decoder
```

The two paths are not separate languages; they converge at the hardware boundary.
A Laminar Lang program targeting an SPU-4 Sentinel emits Chord words. Targeting
an SPU-13 Cortex, it emits 64-bit SAS words.

---

## 4. Laminar Lang: The Source Language

### 4.1 Design Principles

1. **No division operator** — `a / b` is not valid syntax. Use `spread(a, b)` which returns a `Spread` pair.
2. **No branches** — `if`/`else`/`match` are not in the language. Conditional selection is expressed as a MUX polynomial (see §5.3).
3. **No floating-point literals** — `3.14` is a syntax error. Use `surd(a, b)` or named constants from the standard prelude.
4. **No implicit coercion** — `Surd` and `Quadrant` are distinct types; mixing them requires explicit projection.
5. **Static axis iteration** — `for axis in Axes` unrolls at compile time to 13 concrete instances.

### 4.2 Lexical Structure

**Keywords:**
```
fn  let  for  in  return  surd  spread  equil  snap  log  anneal  rotor  qrot  idnt
```

**Types:**
```
Surd       -- a + b·√3
Quadrant   -- (a,b,c,d) IVM vector
Spread     -- (numer,denom) rational ratio
Axis       -- compile-time constant in 0..12
```

**Literals:**
```
surd(2, 1)     -- 2 + 1·√3  (the Pell rotor)
surd(1, 0)     -- 1  (unity)
surd(0, 0)     -- 0  (zero)
0              -- integer coerced to surd(n, 0)
```

**Operators:**
```
+  -  *        -- Surd arithmetic (exact, no division)
==  !=         -- Equality test on Surd pairs
<  >  <=  >=  -- Comparison on P component (rational part)
&              -- MUX select (Boolean polynomial, §5.3)
```

**Identifiers:** `[a-zA-Z_][a-zA-Z0-9_]*`

**Comments:** `//` line comment, `/* */` block comment

### 4.3 Formal Grammar (EBNF)

```ebnf
program       = { fn_def } ;

fn_def        = "fn" ident "(" param_list ")" "->" type_expr "{" stmt_list "}" ;

param_list    = [ param { "," param } ] ;
param         = ident ":" type_expr ;

type_expr     = "Surd" | "Quadrant" | "Spread" | "Axis" | "(" type_expr ")" ;

stmt_list     = { stmt } ;

stmt          = let_stmt
              | assign_stmt
              | return_stmt
              | for_stmt
              | log_stmt
              | snap_stmt
              | equil_stmt
              | anneal_stmt
              ;

let_stmt      = "let" ident [ ":" type_expr ] "=" expr ";" ;
assign_stmt   = ident "=" expr ";" ;
return_stmt   = "return" expr ";" ;
for_stmt      = "for" ident "in" range_expr "{" stmt_list "}" ;
log_stmt      = "log" "(" expr ")" ";" ;
snap_stmt     = "snap" "(" ")" ";" ;
equil_stmt    = "equil" "(" ")" ";" ;
anneal_stmt   = "anneal" "(" expr "," expr ")" ";" ;

range_expr    = ident            (* named range like "Axes" = 0..12 *)
              | int ".." int
              ;

expr          = primary
              | expr bin_op expr
              | unary_op expr
              | call_expr
              | mux_expr
              ;

primary       = ident
              | int_lit
              | surd_lit
              | quadrant_lit
              | "(" expr ")"
              ;

surd_lit      = "surd" "(" int_expr "," int_expr ")" ;
quadrant_lit  = "quadrant" "(" expr "," expr "," expr "," expr ")" ;

call_expr     = ident "(" [ expr { "," expr } ] ")" ;

mux_expr      = "mux" "(" expr "," expr "," expr ")" ;
              (*  mux(sel, if_true, if_false)
                  compiles to: (sel & if_true) ^ (~sel & if_false)  *)

bin_op        = "+" | "-" | "*" | "==" | "!=" | "<" | ">" | "<=" | ">=" ;
unary_op      = "-" | "~" ;

int_expr      = int_lit | ident ;
int_lit       = [ "-" ] digit { digit } ;
digit         = "0" | ... | "9" ;
ident         = letter { letter | digit | "_" } ;
```

### 4.4 Standard Prelude

The following identifiers are always in scope:

```laminar
// Field constants
let UNITY   = surd(1, 0)    // 1
let ZERO    = surd(0, 0)    // 0
let ROTOR   = surd(2, 1)    // 2 + √3  (Pell rotor, norm = 1)
let SQRT3   = surd(0, 1)    // √3
let PHI_NUM = surd(1,  1)   // 1 + √3  (near golden ratio; use with care)

// Axis range
let Axes    = 0..12         // unrolls to 13 concrete values at compile time

// Geometry functions
fn spread(a: Quadrant, b: Quadrant) -> Spread { ... }  // Rational Trigonometry
fn quadrance(a: Quadrant) -> Spread             { ... }  // ||a||² as (numer,denom)
fn rotor(r: Surd) -> Surd                       { ... }  // apply Pell rotor once
fn qrot(q: Quadrant) -> Quadrant                { ... }  // IVM rotation (a,b,c,d)→(b,c,d,a)

// Control
fn equil() -> ()    // assert Vector Equilibrium on all axes (EQUIL instruction)
fn snap()  -> ()    // assert all active registers are laminar (SNAP instruction)
```

### 4.5 Example Programs

#### Poiseuille Pipe Flow (exact parabolic profile)

```laminar
// poiseuille.lam
// 13-node exact Poiseuille flow in a cylindrical pipe.
// V(r) ∝ (R² - r²) where r = distance from centre axis.
// In Q(√3) spread terms: V(node) = center × (unity - spread(node, centre))

fn velocity(node: Axis, center: Surd) -> Surd {
    let q = surd(node * node, 0)   // radial quadrance (integer — exact)
    let r2 = surd(169, 0)          // R² = 13² = 169  (pipe radius in IVM units)
    let diff = r2 - q
    return center * diff
}

fn main() {
    let center = surd(65536, 0)    // scale factor (avoids sub-integer values)
    for axis in Axes {
        let v = velocity(axis, center)
        log(v)
    }
    snap()
}
```

#### IVM Kinematic Chain

```laminar
// kinematic_chain.lam
// 4-joint robotic arm in IVM basis.
// Each qrot() is a 60° rotation — spread(before, after) = 3/4, exactly.

fn main() {
    let arm = quadrant(1, 0, 0, 0)   // initial end-effector position

    // Apply 6 rotations (one full IVM cycle returns to origin exactly)
    for step in 0..5 {
        let arm = qrot(arm)
        log(arm)
    }

    // Verify closure: arm must equal initial value
    snap()
}
```

#### Mux-based conditional (no branching)

```laminar
// flow_selector.lam
// Select between laminar and turbulent regime without a branch.
// mux() compiles to: (sel & laminar) ^ (~sel & turbulent)

fn select_regime(reynolds: Surd, laminar_v: Surd, turbulent_v: Surd) -> Surd {
    // Reynolds < 2300 → laminar (P component comparison → integer)
    let is_laminar = reynolds < surd(2300, 0)
    return mux(is_laminar, laminar_v, turbulent_v)
}
```

---

## 5. Compilation Model

### 5.1 Overview

```
.lam source
    │
    ▼  Pass 1: Lexer + Lark parser
   AST (abstract syntax tree)
    │
    ▼  Pass 2: Type checker
   Typed AST
    │  • All literals have inferred Surd type
    │  • for-over-Axes unrolled to 13 concrete blocks
    │  • mux() validated: condition must reduce to integer boolean
    │
    ▼  Pass 3: Code generator
   .sas assembly text
    │
    ▼  spu13_asm.py (three-pass: label resolve + constant-fold + encode)
   64-bit binary instruction words
    │
    ▼  spu_forge.py build / generate_bram.py
   .mem (BRAM init) or .bin (SPI flash)
```

### 5.2 For-loop Unrolling

The `for axis in Axes` construct is **not a runtime loop**. The compiler unrolls it
to 13 consecutive instruction blocks, each with `axis` substituted as a literal.

This enforces the SPU-13's zero-branch mandate: the hardware has no loop counter,
no branch predictor, no pipeline flush. All 13 iterations execute in fixed sequence,
dispatched at Fibonacci intervals by the sequencer.

### 5.3 The MUX Polynomial Transform

The most important compilation step: every conditional expression is replaced with
a Boolean polynomial identity.

**Source (Laminar Lang):**
```laminar
return mux(sel, a, b)
```

**Emitted SAS assembly:**
```asm
; sel ∈ {0,1} (integer boolean from comparison)
; a, b are Surd registers
;
; Algebraic MUX: out = (sel × a) + (~sel × b)
;              = (sel × a) + ((1 - sel) × b)
;              = sel×a - sel×b + b
;
MUL  R_tmp, R_sel, R_a       ; tmp = sel × a
LD   R_one, 1, 0             ; one = 1
SUB  R_nsel, R_one, R_sel   ; nsel = 1 - sel
MUL  R_tmp2, R_nsel, R_b     ; tmp2 = (1-sel) × b
ADD  R_out, R_tmp, R_tmp2    ; out = sel×a + (1-sel)×b
```

This pattern has **identical latency regardless of sel**. There is no branch
misprediction cost because there is no branch. The instruction count is fixed.
This is how the SPU-13 achieves deterministic timing: not by being fast,
but by making the timing invariant.

For single-bit Verilog-level selects, this collapses further to:
```verilog
assign out = (sel & a) ^ (~sel & b);   // XOR-MUX, 1 LUT
```

### 5.4 Spread Compilation (Division Elimination)

**Source:**
```laminar
let s = spread(QR0, QR1)
```

**Emitted SAS:**
```asm
SPREAD R4, QR0, QR1    ; R4 = numer, R5 = denom  (never divides)
```

The spread is stored as two Surd registers holding numerator and denominator.
Subsequent comparisons use cross-multiplication:

```laminar
// Is spread 3/4?  → 4·numer == 3·denom
let four  = surd(4, 0)
let three = surd(3, 0)
let lhs   = four * s.numer
let rhs   = three * s.denom
snap_if(lhs == rhs)   // integer comparison — exact
```

No `arcsin`. No `cos`. No `π`. The geometric fact is verified by
multiplying two integers and checking equality.

### 5.5 Type Checking Rules

| Expression | Rule |
|------------|------|
| `surd(a, b)` | a, b must be integer literals or integer-typed idents |
| `x + y` | Both x, y must be `Surd`; result is `Surd` |
| `x * y` | Both x, y must be `Surd`; result is `Surd` |
| `spread(x, y)` | Both x, y must be `Quadrant`; result is `Spread` |
| `mux(s, a, b)` | s must be boolean (from `<`, `>`, `==`); a, b must be same type |
| `for axis in Axes` | `axis` binds as `Axis` (compile-time integer 0–12) |
| `snap()` | Valid anywhere; emits SNAP instruction |
| `equil()` | Valid anywhere; emits EQUIL instruction |

**Forbidden at type level:**
- Division (`/`) — no syntax, no runtime implementation
- Float literals — `1.414` is a lex error
- Pointer types — no addresses, no indirection
- Recursion — call graph must be a DAG (stack discipline enforced at compile time)

---

## 6. The Machine ISA (64-bit SAS Format)

### 6.1 Instruction Encoding

```
Bits [63:56]  Opcode   (8-bit)
Bits [55:48]  r1       (dest / first operand register index)
Bits [47:40]  r2       (second operand register index)
Bits [39:24]  p1_a     (immediate P component, signed 16-bit)
Bits [23: 8]  p1_b     (immediate Q component, signed 16-bit)
Bits [ 7: 0]  (reserved)
```

### 6.2 Complete Opcode Table

**Scalar Q(√3) Arithmetic**

| Mnemonic | Opcode | Operation |
|----------|--------|-----------|
| `LD Rd, P, Q` | 0x00 | `Rd ← (P + Q·√3)` |
| `ADD Rd, Rs` | 0x01 | `Rd ← Rd + Rs` |
| `SUB Rd, Rs` | 0x02 | `Rd ← Rd − Rs` |
| `MUL Rd, Rs` | 0x03 | `Rd ← Rd × Rs` via Q(√3) multiply |
| `ROT Rn` | 0x04 | `Rn ← Rn × (2+√3)` — Pell rotor step |
| `LOG Rn` | 0x05 | Print Rn (debug) |

**Control Flow**

| Mnemonic | Opcode | Operation |
|----------|--------|-----------|
| `JMP LABEL` | 0x06 | Unconditional jump |
| `SNAP` | 0x07 | Assert all regs laminar; exit 2 on failure |
| `COND Rn, LABEL` | 0x20 | Jump if Q(Rn) > 0; fall through if Q ≤ 0 |
| `CALL LABEL` | 0x21 | Push PC, jump |
| `RET` | 0x22 | Pop PC, jump |
| `NOP` | 0xFF | No operation |

**Quadray IVM**

| Mnemonic | Opcode | Operation |
|----------|--------|-----------|
| `QLOAD QRn, Rb` | 0x13 | Pack R[Rb..Rb+3] into QRn |
| `QADD QRd, QRs` | 0x10 | `QRd ← QRd + QRs` |
| `QROT QRn` | 0x11 | `(a,b,c,d) → (b,c,d,a)` — cyclic IVM rotation |
| `QNORM QRd, QRs` | 0x12 | Quadrance of QRs into QRd |
| `QLOG QRn` | 0x14 | Print Quadray (debug) |

**Geometry**

| Mnemonic | Opcode | Operation |
|----------|--------|-----------|
| `SPREAD Rd, QRa, QRb` | 0x15 | `Rd=numer, Rd+1=denom`; never divides |
| `HEX Rn` | 0x16 | Output register as hex surd |

**Vector Equilibrium & Janus Layer**

| Mnemonic | Opcode | Operation |
|----------|--------|-----------|
| `EQUIL Rd` | 0x17 | Check VE state; write tension to Rd |
| `IDNT Rd, Rs` | 0x18 | Identity monad: `Rd ← Rs` with provenance |
| `JINV Rn` | 0x19 | Janus inversion: `Rn ← (P, −Q)` — negate surd component only |
| `ANNE Rd, Rs` | 0x1A | Anneal: smooth manifold tension |

### 6.3 Register File

**Scalar registers R0–R25:** 26 × 32-bit Surd registers.

**Quadray registers QR0–QR12:** 13 × (4 × 32-bit) = 13 × 128-bit registers.
One Quadray register per SPU-13 manifold axis.

**Implicit state:**
- `PC` — program counter (not directly addressable)
- `DAVIS` — live Pell norm `P²−3Q²` for all active registers (read by SNAP/EQUIL)
- `HENOSIS` — soft recovery flag (set by hardware Davis Gate on manifold violation)

---

## 7. The Chord Encoding (SPU-4 Sentinel)

The SPU-4 uses a compact 16-bit encoding — the **Chord format** — for real-time
control signals. A Chord maps directly to a Quadray vector `(A, B, C, D)` where
each component is a 4-bit magnitude (0–15).

### 7.1 Chord Word Layout

```
Bits [15:13]  Opcode   (3-bit, 8 operations)
Bits [12:11]  Axis     (2-bit: A=00, B=01, C=10, D=11)
Bits [10: 8]  Mode     (3-bit: Linear/Rotor/Anneal/...)
Bits [ 7: 0]  Payload  (8-bit immediate: spread delta or target address)
```

### 7.2 Chord Opcodes

| Mnemonic | Opcode | Description |
|----------|--------|-------------|
| `ROTR` | 000 | Rotate manifold around selected Axis by Payload spread |
| `TUCK` | 001 | Adjust Henosis threshold τ by Payload delta |
| `SIP` | 010 | Transfer one byte between Dream Log (BRAM) and Artery FIFO |
| `LEAP` | 011 | Phase-locked unconditional jump (aligned to Piranha Pulse) |
| `SYNC` | 100 | Halt execution until next 61.44 kHz Piranha Pulse tick |
| `ANNE` | 110 | Pull manifold toward equilibrium (annealing step) |
| `IDNT` | 111 | Reset selected axis to unity `(1, 0, 0, 0)` |

### 7.3 Named Chord Constants

| Chord Name | Value `(A,B,C,D)` | Effect |
|------------|-------------------|--------|
| `IDENTITY_STRIKE` | `(9,9,9,9)` | Somatic reset: all axes to unity |
| `RESONANT_LEAP` | `(12,0,12,0)` | Enter high-intensity Mode 13 bloom |
| `PULSE_A` | `(5,0,0,0)` | Increment rotor bias on axis A |
| `PULSE_B` | `(0,5,0,0)` | Increment rotor bias on axis B |
| `PULSE_C` | `(0,0,5,0)` | Increment rotor bias on axis C |
| `PULSE_D` | `(0,0,0,5)` | Increment rotor bias on axis D |

### 7.4 Relationship to the 64-bit ISA

The Chord format is the **compressed input protocol** for the SPU-4 Sentinel.
It is not a separate language; it is a physical interface encoding. The SPU-4
hardware decoder (`spu_tetra_decoder.v`) expands each 16-bit Chord into a
sequence of 64-bit SAS instructions. The expansion table is:

```
ROTR (axis=A, payload=p)  →  ROT R_axis_a; ADD R_acc, R_axis_a
SIP  (payload=addr)       →  LD R_tmp, addr; QLOAD QR_next, R_tmp
SYNC                      →  hardware stall until CLK_PIRANHA
```

For the SPU-13 Cortex, Chords arriving over the Artery FIFO are similarly
decoded into the full 64-bit instruction stream by the Laminar Input interface.

---

## 8. Comparison with Von Neumann Languages

### 8.1 What Changes

| Concept | Von Neumann (C/Python) | Lithic-L |
|---------|----------------------|----------|
| **Atomic type** | Bit (0 or 1) | Surd `(P + Q·√3)` |
| **Number system** | Float (approximate) | Q(√3) field (exact) |
| **Conditional** | Branch instruction | MUX polynomial |
| **Iteration** | Loop with counter | Static unroll over Axes |
| **Division** | `/` operator | Not defined; use `spread()` |
| **Angle** | `float` degrees or radians | `Spread` (rational, exact) |
| **"Word size"** | 64 bits | The field Q(√3) |
| **Timing** | Clock cycles (uniform) | Fibonacci intervals (8,13,21) |
| **Error handling** | Exception / return code | Henosis (manifold recovery) |
| **Memory model** | Flat byte-addressed | Axis-strided (golden prime strides) |

### 8.2 What Stays the Same

- Functions with typed parameters and return values
- Let-bindings (immutable, like Rust/Haskell)
- Sequential composition of statements
- Modularity: programs are composed of named functions
- Testability: `snap()` and `equil()` are the assert mechanisms

### 8.3 The Closed System Property

In C, the type `double` is not closed under the operations a physicist needs.
`sqrt(2.0)` returns a `double` — an approximation. Subsequent arithmetic
compounds the error. The system is **not closed**.

In Lithic-L, the type `Surd` is closed under `+`, `-`, `*`. The Pell norm
`P²−3Q²` is an invariant that the hardware verifies every cycle. After any
number of rotations, multiplications, and additions, the manifold norm is
still an exact integer. The system is **formally closed**.

This is what the SPU-13 is: not a processor with a better floating-point unit.
It is a processor where the algebra is right, and the hardware enforces that
rightness at runtime.

---

## 9. Implementation Status

| Layer | Component | Status |
|-------|-----------|--------|
| Layer 0 | SPU-13 RTL (spu_13_top.v, spu_unified_alu_tdm.v) | ✅ 59/59 tests pass |
| Layer 0 | SPU-4 Sentinel (spu4_core.v) | ✅ Complete |
| Layer 0 | Davis Gate, Berry Gate, Janus Mirror | ✅ Complete |
| Layer 1 | 64-bit binary ISA encoding | ✅ Defined (spu_vm.py) |
| Layer 2 | SAS assembler (spu13_asm.py) | ✅ Working |
| Layer 2 | Python soft-CPU (spu_vm.py) | ✅ Working |
| Layer 2 | SAS demo programs | ✅ poiseuille, kinematic, laminar_vs_cubic |
| Layer 3 | `spu_surd.h` — Q(√3) RationalSurd arithmetic | ✅ Complete (30 tests) |
| Layer 3 | `spu_quadray.h` — 4-axis IVM Quadray + Spread | ✅ Complete (40+ tests) |
| Layer 3 | `spu_ivm.h` — Manifold13 + Nguyen weight oracle | ✅ Complete (35+ tests) |
| Layer 3 | `spu_physics.h` — Davis gasket + Jitterbug morph | ✅ Complete (all physics tests) |
| Layer 3 | `spu_lithic_l.h` — 64-bit Chord ISA + MUX primitives | ✅ Complete |
| Layer 3 | `spu_manifold_types.h` — WeightedManifold + `sum_weight` | ✅ Complete |
| Layer 3 | `demos/davis_monitor` — live Davis Law terminal demo | ✅ First end-to-end demo |
| Layer 3 | Laminar Lang parser (Python/Lark) | 🔲 Planned |
| Layer 3 | VS Code extension (.lam / .sas syntax) | 🔲 Planned |
| Hardware | Tang Primer 25K bitstream | 🔲 Board on order |

---

## 10. Roadmap

### Near-term (before board validation)
1. **Laminar Lang skeleton** — Python/Lark parser for the EBNF in §4.3; emit valid SAS
2. **VS Code TextMate grammar** — syntax highlighting for `.lam` and `.sas`
3. **std/physics.lam** — Laminar Lang ports of the physics demos

### Medium-term (after board validation)
4. **C++ emulator** — `software/vm/spu_vm.cpp` based on SynergeticsMath.hpp, 100-1000× faster than Python VM
5. **Laminar Lang type checker** — enforce §5.5 at compile time
6. **std/robotics.lam** and **std/graphics.lam** standard libraries

### Long-term
7. **MLIR dialect** — `mlir::spu13` for integration with larger compiler ecosystems
8. **WebAssembly C++ VM** — browser playground
9. **RISC-V coprocessor interface** — SPU-13 as a deterministic geometry accelerator

---

## Appendix A: Key Algebraic Identities

```
Field definition:
  Q(√3) = { a + b·√3 | a, b ∈ ℤ }

Multiplication closure:
  (a + b√3)(c + d√3) = (ac + 3bd) + (ad + bc)√3   ∈ Q(√3) ✓

Pell equation (unit manifold):
  P² − 3Q² = 1

Pell rotor:
  r = 2 + √3,   r⁻¹ = 2 − √3,   rⁿ·r⁻ⁿ = 1

After 8 rotor steps:
  r⁸ = 18817 + 10864·√3
  18817² − 3 × 10864² = 354,079,489 − 354,079,488 = 1   (exact integer)

Spread (Wildberger):
  s(P, Q) = 1 − (P·Q)² / ((P·P)(Q·Q))
           = [  (P·P)(Q·Q) − (P·Q)²  ]  /  (P·P)(Q·Q)
  
  60° IVM spread:  4 × numer = 3 × denom   (spread = 3/4)
  90° spread:      numer = denom            (spread = 1)

Davis Law (manifold stability):
  ΣABCD = 0   ↔   no cubic leak   ↔   Navier-Stokes regularity (Davis, 2024)
```

---

*Lithic-L Language Specification v1.0 — CC0 1.0 Universal — All contributions are public domain.*
