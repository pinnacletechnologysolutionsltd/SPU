# IROTC — Icosahedral Rotation Opcode Specification (v0.2)

**Status: VM implemented and verified; no RTL, no silicon.** The
mathematical basis is machine-checked
(`software/tests/test_icosahedral_catalog.py`, 22 checks, catalog checksum
`aabef37c9c8b0317`); findings in `docs/ICOSAHEDRAL_QUADRAY_CATALOG.md`.
VM implementation 2026-07-10 (`software/spu_vm.py`, opcodes live in the
main dispatch; table generated + checksum-verified at first dispatch from
`software/lib/irotc_catalog.py`, regenerated via
`test_icosahedral_catalog.py --emit-vm`). Verification: trace equivalence
(`test_irotc_vm_trace.py`), poison proofs (`test_irotc_poison.py`), chain
tests (`test_irotc_chains.py`). Opcode numbers are provisional in the
Lucas MAC sidecar probe space.

**v0.2 (2026-07-10): the DOUBLED tag is a 4-state typestate, not one
bit.** v0.1's rule "IROTC (any index, either catalog) preserves DOUBLED"
was unsound: the doubling theorem composes only *within* one catalog.
Mixed-catalog quadray products `conj(M₁)·M₂` leave ½Z[φ] (denominators
reach 4 — machine-checked, oracle check 20), so a main-then-conjugate
chain produces odd pre-shift sums that the unguarded `>>>1` would
silently truncate (101/200 random VM chains reproduced the corruption).
Register plane decision (same date): the φ-plane **overlays the QR
register file** — Z[φ] pair `(a, b)` in the same component slots as the
`(P, Q)` surd packing — so the cross-plane tag transitions in §3 are
enforceable on real registers.

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

## 3. The DOUBLED typestate (v0.2: four states, 2 bits per register)

Two bits per quadray register in the φ-plane register file. The doubling
is not preprocessing — it is an intrinsic part of the rotational
operation in ½Z[φ] (the matrices are `N/2`; the doubled representation is
what makes the arithmetic closed over Z[φ]). Accordingly the tag is a
**data-plane state, ordered as a prefix of the operation-trace states**:
in the Lucas MAC harness machine the rotation micro-program's trace is

```
IDLE → DOUBLED → SCALED → … (PSCALE/ADD accumulation) → COMMIT
```

and no PSCALE transition belonging to a rotation micro-program may fire
from a register that has not passed through DOUBLED.

The four states (`spu_vm.py` `PHI_*` constants):

| State | Encoding | Meaning | IROTC license |
|---|---|---|---|
| `UNTAGGED` | 00 | no divisibility guarantee | none — faults |
| `FRESH` | 01 | componentwise even (fresh `LOAD2X`/`SCALE2` output) | **either** catalog |
| `MAIN` | 10 | output of a main-catalog `IROTC` | main only |
| `CONJ` | 11 | output of a conjugate-catalog `IROTC` | conjugate only |

Why `FRESH` splits: an even vector satisfies `N·w ≡ 0 (mod 2)` for
*every* integer matrix. But a rotated vector `w = 2Mv` is generally odd;
its next step is licensed by `N_a·N_b = 2·N_ab`, which holds only inside
one A₅. Products across the two catalogs leave ½Z[φ], so `MAIN` and
`CONJ` are mutually exclusive licenses. `SCALE2` re-conditions any
register back to `FRESH` (at the cost of one factor-of-2 in scale —
program-level bookkeeping, same convention family as Q12).

Transition algebra (each rule VM-implemented and test-pinned):

| Event | Effect on state |
|---|---|
| `LOAD2X`, `SCALE2` | → `FRESH` |
| `IROTC` main / conjugate | `FRESH`/matching state → `MAIN` / `CONJ`; mismatched state → **CATMIX fault** |
| `QADD`/`QSUB` | lattice join: `FRESH` yields to the other operand; equal states preserve; `MAIN`+`CONJ` or any `UNTAGGED` → `UNTAGGED` |
| `PCHIRAL` | swaps `MAIN` ↔ `CONJ`, fixes `FRESH` (conjugation is a ring automorphism carrying one license to the other). **Spec-only in the VM** — PCHIRAL is a sidecar op (silicon-verified over J11) with no VM handler, so this transition has no executable proof until the RTL phase; the VM route to the conjugate catalog is `SCALE2` → `FRESH` → `IROTC[sel[6]=1]` |
| A₄ bypass `ROTC` (0,2,5,15–23) | **preserved** (these 12 lie in both catalogs; enables alias interop) |
| octahedral `ROTC` (24–35) | `FRESH` → `FRESH`; `MAIN`/`CONJ` → `UNTAGGED` (integer but not in A₅: sandwiches `M₂·O·M₁` leave ½Z[φ]) |
| thirds `ROTC` (angles 1,3,4,6–14) | → `UNTAGGED` — thirds output breaks A₅ divisibility safety |
| raw load, `QROT`, `QNORM`, `MIN4`, `ANNE`, Henosis pulse | → `UNTAGGED` (Henosis halves components in place — it un-doubles) |
| `QREAD` | copies the source state (bit-identical copy) |

The Davis gate is unaffected: `ΣABCD = 0` is scale-invariant, so the
stability machinery needs no changes. Readback is in half-units — the
same convention family as the existing Q12 fixed-point scaling.

## 4. Dispatch guard and faults (poison discipline)

IROTC guards **only at dispatch** — the same pattern and cost as the
ROTC bad-angle gate; there is no divisibility check anywhere in the
micro-program hot path (no branches in hot paths). Decode order:

- `IROTC_ERR_BADIDX` — `sel[5:0] > 59` (checked first: index decode
  precedes the operand read).
- `IROTC_ERR_UNTAGGED` — source register state is `UNTAGGED`.
- `IROTC_ERR_CATMIX` — source register is catalog-locked the other way
  (`MAIN` source with `sel[6]=1`, or `CONJ` source with `sel[6]=0`).
  Recovery: `SCALE2` re-conditions to `FRESH`. (v0.2 — see header.)

All faults must leave the destination register bit-identically untouched
(including its tag state) and raise the fault flag; all require
poison-value proofs on VM and RTL, mirroring `test_rotc_bad_angle.py`
and the ROTC gate testbenches. VM proofs: `test_irotc_poison.py`.

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

## 6. Engine shape and cost (settled 2026-07-10: term-serial, 13-slot)

Implemented: `hardware/rtl/core/spu13/spu13_irotc_engine.v`. The v0.1
micro-program cost model (PSCALE/ADD decomposition chains, worst case
~27 steps, 21-vs-34-slot dilemma) is superseded: each alphabet value is
a **single-cycle signed map** on a Z[φ] pair, so one shared term unit
executes every rotation in a fixed slot:

```
  ×0 : (0, 0)              ×±1 : ±(a, b)          ×±2 : ±(a+a, b+b)
  ×±φ : ±(b, a+b)          ×±φ⁻¹ : ±(b−a, a)      ×±√5 : ±(2b−a, 2a+b)

  cycle 0     dispatch: guards (BADIDX → UNTAGGED → CATMIX), latch
  cycles 1-9  acc[row] += code(idx,row,col) × w[col]  (×0 burns the cycle)
  cycle 10    acc >>>= 1        (unguarded — typestate-licensed)
  cycle 11    A = −(B+C+D); done, out_tag
  cycle 12    done visible; engine re-dispatchable
```

**Fixed 13-cycle slot for all 60 indices × both catalogs** — lands on the
φ₁₃ meso gate; latency is uniform (deterministic, no index dependence).
This is signed exact Z[φ] arithmetic, NOT the mod-L_p plane of
`spu13_lucas_mac.v` — the engine has its own adders (no multipliers, no
DSPs; generic synth ≈ 6.9k gates incl. the ROM-as-logic). Coefficients:
60×9 4-bit codes (`spu13_irotc_codes.mem`, GENERATED via
`test_icosahedral_catalog.py --emit-rtl`); the conjugate catalog is the
code remap 5↔8, 6↔7, 9↔10 in hardware — no second table.

## 7. Verification plan (before any RTL)

1. ✅ VM: `IROTC`/`LOAD2X`/`SCALE2` + typestate semantics; table
   generated from the oracle, never hand-copied (checksum-checked at
   first dispatch). Assembler mnemonics in `spu13_asm.py` + the VM's
   inline assembler (bit-identical encodings, verified).
2. ✅ Trace oracle: VM-vs-exact-Fraction equivalence over all 60 × both
   catalogs on tagged inputs, junk-A rejection, A₄ alias interop
   (`test_irotc_vm_trace.py`, 9 checks).
3. ✅ Poison proofs for all three fault codes + decode precedence + SCALE2
   re-conditioning (`test_irotc_poison.py`, 14 checks).
4. ✅ Chain tests: 10-step pure-main and pure-conjugate chains exact;
   thirds-ROTC mid-chain faults the next IROTC without corruption;
   octahedral demotion; QADD lattice (`test_irotc_chains.py`, 12 checks).
5. 🟨 RTL engine done (`spu13_irotc_engine.v` + `spu13_irotc_engine_tb.v`:
   120 golden cases from the derivation oracle bit-exact — the same
   oracle the VM is trace-equivalent to, closing VM↔RTL transitively —
   fixed 12-clock latency pinned on every case, 10-step back-to-back
   chain, full fault matrix incl. poison holds; generic yosys synth
   clean, 0 DSP). Remaining: sidecar/SPI integration (0xB1 opcodes
   0xD6-0xD8, tag storage beside the QR file), Tang 25K probe, Artix-7.

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
