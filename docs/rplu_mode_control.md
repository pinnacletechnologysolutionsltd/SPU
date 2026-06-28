# RPLU Mode Control — RP2350 Integration Guide

## Overview

The SPU Sovereign Cluster supports configurable RPLU modes across two architectures:

| Architecture | Module | Field | Mode Control |
|:---|:---|:---|:---|
| **Legacy** (Morse) | `rplu_exp.v` + `rplu_skel.v` | Q(√3) rational surd | SPI CMD 0xAC → `rplu_mode` bit |
| **v2** (Thimble-Padé) | `rplu_thimble_pade.v` + `spu13_fp4_inverter.v` | F_{p^4} over M31 | PHSLK (0x42) pipeline, FLAGS.V for singularity |

### Legacy RPLU Mode Control

The original Adaptive Precision Mode for SPU-4 satellite RPLU units with Morse potential ROM banks.

---

## Hardware Summary

| Component | Change | Cost |
|:---|:---|:---|
| `rplu_dual_bank.mem` | 128-entry ROM (Bank 0 + Bank 1) | 0 extra BRAMs |
| `bank_sel` mux in BRAM | 1-bit address MSB | ~2 LUTs |
| `rplu_mode` register | 1-bit FF in `spu_system` (Ch6) | ~5 FFs |
| SPI CMD 0xAC | Extended to 4 bytes (was 3) | 0 LUTs |

**Total hardware overhead: ~10 LUTs, ~10 FFs.**

---

## SPI Protocol

All communication uses the existing Sovereign SPI protocol at up to 2 MHz, SPI Mode 0.

### Reading Status — CMD `0xAC`

Send 1 byte, receive 4 bytes:

```
TX: [0xAC]
RX: [laminar_hi] [laminar_lo] [flags] [mode]
```

| Byte | Bits | Meaning |
|:---|:---|:---|
| 0 | `[15:8]` | `laminar_index` high byte |
| 1 | `[7:0]`  | `laminar_index` low byte |
| 2 | `[7:5]`  | `ratio_lat` (signed 3-bit residual) |
| 2 | `[4]`    | `ratio_valid` (sticky) |
| 2 | `[3]`    | `fifo_full` |
| 2 | `[2]`    | `turbulence` alert |
| 2 | `[1]`    | `is_janus_point` |
| 2 | `[0]`    | `snap_lock` |
| 3 | `[0]`    | **`rplu_mode`** — `0`=Smooth, `1`=Turbulent |

### Switching Mode — CMD `0xA5`

Send the standard two-chord packet with `sel=6`:

```
Command:      [0xA5]
Header chord: [0xA5][0x06][0x00][0x00][0x00][0x00][0x00][0x00]
              magic  sel=6 ...
Data chord:   [0x00][0x00][0x00][0x00][0x00][0x00][0x00][mode]
                                                           ^0=Smooth 1=Turbulent
```

> [!IMPORTANT]
> The existing CMD `0xA5` path uses `sel` bits `[50:48]` from the header chord.
> Set `hdr_shift[50:48] = 3'd6` to target the `rplu_mode` register.

---

## RP2350 Reference Implementation

```c
// rplu_southbridge.c — RPLU Adaptive Mode Controller
// Runs on RP2350 Hazard3 core. Poll rate: ~1kHz.

#include "pico/stdlib.h"
#include "hardware/spi.h"

#define SPI_PORT    spi0
#define PIN_CS      5
#define PIN_SCK     2
#define PIN_MOSI    3
#define PIN_MISO    4

// Threshold tuning — adjust after Phase 3 calibration
#define TURBULENCE_THRESH   5    // consecutive turbulent polls before switch
#define LAMINAR_THRESH      20   // consecutive laminar polls before revert

typedef enum { MODE_SMOOTH = 0, MODE_TURBULENT = 1 } rplu_mode_t;

static uint8_t read_status(uint16_t *laminar, uint8_t *flags, uint8_t *mode) {
    uint8_t tx[5] = {0xAC, 0, 0, 0, 0};
    uint8_t rx[5] = {0};
    gpio_put(PIN_CS, 0);
    spi_write_read_blocking(SPI_PORT, tx, rx, 5);
    gpio_put(PIN_CS, 1);
    *laminar = (rx[1] << 8) | rx[2];
    *flags   = rx[3];
    *mode    = rx[4] & 0x01;
    return (rx[3] >> 2) & 0x01;  // return turbulence bit
}

static void set_rplu_mode(rplu_mode_t m) {
    // Header: magic=0xA5, sel=6 at bits[50:48] of 64-bit header
    // Header byte layout (big-endian 8 bytes):
    //   byte0=0xA5, byte1=0x06 (sel in low 3 bits of this byte)
    uint8_t cmd = 0xA5;
    uint8_t hdr[8] = {0xA5, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    uint8_t dat[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, (uint8_t)m};
    gpio_put(PIN_CS, 0);
    spi_write_blocking(SPI_PORT, &cmd, 1);
    spi_write_blocking(SPI_PORT, hdr, 8);
    spi_write_blocking(SPI_PORT, dat, 8);
    gpio_put(PIN_CS, 1);
}

void rplu_southbridge_task(void) {
    static rplu_mode_t current_mode = MODE_SMOOTH;
    static int turbulent_count = 0;
    static int laminar_count   = 0;

    uint16_t laminar;
    uint8_t flags, reported_mode;
    uint8_t turbulence = read_status(&laminar, &flags, &reported_mode);

    if (turbulence) {
        turbulent_count++;
        laminar_count = 0;
    } else {
        laminar_count++;
        turbulent_count = 0;
    }

    // Switch to Turbulent mode after sustained stress
    if (current_mode == MODE_SMOOTH && turbulent_count >= TURBULENCE_THRESH) {
        set_rplu_mode(MODE_TURBULENT);
        current_mode = MODE_TURBULENT;
        printf("[RPLU] Mode -> TURBULENT | laminar=0x%04X\n", laminar);
        turbulent_count = 0;
    }

    // Revert to Smooth after sustained calm
    if (current_mode == MODE_TURBULENT && laminar_count >= LAMINAR_THRESH) {
        set_rplu_mode(MODE_SMOOTH);
        current_mode = MODE_SMOOTH;
        printf("[RPLU] Mode -> SMOOTH    | laminar=0x%04X\n", laminar);
        laminar_count = 0;
    }
}
```

---

## ROM Banks

### Bank 0 — Smooth Flow (Q√3)

13 entries of small prime rational bases: `5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47`.
Optimised for low-energy, high-throughput rational addition in stable manifold regions.

### Bank 1 — Turbulent (Q√5 Fibonacci)

48 entries of the Fibonacci sequence `F(1)..F(48)`.
Each entry deepens resolution of the rational `Q(√5)` bisection available to the Davis Gate.
As index increases, `F(n)/F(n-1) → φ = (1+√5)/2`, progressively weighting the surd field toward
higher-precision manifold anchoring.

> [!NOTE]
> Entries 48–63 of Bank 1 (ROM addresses `0x70–0x7F`) are zero-padded.
> **Phase 3 calibration**: run a sustained turbulence scenario, capture `laminar_index`
> vs. `debug_reg_r0` per satellite, then fill these entries with the observed
> residual correction coefficients.

---

## Threshold Calibration Procedure (Phase 3)

1. Load a known manifold state (e.g., axis 0 = `0x00019E38` ≈ φ)
2. Run `TURBULENCE_THRESH = 1` to force immediate switches
3. Log `debug_reg_r0` from CMD `0xB0` in both modes for 100 cycles
4. Measure transition glitch: delta between last smooth R0 and first turbulent R0
5. Set `TURBULENCE_THRESH` / `LAMINAR_THRESH` to keep glitch below application tolerance
6. Populate ROM entries `0x70–0x7F` with residual correction terms

---

## Ext Config Channel Map

| Channel | `rplu_cfg_sel` | Function |
|:---|:---|:---|
| 0–4 | `3'd0`–`3'd4` | RPLU node config |
| 5 | `3'd5` | `global_sentinel_mode` (PLC scan) |
| **6** | **`3'd6`** | **`rplu_mode`** (RPLU bank select) |
| 7 | `3'd7` | Broadcast to all nodes |

---

## RPLU v2 — Thimble-Padé Mode Control (F_{p^4})

The v2 RPLU operates over the Mersenne prime field F_{p^4} (p = 2^31−1) and
does not use ROM banks. Mode selection is handled via the PHSLK (0x42) opcode
pipeline rather than SPI config channels.

### Singularity Exception (FLAGS.V)

When the SOM classifier routes an input vector near a geometric singularity
(norm → 0), the F_{p^4} conjugate reduction tower asserts **FLAGS.V** before
the zero-norm reaches the Fermat exponentiation chain. The RP2350 Southbridge
should monitor this flag via CMD 0xAC byte 2 bit 0 and re-route the path
integral when asserted.

### Padé Coefficient Loading

Coefficients are loaded via the RCFG (0x50) opcode at boot:

```
RCFG R1, #COEFF_WORD    ; Load {sel=num/den, addr[2:0], c0, c1, c2, c3}
```

where each coefficient is a 4-tuple (c0, c1, c2, c3) in F_{p^4} over M31.

### Pipeline Stall Handling

The BTU collision resolver inserts pipeline bubbles when multiple Kohonen
saddle points activate simultaneously. The Southbridge should poll the
`pipeline_stall` line (CMD 0xAC byte 2 bit 2) and buffer incoming wave
vectors during stall windows.