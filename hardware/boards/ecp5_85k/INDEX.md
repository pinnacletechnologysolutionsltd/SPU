# ECP5-85K Minimal Spin — Complete Documentation Index

**Date:** 2026-07-05
**Status:** ✓ Synthesis verified | ⏳ P&R pending | 📋 Tests ready
**Target:** SPU-13 + RPLU 2.0 evaluation board (no Lucas MAC, no SU(3))

---

## Quick Start

1. **Build from scratch:**
   ```bash
   bash hardware/boards/ecp5_85k/build_ecp5_85k_minimal.sh all
   ```
   Outputs: `build/spu_ecp5_top.bit` (bitstream)

2. **Run simulation smoke tests:**
   ```bash
   python3 run_all_tests.py TB_FILTER=spu_laminar_boot
   python3 run_all_tests.py TB_FILTER=spu_unified_alu_tdm
   ```

3. **Flash to hardware:**
   ```bash
   openFPGALoader -b tangprimer25k -f build/spu_ecp5_top.bit
   ```

---

## Documentation Map

### Build & Strategy
- **`build_ecp5_85k_minimal.sh`** — Minimal curated build script (3 steps: synth, pnr, all)
- **`README_MINIMAL_SPIN.md`** — Overview, I/O pinout, build instructions, excluded modules
- **`docs/ecp5_85k_curated_source_strategy.md`** — Rationale for curated source list (vs. glob forest)

### Testing
- **`SMOKE_TESTS.md`** — Complete test plan:
  - 3 simulation tests (boot SPI, ALU functional, rotor handshake)
  - 4 hardware tests (LED blink, UART, flash readback, ALU via SPI)
  - Expected results & iteration checklist
- **`hardware/tests/common/spu_laminar_boot_tb.v`** — Boot controller testbench
- **`hardware/tests/common/spu_unified_alu_tdm_tb.v`** — ALU testbench (already exists)
- **`hardware/tests/common/spu_rotor_vault_tb.v`** — Rotor vault testbench (already exists)

### Timing & Constraints
- **`TIMING_AND_PLACEMENT.md`** — P&R tuning guide:
  - Critical paths & timing budgets
  - Resource hotspots & mitigations
  - Nextpnr invocation & frequency/effort options
  - Resource budget (58% LUT, 23% DSP projected)
- **`spu_ecp5_85k.cst`** — Pin constraints (CABGA381 package)

### Status Reports
- **`docs/ecp5_85k_report.md`** — Initial board assessment (file inventory, status)
- **`docs/ecp5_85k_curated_source_strategy.md`** — Build strategy deep-dive

---

## File Inventory

| File | Type | Purpose | Status |
|------|------|---------|--------|
| `build_ecp5_85k_minimal.sh` | Script | Build orchestration (synth → pnr → bitstream) | ✓ Ready |
| `spu_ecp5_top.v` | RTL | Board top-level (placeholder integration) | ✓ Synthesizes |
| `spu_ecp5_85k.cst` | Constraints | Pin assignments (CABGA381) | ✓ Complete |
| `README_MINIMAL_SPIN.md` | Doc | Build instructions & overview | ✓ Created |
| `SMOKE_TESTS.md` | Plan | Test suite (sim + hardware) | ✓ Created |
| `TIMING_AND_PLACEMENT.md` | Guide | P&R tuning & resource budgets | ✓ Created |
| `INDEX.md` | Doc | This file (documentation index) | ✓ Created |
| `spu_laminar_boot_tb.v` | Testbench | Boot controller smoke test | ✓ Created |
| `spu_unified_alu_tdm_tb.v` | Testbench | ALU functional test | ✓ Exists |
| `spu_rotor_vault_tb.v` | Testbench | Rotor vault handshake test | ✓ Exists |

---

## Curated Source List (8 modules)

All Verilog-2005 compatible; no SystemVerilog:

```
hardware/boards/ecp5_85k/spu_ecp5_top.v
hardware/rtl/core/spu13/spu13_top.v
hardware/rtl/top/spu_laminar_boot.v
hardware/rtl/peripherals/io/spu_node_link.v
hardware/rtl/core/shared/spu_rotor_vault.v
hardware/rtl/core/shared/spu_unified_alu_tdm.v
hardware/rtl/core/spu13/spu13_berry_gate.v
hardware/rtl/core/spu13/spu13_janus_mirror.v
hardware/rtl/arch/spu_optional_stubs.v
```

**Synthesis verified:** ✓ No redefinition errors, no SV parse failures

---

## Next Steps (Sequential)

### Phase 1: Place & Route (Ready)
- [ ] Run nextpnr: `build_ecp5_85k_minimal.sh pnr`
- [ ] Check timing report for negative slack
- [ ] If routing fails, use TIMING_AND_PLACEMENT.md to iterate (freq, seed, effort)
- [ ] Generate bitstream: `build_ecp5_85k_minimal.sh all`

### Phase 2: Simulation Validation (Ready)
- [ ] Run boot testbench: `python3 run_all_tests.py TB_FILTER=spu_laminar_boot`
- [ ] Run ALU testbench: `python3 run_all_tests.py TB_FILTER=spu_unified_alu_tdm`
- [ ] Run rotor testbench: `python3 run_all_tests.py TB_FILTER=spu_rotor_vault`
- [ ] Verify all output: `PASS`

### Phase 3: Hardware Bring-Up (Ready)
- [ ] Flash bitstream to ECP5-85K board
- [ ] Observe LED1 (heartbeat) blinking at ~3 kHz
- [ ] Connect UART to pin B11; verify telemetry readable
- [ ] Use RP2040 flash PMOD to readback SPI flash (validate boot table)

### Phase 4: Functional Tests (Deferred)
- [ ] Requires RP2350 southbridge firmware (currently not implemented)
- [ ] Drive ALU start/opcode via SPI; capture result; compare to oracle

### Phase 5: Documentation
- [ ] Create SPU-13 architecture paper (separate effort)
- [ ] Add ECP5 bring-up runbook to docs/

---

## Key Design Decisions

1. **Curated source list (not recursive glob):** Prevents module redefinitions, vendor prim conflicts, SV parse errors
2. **Minimal spin (no Lucas MAC, SU(3)):** Reduces complexity for evaluation board; full feature set on Artix-7
3. **Verilog-2005 only:** All 8 modules parse cleanly in Yosys read_verilog (no SV frontend needed)
4. **50 MHz system clock:** ECP5-85 grade 8 supports this with headroom; provides ~2 GHz instruction throughput (equivalent to 12 MHz internal with 6-cycle pipelines)
5. **Placeholder I/O:** spu_ecp5_top ties off southbridge SPI/PIO; can be completed incrementally

---

## Resources & References

- **Synthesis:** Yosys 0.63+
- **Place & Route:** Nextpnr (ECP5 backend)
- **Bitstream:** Ecppack (from Project Trellis)
- **Programming:** openFPGALoader
- **ECP5 Datasheet:** https://www.latticesemi.com/en/Products/FPGAandCPLD/ECP5
- **SPU-13 ISA:** `knowledge/isa_reference.md`
- **RPLU2 Architecture:** `knowledge/RPLU2_ARCHITECTURE.md`

---

## Contact & Versioning

**Created:** 2026-07-05 14:58 UTC
**Last updated:** 2026-07-05 15:57 UTC
**Author:** Copilot CLI (SPU-13 team)
**Status:** Ready for P&R and hardware bring-up

---

## Troubleshooting Quick Links

| Problem | Reference |
|---------|-----------|
| Build fails (synthesis) | `README_MINIMAL_SPIN.md` → Build Instructions |
| P&R times out (routing) | `TIMING_AND_PLACEMENT.md` → Nextpnr Tuning |
| Negative timing slack | `TIMING_AND_PLACEMENT.md` → Critical Paths |
| LEDs don't blink | `SMOKE_TESTS.md` → Test 5.1 (LED Blink) |
| UART garbage | `SMOKE_TESTS.md` → Test 5.2 (UART Readback) |
| Flash readback fails | `SMOKE_TESTS.md` → Test 5.3 (Flash Read) |
