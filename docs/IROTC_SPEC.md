# IROTC — Icosahedral Rotation Opcode Specification (v0.1)

**Status: specification only.** The mathematical basis is machine-checked
(`software/tests/test_icosahedral_catalog.py`, 21 checks, catalog checksum
`aabef37c9c8b0317`); findings in `docs/ICOSAHEDRAL_QUADRAY_CATALOG.md`.
No VM implementation, no RTL, no silicon. Opcode numbers are provisional
in the Lucas MAC sidecar probe space. Spec fixed 2026-07-10.

## 1. Why a new opcode (not new ROTC angles)

The ROTC angle field is 6 bits (0–63). The verified catalog already uses
0–35, and one icosahedron adds 48 rotations: 36 + 48 = 84 > 64. The
icosahedral family therefore **cannot** extend the ROTC angle space —
IROTC gets its own opcode and its own 6-bit index space (0–59, the full
A₅ including the 12 A₄ members, so chains never mix opcode spaces
mid-program).

The operand field is also a different arithmetic plane: IROTC components
are Z[φ] pairs `(a, b)` meaning `a + b·φ` — the Lucas MAC operand format,
not the Q(√3) `RationalSurd` packing.

## 2. Opcodes (provisional encodings, Lucas MAC sidecar space)

The sidecar probe opcodes occupy `0xD0–0xD5` (PSCALE, PCHIRAL, PMUL,
PINV, PHSLK×2), delivered via SPI `CMD 0xB1`. IROTC continues the block:

| Mnemonic | Provisional | Operands | Semantics |
|---|---|---|---|
| `IROTC`  | `0xD6` | `qrD, qrS, sel` | Apply icosahedral rotation `sel[5:0]` to qrS's (B,C,D), recompute A from zero-sum, write qrD. `sel[6]` = conjugate-catalog flag (§5). `sel[7]` reserved 0. |
| `LOAD2X` | `0xD7` | `qrD, imm` | Load immediate shifted left 1 (both halves of each Z[φ] pair); set qrD's DOUBLED tag. |
| `SCALE2` | `0xD8` | `qrD, qrS` | `qrD = qrS + qrS`; set DOUBLED tag (runtime conditioning for data that arrives undoubled, e.g. via the southbridge). |

Operand layout mirrors ROTC (`p1_a[5:0]` = index, high bits = flags) so
the decoder pattern carries over.

## 3. The DOUBLED tag

One bit per quadray register in the φ-plane register file. The doubling
is not preprocessing — it is an intrinsic part of the rotational
operation in ½Z[φ] (the matrices are `N/2`; the doubled representation is
what makes the arithmetic closed over Z[φ]). Accordingly DOUBLED is a
**data-plane state, ordered as a prefix of the operation-trace states**:
in the Lucas MAC harness machine the rotation micro-program's trace is

```
IDLE → DOUBLED → SCALED → … (PSCALE/ADD accumulation) → COMMIT
```

and no PSCALE transition belonging to a rotation micro-program may fire
from a register that has not passed through DOUBLED.

Tag algebra (each rule verified by the oracle):

| Event | Effect on DOUBLED |
|---|---|
| `LOAD2X`, `SCALE2` | **set** |
| `IROTC` (any index, either catalog) | **preserved** (doubling theorem: `N_a·N_b = 2·N_ab`, so every pre-division sum in an A₅ chain is even) |
| `QADD`/`QSUB` with both operands tagged | **preserved** (linearity) |
| `PCHIRAL` | **preserved** (conjugation is a ring automorphism; enables the dual catalog) |
| thirds `ROTC` (angles 1,3,4,6–14) | **cleared** — the DOUBLED→PENDING harness transition; thirds output breaks A₅ divisibility safety |
| `QADD`/`QSUB` with mixed tags | **cleared** (scale incoherence; assembler should warn) |
| raw load over the register | **cleared** |

The Davis gate is unaffected: `ΣABCD = 0` is scale-invariant, so the
stability machinery needs no changes. Readback is in half-units — the
same convention family as the existing Q12 fixed-point scaling.

## 4. Dispatch guard and faults (poison discipline)

IROTC has **exactly one guard, at dispatch** — the same pattern and cost
as the ROTC bad-angle gate; there is no divisibility check anywhere in
the micro-program hot path (no branches in hot paths):

- `IROTC_ERR_UNTAGGED` — source register's DOUBLED tag is clear.
- `IROTC_ERR_BADIDX` — `sel[5:0] > 59`.

Both faults must leave the destination register bit-identically untouched
and raise the fault flag; both require poison-value proofs on VM and RTL,
mirroring `test_rotc_bad_angle.py` and the ROTC gate testbenches.

## 5. Canonical index space and the conjugate catalog

Ordering rule (deterministic, no hand numbering): sort all 60 rotations
by `(period, row-major numerator key)` where the numerator key of an
entry is the integer pair `(a, b)` of `2M` in Z[φ]. Index 0 is the
identity. The oracle pins the resulting catalog with SHA-256 prefix
`aabef37c9c8b0317`; VM table, RTL, and the appendix table below must stay
bit-identical to it (regenerate with
`python3 software/tests/test_icosahedral_catalog.py --emit`).

Layout: idx 0 identity · 1–15 period 2 (all self-inverse) · 16–35
period 3 · 36–59 period 5 (twelve ±72°, twelve ±144°). Inverse is always
a single catalog index (inverse = transpose).

**A₄ aliases** (verified against the VM's bypass permutation semantics):
idx 0→ROTC 0, 1→21, 11→22, 12→23, 16→17, 17→19, 26→18, 27→2, 28→20,
29→5, 33→15, 34→16. Programs may use either encoding for these 12; the
IROTC path also works on untagged data for them in principle (integer
matrices), but for uniformity the tag guard applies to all indices.

**Conjugate catalog** (`sel[6] = 1`): apply the Galois conjugate
(φ → 1−φ) of the indexed numerator matrix — equivalently
PCHIRAL ∘ R ∘ PCHIRAL. This reaches the dual-orientation icosahedron's
48 new rotations with the same index space and the same costs; the two
catalogs share exactly the 12 A₄ aliases (conjugation fixes rational
matrices, so `sel[6]` is a don't-care for aliased indices).

## 6. Micro-program shape and cost

Per output component: accumulate over the three inputs with coefficients
from the numerator alphabet, then one shared arithmetic shift right:

```
  ×0 : skip            ×±1 : ADD/SUB          ×±2 : ADD twice
  ×±φ : PSCALE, ADD    ×±φ⁻¹ : PSCALE, ADD, SUB (φx − x)
  ×±√5 : PSCALE, ADD×2, SUB (2φx − x)
  finally: out = acc >>> 1   (unguarded — licensed by DOUBLED)
```

No PMUL, no PINV, no DSPs. Cost bounds from the catalog: worst rotation
is 8 PSCALE + 16 ADD/SUB (+3 shifts); the A₄ aliases are 0 PSCALE.
Sequencer note: PSCALE is 1-cycle/0-DSP on the existing sidecar, so a
worst-case IROTC is a ~27-step micro-program before overlap — dispatch
fits inside a single Fibonacci slot (21) only with 2 ops/cycle; otherwise
IROTC occupies the 34 slot. To be settled at RTL design time.

## 7. Verification plan (before any RTL)

1. VM: implement `IROTC`/`LOAD2X`/`SCALE2` + tag semantics; table
   generated from the oracle, never hand-copied (checksum-checked).
2. Trace oracle: VM-vs-exact-Fraction equivalence over all 60 × both
   catalogs on tagged inputs (style of `test_rotc_vm_rtl_trace.py`).
3. Poison proofs for both fault codes.
4. Chain tests: doubled load → mixed 10-step A₅ chains exact;
   thirds-ROTC-in-the-middle must fault the subsequent IROTC (tag
   cleared), not corrupt.
5. RTL micro-program engine on the Lucas MAC; bit-exact against VM.

## Appendix A — canonical catalog (generated, do not hand-edit)

`python3 software/tests/test_icosahedral_catalog.py --emit`

| idx | period | inverse | ROTC alias | angle | PSCALE | ADD/SUB |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 0 | 0 | 0° | 0 | 6 |
| 1 | 2 | 1 | 21 | 180° | 0 | 10 |
| 2 | 2 | 2 | — | 180° | 6 | 14 |
| 3 | 2 | 3 | — | 180° | 5 | 12 |
| 4 | 2 | 4 | — | 180° | 5 | 12 |
| 5 | 2 | 5 | — | 180° | 6 | 12 |
| 6 | 2 | 6 | — | 180° | 6 | 12 |
| 7 | 2 | 7 | — | 180° | 5 | 12 |
| 8 | 2 | 8 | — | 180° | 6 | 14 |
| 9 | 2 | 9 | — | 180° | 6 | 12 |
| 10 | 2 | 10 | — | 180° | 5 | 12 |
| 11 | 2 | 11 | 22 | 180° | 0 | 10 |
| 12 | 2 | 12 | 23 | 180° | 0 | 10 |
| 13 | 2 | 13 | — | 180° | 5 | 12 |
| 14 | 2 | 14 | — | 180° | 6 | 14 |
| 15 | 2 | 15 | — | 180° | 5 | 12 |
| 16 | 3 | 26 | 17 | ±120° | 0 | 10 |
| 17 | 3 | 28 | 19 | ±120° | 0 | 10 |
| 18 | 3 | 22 | — | ±120° | 4 | 14 |
| 19 | 3 | 20 | — | ±120° | 4 | 14 |
| 20 | 3 | 19 | — | ±120° | 8 | 16 |
| 21 | 3 | 23 | — | ±120° | 6 | 14 |
| 22 | 3 | 18 | — | ±120° | 8 | 16 |
| 23 | 3 | 21 | — | ±120° | 6 | 14 |
| 24 | 3 | 31 | — | ±120° | 6 | 14 |
| 25 | 3 | 30 | — | ±120° | 6 | 14 |
| 26 | 3 | 16 | 18 | ±120° | 0 | 10 |
| 27 | 3 | 29 | 2 | ±120° | 0 | 6 |
| 28 | 3 | 17 | 20 | ±120° | 0 | 10 |
| 29 | 3 | 27 | 5 | ±120° | 0 | 6 |
| 30 | 3 | 25 | — | ±120° | 6 | 14 |
| 31 | 3 | 24 | — | ±120° | 6 | 14 |
| 32 | 3 | 35 | — | ±120° | 8 | 16 |
| 33 | 3 | 34 | 15 | ±120° | 0 | 10 |
| 34 | 3 | 33 | 16 | ±120° | 0 | 10 |
| 35 | 3 | 32 | — | ±120° | 4 | 14 |
| 36 | 5 | 39 | — | ±72° | 4 | 14 |
| 37 | 5 | 49 | — | ±72° | 4 | 14 |
| 38 | 5 | 48 | — | ±72° | 5 | 12 |
| 39 | 5 | 36 | — | ±72° | 8 | 16 |
| 40 | 5 | 54 | — | ±144° | 4 | 14 |
| 41 | 5 | 50 | — | ±144° | 4 | 14 |
| 42 | 5 | 46 | — | ±72° | 5 | 12 |
| 43 | 5 | 56 | — | ±144° | 5 | 12 |
| 44 | 5 | 53 | — | ±144° | 5 | 12 |
| 45 | 5 | 57 | — | ±72° | 5 | 12 |
| 46 | 5 | 42 | — | ±72° | 5 | 12 |
| 47 | 5 | 59 | — | ±144° | 8 | 16 |
| 48 | 5 | 38 | — | ±72° | 5 | 12 |
| 49 | 5 | 37 | — | ±72° | 8 | 16 |
| 50 | 5 | 41 | — | ±144° | 8 | 16 |
| 51 | 5 | 55 | — | ±144° | 5 | 12 |
| 52 | 5 | 58 | — | ±72° | 8 | 16 |
| 53 | 5 | 44 | — | ±144° | 5 | 12 |
| 54 | 5 | 40 | — | ±144° | 8 | 16 |
| 55 | 5 | 51 | — | ±144° | 5 | 12 |
| 56 | 5 | 43 | — | ±144° | 5 | 12 |
| 57 | 5 | 45 | — | ±72° | 5 | 12 |
| 58 | 5 | 52 | — | ±72° | 4 | 14 |
| 59 | 5 | 47 | — | ±144° | 4 | 14 |
