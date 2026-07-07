# ECP5-85K vs Artix-7 — Gap Analysis & Wiring Plan

**Date:** 2026-07-05
**Scope:** Compare spu_ecp5_top.v to spu_a7_top.v; identify missing connections

---

## Quick Summary

**ECP5 status:** Placeholder integration — core is instantiated, but southbridge protocol and result pathways are tied off.

**Artix-7 status:** Full integration — SPI protocol handler, instruction fetch, result commit, error reporting all connected.

**Gap:** ~5 HIGH-priority signal routings + 4 MEDIUM features needed for parity.

---

## 1. Southbridge Protocol Status

### Artix-7 (spu_a7_top.v)
- **SPI mode 0, 2 MHz** from RP2350
- **CMD 0xA0:** Read manifold (32 bytes)
- **CMD 0xAC:** Read status + sticky RPLU flags
- **CMD 0xAE:** Read last QR commit
- **CMD 0xB1:** Write + pulse 64-bit instruction word
- **Instruction stream:** `spi_inst_valid` and `spi_inst_word[63:0]`
- **Result path:** `qr_commit_*` signals → SPI multiplexor → spi_miso

### ECP5 (spu_ecp5_top.v, Current)
- **SPI ports present:** spi_cs, spi_sck, spi_mosi, spi_miso
- **PIO ports present:** pio_d[7:0], pio_strobe, pio_dir, pio_ready
- **Current action:** All tied off (`spi_miso = 1'b0`, `pio_ready = 1'b0`)
- **ALU control:** `alu_start`, `alu_opcode` hardcoded to 0
- **Status:** No instruction fetching; no result readback

---

## 2. HIGH Priority Wiring (Required for Functional SPI)

### 2.1: SPI Protocol Handler
**Currently:** Missing
**What it does:** Parses commands from RP2350 (0xA0, 0xAC, 0xAE, 0xB1)
**Where to add:** New module `spu_ecp5_spi_southbridge.v`

**Signals needed:**
```verilog
input  spi_cs, spi_sck, spi_mosi;
output spi_miso;

// From parser
output spi_inst_valid;
output [63:0] spi_inst_word;
output spi_status_rd_en;
output spi_qr_rd_en;

// Status inputs (from core)
input [7:0] core_status;
input [63:0] qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D;
```

**Option A (Recommended):** Extract SPI protocol handler from `spu_a7_top.v` (lines ~400–600)
**Option B:** Wire-instantiate existing SPI slave from common RTL if available

---

### 2.2: Instruction Feed to ALU
**Currently:** Tied off
**What it does:** Routes SPI instruction to spu13_top control input

**Connections needed:**
```verilog
// spu_ecp5_top.v changes:

// From SPI parser (see 2.1)
wire spi_inst_valid;
wire [63:0] spi_inst_word;

// Decode instruction word
wire alu_start_spi;
wire [2:0] alu_opcode_spi;
wire [31:0] operand_A_spi, operand_B_spi, operand_C_spi, operand_D_spi;

spu_instruction_decoder decode_spi (
    .inst_word(spi_inst_word),
    .valid(spi_inst_valid),
    .alu_start(alu_start_spi),
    .alu_opcode(alu_opcode_spi),
    .operand_A(operand_A_spi),
    .operand_B(operand_B_spi),
    .operand_C(operand_C_spi),
    .operand_D(operand_D_spi)
);

// Wire to core (instead of tied-off 0)
spu13_top spu13_core_inst (
    ...
    .alu_start(alu_start_spi),  // Was 1'b0
    .alu_opcode(alu_opcode_spi),  // Was 3'b0
    ...
);
```

---

### 2.3: QR Result Commit Path
**Currently:** spu13_top outputs `A_out, B_out, C_out, D_out` but they're not connected back to SPI

**Signals to route:**
```verilog
// From spu13_top
wire alu_done;
wire [31:0] alu_A, alu_B, alu_C, alu_D;

// Create commit packet
wire qr_commit_valid = alu_done;
wire [3:0] qr_commit_lane = 4'h0;  // Single-lane for now
wire [63:0] qr_commit_A = {alu_A, alu_B};  // Pack into 64-bit
wire [63:0] qr_commit_B = {alu_C, alu_D};
wire [63:0] qr_commit_C = 64'h0;
wire [63:0] qr_commit_D = 64'h0;

// Wire to SPI mux
spi_southbridge u_spi_sb (
    ...
    .qr_commit_valid(qr_commit_valid),
    .qr_commit_lane(qr_commit_lane),
    .qr_commit_A(qr_commit_A),
    .qr_commit_B(qr_commit_B),
    .qr_commit_C(qr_commit_C),
    .qr_commit_D(qr_commit_D),
    ...
);
```

---

### 2.4: Status Register (Davis Ratio, Errors)
**Currently:** Only 3 LEDs output status
**What's needed:** 8-bit or 16-bit status register visible via SPI (CMD 0xAC)

**Status bits to expose:**
```verilog
wire [7:0] core_status;
assign core_status = {
    1'b0,                      // [7] reserved
    davis_violation,           // [6] Davis ratio out-of-band
    1'b0,                      // [5] reserved
    is_dissonant,              // [4] algebraic harmony violation
    alu_done,                  // [3] ALU complete
    piranha_pulse,             // [2] system heartbeat
    uart_tx,                   // [1] telemetry active
    boot_complete              // [0] boot done
};
```

---

## 3. MEDIUM Priority Features (Debug & Iteration)

### 3.1: Manifold Telemetry Output
**Purpose:** Stream full 13D state for debug
**Current:** Only LED blink
**Option:** Route 831-bit manifold_state to UART or debug port

**Complexity:** Needs uart_tx protocol (already in spu13_top)

---

### 3.2: Fault & Error Reporting
**Purpose:** Detect algebraic violations, ECC, RNS parity errors
**Current:** Not connected
**Signals to add:**
```verilog
wire axiomatic_fault;        // Davis gate violation
wire [1:0] fault_type;       // 0=Davis, 1=ECC, 2=RNS
wire [15:0] fault_count;     // Sticky counter
```

---

### 3.3: Feature Flag Parameters
**Current:** spu_ecp5_top has no parameters (hardcoded to SPU-13 core only)
**Artix-7 pattern:** 11 ENABLE_* flags + SPIN selection

**For ECP5 minimal spin, add:**
```verilog
module spu_ecp5_top #(
    parameter ENABLE_MATH = 1,
    parameter ENABLE_RPLU_V2 = 1,
    parameter ENABLE_RPLU_V2_PIPELINE = 1,
    parameter ENABLE_LUCAS_MAC = 0,  // Excluded for eval board
    parameter ENABLE_SU3 = 0         // Excluded for eval board
) (
    ...
);
```

---

### 3.4: Clock PLL Option
**Current:** Simple divider (50 MHz → 12.5 MHz)
**Better:** ECP5 PLL for arbitrary frequency targets

**If adding PLL:**
```verilog
parameter ECP5_CLK_DIV_LOG2 = 0;  // 0 = raw 50 MHz, 1 = 25 MHz, 2 = 12.5 MHz, etc.

generate
    if (ECP5_CLK_DIV_LOG2 == 0) begin
        // Raw 50 MHz (via BUFG)
        assign clk_sys = clk_50m;
    end else begin
        // Programmable divider
        reg [7:0] clk_div = 0;
        always @(posedge clk_50m) clk_div <= clk_div + 1;
        assign clk_sys = clk_div[ECP5_CLK_DIV_LOG2 - 1];
    end
endgenerate
```

---

## 4. LOW Priority (Full Parity)

### 4.1: GPU/HDMI Support
**Artix-7:** 4-lane HDMI video output
**ECP5-85:** Possible but space-constrained
**Recommendation:** Defer; minimal spin focuses on core + RPLU2

### 4.2: Audio (I2S)
**Artix-7:** I2S stereo output
**ECP5-85:** Possible
**Recommendation:** Defer; add if space after P&R

### 4.3: SOM/Lucas/SU3 Sidecars
**Artix-7:** All three available via instruction dispatch
**ECP5:** Excluded from minimal spin by design
**Recommendation:** Defer to future variant

---

## 5. Implementation Roadmap

### Phase 1: Core Wiring (Next)
**Effort:** 2–4 hours
**Files to create/modify:**
- [ ] `spu_ecp5_spi_southbridge.v` (extract/adapt from Artix-7)
- [ ] `spu_instruction_decoder.v` (decode 64-bit instruction word)
- [ ] Modify `spu_ecp5_top.v`:
  - Add SPI protocol handler instantiation
  - Route `spi_inst_valid`, `spi_inst_word` to ALU
  - Route `qr_commit_*` back to SPI mux
  - Add status register

**Verification:**
- [ ] Simulation: testbench exercises SPI commands (0xA0, 0xAC, 0xAE, 0xB1)
- [ ] P&R passes with new wiring
- [ ] Resource utilization stays <60% LUT

---

### Phase 2: Error Reporting (After Core Wiring)
**Effort:** 1–2 hours
**Files:**
- [ ] Add fault detection signals from spu13_top
- [ ] Wire to status register
- [ ] Update SPI CMD 0xAC response

---

### Phase 3: Feature Flags & Parameters (Polish)
**Effort:** 1 hour
**Files:**
- [ ] Add ENABLE_* parameters to spu_ecp5_top
- [ ] Add conditional instantiation logic

---

## 6. Reference: Artix-7 SPI Protocol Extract

**Location:** `hardware/boards/artix7/spu_a7_top.v` lines ~350–550 (approx.)

**Key functions:**
- `spu_spi_slave_handler` (or equivalent) — parses CMD byte, schedules reads/writes
- `qr_commit_mux` — multiplexes instruction results to output
- `spi_status_latch` — holds sticky flags between SPI reads

**For ECP5:** Can extract and adapt directly (same RTL logic, different board context)

---

## 7. Test Plan After Wiring

### Test 7.1: SPI CMD 0xB1 (Instruction Write)
```bash
# Send ROT opcode via SPI
# RP2350 firmware: write(0xB1, opcode, operands...)
# Expect: alu_done pulses; result available on next read
```

### Test 7.2: SPI CMD 0xAE (QR Readback)
```bash
# Send instruction, poll result
# RP2350 firmware: write(0xB1, ...) → read(0xAE) loop
# Expect: 16 bytes (4×32-bit QR commit) match computed value
```

### Test 7.3: SPI CMD 0xAC (Status)
```bash
# Read status after boot + error
# RP2350 firmware: read(0xAC)
# Expect: bit[0]=boot_complete, bit[3]=alu_done
```

---

## Summary: What's Missing vs. Artix-7

| Component | Artix-7 | ECP5 (Current) | Priority | Effort |
|---|---|---|---|---|
| SPI protocol | ✓ | ✗ | HIGH | 2h |
| Instruction decode | ✓ | ✗ | HIGH | 1h |
| QR commit path | ✓ | ✗ | HIGH | 1h |
| Status register | ✓ | Partial (LEDs) | HIGH | 30m |
| Feature flags | ✓ | ✗ | MEDIUM | 1h |
| Fault reporting | ✓ | ✗ | MEDIUM | 1h |
| Clock PLL | ✓ | Divider only | MEDIUM | 1h |
| Manifold telemetry | ✓ | ✗ | LOW | 2h |
| HDMI/GPU | ✓ | N/A | LOW | Defer |
| Audio/I2S | ✓ | N/A | LOW | Defer |

**Total HIGH effort:** ~4 hours → functional SPI bring-up

---

**Next:** Proceed with Phase 1 (core wiring)?
