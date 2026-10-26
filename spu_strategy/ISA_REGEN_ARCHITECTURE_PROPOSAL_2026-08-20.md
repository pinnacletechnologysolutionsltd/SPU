# SPU-13 ISA Extension Proposal: REGEN as a First-Class Operation
## The Regeneration-Boundary Architecture

**Date:** 2026-08-20
**Status:** DECISION-COMPLETE PROPOSAL (all §7 decisions resolved by John;
next step is a frozen machine-actionable contract per `contract_template.md`)
**Grounded in:** `knowledge/isa_reference.md` (canonical ISA), `knowledge/rotc_tables.md`,
and the seven frozen photonic experiments (`results/sweeps/*_frozen_v1_2026-08-20.json`,
contracts `contract_photonics_*_2026-08-20.md`).

---

## 1. The proposition

The SPU-13 ISA is unusual in that its primitive operations are defined by an
exact algebraic/geometric structure (Q(√3) scalar + Quadray geometric state)
that is **the same structure encoded into the physical substrate**. The seven
frozen experiments constrain this claim quantitatively and add one genuinely
new architectural primitive:

> **REGEN** — the boundary operation that collapses a continuous physical
> (optical) state back onto the exact discrete algebraic lattice.

It is not an arithmetic instruction. It is the boundary between continuous
physical computation and exact symbolic state — and, per experiment #6, it is
primarily a **numerical scale-management device** (resetting the accumulated
normalization Sigma_total), with error correction as the secondary role.

## 2. Existing ISA mapping (what already exists)

| State type | Register file | Ops (canonical ISA) | Photonic role |
|---|---|---|---|
| Scalar Q(√3) | R0–R25 (SurdFixed64) | LD, ADD, SUB, **MUL**, **ROT** (Pell rotor), PHADD/PHCFG | MUL compiled optically (the SMUL chain); ROT = Pell rotor |
| Quadray IVM | QR0–QR12 (4-axis) | QADD, QSUB, QNORM, QLDI, **ROTC** (36-angle), **IROTC** (A5), SCALE2, LOAD2X, DELTA, MIN4 | geometric transformations; the ROTC/IROTC circulant/rotor structure is the geometric substrate |
| Control | PC, stack | JMP, CALL, RET, HALT, NOP, SNAP, EQUIL | REGEN placement must respect block boundaries |

The proposal **adds** REGEN (and the K parameter). It does not alter any
existing opcode.

## 3. REGEN: proposed semantics

```
REGEN
```

- **Action:** take the current continuous optical state (the accumulated
  K-operation product, in the normalized field representation), apply the
  **calibrated detection** (gain trim per experiment #3), run BQE, and project
  the result onto the exact SurdFixed64 / Quadray lattice. Cost ≈ 1/K
  (one regeneration per K operations). Whole-state projection (decision 1);
  no register operands.
- **Calibrated reference (mandatory, per experiment #1–#3):** the receiver
  gain trim ε* = cos(K·δφ(T)) − 1, where δφ(T) is the per-op thermal drift
  from the canonical silicon parameters and K the block length. Without it,
  the 99.9% envelope is ±1.14 K; with it, the common-mode mechanism imposes
  no boundary through K = 16 (experiment #5).
- **Dynamic-range role (primary, per experiment #6):** the continuous chain
  attenuates the field by Sigma_total = ∏σmax_i per block. REGEN resets the
  numerical scale so detection precision stays at 1/σmax (per-op) instead of
  1/Sigma_total (2.2e10 mean at K=16). REGEN is therefore a
  **scale-management instruction**, not merely a correctness instruction.
- **Fault semantics:** a REGEN whose projected result is out of the
  SurdFixed64 range, or whose calibration reference is out of the
  cos(K·δφ) > 0 regime, sets a status bit (analogous to existing
  `rotc_debug_status`/typestate fault handling) and leaves the destination
  untouched.
- **Non-architectural telemetry (decision 5 refinement):** REGEN exposes a
  debug/telemetry interface — K, Σ_total, temperature, phase compensation,
  detector headroom, calibration status, saturation/rejection counters —
  for engineering observability **without** making any of it program-visible
  ISA state. Keeps the ISA contract implementation-independent while
  preserving diagnostic access.

## 4. K as an ISA-level parameter

K = number of optical operations between regeneration boundaries is elevated
from an implementation detail to an ISA parameter:

- **Static block form:** `REGEN` marks the end of a K-op block; the block
  length K is known to the assembler/regenerator (e.g., from a `.block K` /
  `REGEN cfg` directive) and used for the compensation law and the
  normalization bookkeeping.
- **Evidence-constrained placement rules (from the frozen experiments):**
  1. Common-mode thermal drift alone: **no boundary needed through K=16**
     (experiment #5) with the compensation law.
  2. Any stochastic noise: the chain accumulates (phase random-walk,
     amplitude √K, detector ×Sigma_total) — per-op regeneration (K=1) is the
     safe default (experiment #6).
  3. **No compounding:** combined noise never does worse than the product of
     per-mechanism budgets (experiment #7) → the regeneration interval can be
     budgeted per mechanism and multiplied; a joint budget is not required.
  4. The binding depth limit is the **detector dynamic range** (Sigma_total),
     not arithmetic error: K can be large only where detection precision
     (or per-block gain) can be budgeted.
- **Economic form (the ISA's own cost model):**
  `K*(P_target, noise budget) = largest K whose block recovery >= P_target`
  with regeneration overhead ∝ 1/K — the phase diagram (experiments #5–#7)
  is the data sheet for this parameter.

## 5. Execution model (optical block + REGEN boundary)

```
        ┌─────────────── continuous optical domain ───────────────┐  ┌─ exact ─┐
MUL/SROT/ROTC/IROTC  →  op → op → … → op(K)  →  calibrated det  →  BQE → exact state
        └─────────────────────────────────────────────────────────┘  └─────────┘
        (state stays in the field representation; no hidden rounding)   REGEN
```

- Ops between REGEN boundaries operate on the continuous complex state
  (experiment #5 validated no-intermediate-rounding composition).
- The final projection is against the **independent exact oracle** for the
  whole block (experiment #5's oracle discipline), not against the previous
  optical state.

## 6. Proposed encoding sketch (post-decision)

- **Opcode:** reserve one opcode in the control/extension space
  (e.g., `0x09 REGEN`; note `0x08` is HALT, `0x0A–0x0F` free).
- **Operands:** `REGEN` (no register operands — whole-state projection,
  decision 1). Block length K is static and known to the
  assembler/regenerator via a `.block K` directive (decision 3); REGEN's
  semantics use that compile-time K for the compensation law and the
  normalization bookkeeping.
- **Semantics (per decisions 4–5):** REGEN applies, in hardware, the
  calibrated detection: gain trim ×1/cos(K·δφ_ref(T)) with T from the shared
  thermal reference, then BQE, then whole-state projection to the exact
  SurdFixed64 + Quadray lattice. Σ_total and calibration state are internal;
  atomic from the program's view.
- **Status/typestate:** extend the existing fault/typestate machinery
  (ROTC/IROTC guards) with a `REGEN_PREC` bit set when the calibrated
  reference cannot guarantee the projection (e.g., cos(K·δφ) ≤ 0, or
  Sigma_total beyond the detector budget) — the only externally visible
  bookkeeping consequence.

## 7. Open design decisions (need spec-author discussion)

**ALL RESOLVED (2026-08-20).**

1. **Granularity — whole-state REGEN.** REGEN regenerates the full machine
   state the optical block touched: scalar SurdFixed64 registers AND Quadray
   4-axis registers, one instruction, whole-state projection. Matches the
   paired multi-coordinate experiments.
2. **Calibration source — shared thermal reference.** One shared thermal
   reference for the whole optical substrate; δφ(T) = K·δφ_ref(T) scales with
   the static block length. The compensation law needs only T.
3. **K — static per-block.** K is a per-block assembler directive (`.block K`
   before the op sequence). The assembler/regenerator knows K statically;
   compensation law and normalization bookkeeping are compile-time.
4. **Trim placement — hardware trim in the REGEN datapath.** The gain trim
   (×1/cos(K·δφ)) is applied during detection by REGEN hardware; the ISA
   exposes the calibrated REGEN as one instruction; the law is baked into the
   op semantics (per experiment #3's exactness).
5. **Bookkeeping — internal to REGEN.** The accumulated normalization
   (Σ_total) and per-block calibration state are internal architectural state
   of REGEN, not exposed as program-visible registers. REGEN is atomic from
   the program's view; the `REGEN_PREC` fault bit is the only externally
   visible consequence of bookkeeping.
   **Rationale (confirmed):** Σ_total is a physical implementation quantity,
   not part of the mathematical Surd state — the ISA contract is
   `SMUL: S_a,S_b ↦ S_c`, and Σ_total belongs to the implementation realizing
   that mapping. Exposing it would leak implementation into the ISA and break
   portability across photonic / FPGA / ASIC / vector / digital-reference
   implementations of the same contract. Diagnostic observability is
   preserved through the **non-architectural telemetry interface** (§3).
   **Architectural principle (whole SPU):** *expose algebraic state; hide
   physical bookkeeping unless it is genuinely required for computation.*

## 8. Constraints ledger (the evidence bridge)

| Frozen result | ISA constraint |
|---|---|
| #1 ΔT envelope ±1.14K @ 99.9% | uncompensated operation is not viable; trim is mandatory |
| #2 calibration 1.5e-5 @ 99.9% | REGEN's reference must be calibrated (10^-5-level gain knowledge) |
| #3 ε* = cos(K·δφ) − 1 ridge | exact compensation law exists; REGEN carries it |
| #4 amp/φ/det axes, worst-axis dominance | noise budget per mechanism; worst axis sets the floor |
| #5 K-chain, B=100% @ K=16 | continuous composition is coherent under common-mode |
| #6 A≥B everywhere; Σ_total wall | REGEN = dynamic-range management; K bound by detector precision |
| #7 no compounding | K settable from single-factor budgets (product model is conservative) |

## 9. Non-goals

- NOT an implementation contract (no RTL/opcode freeze; no verification gates
  yet).
- Does NOT touch the experimental Wheeler–Feynman twin-register adapter
  profile (`docs/spu13_isa_spec.md`) or the existing opcode table.
- Does NOT decide hardware vs software split for the optical block.

---

*Status: DECISION-COMPLETE (2026-08-20). Superseded as the normative
specification by the frozen contract
`spu_strategy/contract_regen_isa_0x09_2026-08-20.md` (REGEN 0x09, `.block K`,
REGEN_PREC envelope, verification gates; the emulator
`software/tests/regen_emulator.py` is its executable reference model).*
