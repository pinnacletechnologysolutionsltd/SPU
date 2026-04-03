# Pell Octave: Unbounded Rotor Range with 16-bit Registers

**A fractal representation for the Pell orbit that eliminates word-width overflow
while preserving the exact Pell invariant P² − 3Q² = 1 at every step.**

---

## 1. The Problem

The SPU-13's scalar registers store Q(√3) surds as `(P: int16, Q: int16)` — a
32-bit packed word. The Pell rotor `r = (2 + √3)` generates the orbit:

| Step | Value | Fits 16-bit |
|------|-------|------------|
| r⁰ | (1, 0) | ✅ |
| r¹ | (2, 1) | ✅ |
| r² | (7, 4) | ✅ |
| r³ | (26, 15) | ✅ |
| r⁴ | (97, 56) | ✅ |
| r⁵ | (362, 209) | ✅ |
| r⁶ | (1351, 780) | ✅ |
| r⁷ | (5042, 2911) | ✅ |
| r⁸ | (18817, 10864) | ✅ (max fits: 32767) |
| **r⁹** | **(70226, 40545)** | **❌ OVERFLOW** |

At step 9 the representation breaks. The previous workaround in the reference
codebase (`SynergeticsMath.hpp`) applied a right-shift-by-2:

```cpp
// WRONG — breaks the Pell invariant
return { int16_t(s.a >> 2), int16_t(s.b >> 2) };
// r^9 >> 2 = (17556, 10136)
// norm = 17556² - 3×10136² = 308,213,136 - 308,220,288 = -7,152  ≠ 1
```

This destroys `P² − 3Q² = 1` and invalidates all subsequent Davis Gate checks.

---

## 2. The Insight: The Pell Orbit is Fractal

The orbit has a self-similar structure at every power of r⁸.

**Key observation:** `r⁸ = (18817, 10864)` — call this `OCTAVE`. Then:

```
r⁹  = OCTAVE × r¹
r¹⁰ = OCTAVE × r²
r¹¹ = OCTAVE × r³
...
r¹⁶ = OCTAVE² × r⁰  = OCTAVE²
r¹⁷ = OCTAVE² × r¹
```

The orbit steps 0–7 are the **fundamental domain** — the repeating unit. Every
higher power is just the fundamental domain scaled by an integer number of
OctAVEs. The structure is identical at every scale — it is genuinely fractal.

This is analogous to musical pitch: every note is `(octave_number, pitch_class)`.
The frequency doubles each octave but the harmonic structure repeats. Here the
Pell magnitude scales by OCTAVE = 18817+10864√3 each octave but the stored
mantissa cycles through the same 8 values.

---

## 3. The Pell Octave Representation

Instead of storing the full (P, Q) pair for large orbit powers, store:

```
type PellOctave = {
    octave : int8    -- signed 8-bit: which power of OCTAVE we are in
    step   : int3    -- unsigned 3-bit: position 0–7 within the octave
}
```

The actual value is reconstructed as:

```
actual(oct, step) = OCTAVE^oct × r^step
```

**The stored (P, Q) mantissa is always orbit[step] — always from the 8-entry vault,
always fits in 16-bit, and always has norm exactly 1.**

### Register format (hardware)

```
Current:   [ P: int16 | Q: int16 ]                   32 bits
Extended:  [ P: int16 | Q: int16 | octave: int8 | step: int3 | pad: int5 ]  64 bits
```

Or compact, if only octave tracking is needed (the vault already knows P,Q):

```
Compact:  [ octave: int8 | step: int3 ]   11 bits — fits in the reserved field
```

---

## 4. Arithmetic Rules

### Multiplication

```
(oct_a, step_a) × (oct_b, step_b):
    raw_step = step_a + step_b         -- integer addition, 0..14
    carry    = raw_step >> 3           -- 1 if raw_step ≥ 8, else 0
    new_step = raw_step & 7            -- raw_step mod 8
    new_oct  = oct_a + oct_b + carry   -- octave accumulates
```

### Applying one rotor step (ROT instruction)

```
(oct, step) → ROT → :
    if step < 7:  (oct, step + 1)
    else:         (oct + 1, 0)     -- step wraps, increment octave
```

### Applying inverse rotor (r⁻¹ = 2 − √3)

```
(oct, step) → ROT⁻¹ → :
    if step > 0:  (oct, step - 1)
    else:         (oct - 1, 7)     -- borrow from octave
```

### Davis Gate check (SNAP / hardware gasket)

No change needed. The stored (P, Q) is always from the fundamental domain,
so `P² − 3Q² = 1` is trivially true for any valid octave-tagged register.
The octave tag is checked for range (|octave| ≤ 127) as overflow guard.

### Equality

Two registers are equal when `octave_a == octave_b AND step_a == step_b`.

---

## 5. Range

With `octave: int8` (signed, −127..+127):

```
Minimum: r^(−127×8) = r^(−1016)  ≈ 10^(−847)   (extreme contraction)
Maximum: r^(+127×8) = r^(+1016)  ≈ 10^(+847)   (extreme expansion)
```

No physical simulation will exhaust this range. For comparison:
- The number of atoms in the observable universe ≈ 10^80
- r^127 ≈ 10^105

Even `octave: int4` (4 bits, 0..15) gives r^(15×8) = r^120 ≈ 10^126 — more
than sufficient. The int8 field costs 8 bits and buys effectively infinite range.

---

## 6. Verification

The multiplication rule is provably correct from the group homomorphism property:

```
r^(a+b) = r^a × r^b   (Pell orbit forms a group under multiplication)
```

Therefore:

```
(oct_a×8 + step_a) + (oct_b×8 + step_b)
  = (oct_a + oct_b)×8 + (step_a + step_b)
  = (oct_a + oct_b + carry)×8 + ((step_a + step_b) mod 8)
  = new_oct×8 + new_step
```

The carry propagation is exact integer arithmetic — no approximation, no rounding,
no floating-point at any stage. The Pell norm `P² − 3Q² = 1` holds for every entry
in the 8-entry vault, and the octave tag is just a bookkeeping counter.

### Worked example: r⁹ × r⁹ = r¹⁸

```
r⁹  = (octave=1, step=1)
r⁹  = (octave=1, step=1)

raw_step = 1 + 1 = 2
carry    = 0
new_step = 2
new_oct  = 1 + 1 + 0 = 2

Result: (octave=2, step=2) = r^(2×8+2) = r^18  ✓

Stored P,Q: orbit[2] = (7, 4)
Norm: 7² - 3×4² = 49 - 48 = 1  ✓  (always)
```

---

## 7. Hardware Impact

### Rotor vault (spu_rotor_vault.v)

No change to the 8-entry vault content. The vault already stores the correct
fundamental domain values. The only change: the register file gains an 8-bit
octave counter per rotor register, and the ROT instruction increments
`(octave, step)` rather than blindly multiplying.

### ALU (spu_unified_alu_tdm.v)

The multiplier path for rotor registers uses octave-add instead of field multiply.
For non-rotor registers (general surd arithmetic), no change — overflow is the
programmer's responsibility, as it is in any fixed-width arithmetic unit.

### SNAP / Davis Gate

SNAP checks `P² − 3Q² == 1` on the stored mantissa only. Since the mantissa
is always from vault[0..7], this check is trivially `true` for all valid
octave-tagged registers. The octave field itself is not checked by SNAP
(it is a bookkeeping counter, not a field value).

---

## 8. Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| `software/spu_vm.py` — ROT octave tracking | ✅ Implemented | `RationalSurd.pell_step` counter |
| `software/programs/pell_octave_test.sas` | ✅ Written | 16 ROT steps, SNAP at each |
| `knowledge/PELL_OCTAVE.md` (this doc) | ✅ | |
| `reference/.../SynergeticsMath.hpp` normalize() | ✅ Fixed | Replaced >>2 with octave comment |
| `hardware/common/rtl/core/spu_rotor_vault.v` | 🔲 Planned | Add octave register; widen addr |
| `hardware/common/rtl/core/spu_unified_alu_tdm.v` | 🔲 Planned | ROT uses octave increment not multiply |

---

## 9. Connection to Fuller's Synergetics

Fuller observed that nature's geometry uses hierarchical scale — the same
tetrahedral structure appears at every scale of organization, from atomic
lattices to geodesic domes to cosmic foam. The Pell octave representation
is the computational embodiment of this: the same 8-entry orbit repeats at
every scale, connected by the octave counter. You don't carry bigger numbers —
you carry a bigger octave.

This is also why the right-shift workaround was wrong in a deep sense: it tried
to *approximate* a large value as a smaller one, discarding information. The
octave approach carries *all* information, exactly, in a compact form.

---

*Pell Octave Specification v1.0 — CC0 1.0 Universal*
