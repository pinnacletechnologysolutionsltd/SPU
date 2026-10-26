# Engineering Contract: REGEN-in-Verilog Follow-On (Scoping)

**Date:** 2026-08-20
**Contract ID:** `contract_regen_verilog_scope_2026-08-20.md`
**Status:** FROZEN (scoping contract; scopes the follow-on implementation
contracts. No RTL changes under THIS contract.)

**Supersedes / normatively references:**
- `spu_strategy/contract_regen_isa_0x09_2026-08-20.md` (frozen REGEN ISA
  semantics — normative; this contract does not re-litigate them)
- `software/tests/regen_emulator.py` + `test_regen_emulator.py` (executable
  reference model of the contract)
- `knowledge/isa_reference.md` (canonical ISA; 0x09 is free, HALT = 0x08)

**Roles:**
- **Spec Author:** John + Deep Code. Answers the scoping question: *we do not
  model optics in Verilog; Verilog implements the digital boundary and a
  digital realization of the same ISA contract.*
- **Halt-and-Flag Implementer:** pre-review each follow-on implementation
  contract against THIS scoping contract and the frozen ISA contract.
- **Integration Auditor:** executes §5 gates; evidence ledger discipline
  (`docs/hardware_evidence.md` — no unbacked "silicon-verified" claims).

---

## 1. Scope: what "REGEN in Verilog" means (frozen)

Verilog (Yosys/nextpnr, Tang 25K / Artix-7) is digital logic synthesis. It
cannot and will not model the optical substrate. The scope of any Verilog
follow-on is therefore exactly two things:

1. **The digital boundary of REGEN**: instruction decode of `0x09`, block
   bookkeeping (`.block K`), the REGEN datapath (trim + BQE + quantization),
   `REGEN_PREC` typestate, whole-state commit. This is RTL.
2. **A digital realization of the continuous chain** ("FPGA reference
   backend"): fixed-point chain with 2-normalized Sigma — a second
   implementation satisfying the same ISA contract (the contract's own
   portability claim: photonic / FPGA / ASIC / vector / digital).

The photonic backend remains the frozen Python model (never RTL). The same
backend-measurement interface (§3) serves every realization.

## 2. Realization path (frozen, staged)

| Stage | What | Why | Evidence |
|---|---|---|---|
| **A** | ISA plumbing: decode `0x09`, `.block K` in `spu13_asm.py` + validation, block-op counter, `REGEN_PREC` typestate, DigitalSurdBackend semantics (REGEN pass-through on exact arithmetic) | proves the plumbing honestly, minimal surface | iverilog tb + assembler tests |
| **B** | FPGA reference backend: fixed-point continuous chain module + real REGEN datapath (trim, BQE, quantization) | second real implementation; silicon evidence target on Tang 25K / Artix-7 | trace-equivalence vs emulator, fixed-point tolerance analysis, synthesis |
| **C** (deferred, optional) | Photonic-backend cosimulation: testbench drives the measurement interface from the frozen Python model | boundary contract exercised with the real physical model, in simulation | iverilog tb + Python co-driver |

Stage A and Stage B are separate follow-on implementation contracts. Stage C
is documented but NOT scheduled unless requested.

## 3. Backend measurement interface (frozen — the key scoping decision)

One synchronous interface carries the measured state from any backend into the
REGEN datapath:

```
bk_meas_a    [31:0]  measured inphase component a (backend scale units)
bk_meas_b    [31:0]  measured inphase component b
bk_angle_K   [31:0]  accumulated common-mode angle (per block, backend units)
bk_sigma     [31:0]  accumulated normalization (Sigma_total, backend units)
bk_valid     [1:0]   handshake: 0 idle, 1 valid, 2 fault(REGEN_PREC)
bk_scale     [7:0]   backend scale factor tag (permitted: {0.1 photonic-model,
                     0.25 fpga-ref, 1.0 digital}; extensible)
```

- REGEN asserts `bk_valid == 1` → latches, applies compensation
  (`×1/cos(bk_angle_K)`, the frozen compensation law), BQE with
  `bk_sigma`/`bk_scale`, commits whole state, clears block counter.
- `bk_valid == 2` (backend declares out-of-envelope) → `REGEN_PREC` fault,
  destination untouched (frozen ISA contract §2.3/§5).
- Stage A: the interface is driven by the exact-arithmetic datapath.
  Stage B: driven by the fixed-point chain module. Stage C: driven by the
  testbench from the Python model. **Same interface, all realizations.**

## 4. Block semantics in the machine (frozen)

- `.block K` remains **compile-time metadata**: `spu13_asm.py` validates
  exactly K eligible ops (mirrors `parse_block` in the reference model).
- Hardware keeps a **block-op counter** (counts eligible ops since last
  REGEN). The counter's declared value K is held in a **control register**
  (`BLOCKCFG`) — implementation/control state, NOT general-purpose
  architectural state (frozen ISA contract §2.1, decision 3).
- REGEN validates `counter == BLOCKCFG.K`; mismatch → `REGEN_PREC`-style
  assembly/fault semantics (frozen contract §3).
- **Idempotence invariant** `REGEN(REGEN(S)) = S` holds in hardware: REGEN on
  an exact state (zero accumulated ops) is a pass-through commit.

## 5. Verification approach (frozen)

Follow-on implementation contracts must include, in exact order:

```bash
# 1. Module testbenches (existing iverilog convention)
iverilog -g2012 -I hardware/rtl/arch -o build/<mod>_tb.vvp \
  hardware/rtl/core/spu13/<mod>.v hardware/tests/spu13/<mod>_tb.v && \
  vvp build/<mod>_tb.vvp

# 2. Trace equivalence vs the executable reference model (the emulator)
#    RTL REGEN datapath must reproduce regen() from regen_emulator.py on:
#    - K in {1,2,4,8,16}, thermal compensated and uncompensated
#    - valid / too-short / too-long blocks (assembler-side)
#    - REGEN(REGEN(S)) == S
#    - same block, different bk_scale/bk_sigma -> identical exact state
cd software/tests && .venv/bin/python test_regen_emulator.py   # reference gates stay green

# 3. Stage-B fixed-point tolerance gate: the FPGA chain is a fixed-point
#    approximation; REGEN must still restore exactness within the envelope.
#    (Implementation contract defines the exact tolerance analysis.)

# 4. Repo hygiene + full regression (auditor)
bash tools/verify_repo.sh

# 5. Evidence ledger: per docs/hardware_evidence.md — silicon-verified only
#    with a dated, reproduced board run; otherwise testbench-verified.
```

## 6. Scoped files (for the follow-on implementation contracts)

- `hardware/rtl/core/spu13/spu13_regen.v` — REGEN datapath (Lithic, 50–150
  lines; trim + BQE + quantization + typestate commit)
- `hardware/rtl/core/spu13/fpga_chain.v` — Stage B fixed-point chain (Lithic)
- `hardware/rtl/core/spu13/spu_instr_decode.v` — add `OP_REGEN = 8'h09`
- `hardware/rtl/core/spu13/spu13_core.v` — integration point + `BLOCKCFG`
  control register + `rotc_debug_status`-style REGEN status
- `software/tools/spu13_asm.py` — `.block K` directive + legality validation
- `hardware/tests/spu13/spu13_regen_tb.v`, `spu13_fpga_chain_tb.v` — iverilog
  testbenches per existing convention
- `software/tests/test_regen_asm.py` — assembler legality tests
  (valid / too-short / too-long blocks)

## 7. Non-goals (frozen)

- NO photonic backend in RTL (impossible; the optics stay in the Python
  model).
- NO analog modeling (no Verilog-AMS; the toolchain is digital-only).
- NO changes to existing opcodes, the WF twin-register profile, or the
  frozen ISA contract's semantics.
- NO new Monte Carlo experiments required by any follow-on (the seven frozen
  artifacts + emulator gates are the evidence).

## 8. Stop conditions (Emergency Brake)

- **HALT** if a follow-on contract implements REGEN semantics that diverge
  from `contract_regen_isa_0x09_2026-08-20.md` (the frozen contract is
  normative).
- **HALT** if the backend-measurement interface (§3) is bypassed or altered
  per-realization (it is frozen for all backends).
- **HALT** if block legality is enforced only in hardware and not in the
  assembler (K is compile-time metadata; the assembler validates).
- **HALT** on any unbacked "silicon-verified" claim without a dated,
  reproduced board run in `docs/hardware_evidence.md`.
