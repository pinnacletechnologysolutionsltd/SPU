# Engineering Contract: Stage A — REGEN (0x09) ISA Plumbing

**Date:** 2026-08-20
**Contract ID:** `contract_regen_stageA_2026-08-20.md`
**Status:** FROZEN (implementation contract per the frozen scoping contract
`contract_regen_verilog_scope_2026-08-20.md`, Stage A)

**Normative references:** `contract_regen_isa_0x09_2026-08-20.md` (frozen ISA
semantics), `contract_regen_verilog_scope_2026-08-20.md` (scoping), the
emulator reference model (`software/tests/regen_emulator.py`), and the
canonical ISA (`knowledge/isa_reference.md`).

**Roles:**
- **Spec Author:** John + Deep Code.
- **Halt-and-Flag Implementer:** pre-review (see §6 flags below).
- **Integration Auditor:** executes §4 gates; evidence-ledger discipline.

---

## 0. Recorded Architectural Clarification (FROZEN)

> **Stage A encodes the compile-time `.block K` value in the REGEN P1_A
> immediate. K is validated by hardware but is not architectural state.
> This replaces the earlier BLOCKCFG transport mechanism for Stage A
> without changing the `.block K` semantic contract.**
>
> This is a **Stage-A encoding decision**, not a rejection of the conceptual
> `.block K` abstraction. A later encoding (e.g., a persistent block
> configuration register) remains available if the physical implementation
> benefits from persistent block configuration.

**Naming note (frozen):** this contract is and remains "Stage A". It proves
ISA semantics + block accounting + faulting + toolchain agreement. It does
NOT prove photonic REGEN hardware (the optical BQE/normalization mechanism is
Stage B+). Any future reader of `spu13_regen.v` must not conclude otherwise.

---

## 1. Objective & Scoped Files (CORRECTED)

Stage A proves the REGEN ISA plumbing: decode `0x09`, `.block K` assembler
validation, block-op counter, `REGEN_PREC` typestate, DigitalSurdBackend
semantics (REGEN is a pass-through commit on exact arithmetic). No
fixed-point chain (Stage B), no optics in RTL.

**Scoping-contract correction (flagged):** `spu_instr_decode.v` is NOT
instantiated by `spu13_core.v` (it serves only the standalone
`spu13_isa_math_tb.v`). The real decode/dispatch is `spu13_core.v`'s own
`if/else` chain on `eff_inst_word[63:56]` (lines ~683, ~1214–1450). Stage A
therefore modifies `spu13_core.v`; `spu_instr_decode.v` is untouched.

| File | Change |
|---|---|
| `hardware/rtl/core/spu13/spu13_regen.v` | **NEW** Lithic module (50–150 lines): block-op counter, declared-K compare, REGEN_PREC fault, start/done handshake, commit pass-through |
| `hardware/rtl/core/spu13/spu13_core.v` | Surgical: `core_regen_opcode` + `regen_eligible_op` wires; instantiate `spu13_regen`; REGEN in the dispatch chain; new `regen_debug_status[15:0]` output (additive, `rotc_debug_status` untouched) |
| `software/tools/spu13_asm.py` | `OPCODES["REGEN"] = 0x09`; `.block K` / `.regen` directives + eligibility validation |
| `software/spu_vm.py` | `OPCODES["REGEN"] = 0x09` (sync rule); minimal VM semantics (counter/pass-through, mirroring the emulator) |
| `hardware/tests/spu13/spu13_regen_tb.v` | **NEW** iverilog testbench (vectors in §4.2) |
| `software/tests/test_regen_asm.py` | **NEW** assembler legality tests (valid / too-short / too-long / orphan `.regen` / unterminated `.block`) |

## 2. Invariants & Hard Constraints (the "Never" List)

- [ ] **No optics in RTL.** Stage A is exact-arithmetic pass-through only.
- [ ] **Frozen semantics are normative.** REGEN: S̃_K ↦ S_K (whole state);
      `REGEN(REGEN(S)) = S` is a permanent invariant; REGEN_PREC leaves state
      untouched.
- [ ] **K is compile-time metadata.** The declared K rides in the REGEN
      instruction's P1_A immediate (assembler-filled from `.block K`),
      validated by the hardware counter. K is NOT architectural state.
      *Stage-A encoding decision, recorded in §0; replaces the scoping
      contract's "BLOCKCFG control register" transport for Stage A without
      changing the `.block K` semantic contract.*
- [ ] **Assembler, RTL counter, and VM count the SAME eligible set**
      (E_REGEN, §3). The runtime counter is the safety net that catches
      divergence (REGEN_PREC fault).
- [ ] **`regen_debug_status` is non-architectural.** Software must not depend
      on it for program semantics (expose algebraic state; hide physical
      bookkeeping).
- [ ] **No unbacked silicon claims.** Stage A is testbench-verified only.

## 3. Step-by-Step Implementation Instructions

1. **`spu13_regen.v`** (new, Lithic ≤150 lines):
   - Inputs: `clk, rst_n`, `start` (REGEN accepted), `declared_k[15:0]`
     (P1_A), `eligible_op` (pulse per block-eligible op), `bk_valid` (tied to
     `start` in Stage A — digital backend is always in-envelope),
     `bk_meas_a/b` (tied to the QR file read in Stage A — pass-through).
   - Behavior: count `eligible_op` pulses; on `start`: if
     `counter == declared_k` → pass-through commit, `REGEN_PREC=0`, clear
     counter, pulse `done`; else → `REGEN_PREC=1`, state untouched, counter
     NOT cleared (debug visibility), pulse `done` (fault completes the
     instruction; `regen_debug_status` exposes the fault).
   - Idempotence: `declared_k == 0` with `counter == 0` → clean pass-through
     (`REGEN(REGEN(S)) = S`).
   - Outputs: `done`, `regen_prec_fault`, `block_op_count[15:0]`,
     `regen_debug_status[15:0]`.
   - `regen_debug_status[15:0]` field layout (non-architectural): block
     active, K valid, block count[5:0], K mismatch, REGEN_PREC fault,
     REGEN busy, REGEN done. Software must NOT depend on it for program
     semantics.
2. **`spu13_core.v`** (surgical):
   - `wire core_regen_opcode = (eff_inst_word[63:56] == 8'h09);`
   - The eligible set is a **named architectural definition**:

     ```
     E_REGEN = {QLDI(0x1D), IDNT(0x18), QSUB(0x1B), ROTC(0x1C),
                DELTA(0x1E), HEX(0x16), QLOG(0x14), IROTC}
     ```
     with IROTC conditional on `ENABLE_IROTC` (per the existing ISA rules).
     `wire regen_eligible_op = inst_accept && (opcode in E_REGEN)`.
     **The assembler (step 3), the RTL counter, and the VM (step 4) MUST use
     the identical set.**
   - Dispatch: `else if (inst_accept && core_regen_opcode)` → drive
     `regen_start`, `declared_k = eff_inst_word[39:24]`, and complete via the
     regen module's `done` (register the REGEN completion into `inst_done_r`).
   - Instantiate `spu13_regen`; wire `regen_debug_status` to a new output
     port (additive; do NOT alter `rotc_debug_status` composition).
3. **`spu13_asm.py`**:
   - `OPCODES["REGEN"] = 0x09` (and keep `spu_vm.py` OPCODES in sync).
   - `.block K=n` and `.regen` directive handling in the two-pass parser:
     pass 1: `.BLOCK` adds 0 instructions, `.REGEN` adds 1, ops add 1 as
     usual; pass 2: validate and emit — `.block K=n` opens a block, exactly K
     eligible mnemonics follow, `.regen` emits the REGEN instruction with
     P1_A = K and closes the block.
   - Assembly errors (`AssemblyError`): `.regen` with no open `.block`;
     unterminated `.block` at EOF; fewer than K ops at `.regen`; an op beyond
     the declared K before `.regen` (too-long); nested `.block`.
   - Eligible mnemonics (MUST equal E_REGEN, step 2's set): QLDI, IDNT, QSUB,
     ROTC, DELTA, HEX, QLOG, IROTC.
4. **`spu_vm.py`**: add the REGEN opcode + pass-through/counter semantics
   mirroring the emulator (a block must be declared in the program;
   `REGEN` validates the count against the same E_REGEN set, sets a
   `REGEN_PREC` status on mismatch).
5. **Eligibility tests (mandatory, all three layers agree on E_REGEN):**
   - every eligible op (QLDI, IDNT, QSUB, ROTC, DELTA, HEX, QLOG, IROTC)
     increments the RTL counter;
   - every ineligible op does NOT increment the RTL counter;
   - the assembler's `.block K` validation accepts exactly the same mnemonics;
   - IROTC behaves identically when disabled (`ENABLE_IROTC=0` → not
     eligible, per the existing ISA feature rule) and enabled.
6. **Testbenches** (§4.2 vectors).

## 4. Mandatory Verification Commands (for Auditor)

**Gate ordering (frozen):**
RTL REGEN vectors → assembler legality → emulator reference gates → VM trace
parity → complete repository regression.

```bash
# 1. RTL REGEN vectors (new REGEN datapath, iverilog convention)
cd /home/user/Projects/hardware/SPU
iverilog -g2012 -I hardware/rtl/arch -o build/spu13_regen_tb.vvp \
  hardware/rtl/core/spu13/spu13_regen.v hardware/tests/spu13/spu13_regen_tb.v \
  && vvp build/spu13_regen_tb.vvp

# 2. Assembler legality tests (NEW)
cd software/tests && .venv/bin/python test_regen_asm.py

# 3. Executable reference model stays green (frozen contract gate)
cd software/tests && .venv/bin/python test_regen_emulator.py

# 4. VM trace parity (assembly → VM → RTL connectivity)
cd software/tests && .venv/bin/python test_rotc_vm_rtl_trace.py

# 5. Complete repository regression
bash tools/verify_repo.sh
```

### 4.1 Stage-A vectors (RTL testbench `spu13_regen_tb.v`)

| Vector | Expectation |
|---|---|
| QLDI; QLDI; `REGEN K=2` | REGEN_PREC=0, counter cleared, state unchanged (pass-through), done |
| QLDI; `REGEN K=2` | REGEN_PREC=1, state untouched, counter NOT cleared |
| `REGEN K=0` (no block ops) | REGEN_PREC=0 — idempotence `REGEN(REGEN(S))=S` |
| QLDI; QLDI; QLDI; `REGEN K=2` | REGEN_PREC=1 (too-long block: counter 3 ≠ 2) |
| QLDI; `REGEN K=1`; `REGEN K=0` | first clears counter; second is clean pass-through |
| REGEN with `bk_valid` fault path (simulated out-of-envelope) | REGEN_PREC=1, untouched |

### 4.2 Stage-A vectors (assembler tests `test_regen_asm.py`)

| Program | Expectation |
|---|---|
| `.block K=2` QLDI QLDI `.regen` | assembles; emits REGEN with P1_A=2 |
| `.block K=2` QLDI `.regen` | `AssemblyError` (too-short) |
| `.block K=2` QLDI QLDI QLDI `.regen` | `AssemblyError` (too-long) |
| `.block K=4` QLDI QLDI QLDI `.regen` | `AssemblyError` (too-short, K=4 with 3 eligible ops) |
| `.block K=4` QLDI QLDI QLDI QLDI QLDI `.regen` | `AssemblyError` (too-long, K=4 with 5 eligible ops) |
| QLDI `.regen` (no block) | `AssemblyError` (orphan) |
| `.block K=2` QLDI QLDI (no `.regen`) | `AssemblyError` (unterminated) |
| `.block K=1` LD R0, 1 `.regen` | `AssemblyError` (LD not in E_REGEN) |
| `.block K=1` QLDI `.regen` ... `.regen` (orphan second) | `AssemblyError` |
| any REGEN_PREC mismatch in RTL (see 4.1) | fault; state untouched |

## 5. Stop Conditions (Emergency Brake)

- **HALT** if any change touches the existing opcode table semantics, the
  `rotc_debug_status` composition, or the WF profile.
- **HALT** if the hardware eligible set and assembler eligible set diverge
  (they are normative-equal by contract).
- **HALT** if REGEN ever modifies the QR state in Stage A (pass-through
  only; the exact state must not be rewritten).
- **HALT** on any unbacked "silicon-verified" claim — Stage A is
  testbench-verified by definition.

## 6. Halt-and-Flag pre-review (implementer flags, resolved by Spec Author)

1. **BLOCKCFG vs P1_A-immediate K — RESOLVED (John, 2026-08-20): accepted.**
   Stage A carries the declared K in the REGEN instruction's P1_A immediate
   (assembler-filled from `.block K`), eliminating a control-register write
   path. Recorded as the §0 architectural clarification: a **Stage-A encoding
   decision**, not a rejection of the `.block K` abstraction; a later
   persistent-block-configuration encoding remains available.
2. **`spu_instr_decode.v` correction.** Scoping contract §6 listed it; it is
   not in the core's path. Core dispatch (`spu13_core.v`) is the integration
   point. Corrected above.
3. **Eligible-op set.** Frozen as {QLDI, IDNT, QSUB, ROTC, DELTA, HEX, QLOG,
   IROTC-if-enabled} — the QR exact ops dispatched by the core. If the core
   does not dispatch some of these in all configurations (e.g., QLOG), the
   implementer must HALT and flag rather than silently adjusting the set.

---

*Status: FROZEN (2026-08-20). Approved by John with conditions folded in:
§0 architectural clarification (P1_A K transport), named E_REGEN set + three-
layer eligibility agreement, non-architectural `regen_debug_status` field
layout, frozen gate ordering with negative vectors, Stage A naming retained.
Begin implementation.*
