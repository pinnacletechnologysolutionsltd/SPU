# SPU-13 Bench Metrics & Southbridge Adapter — Rev A Specification

**Status:** Netlist-level specification, ready for KiCad capture.
**Scope:** 2-layer, hand-solderable, all-through-hole/module carrier board.
**License:** CERN-OHL-W-2.0 (this directory), docs CC0 1.0.
**Role:** First OSHWA-certifiable SPU-13 board; permanent bench replacement for
jumper-wire SPI southbridge hookups; in-line power metering for the paper
metrics program.

This board deliberately contains **no bare ICs**. Every active component is an
off-the-shelf module on socket headers. The board is the wiring, termination,
pullups, and metering path — the failure classes documented in bring-up
(cracked `/CS` joints, floating `WP`/`HOLD`, rat's-nest SPI) are what it fixes.

---

## 1. Block Diagram

```
   5V IN (screw term / USB-C PD breakout fp)
        │
   [PWR LED + R]  ← on INPUT side: excluded from measurement
        │
   INA219 module ── I2C0 (GP8/GP9) ──┐
   VIN+ ─shunt─ VIN-                 │
        │                            │
   5V OUT (screw term + USB-A fp)    │
        → powers target FPGA board   │
                                     │
  ┌──────────────────────────────────┴─┐
  │  Raspberry Pi Pico 2 (socketed)    │
  │                                    │
  │ GP16-19 ──[33R]── J11/PMOD SPI hdr ├── to Tang 25K southbridge /
  │                   (10k on CS#)     │   Wukong J11
  │ GP2-5   ──[33R]── FLASH PMOD hdr   ├── W25Q flash PMOD (rp2040_flash_pmod)
  │                   (10k CS/WP/HOLD) │
  │ GP10-13 ────────── microSD module  │   (SD hydration path)
  │ GP4/GP5 ────────── FPGA UART hdr   ├── FPGA telemetry TX/RX
  │ GP14    ──[R+LED]─ ACT             │
  └────────────────────────────────────┘
        │
   LA header (2x5): CS/SCK/MOSI/MISO/UART_TX/UART_RX + 4x GND
```

---

## 2. Pin Map (matches proven firmware — do not "improve")

All GP assignments are copied from silicon-verified firmware in this repo.
The board adapts to the firmware, never the reverse.

### 2.1 Southbridge SPI → J11/PMOD header (J2)

Source: `hardware/rp2350/rp2350_su3_j11_smoke.c:49-58`, `rp2350_spu_diag.c`,
`rp2350_spu_arithmetic_test.c` (identical in all).

| Signal | Pico 2 GPIO | Pico pin | Series R | Pull | J2 pin |
|---|---|---|---|---|---|
| SPI_MISO | GP16 | 21 | 33 Ω (near header) | — | 3 |
| SPI_CS#  | GP17 | 22 | 33 Ω (near Pico) | 10 kΩ → 3V3 | 1 |
| SPI_SCK  | GP18 | 24 | 33 Ω (near Pico) | — | 4 |
| SPI_MOSI | GP19 | 25 | 33 Ω (near Pico) | — | 2 |
| 3V3 (sense/ref only) | — | 36 | — | — | 6 |
| GND | — | 23 | — | — | 5 |

J2 = 1x6 male 2.54 mm header (plus an optional parallel 2x6 PMOD-pattern
footprint, unpopulated in Rev A). The CS# pullup guarantees idle-high during
Pico reboot — required by the FPGA-side SPI deadman timer.

**3V3 on J2 pin 6 is a reference/sense line only.** The target FPGA board is
never powered from the Pico's 3V3 regulator.

### 2.2 Flash-PMOD programmer header (J3)

Source: `hardware/rp2040/rp2040_flash_pmod.c:21-30`. Lets the same board run
`rp2040_flash_pmod.uf2` (RP2040 Pico) or a Pico 2 rebuild, with
`tools/rp2040_flash_pmod.py` unchanged.

| Signal | Pico GPIO | Pico pin | Series R | Pull | J3 pin |
|---|---|---|---|---|---|
| FLASH_SCK  | GP2 | 4 | 33 Ω | — | 4 |
| FLASH_MOSI (D1) | GP3 | 5 | 33 Ω | — | 2 |
| FLASH_MISO (DO) | GP4* | 6 | 33 Ω | — | 3 |
| FLASH_CS#  | GP5* | 7 | 33 Ω | 10 kΩ → 3V3 | 1 |
| 3V3 | — | 36 | — | — | 6 |
| GND | — | 3 | — | — | 5 |
| (WP#, HOLD#) | — | — | — | 10 kΩ → 3V3 each | — |

The WP#/HOLD# pullups live on the adapter so bare W25Q PMODs work without
their own — this directly implements the bring-up rule from `AGENTS.md`.

> *Conflict note:* GP4/GP5 are shared between the flash-PMOD role (MISO/CS)
> and the southbridge FPGA-UART role (TX/RX, §2.4). The two roles are never
> active in the same firmware image, but J3 and J4 must not be cabled
> simultaneously. Rev A resolves this with jumper JP2 (3-pin, selects GP4/GP5
> routing to either J3 or J4); silkscreen: "FLASH ⟷ UART — pick one".

### 2.3 microSD module socket (J5)

Source: `hardware/rp_common/spu_sd.c:15-24` (SPI1). Socket for the common
6-pin SPI microSD breakout module.

| Signal | Pico 2 GPIO | Pico pin | J5 pin (module order: 3V3 CS MOSI CLK MISO GND) |
|---|---|---|---|
| SD_CS#   | GP13 | 17 | 2 |
| SD_MOSI  | GP11 | 15 | 3 |
| SD_SCK   | GP10 | 14 | 4 |
| SD_MISO  | GP12 | 16 | 5 |
| 3V3 | — | 36 | 1 |
| GND | — | 18 | 6 |

### 2.4 FPGA UART tap (J4)

Source: `hardware/rp2350/rp2350_uart_injector.c:17-18`.

| Signal | Pico 2 GPIO | Pico pin | J4 pin |
|---|---|---|---|
| UART_TX (→ FPGA RX) | GP4 | 6 | 2 |
| UART_RX (← FPGA TX) | GP5 | 7 | 3 |
| GND | — | 8 | 1 |

115200 baud telemetry capture without the FTDI/BL616 USB path — this is what
lets a metrics soak run on metered power with no other cable attached.

### 2.5 INA219 module socket (J6) and metering path

| Signal | Pico 2 GPIO | Pico pin | J6/module pin |
|---|---|---|---|
| I2C0 SDA | GP8 | 11 | SDA |
| I2C0 SCL | GP9 | 12 | SCL |
| 3V3 | — | 36 | VCC |
| GND | — | 13 | GND |
| VIN+ | — | — | screw terminal T1 (5V IN) |
| VIN− | — | — | screw terminal T2 (5V OUT) + USB-A fp J7 |

Stock module shunt is 0.1 Ω: ±3.2 A range, ~0.8 mA resolution, 50 mV drop at
500 mA — fine for every board in the fleet (Tang 25K, Wukong, Colorlight i9
all draw well under 2 A at 5 V). Module carries its own I2C pullups.

The power-indicator LED hangs on the **input** side of the shunt so it never
appears in measurements. The ACT LED (GP14, pin 19) is firmware-controlled;
metrics firmware must hold it off during sampling windows.

### 2.6 Logic analyzer header (J8, 2x5)

| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | SPI_CS# | 2 | GND |
| 3 | SPI_SCK | 4 | GND |
| 5 | SPI_MOSI | 6 | GND |
| 7 | SPI_MISO | 8 | GND |
| 9 | UART_TX | 10 | UART_RX |

Tapped after the series resistors. Sized for the fx2lafw/sigrok 8-channel
clone probes (24 MHz, comfortable at the 25 kHz–2 MHz bench SPI rates).

---

## 3. Power hookup recipes

| Target | Recipe |
|---|---|
| Wukong Artix-7 (barrel/5V) | Splice barrel lead or bench PSU through T1→T2. JTAG/USB untouched — SRAM-load sessions meter cleanly. |
| Tang 25K, flash-booted probes | Metered USB-A jack (J7) → stock A-to-C cable → Tang USB-C. Board boots its probe from flash; UART telemetry via J4. No data cable needed. |
| Tang 25K, SRAM-load sessions | SRAM images die on power-cycle, and J7 passes power only. Load first over the normal cable, keep it attached for data, and meter via the dock's 5V header injection instead — verify dock back-power behaviour against the Sipeed schematic before first use. |

---

## 4. Bill of Materials (all off-the-shelf)

| Ref | Part | Qty | Est. NZD | Notes |
|---|---|---|---|---|
| A1 | Raspberry Pi Pico 2 | 1 | 12 | Socketed, 2× 1x20 female headers. Pico 1 also fits (flash-PMOD role). |
| A2 | INA219 breakout module | 1 | 5 | Common 6-pin purple module, 0.1 Ω shunt |
| A3 | microSD SPI breakout module | 1 | 4 | 6-pin, 3V3-native (no level shifter type) |
| J1 | 2-pin 5.08 mm screw terminal | 2 | 2 | T1 5V IN, T2 5V OUT |
| J7 | USB-A female TH jack | 1 | 2 | Metered power out |
| J1b | USB-C 5V breakout module fp | 0–1 | 3 | Optional alternative input, unpopulated default |
| J2–J4, J8 | 2.54 mm male headers | ~40 pins | 2 | |
| JP2 | 3-pin header + jumper | 1 | 0.5 | GP4/GP5: FLASH ⟷ UART select |
| R | 33 Ω 1/4 W TH | 9 | 1 | Series termination |
| R | 10 kΩ 1/4 W TH | 5 | 1 | CS# ×2, WP#, HOLD#, spare |
| R | 1 kΩ 1/4 W TH | 2 | 0.5 | LED series |
| LED | 3 mm green + red | 2 | 0.5 | PWR (input side), ACT (GP14) |
| PCB | 2-layer, ~80×60 mm, HASL | 5 pcs | 15 | Any prototype fab |
| | **Total** | | **~NZ$50** | including 5 spare PCBs |

## 5. Layout guidance

- 2 layers; bottom = ground pour, top = signal + 5V metering trace.
- Metering path (T1 → INA219 VIN+ → VIN− → T2/J7) in ≥2 mm trace, kept away
  from SPI. Everything else is ≤2 MHz digital — routing is uncritical.
- Keep each SPI group's traces together; grounds interleaved on J8 as tabled.
- Hex/IVM silkscreen motif welcome; keep the outline rectangular in Rev A.
- Mounting: 4× M3 holes.

## 6. Bring-up & test plan (uses only existing repo firmware)

1. **Continuity:** every table row above, before any module is socketed.
2. **Meter sanity:** Pico 2 + INA219 + 47 Ω/5 W resistor on T2 → expect
   ~106 mA ±5% at 5.0 V via the I2C logger.
3. **Southbridge smoke:** `rp2350_spu_diag` UF2, J2 → Tang 25K
   `southbridge_link` probe → expect 0xAC status responses (known-good
   baseline from `docs/SOUTHBRIDGE_SPI_PROTOCOL.md`).
4. **Flash PMOD:** `rp2040_flash_pmod.uf2` on a Pico 1 in the same socket,
   JP2 → FLASH; `tools/rp2040_flash_pmod.py --port <tty> id` must report
   `JEDEC: EF4018` on a known-good W25Q PMOD.
5. **SD path:** SD hydration regression via `spu_sd` firmware on J5.
6. **First real metrics run:** Tang 25K probe ladder power table — idle vs.
   active for each silicon-verified probe, logged to CSV. This table feeds
   the central paper §Power and Timing.

## 7. OSHWA mapping

| OSHWA requirement | This board |
|---|---|
| Original design files | KiCad project in this directory (to be captured from this spec) |
| Public BOM | §4, with MPN column to be added at capture time |
| Open license | CERN-OHL-W-2.0 |
| Docs to build/modify | This spec + assembly notes at capture |
| No proprietary blobs | All firmware already MIT in-repo |

Certification target: after Rev A is assembled and the §6 plan passes.

## 8. Rev B candidates (explicitly NOT in Rev A scope)

- **RP2040 "swiss-army" bench probe:** one RP2040 running a
  DirtyJTAG-class composite firmware — openFPGALoader-compatible JTAG
  (Wukong programming) + CDC UART (probe telemetry) on a single USB
  device. Firmware first, per the Rev A rule: the board adapts to proven
  firmware, never the reverse. Until then the bench RP2040 stays a
  dedicated JTAG programmer and UART monitoring uses a separate bridge.
- **Socketed Tang 25K carrier:** a second board that permanently seats
  the spare Tang 25K (the one bought during the SDRAM-fault diagnosis —
  the FPGA was healthy) + RP2350-Zero southbridge as the always-wired
  edge-tier regression rig. Separate board, separate spec; Rev A's scope
  stays frozen for OSHWA capture.
