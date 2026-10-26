# Engineering Contract: Stage B — Fixed-Point REGEN Datapath (FPGA Reference Backend)

**Date:** 2026-08-20
**Contract ID:** `contract_regen_stageB_2026-08-20.md`
**Status:** IMPLEMENTED — all §5 gates green (2026-08-20; testbench-verified, no silicon claim).
**Role (frozen 2026-08-20):** the **deterministic reference implementation** of
the REGEN v1 contract — the fixed-point realization against which any future
substrate (photonic or otherwise) is compared for bit-exact architectural
equivalence.
**Status note:** was DRAFT — awaiting freeze (implementation contract per the frozen
scoping contract `contract_regen_verilog_scope_2026-08-20.md`, Stage B)

**Normative references:** `contract_regen_isa_0x09_2026-08-20.md` (frozen ISA
semantics), `contract_regen_stageA_2026-08-20.md` (Stage A — this builds on
its plumbing), the emulator reference model (`software/tests/regen_emulator.py`,
`FpgaReferenceBackend`), the seven frozen photonic experiments
(`results/sweeps/*_frozen_v1_2026-08-20.json`).

**Roles:**
- **Spec Author:** John + Deep Code.
- **Halt-and-Flag Implementer:** pre-review (see §7).
- **Integration Auditor:** executes §5 gates; evidence-ledger discipline.

---

## 1. Objective (the question Stage B answers)

> **Can the REGEN contract be implemented as an ordinary deterministic
> fixed-point datapath, with the same architectural behavior, before we
> attempt to reproduce it optically?**

Stage B is a **second real implementation** of the frozen REGEN contract — an
FPGA reference backend — deliberately separated from the photonic proof. The
photonic implementation becomes a *third backend*; the ISA does not depend on
any one of them.

**Primary requirement (frozen): bit-exact architectural equivalence.** For
identical programs and inputs:

```
Digital reference ≡ Stage-A RTL ≡ Stage-B fixed-point RTL ≡ VM
```

(where applicable — the architectural state after REGEN is identical).

**Secondary requirement (frozen, measured SEPARATELY):** the implementation's
internal numerical error (the fixed-point chain's deviation from the exact
field) is measured and reported as telemetry — never part of the ISA
semantics.

**Scope guard (per Spec Author): this is NOT another experiment.** It is one
new fixed-point chain module + a REGEN datapath upgrade + an equivalence
harness. No new Monte Carlo work.

## 2. Frozen Design Decisions

### 2.1 Fixed-point chain (`fpga_chain.v`, new Lithic module, 50–150 lines)

- Mirrors the **E_REGEN state-transform ops** in fixed-point arithmetic:
  QLDI (encode), IDNT (identity), QSUB (subtract), ROTC (circulant F,G,H),
  DELTA (load). Output ops HEX/QLOG do not change QR state → no chain effect.
  IROTC is excluded when `ENABLE_IROTC=0` (per E_REGEN).
- **2-normalized normalization:** per-op σ' = 2^ceil(log2 σmax) (power of
  two); the field is normalized per op so amplitudes stay bounded; the
  accumulated Σ_total = ∏σ' = 2^m is a wide (≥ 40-bit) exponent-accumulated
  counter. **The BQE divide by Σ_total is therefore a shift** (the point of
  2-normalization).
- **Fixed-point format (frozen):** 32-bit Q2.30 (2 integer, 30 fractional),
  two's complement — the per-op normalized field components are bounded in
  [−2, 2). Multiplies use the existing exact-multiplier discipline
  (rational_surd5-style or primitive mults; no float).
- **Per-op common-mode rotation (compensation exercise):** an input
  `dphi_cfg[7:0]` (units: 2^-16 rad) applies a deterministic per-op rotation
  to the field, modeling the frozen common-mode drift. Default 0
  (drift-free). The REGEN trim must restore bit-exactness at non-zero dphi —
  this exercises the frozen compensation law (experiment #3) in hardware.

### 2.2 REGEN datapath upgrade (`spu13_regen.v`)

- The Stage-A pass-through measurement tie is replaced by the **real
  measurement interface** (frozen in the scoping contract §3):
  `bk_meas_a/b`, `bk_angle_K`, `bk_sigma`, `bk_valid`, `bk_scale`, now driven
  by `fpga_chain` (not tied to `regen_start`).
- REGEN applies: **trim** ×1/cos(K·δφ) via a fixed-point cosine LUT, then
  **BQE** (shift by m + scale + round), then whole-state commit.
- **Trim precision (frozen, the honest constraint):** the LUT must meet the
  frozen experiment #2 requirement — relative gain error ≤ 1.5e-5 — for
  bit-exact recovery at |x| ≤ 32767. A 256-entry × 20-bit piecewise LUT is
  the reference; the equivalence gate at non-zero dphi is the arbiter.
- Fault semantics unchanged (REGEN_PREC on K mismatch / out-of-envelope;
  state untouched; counter kept on fault).

### 2.3 Numerical-error telemetry (non-architectural)

- `fpga_chain` exposes the final measurement and Σ as
  `regen_debug_status`-style telemetry (extension of the Stage-A layout).
- **Separate numerical-error report** (harness-side): the equivalence harness
  compares the chain's field trace against the exact field and reports
  per-op max deviation — a diagnostic, never part of the ISA contract
  (frozen ISA contract §2.4: expose algebraic state, hide physical
  bookkeeping).

## 3. Scoped Files

| File | Change |
|---|---|
| `hardware/rtl/core/spu13/fpga_chain.v` | **NEW** Lithic fixed-point chain (2-normalized, Q2.30, dphi_cfg) |
| `hardware/rtl/core/spu13/spu13_regen.v` | REGEN datapath: real trim (cos LUT) + BQE (shift+round) consuming the bk_* interface |
| `hardware/rtl/core/spu13/spu13_core.v` | Wire `fpga_chain` to the REGEN measurement interface; chain inputs from the QR datapath; keep Stage-A plumbing |
| `hardware/tests/spu13/spu13_regen_tb.v` | Extend: measurement-interface vectors (real bk_meas/bk_sigma paths) |
| `hardware/tests/spu13/spu13_core_regen_tb.v` | Extend: dphi=0 and dphi≠0 programs |
| `software/tests/test_regen_equivalence.py` | **NEW** bit-exact equivalence harness (Digital ≡ Stage-A RTL ≡ Stage-B RTL ≡ VM) + numerical-error report |

## 4. Verification Vectors (frozen)

| Vector | Expectation |
|---|---|
| K ∈ {1,2,4}, dphi=0, random QLDI/QSUB/ROTC blocks | Stage-B REGEN == exact QR result (bit-exact) |
| K=2, dphi≠0 (compensation exercised) | Stage-B REGEN == exact (trim restores) |
| same programs on VM / Stage-A RTL / Stage-B RTL | identical architectural state |
| REGEN_PREC mismatch (K wrong) | fault; state untouched |
| `REGEN(REGEN(S)) = S` | unchanged (permanent invariant) |
| chain field vs exact field | numerical-error report (informational; must be < 0.5/s×2^m in BQE-normalized units for bit-exactness) |

## 5. Mandatory Verification Gates (for Auditor)

```bash
# 1. Module testbenches (Stage-B REGEN datapath + chain)
cd /home/user/Projects/hardware/SPU
iverilog -g2012 -o build/spu13_regen_tb.vvp \
  hardware/rtl/core/spu13/spu13_regen.v hardware/rtl/core/spu13/fpga_chain.v \
  hardware/tests/spu13/spu13_regen_tb.v && vvp build/spu13_regen_tb.vvp

# 2. Core smoke (dphi=0 and dphi≠0 programs)
iverilog -g2012 -y hardware/rtl -y hardware/rtl/core -y hardware/rtl/core/spu13 \
  -y hardware/rtl/core/shared -y hardware/rtl/arch -y hardware/rtl/math \
  -y hardware/rtl/common/prim -y hardware/rtl/top -I hardware/rtl/arch \
  -o build/spu13_core_regen_tb.vvp hardware/rtl/arch/spu_optional_stubs.v \
  hardware/rtl/common/prim/spu_xilinx_prim.v hardware/tests/spu13/spu13_core_regen_tb.v \
  && vvp build/spu13_core_regen_tb.vvp

# 3. Bit-exact equivalence harness (NEW; Digital ≡ Stage-A ≡ Stage-B ≡ VM)
cd software/tests && .venv/bin/python test_regen_equivalence.py

# 4. Frozen reference gates stay green (Stage A + emulator + assembler)
cd software/tests && .venv/bin/python test_regen_emulator.py && \
  .venv/bin/python test_regen_asm.py && .venv/bin/python test_regen_emulator.py

# 5. VM trace parity + complete repository regression
cd software/tests && .venv/bin/python test_rotc_vm_rtl_trace.py && \
  cd /home/user/Projects/hardware/SPU && bash tools/verify_repo.sh
```

## 6. Stop Conditions (Emergency Brake)

- **HALT** if Stage-B REGEN deviates from the frozen ISA contract (the
  frozen contract is normative; Stage B is a *realization*, not a revision).
- **HALT** if the bit-exact equivalence fails at any supported (K, dphi)
  vector — the primary requirement is not negotiable.
- **HALT** if the numerical-error telemetry is promoted into architectural
  state (it is non-architectural by contract).
- **HALT** on any unbacked "silicon-verified" claim (Stage B is
  testbench-verified unless a dated board run is recorded in
  `docs/hardware_evidence.md`).

## 7. Halt-and-Flag pre-review (implementer flags, resolved by Spec Author)

1. **dphi/compensation scope.** Stage B includes the deterministic common-mode
   rotation knob to exercise the frozen compensation law (experiment #3) in
   hardware. If the cos-LUT precision cannot meet the 1.5e-5 relative
   requirement (experiment #2) within a Lithic module, the implementer must
   HALT and flag — the trim precision is the bit-exactness arbiter at
   non-zero dphi.
2. **Chain op coverage.** QLDI/IDNT/QSUB/ROTC/DELTA mirror; HEX/QLOG no-op;
   IROTC conditional. If the core's ROTC circulant path makes the fixed-point
   mirror non-Lithic, the implementer must HALT and flag (a sub-module for
   the circulant is permitted).
3. **No experimental expansion.** Per Spec Author: this contract is bounded;
   no new Monte Carlo, no K extension, no new noise models.

---

*Status: IMPLEMENTED — all §5 gates green (2026-08-20; testbench-verified, no silicon claim).*
