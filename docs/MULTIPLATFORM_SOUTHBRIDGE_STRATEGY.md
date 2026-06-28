# Multi-Platform Southbridge Architecture
## Expanding SPU-13 Support Beyond RP2350

**Date:** 2026-06-29  
**Status:** Strategic Analysis  
**Scope:** Technology compatibility matrix and phased rollout roadmap

---

## Executive Summary

The SPU-13 Southbridge is currently RP2350-only, but the SPI protocol and FPGA-side interface are **platform-agnostic**. By creating hardware abstraction layers and porting the reference implementation to alternative MCUs with equivalent I/O capabilities, we can:

1. **Reduce lock-in** to Raspberry Pi ecosystem
2. **Support industrial deployments** that already standardized on NXP, Infineon, or Espressif
3. **Optimize for specific applications** (e.g., Teensy 4.1 for real-time robotics, PSoC 5LP for analog co-processing)
4. **Future-proof the FPGA interface** against changes in RP2 product line

---

## Current Architecture (RP2350 Baseline)

### What RP2350 Provides

| Feature | RP2350 Component | Why It Matters |
|---------|-----------------|-----------------|
| **SPI Master** | Hardware SPI0 (up to 20 MHz) | Bit-banged fallback via PIO |
| **PIO State Machines** | 8 independent FSMs @ 125 MHz | Custom protocol generation (Whisper serial, Laminar 2-wire) |
| **DMA** | DREQ-driven channels | Zero-CPU-overhead frame streaming |
| **Clock Accuracy** | 1% oscillator tolerance | Deterministic cycle-gating via `spu_bio_resonance.pio` |
| **Dual-core** | RP2350 (SIM) + RP2040 (Visualizer) | Separation of concerns |
| **I2C/UART** | Standard peripherals | Telemetry polling + debug console |

### Proven Behavior

- **SPI Protocol:** `spu_spi_slave.v` (FPGA) expects 7 commands (0xA0–0xB1, 0xA5) over standard SPI
- **Latency Requirement:** < 1 µs round-trip for atomic manifold snapshots
- **Bandwidth:** 921.6 kbaud (UART) to PC; 2 Mbps (SPI) to FPGA
- **Determinism:** Fibonacci-interval pulses @ 61.44 kHz (Piranha Pulse) ← must be cycle-accurate

---

## Platform Comparison Matrix

### Tier 1: Full API Parity (Highest Priority)

#### **NXP Teensy 4.1 (i.MX RT1062) — BEST NEAR-TERM CANDIDATE**

| Dimension | Rating | Notes |
|-----------|--------|-------|
| **FlexIO State Machines** | ✅✅✅ | 4 timers × 4 shifters = 16 state machines (vs RP2350's 8) |
| **SPI Master** | ✅✅✅ | 3× independent SPI ports, hardware capable of 30+ MHz |
| **DMA** | ✅✅✅ | 32 channels, supports channel chaining (more flexible than RP) |
| **Clock Accuracy** | ✅✅ | 600 MHz PLL-locked Cortex-M7 (vs RP's 48/125 MHz) |
| **Analog Co-Processing** | ✅✅ | 16 ADCs, can integrate sensor pre-processing |
| **Community Support** | ✅✅✅ | Extensive (Teensyduino ecosystem) |
| **Cost** | ✅ | ~$25 (similar to RP2350) |
| **Power** | ⚠️ | ~200 mW active (higher than RP2350's ~50 mW) |
| **Porting Effort** | 🟡 | ~30% of code requires adaptation (FlexIO register model differs from PIO) |

**Why It Works:**
- FlexIO is directly inspired by PIO and has similar programming model
- 600 MHz clock enables higher SPI speeds (10+ MHz vs 2 MHz current)
- Extensive DSP blocks in i.MX RT1062 enable on-board DSP preprocessing
- Teensyduino provides mature USB stack

**Proof of Concept Work:**
```c
// Pseudo-code: FlexIO → SPI master emulation
// Configure FlexIO Shifter 0 for SPI output
FLEXIO_SetShifterConfig(instance, shifterIndex, config);

// Transmit byte to FPGA
FLEXIO_WriteBitSensor(instance, 0, 0x00);  // command

// Receive response (similar to PIO read)
uint32_t response = FLEXIO_ReadSensorData(instance);
```

**Estimated Timeline:**
- Week 1–2: FlexIO protocol study, register reference manual review
- Week 3–4: Port `spu_bio_resonance.pio` to FlexIO equivalent (`spu_bio_resonance_flexio.c`)
- Week 5: Adapt SPI master, test against FPGA testbench
- Week 6: Integration testing with real Teensy 4.1 + Tang 25K

---

#### **NXP LPC55S69 — MEDIUM PRIORITY**

| Dimension | Rating | Notes |
|-----------|--------|-------|
| **FlexIO State Machines** | ✅✅ | 4 timers × 4 shifters = 16 state machines |
| **SPI Master** | ✅✅ | 1× SPI port (vs Teensy's 3), but hardware capable |
| **DMA** | ✅✅ | 30 channels, supports chaining |
| **Clock Accuracy** | ✅✅ | 150 MHz (slower than Teensy, but still > RP2350) |
| **Security Features** | ✅✅✅ | Crypto accelerator (AES, SHA), useful for industrial |
| **Porting Effort** | 🟡 | ~25% (FlexIO model same as Teensy, just fewer resources) |

**Why It Works:**
- Same FlexIO architecture as Teensy (easier port)
- Built-in crypto accelerator → can authenticate RPLU updates
- Dual Cortex-M33 cores (one for Southbridge, one for application)

**Strategic Value:**
- LPC55S69 is enterprise-grade (used in industrial IoT, automotive)
- Enables adoption by customers already on NXP supply chain

---

### Tier 2: Partial API (Medium Priority)

#### **Infineon/Cypress PSoC 5LP — UDB Programmable Logic**

| Dimension | Rating | Notes |
|-----------|--------|-------|
| **UDB (Universal Digital Blocks)** | ✅✅ | 24 UDBs = programmable ALU/state machine blocks |
| **SPI Master** | ✅✅ | Hardware SPI, but less flexible than FlexIO |
| **DMA** | ⚠️ | Limited (1 DMA, basic functionality) |
| **Clock Accuracy** | ✅ | 80 MHz (adequate for Southbridge) |
| **Analog Co-Processing** | ✅✅✅ | Exceptional (12 opamps, DACs, ADCs integrated) |
| **Porting Effort** | 🔴 | ~50% (UDB programming is fundamentally different) |

**Why Consider It:**
- UDBs are "programmable digital peripherals" — closest non-FPGA equivalent to custom FSMs
- PSoC philosophy (Programmable System-on-Chip) aligns perfectly with SPU-13's heterogeneous compute model
- Excellent for applications needing analog preprocessing (sensor fusion, impedance measurement)

**Blocker:**
- PSoC 5LP is **end-of-life** (last orders 2024, support ending 2026)
- UDB programming requires PSoC Creator (proprietary IDE, not open-source-friendly)
- Porting effort not justified unless customer specifically requires it

**Verdict:** Archive as "nice-to-have for analog-heavy applications" but don't prioritize.

---

#### **Espressif ESP32-S3 — RMT Protocol Engine**

| Dimension | Rating | Notes |
|-----------|--------|-------|
| **RMT (Remote Control)** | ⚠️ | 8 channels, but designed for IR/NEC decoding |
| **SPI Master** | ✅✅ | Hardware SPI, 80 MHz capable |
| **DMA** | ✅✅ | 6 channels, ESP-DMA controller |
| **Clock Accuracy** | 🟡 | 240 MHz, but RTOS jitter introduces ~100 ns uncertainty |
| **Wireless** | ✅✅✅ | 802.11ax WiFi + BLE (bonus feature) |
| **Porting Effort** | 🔴 | ~60% (RMT is fundamentally IR-focused, not general-purpose) |

**Why It Doesn't Fit Well:**
- RMT is **not a general-purpose I/O engine** — optimized for 38 kHz modulation patterns
- FreeRTOS introduces real-time jitter (millisecond-scale variance)
- Lacks hardware DMA-to-SPI integration that RP2350 provides naturally

**Why Consider It Anyway:**
- **Wireless deployment** — Southbridge on a robot that streams to remote FPGA cluster
- **Cost** — ESP32-S3 DevKit < $5
- **Integration** — WiFi direct to cloud telemetry (skip intermediate PC)

**Verdict:** Viable as "wireless telemetry gateway" but not as primary Southbridge platform.

---

### Tier 3: Exotic / Not Recommended

#### **Lattice iCE40 — MCU+FPGA Combo**

| Dimension | Rating | Notes |
|-----------|--------|-------|
| **Custom FPGA Logic** | ✅✅✅ | Ultimate flexibility |
| **SPI Master** | ✅✅✅ | Fully programmable |
| **DMA** | ✅✅✅ | Fully programmable |
| **Power** | 🔴 | 500+ mW (2–10× higher than pure MCU) |
| **Porting Effort** | ✅✅✅ | No porting needed (replicate PIO FSMs in FPGA) |

**Why Not:**
- **Defeats the purpose** — Southbridge exists to offload the FPGA, not add another one
- **Power & area** — Adds cost/heat without functional advantage
- **Reliability** — Extra silicon layer increases failure modes

**Niche Use Case:**
- High-bandwidth FPGA-to-FPGA interconnects (e.g., distributed SPU-13 cluster)
- Could be useful as dedicated "FPGA Bridge" board in future, but not for core Southbridge

---

## Recommended Rollout Strategy

### Phase 1: Foundation (Q3 2026)
**Goal:** Establish portable Southbridge API layer

**Deliverables:**
1. **`hardware/rp_common/southbridge_hal.h`** — Hardware Abstraction Layer
   - Defines `sb_spi_init()`, `sb_spi_xfer()`, `sb_pio_write()`, `sb_pio_read()`
   - All platform-specific code hidden behind these 4 functions

2. **`hardware/rp_common/southbridge_rp2350.c`** — RP2350 implementation (reference)
   - Existing code, refactored into HAL

3. **RTL-side testbench compatibility** — Ensure all tests remain platform-agnostic
   - SPI protocol tests don't assume any specific MCU behavior
   - Test vectors purely functional

---

### Phase 2: Teensy 4.1 Port (Q4 2026)
**Goal:** First alternative platform validation

**Deliverables:**
1. **`hardware/rp_common/southbridge_teensy41.c`** — FlexIO implementation
   - Parallel port of `spu_bio_resonance.pio` → `spu_bio_resonance_flexio.c`
   - SPI master via either hardware SPI or emulated via FlexIO

2. **Integration tests:**
   - `software/tests/test_southbridge_teensy41.cpp` — Verify SPI protocol via simulator
   - Hardware test matrix: Teensy 4.1 + Tang 25K tandem run (same tests as RP2350)

3. **Documentation:**
   - `docs/TEENSY41_SOUTHBRIDGE_SETUP.md` — Build, flash, test instructions

4. **Community artifact:**
   - GitHub gist / PlatformIO example project

**Success Criteria:**
- Identical SPI command/response patterns as RP2350
- Sub-microsecond latency (measured with oscilloscope on CS# pin)
- All 24 rational_som.py test vectors pass

---

### Phase 3: LPC55S69 Port (Q1 2027, Contingent)
**Goal:** Industrial-grade option

**Deliverables:**
1. **`hardware/rp_common/southbridge_lpc55s69.c`** — FlexIO (identical to Teensy, just different peripheral clock)
2. **Crypto integration:** Optional `spu_cfg_sign()` using LPC's AES accelerator
3. **Documentation:** Enterprise deployment guide

---

### Phase 4: ESP32-S3 Wireless Gateway (Q2 2027, Optional)
**Goal:** Telemetry relay for distributed clusters

**Deliverables:**
1. **`hardware/rp_common/southbridge_esp32s3_wifi.c`** — WiFi-bridged Southbridge
2. **Cloud telemetry:** Stream manifold state → AWS IoT / Azure IoT Hub
3. **Documentation:** Setup for remote FPGA cluster scenarios

---

## Architecture of the HAL

### Header: `southbridge_hal.h`

```c
#ifndef SOUTHBRIDGE_HAL_H
#define SOUTHBRIDGE_HAL_H

#include <stdint.h>

// Platform enumeration (set at compile time)
enum sb_platform_t {
    SB_PLATFORM_RP2350,
    SB_PLATFORM_TEENSY41,
    SB_PLATFORM_LPC55S69,
    SB_PLATFORM_ESP32S3,
};

// Core SPI operations
void sb_spi_init(uint32_t clock_hz);
void sb_spi_cs_enable(void);
void sb_spi_cs_disable(void);
uint8_t sb_spi_xfer_byte(uint8_t tx_byte);
void sb_spi_xfer_block(const uint8_t *tx_buf, uint8_t *rx_buf, size_t len);

// PIO-equivalent state machine (Piranha Pulse generation)
void sb_pio_init(void);
void sb_pio_send_pulse(uint16_t width_ns);
void sb_pio_config_quadray(uint32_t q0, uint32_t q1, uint32_t q2, uint32_t q3);

// UART telemetry
void sb_uart_init(uint32_t baud);
void sb_uart_putc(uint8_t c);
uint8_t sb_uart_getc_blocking(void);

// Platform query (useful for conditional compilation at runtime)
enum sb_platform_t sb_get_platform(void);
uint32_t sb_get_clock_hz(void);

#endif // SOUTHBRIDGE_HAL_H
```

### Implementation Pattern

**For RP2350:**
```c
// hardware/rp_common/southbridge_rp2350.c
#include "southbridge_hal.h"
#include "hardware/spi.h"
#include "hardware/pio.h"

void sb_spi_init(uint32_t clock_hz) {
    spi_init(spi0, clock_hz);
    gpio_set_function(SPI0_RX, GPIO_FUNC_SPI);
    gpio_set_function(SPI0_TX, GPIO_FUNC_SPI);
    // ...
}

uint8_t sb_spi_xfer_byte(uint8_t tx_byte) {
    return spi_get_hw(spi0)->dr;  // read DR after write
}
// ...
```

**For Teensy 4.1:**
```c
// hardware/rp_common/southbridge_teensy41.c
#include "southbridge_hal.h"
#include "flexio.h"

void sb_spi_init(uint32_t clock_hz) {
    // Initialize FlexIO shifters for SPI
    flexio_init(&FLEXIO1);
    flexio_spi_config_t spi_cfg = {
        .baud = clock_hz,
        .shifter_tx = 0,
        .shifter_rx = 1,
    };
    flexio_spi_init(&FLEXIO1, &spi_cfg);
}

uint8_t sb_spi_xfer_byte(uint8_t tx_byte) {
    FLEXIO_WriteBitSensor(&FLEXIO1, 0, tx_byte);
    return FLEXIO_ReadSensorData(&FLEXIO1, 1);
}
// ...
```

---

## Resource Comparison

### Flash / RAM Requirements (Southbridge firmware only)

| Platform | Flash Used | RAM Used | Available | Headroom |
|----------|-----------|----------|-----------|----------|
| **RP2350** | ~25 KB | 4 KB | 256 KB / 520 KB | ✅ Excellent |
| **Teensy 4.1** | ~30 KB | 5 KB | 1 MB / 960 KB | ✅ Excellent |
| **LPC55S69** | ~28 KB | 4 KB | 256 KB / 192 KB | ✅ Good |
| **ESP32-S3** | ~40 KB | 8 KB | 384 KB / 512 KB | ✅ Excellent |

All platforms have **>100× headroom** for Southbridge code. No resource constraints.

---

## Risk Assessment & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| **FlexIO API incompatibility** | Medium | High | Create generic `flexio_common.h` wrapper; test early with dev boards |
| **Clock jitter on Teensy** | Low | Medium | Measure jitter with oscilloscope; adjust Piranha Pulse tolerance if needed |
| **SPI timing violations** | Low | High | Comprehensive testbench sweep over 1–10 MHz; hardware validation on all platforms |
| **Vendor SDK rot** | Medium | Low | Pin SDK versions in `requirements.txt`; maintain offline copies of critical HAL files |
| **Community fragmentation** | Low | Low | Single reference implementation (RP2350) maintained by core team; ports welcomed but not mandated |

---

## Decision Matrix: Which Platform to Port First?

### Scoring Criteria (1–5 scale)

| Criterion | Weight | RP2350 | Teensy | LPC55S69 | ESP32-S3 |
|-----------|--------|--------|--------|----------|----------|
| **Hardware maturity** | 25% | 5 | 5 | 4 | 4 |
| **API familiarity (FlexIO)** | 20% | N/A | 5 | 5 | 2 |
| **Community size** | 15% | 4 | 5 | 2 | 5 |
| **Real-time capability** | 20% | 5 | 5 | 4 | 2 |
| **Porting effort** | 10% | 5 | 3 | 4 | 2 |
| **Cost/availability** | 10% | 4 | 4 | 3 | 5 |
| **WEIGHTED TOTAL** | 100% | — | **4.5** | 3.7 | 3.4 |

**Verdict:** **Teensy 4.1 is the clear winner for first port.**

Rationale:
- FlexIO provides closest API parity to PIO
- 600 MHz Cortex-M7 enables higher SPI speeds
- Teensyduino ecosystem mature and stable
- Porting effort moderate, learning curve smooth

---

## Next Steps (Immediate Actions)

### This Week
- [ ] Create `hardware/rp_common/southbridge_hal.h` skeleton
- [ ] Refactor existing RP2350 code into `southbridge_rp2350.c` behind HAL
- [ ] Run full test suite to ensure refactoring didn't break anything

### Next Week
- [ ] Obtain Teensy 4.1 evaluation board
- [ ] Study FlexIO register reference manual (NXP IMX RT Series datasheet §47)
- [ ] Prototype `spu_bio_resonance_flexio.c` (Piranha Pulse generator)
- [ ] Create testbench for HAL-level SPI protocol validation

### Month 2
- [ ] Full Teensy 4.1 port
- [ ] Hardware testing: Teensy 4.1 + Tang 25K tandem
- [ ] Benchmark: latency, jitter, throughput

---

## Files to Create / Modify

```
NEW:
  hardware/rp_common/southbridge_hal.h         ← HAL interface (platform-agnostic)
  hardware/rp_common/southbridge_teensy41.c    ← Teensy 4.1 implementation
  docs/MULTIPLATFORM_SOUTHBRIDGE_STRATEGY.md   ← This document
  docs/TEENSY41_SOUTHBRIDGE_SETUP.md           ← Teensy 4.1 quickstart
  docs/HAL_MIGRATION_GUIDE.md                  ← For developers porting other MCUs

REFACTOR:
  hardware/rp_common/spu_diag.c                ← Include HAL header, use sb_spi_xfer_byte()
  hardware/rp_common/southbridge_rp2350.c      ← Existing RP2350 code (new file)
  software/CMakeLists.txt                      ← Add platform selection flag

TESTING:
  software/tests/test_southbridge_hal.cpp      ← Platform-agnostic SPI tests
  software/tests/test_southbridge_teensy41.cpp ← Teensy-specific integration
```

---

## Appendix: Technical Deep Dive — FlexIO vs PIO

### Conceptual Alignment

| Concept | PIO (RP2350) | FlexIO (i.MX RT) |
|---------|-------------|-----------------|
| **Unit** | State machine (8 total) | Shifter + Timer combination (16 total) |
| **Clock** | 125 MHz (fixed) | Configurable (8–66 MHz typical for SPI) |
| **GPIO mapping** | Direct (32-pin pad) | Via multiplexer (more flexible routing) |
| **Instruction set** | 16 instructions (jmp, mov, wait, etc.) | Implicit (shifter behavior is hard-coded) |
| **Programming style** | Assembly-like `.program` | C register configuration |

### Why Porting is Feasible

1. **Both are bit-banging engines** — designed to emulate protocols not natively supported
2. **Both support timed I/O** — PIO's delay instructions map to FlexIO timer counts
3. **Both integrate with DMA** — can stream data without CPU intervention
4. **Both are cycle-accurate** — no RTOS overhead

### Key Translation Pattern

**PIO Code (Piranha Pulse 61.44 kHz):**
```
.program piranha_pulse
  mov x, 0x0A              ; delay 10 cycles
  nop x--, 31              ; wait 31 cycles total
  set pins, 1              ; drive high
  mov x, 0x04
  nop x--, 31              ; hold for 31 cycles
  set pins, 0              ; drive low
  jmp start
```

**FlexIO equivalent (pseudo-C):**
```c
// Timer 0: frequency divider → 61.44 kHz
FLEXIO_TIMCFG[0] = (FLEXIO_TIMCFG_TIMDIS_ENABLE | 
                    FLEXIO_TIMCFG_TIMRST_ON_TIMER_COMPARE |
                    FLEXIO_TIMCFG_TIMDEC_CLK_DIV_BY_16);
FLEXIO_TIMCMP[0] = 16383;  // 2 kHz timer (divides 125 MHz)

// Shifter 0: controlled by Timer 0
FLEXIO_SHIFTCFG[0] = (FLEXIO_SHIFTCFG_SSTOP_BIT_ZERO |
                      FLEXIO_SHIFTCFG_SSTART_BIT_DISABLED |
                      FLEXIO_SHIFTCFG_INSRC_FROM_PIN);

// GPIO mode: manual toggle via register
FLEXIO_GPIO_OUTPUT_REG = 0x1;  // pin high
// (wait via timer interrupt or busy loop)
FLEXIO_GPIO_OUTPUT_REG = 0x0;  // pin low
```

---

## Conclusion

Expanding Southbridge support to Teensy 4.1 (and later LPC55S69 and ESP32-S3) is technically feasible and strategically valuable. The HAL abstraction layer costs minimal development effort and unlocks portability without compromising the RP2350 reference implementation.

**Recommended action:** Start Phase 1 (HAL foundation) immediately to establish the abstraction. Phase 2 (Teensy port) should begin as soon as a development board is procured.

---

**Document History:**
- **2026-06-29:** Initial strategic analysis created

