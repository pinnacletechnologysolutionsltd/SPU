# Historical Note

This file contains early ECP5-85F smoke-test planning. For current measured
build status, use `docs/ecp5_85k_curated_source_strategy.md`. The 2026-07-06
curated placeholder build passes synthesis, P&R, and bitstream packaging, but
no physical ECP5-85F board smoke has been recorded.

# ECP5-85K Minimal Spin — Smoke Test Plan

**Date:** 2026-07-05
**Target:** SPU-13 + RPLU 2.0 on ECP5-85F
**Scope:** Boot, ALU functional vectors, rotor handshake, basic I/O

---

## 1. Pre-Synthesis Checklist

- [ ] All 8 curated source files exist and are readable
- [ ] No SV syntax errors in modules (verified in prior analysis)
- [ ] Constraints file (spu_ecp5_85k.cst) has PULL_MODE=NONE on sys_clk
- [ ] build_ecp5_85k_minimal.sh is executable

## 2. Simulation Smoke Tests

### Test 2.1: SPI Boot Controller (spu_laminar_boot_tb.v)

**Purpose:** Verify flash read sequence and BRAM write

**Testbench steps:**
1. Instantiate spu_laminar_boot with simulated W25Q flash (modeled as simple mem)
2. Assert rst_n, pulse clk_12mhz
3. Expect: boot_done asserts after ~2000 cycles (depends on flash latency model)
4. Verify: bram_data appears on output (spot-check first 8 32-bit words)
5. Verify: pell_addr/pell_we signals strobe correctly

**Expected output:** `PASS` or `FAIL`

**Files to create:**
- `hardware/boards/ecp5_85k/tests/spu_laminar_boot_tb.v` (if doesn't exist)

---

### Test 2.2: ALU Functional Vectors (spu_unified_alu_tdm_tb.v)

**Purpose:** Verify rotation (ROT), addition (ADD), NOP operations

**Testbench steps:**
1. Instantiate spu_unified_alu_tdm with DEVICE="SIM" (inferred multiplier)
2. Test OP_NOP: A_in={1,0}, B_in={0,1} → expect A_out={1,0}, B_out={0,1} after 1 cycle
3. Test OP_ADD: A_in=1, B_in=0, C_in=2, D_in=3 → expect A_out=3, B_out=3 after 1 cycle
4. Test OP_ROT: Apply rotor {Ra, Rb} and verify Q(√3) rotation formula: A' = A*Ra + 3*B*Rb
5. Spot-check Q12 scaling (input Q12×Q12 → Q24, extract [27:12] → Q12)

**Expected output:** `PASS` or `FAIL`

**Files to reference:**
- `hardware/tests/spu13/spu_unified_alu_tdm_tb.v` (may already exist)
- If missing, create in `hardware/boards/ecp5_85k/tests/`

---

### Test 2.3: Rotor Vault Handshake (spu_rotor_vault_tb.v)

**Purpose:** Verify rotor state machine and axis stepping

**Testbench steps:**
1. Instantiate spu_rotor_vault with default Pell rotor table
2. Assert rot_en pulse in IDLE state, provide rot_axis=0
3. Verify: vault_rotor updates to correct Pell rotor value for axis 0
4. Verify: vault_octave, vault_step strobed correctly
5. Repeat for rot_axis=1,2,3,12 (boundary cases)

**Expected output:** `PASS` or `FAIL`

**Files to reference:**
- `hardware/tests/spu13/spu_rotor_vault_tb.v` (may already exist)

---

## 3. Post-Synthesis Checks (Static)

After `build_ecp5_85k_minimal.sh synth`:

- [ ] `build/spu_ecp5_top.json` exists and is valid JSON
- [ ] Yosys log contains no "Re-definition" errors
- [ ] Yosys log contains no "syntax error" messages
- [ ] Cell count ~ 5,000–15,000 (reasonable for minimal SPU-13 + RPLU2)
- [ ] DSP count ~ 30–50 (M31 multiplier + ALU TDM)
- [ ] BRAM count ~ 2–4 (rotor vault, boot table)

---

## 4. Post-P&R Checks (Static)

After `build_ecp5_85k_minimal.sh pnr`:

- [ ] `build/spu_ecp5_top_out.config` exists
- [ ] Nextpnr log shows "success" or "routing complete"
- [ ] Timing report: no negative slack on critical path (clk_12mhz → ALU → output)
- [ ] Resource utilization: <60% LUTs, <80% slices (healthy margin on ECP5-85)
- [ ] No unplaced cells or missing I/O

---

## 5. Hardware Smoke Tests

### Test 5.1: Bitstream Programming & LED Blink

**Equipment:** ECP5-85K board, openFPGALoader, USB cable

**Steps:**
1. Generate bitstream: `bash build_ecp5_85k_minimal.sh all`
2. Program board: `openFPGALoader -b tangprimer25k -f build/spu_ecp5_top.bit`
   (Note: adapt board name if ECP5 is on a different carrier)
3. Observe LEDs (active low on pins L6, E8, D7):
   - LED0 should pulse if uart_tx is toggling (boot telemetry)
   - LED1 should pulse at ~12 MHz / 4096 = ~2.9 kHz (piranha_pulse heartbeat)
   - LED2 should pulse if alu_done strobes (ALU computation done)
4. Expected: LEDs blink at different rates; at least LED1 (heartbeat) visible

**Pass criteria:** At least LED1 visible blinking; LEDs not stuck high/low

---

### Test 5.2: Telemetry UART Readback

**Equipment:** USB-to-UART adapter, terminal (picocom/miniterm)

**Steps:**
1. Connect USB-UART RX to ECP5 pin B11 (telemetry UART TX)
2. Open terminal: `picocom -b 115200 /dev/ttyUSB0` (adjust tty as needed)
3. After reset, expect: boot handshake messages (depends on spu_laminar_boot behavior)
4. Expected: 921.6 kbaud or 115.2 kbaud telemetry frames, or debug output

**Pass criteria:** UART produces readable 8-bit characters; no garbage

---

### Test 5.3: SPI Flash Readback

**Equipment:** RP2040 USB-to-SPI PMOD programmer (from `tools/rp2040_flash_pmod.py`)

**Steps:**
1. Ensure RP2040 is loaded with flash PMOD firmware
2. Connect PMOD to J4 on ECP5 board (or use alternate SPI header)
3. Run diagnostic: `tools/rp2040_flash_pmod.py --port /dev/ttyACM0 id`
4. Expected: Flash JEDEC ID `EF4018` (or similar W25Q-class)
5. Read first 256 bytes: `tools/rp2040_flash_pmod.py --port /dev/ttyACM0 read 0 256`
6. Spot-check for BRAM initialization data (Pell primes, rotor table, etc.)

**Pass criteria:** JEDEC ID valid; readback contains expected patterns (not 0xFF or 0x00)

---

### Test 5.4: ALU Functional Vector (Hardware via UART)

**Equipment:** Terminal connected to telemetry UART (Test 5.2)

**Steps:**
1. (Requires custom RP2350 firmware or debug interface to drive ALU start/opcode)
2. Send SPI command to southbridge: write alu_start=1, alu_opcode=1 (ROT), data=test vector
3. Poll alu_done on telemetry channel
4. Read result from ALU output latches
5. Compare to expected Q(√3) rotation result

**Pass criteria:** alu_done strobes; result matches oracle value (within rounding)

**Note:** This test requires RP2350 southbridge firmware (currently placeholder in spu_ecp5_top.v)

---

## 6. Expected Results Summary

| Test | Phase | Pass Criterion | Status |
|------|-------|-----------------|--------|
| 2.1 | Simulation | boot_done asserts; BRAM written | ⏳ Pending |
| 2.2 | Simulation | All opcodes correct (NOP, ADD, ROT) | ⏳ Pending |
| 2.3 | Simulation | Rotor state machine stable; rot_en pulse handled | ⏳ Pending |
| 4.x | Static (P&R) | No negative slack; <60% LUT util | ⏳ Pending |
| 5.1 | Hardware | LED1 heartbeat visible blinking | ⏳ Pending |
| 5.2 | Hardware | UART telemetry readable | ⏳ Pending |
| 5.3 | Hardware | Flash JEDEC ID valid; readback has data | ⏳ Pending |
| 5.4 | Hardware | ALU result matches oracle (requires southbridge FW) | ⏳ Deferred |

---

## 7. Iteration Plan

### If synthesis fails:
1. Check for SV syntax errors (should not occur given prior validation)
2. Verify all 8 source files exist
3. Check for missing include paths in build_ecp5_85k_minimal.sh

### If P&R fails (routing, timing):
1. Check for LUT density hotspots (likely the M31 multiplier or BTU collision resolver)
2. Consider pipelining critical paths (ALU → output)
3. Reduce clock frequency target (50 MHz → 40 MHz) if timing slack <0
4. Check ECP5 timing grade (should be grade 8 for 50 MHz headroom)

### If LEDs don't blink (hardware):
1. Verify bitstream actually programmed (check FPGA LED or status)
2. Verify clock is running (measure 50 MHz on sys_clk input)
3. Check reset polarity (spu_ecp5_top has rst_n active-low)
4. Check LED constraints in .cst (active low, correct pins L6/E8/D7)

### If UART produces garbage:
1. Verify baud rate setting (115,200 on boot telemetry UART)
2. Check pin constraint for uart_tx on B11
3. Verify UART TX is driven by spu13_top.uart_tx (currently mapped to LED0 in placeholder)

---

## 8. Test Automation

To run all simulation tests automatically:

```bash
cd hardware/boards/ecp5_85k/tests/
iverilog -Ihardware/rtl/arch -Ihardware/common/rtl/include \
  spu_laminar_boot_tb.v && vvp a.out
iverilog -Ihardware/rtl/arch -Ihardware/common/rtl/include \
  spu_unified_alu_tdm_tb.v && vvp a.out
iverilog -Ihardware/rtl/arch -Ihardware/common/rtl/include \
  spu_rotor_vault_tb.v && vvp a.out
```

Expected: All output `PASS`.

---

**Next step:** Historical planning note; use the docs listed at the top for
current measured status.
