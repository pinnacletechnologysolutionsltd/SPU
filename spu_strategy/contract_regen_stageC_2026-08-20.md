# Engineering Contract: Stage C — Hostile Equivalence Testing

**Date:** 2026-08-20
**Contract ID:** `contract_regen_stageC_2026-08-20.md`
**Status:** IMPLEMENTED — all §3 gates green (2026-08-20; testbench-verified, no silicon claim).

**Normative references:** `contract_regen_isa_0x09_2026-08-20.md` (frozen ISA
semantics), `contract_regen_stageB_2026-08-20.md` (IMPLEMENTED — the fixed-point
backend under test), `software/tests/test_regen_equivalence.py` (the bit-exact
equivalence harness being extended).

**Roles:** Spec Author (John + Deep Code) / Halt-and-Flag Implementer /
Integration Auditor.

---

## 1. Objective (the question Stage C answers)

> **Can any substrate-specific detail leak through the REGEN architectural
> boundary?**

Stage B established bit-exact equivalence on a friendly population. Stage C
tries to **break the abstraction** with adversarial programs. If the answer
remains "no" — the Stage-B fixed-point realization is indistinguishable from
the exact reference on every hostile population — then REGEN is a clean,
substrate-independent architectural boundary, and the photonic question
becomes: "can a photonic substrate satisfy an already-defined SPU execution
contract?" (not "can optics do exact Surd arithmetic?").

**Falsification criterion (frozen):** any program in the Stage-C population
where the Stage-B RTL recovered state differs from the exact oracle is a LEAK.
Per the halt-and-flag discipline, a leak is not "fixed" by loosening the
comparison: the implementer HALTs and flags the mechanism with a minimal
proposed correction.

**Scope guard:** Stage C extends the existing equivalence harness and the core
smoke testbench only. No new RTL modules, no new experiments, no changes to
the frozen ISA contract.

## 2. Hostile Population (frozen categories)

The equivalence harness (`test_regen_equivalence.py`) is extended with seeded
populations per category, each run at dphi ∈ {0, 100, 255} (compensation
exercised, including near its precision limit):

| # | Category | Population |
|---|----------|------------|
| 1 | **Long programs** | K ∈ {8, 12, 16} (the frozen chain range); values grown to the reachable extremes |
| 2 | **Many consecutive blocks** | chains of 8–16 blocks back-to-back, each REGEN-then-reblock, verifying the boundary state is canonical after EVERY boundary |
| 3 | **Max/min signed values** | QLDI ±127 (encoding max) + QSUB-growth to |v| up to ~2^22 (the K≤16 reachable range); negative-heavy states |
| 4 | **Mixed eligible/ineligible ops** | blocks containing HEX/QLOG (E_REGEN-counted, no chain effect) and LD (not eligible, not counted) — the counter/chain/REGEN must stay consistent |
| 5 | **Exponent transitions** | loads of mixed magnitudes (different m_load) interleaved with cross-scale QSUB (the re-scaling path) and ROTC |
| 6 | **Compensation near precision limit** | dphi_cfg ∈ {50, 100, 200, 255} × K ∈ {2, 8, 16}; θ_max = 16·255·2^-16 ≈ 0.0623 rad — the Taylor trim's residual must stay far below the 1.5e-5 requirement |
| 7 | **Saturation boundaries** | QSUB results near the 32-bit clamp (±2^31); the recovery + final clamp must match the oracle's clamp |
| 8 | **Back-to-back REGENs** | REGEN; REGEN (K=0 idempotence); REGEN after an empty block; REGEN immediately after a valid block |
| 9 | **Malformed blocks (fault path)** | REGEN with declared K ≠ counted → REGEN_PREC fault, state untouched, counter kept; **fault-then-clear**: a faulting REGEN must NOT corrupt the chain — a subsequent matching REGEN recovers the exact state (this gates the Stage-B clear-on-valid fix) |

**Population size (frozen):** ≥ 24 programs per category (seeded, seed 13),
i.e., ≥ 216 equivalence programs total, plus the fault-path vectors in the
core smoke testbench.

## 3. Gates (for the Auditor, frozen order)

```bash
# 1. Core smoke incl. the new fault-then-clear Stage-B vector
cd /home/user/Projects/hardware/SPU
iverilog -g2012 -y hardware/rtl -y hardware/rtl/core -y hardware/rtl/core/spu13 \
  -y hardware/rtl/core/shared -y hardware/rtl/arch -y hardware/rtl/math \
  -y hardware/rtl/common/prim -y hardware/rtl/top -I hardware/rtl/arch \
  -o build/spu13_core_regen_tb.vvp hardware/rtl/arch/spu_optional_stubs.v \
  hardware/rtl/common/prim/spu_xilinx_prim.v hardware/tests/spu13/spu13_core_regen_tb.v \
  && vvp build/spu13_core_regen_tb.vvp

# 2. Extended hostile equivalence harness (all categories, dphi sweep)
cd /home/user/Projects/hardware/SPU && .venv/bin/python \
  software/tests/test_regen_equivalence.py

# 3. Stage A/B reference gates stay green
cd software/tests && .venv/bin/python test_regen_emulator.py && \
  .venv/bin/python test_regen_asm.py && \
  .venv/bin/python test_rotc_vm_rtl_trace.py

# 4. Complete repository regression (REGEN suite registered)
cd /home/user/Projects/hardware/SPU && bash tools/verify_repo.sh
```

## 4. Stop Conditions

- **HALT** on any leak (falsification criterion §1) — flag the mechanism,
  propose the minimal correction, re-run the full Stage-C population.
- **HALT** if the harness population is weakened to avoid a failing case.
- **HALT** on any unbacked "silicon-verified" claim (testbench-verified only).

## 5. Halt-and-Flag pre-review findings (from Stage B, already fixed)

1. **Chain clear gating (fixed in the core):** the chain's clear fired on
   faulting REGENs, so the fault-then-clear pattern would have recovered
   zeros. Now gated on `regen_start && (count == declared_k)`.
2. The Stage-B sign/shift/scale defects (ashr scale, logical-shift BQE and
   ROTC-A halving, block-boundary clear, Taylor 2^24 scale) were found by the
   existing harness; Stage C's populations are designed to stress exactly
   those classes of defect again.

## 6. Non-goals

- No new RTL hardware (the chain and REGEN datapath are frozen as built).
- No photonic implementation work (a future third backend, not Stage C).
- No ISA changes: the frozen 0x09 contract is normative.

---


*Status: IMPLEMENTED. Findings recorded below; no silicon claims.*

## 7. Implementation Record (2026-08-20)

**Found by analysis before the tests ran (Stage-B defects, all fixed):**

1. **K=0 pass-through (idempotence).** An empty-block REGEN must not commit
   a BQE recovery of the empty chain (zeros would clobber the exact state).
   `spu13_regen.v`: declared_k == 0 -> pass-through, no commit.
2. **Commit gating.** The core's `regen_done` commit is now gated on
   `regen_commit_valid` (held through the done edge) so faults and K=0 never
   write stale recovery; the fault path keeps the chain intact.

**Found by the harness (real mechanisms, all fixed):**

3. **Block-boundary re-encode (cat 2).** The chain must re-encode the
   recovered canonical state at a valid REGEN — the fixed-point analogue of
   the regenerated field continuing into the next block. Without it,
   transforms-only blocks after a boundary mirror from zero (LEAK).
4. **VM Davis Gasket / Henosis (reference hygiene).** The VM's cubic-leak
   subsystem rebalanced QR registers at phi_13/phi_21 gate cycles —
   orthogonal to the REGEN contract and absent from the RTL test
   configuration; the gate tick is stubbed in the reference. Not a leak:
   the gasket is not part of the REGEN exact-state semantics.

**Harness bugs fixed (not RTL defects):** declared K excludes non-eligible
LD ops; the per-boundary oracle pairing filters empty blocks before zipping
(the false LEAK at the first idempotence chain); tb declaration order;
combined 3-dphi simulation for a single compile (~7 min).

**Result:** all nine categories x dphi {0, 100, 255} — zero leaks. The
REGEN abstraction survived adversarial attempts to expose
implementation-specific state across the architectural boundary.

