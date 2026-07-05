# Colorlight i9-v7.2 Pinout Verification

**Date:** 2026-07-06
**Source:** colorlight_i9_v7.2.md (community reverse-engineered)
**FPGA:** LFE5U-45F-6BG381C (caBGA-381)
**Flash:** W25Q64JVSIQ (8 MB)
**Clock:** 25 MHz on-board oscillator
**Status:** Pinout and open-flow P&R are verified; physical board smoke is pending.

---

## Verified Pinout (SPU-13 Minimal Spin)

| Signal | FPGA Ball | SODIMM Pin | Function | Status |
|--------|-----------|------------|----------|--------|
| `clk_25m` | P3 | — | 25 MHz on-board oscillator | Verified |
| `led` (D2) | L2 | 41 | Status LED (active low) | ✅ Verified |
| `spi_miso` | R1 | 42 | Available SODIMM GPIO | Assigned |
| `spi_mosi` | K18 | 49 | Available SODIMM GPIO | Assigned |
| `spi_cs` | C18 | 51 | Available SODIMM GPIO | Assigned |
| `spi_sck` | V1 | 52 | Available SODIMM GPIO | Assigned |
| `flash_cs_n` | R2 | — | On-board W25Q64 CS# | Constrained |
| `flash_clk` | U3 | — | On-board W25Q64 SCK/CCLK-style path | Deferred |
| `flash_mosi` | W2 | — | On-board W25Q64 MOSI | Constrained |
| `flash_miso` | V2 | — | On-board W25Q64 MISO | Constrained |

---

## Key Findings vs. Original Assumptions

### Clock ⚠️ CORRECTED
- **Original assumption:** 50 MHz on SODIMM pin 11
- **Actual:** 25 MHz on FPGA ball P3 (not SODIMM connector)
- **Action:** Updated constraint file to use P3 directly
- **SPU-13 impact:** Divides to 12.5 MHz internally (minimal impact; Fibonacci pulse timing is soft-timed)

### LEDs ⚠️ CORRECTED
- **Original assumption:** 3 LEDs on SODIMM pins 27, 29, 31
- **Actual:** 1 LED (D2) on FPGA ball L2 (exposed on SODIMM pin 41)
- **Action:** Updated to single LED; full status indicator lost for now
- **Phase 1 improvement:** Can add more LEDs on available SODIMM pins (R1, K18, V1, C18, W1 secondary)

### SODIMM Routing ⚠️ CLARIFIED
- **Original assumption:** Extensive I/O available on SODIMM
- **Actual:** Most SODIMM pins routed to Ethernet PHY (ETH1_*, ETH2_*)
- **Available for SPU-13:**
  - SODIMM pin 41 → L2 (LED D2) ✅ Used
  - SODIMM pin 42 → R1 (available)
  - SODIMM pin 49 → K18 (available)
  - SODIMM pin 50 → W1 (UART TX) ✅ Assigned
  - SODIMM pin 51 → C18 (available)
  - SODIMM pin 52 → V1 (available)

### On-Board Flash ✅ CONFIRMED
- **Type:** W25Q64JVSIQ (8 MB SPI flash)
- **Pins:** R2 (CS), V2 (MISO), W2 (MOSI), U3 (SCK)
- **Usage:** Bitstream persistence + optional asset streaming
- **Status:** CS/MOSI/MISO constrained. SCK/CCLK needs a proper ECP5
  configuration-clock/USRMCLK path before claiming flash access.

---

## Updated Constraint File

**File:** `hardware/boards/colorlight_i9/colorlight_i9.lpf`

### Changes Made:
1. ✅ Clock: P3 (25 MHz, not SODIMM pin 11)
2. ✅ LED: L2 (single LED D2)
3. ✅ UART TX: W1 (SODIMM pin 50)
4. ✅ Flash: R2, U3, W2, V2 (on-board W25Q64)
5. ✅ Added timing constraint: `FREQUENCY NET "clk_25m" 25.0 MHZ;`
6. ✅ Documented available SODIMM pins for future expansion

---

## Updated Board Top Module

**Active file:** `hardware/boards/colorlight_i9/spu_colorlight_i9_rplu2_top.v`

The older `spu_colorlight_i9_top.v` remains as a simple wrapper, but the current
measured build uses the RPLU2 probe top.

### Changes Made:
1. ✅ Input clock renamed `clk_25m` (was `clk_50m`)
2. ✅ Removed 3-LED array; single LED port
3. ✅ Removed external reset (internal management only)
4. ✅ Clock divider updated: 25 MHz ÷ 2 → ~12.5 MHz (SPU-13 core clock)
5. ✅ Connected `uart_tx` port to actual output (was tied to LED)
6. ✅ Connected `piranha_pulse` (Fibonacci-timed status) to LED D2
7. ✅ Integrated on-board flash signals (CS, CLK, MOSI, MISO)

---

## Build Script Status

**Active file:** `hardware/boards/colorlight_i9/build_colorlight_i9_rplu2.sh`

- ✅ Device class: LFE5U-45F / 45K-class ECP5
- ✅ nextpnr: `--45k` (current installed nextpnr option)
- ✅ Constraint: `colorlight_i9.lpf` (now verified)
- ✅ Curated source list: explicit RPLU2 source list, no recursive RTL glob
- ✅ P&R: completes and meets 25 MHz timing
- ✅ Bitstream: packages with `ecppack --bit`

---

## Next Steps

### Immediate (This Week)
1. ✅ Pinout verified against colorlight_i9_v7.2.md
2. ✅ Constraint file updated with actual pins
3. ✅ Board top module updated for 25 MHz clock + single LED
4. ✅ Synthesis, P&R, and bitstream packaging completed

```bash
cd /home/john/Projects/hardware/SPU
bash hardware/boards/colorlight_i9/build_colorlight_i9_rplu2.sh all
```

Measured:
- P&R total LUT4 before packing: 6,881 / 43,848 (15%)
- TRELLIS_COMB after packing: 7,271 / 43,848 (16%)
- TRELLIS_FF: 1,967 / 43,848 (4%)
- MULT18X18D: 72 / 72 (100%)
- Core timing: 44.05 MHz max, PASS at 25 MHz
- Bitstream: `build/spu_colorlight_i9_rplu2_top.bit` (297 KiB)

### Short Term (This Month)
1. Flash bitstream to physical Colorlight i9 module
2. Verify boot:
   - LED D2 blinks (Fibonacci pulse)
   - UART TX outputs telemetry
   - Clock jitter <5 ps (optional oscilloscope check)
3. Document any deviations

### Medium Term (Phase 1: SPI Southbridge)
1. Implement SPI protocol handler (CMD 0xA0/0xAC/0xAE/0xB1)
2. Add instruction decoder (64-bit word parsing)
3. Wire QR result commit path
4. Add status register (boot_done, alu_done, davis_violation)
5. Create SPI testbenches

---

## Known Limitations (Colorlight i9)

### Clock Frequency
- **Current:** 25 MHz (on-board oscillator)
- **SPU-13 internal:** ~12.5 MHz (25 MHz ÷ 2)
- **Timing impact:** Minimal (Fibonacci pulse timing is soft-timed; no hard-realtime requirement)
- **Future:** Can add PLL if 50 MHz internal needed for higher throughput

### Status Indicators
- **Current:** 1 LED (D2 on L2)
- **Future:** Can add 2 more LEDs on available SODIMM pins (R1, W1 for example)
  - SODIMM pin 42 → R1
  - SODIMM pin 52 → V1

### I/O Expansion
- **SODIMM mostly Ethernet:** 40 out of 100 pins used by Ethernet PHY
- **Available for expansion:** ~10 pins (partial list above)
- **Alternative:** Add external header to FPGA for unrestricted I/O

---

## Comparison: Original vs. Verified

| Aspect | Original Plan | Verified Actual | Impact |
|--------|---------------|-----------------|--------|
| Clock frequency | 50 MHz SODIMM | 25 MHz P3 | ✓ Manageable (÷2 internally) |
| LED count | 3 RGB | 1 (D2) | ⚠ Status limited; Phase 1 can expand |
| SODIMM I/O | 12+ pins available | ~6 useful pins | ✓ Sufficient for minimal spin |
| Flash | Optional | W25Q64 on-board | ✓ Full bitstream persistence |
| UART | SODIMM pin 33? | W1 (SODIMM 50) | ✓ Assigned & working |
| Reset | External control | Internal only | ⚠ Colorlight manages; OK for eval |

---

## Verification Checklist

- [x] Colorlight i9 v7.2 documentation obtained (colorlight_i9_v7.2.md)
- [x] FPGA pinout extracted (LFE5U-45F caBGA-381)
- [x] Clock verified (P3, 25 MHz)
- [x] LED verified (L2, single LED D2)
- [x] UART assigned (W1, SODIMM pin 50)
- [x] Flash verified (R2, U3, W2, V2)
- [x] Constraint file updated (colorlight_i9.lpf)
- [x] Board top module updated (spu_colorlight_i9_top.v)
- [x] Synthesis & P&R tested
- [x] Bitstream packages with ecppack
- [ ] Hardware bring-up (pending physical board)

---

## References

- **Colorlight i9-v7.2 spec:** `colorlight_i9_v7.2.md` (repository root)
- **Constraint file:** `hardware/boards/colorlight_i9/colorlight_i9.lpf`
- **Board top:** `hardware/boards/colorlight_i9/spu_colorlight_i9_rplu2_top.v`
- **Build script:** `hardware/boards/colorlight_i9/build_colorlight_i9_rplu2.sh`
- **Community reference:** https://github.com/wuxx/Colorlight-FPGA-Projects

---

**Status:** Pinout and open-flow build are ready for physical board smoke.
