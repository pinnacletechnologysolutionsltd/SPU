# SPU-13 ECP5 Evaluation Carrier — Electrical Engineer Handoff

**Document version:** 1.1 (2026-07-21)
**Status:** Concept specification — EE/funding-dependent, not an active build
target. `docs/CURRENT_STATUS.md`'s board-roles table and `AGENTS.md` both
place this custom ECP5-85K carrier after the Kintex-7 full-stack milestone;
the active open-toolchain ECP5 portability target is the Colorlight i9, not
this board. The pin-out and BOM below are a completed architectural exercise,
ready for schematic capture whenever EE time/funding is committed.
**License:** CERN Open Hardware Licence v2 — Weakly Reciprocal (CERN-OHL-W-2.0)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Philosophy](#2-architecture-philosophy)
3. [IC Support Circuits](#3-ic-support-circuits)
4. [Bus Lane Interconnects](#4-bus-lane-interconnects)
5. [Power Architecture](#5-power-architecture)
6. [Evaluation Circuits](#6-evaluation-circuits)
7. [PCB Constraints](#7-pcb-constraints)
8. [Bill of Materials](#8-bill-of-materials)
9. [Open Items for EE](#9-open-items-for-ee)
10. [Reference Documents](#10-reference-documents)

---

## 1. Project Overview

The SPU-13 ECP5 Evaluation Carrier is an open-hardware development board for the
SPU-13 rational-field processor architecture. It hosts two main ICs:

| Ref | IC | Package | Function |
|:---|:---|:---|:---|
| U1 | Lattice LFE5UM-85F-8BG381C | CABGA381 | SPU-13 FPGA compute engine |
| U2 | Raspberry Pi RP2350 | QFN-60 | Southbridge controller: SPI protocol, SD card, USB CDC, JTAG bit-bang |

The RP2350 is the **single debug and programming interface**. There is no
FT2232HL, no separate UART-USB bridge, and no external JTAG programmer.
Everything — bitstream loading, UART telemetry, JTAG debugging, and RPLU table
hydration — passes through one USB-C connector connected to the RP2350.

---

## 2. Architecture Philosophy

```
                  ┌─────────────────────────────────────┐
                  │         USB-C (single cable)         │
                  │  bitstream + UART + JTAG + hydration │
                  └──────────────────┬──────────────────┘
                                     │
                            ┌────────▼────────┐
                            │    RP2350 (U2)  │
                            │  Southbridge    │
                            │                 │
                            │  USB CDC (tty)  │
                            │  SPI0 bus       │──── SPI southbridge ────┐
                            │  PIO parallel   │──── PIO data plane ────┤
                            │  PIO JTAG       │──── JTAG (DirtyJTAG) ──┤
                            │  SPI1 SD        │── microSD              │
                            │  GPIO BOOT/RUN  │── buttons               │
                            └─────────────────┘                        │
                                                                       │
                                                              ┌───────▼────────┐
                                                              │  ECP5-85F (U1) │
                                                              │  FPGA core     │
                                                              │                 │
                                                              │  SPI slave     │
                                                              │  PIO target    │
                                                              │  JTAG target   │
                                                              │  Master-SPI    │
                                                              │  config flash   │── W25Q128 (U3)
                                                              └────────────────┘
```

### Key design decisions

1. **No FTDI chip.** The RP2350's native USB is sufficient for CDC/ACM (UART),
   UF2 (mass storage bootloader), and PIO-JTAG. This saves ~$5-8 BOM cost and
   simplifies the USB tree.

2. **Two SPI flash chips, separate buses.** U3 (W25Q128) is the ECP5 configuration
   flash on the ECP5's dedicated master-SPI port. U4 (W25Q128) is an RPLU table
   store on the RP2350's SPI0 bus. They are electrically independent.

3. **All ECP5 ball assignments deferred to EE.** The ECP5-85F CABGA381 has 381
   balls in 20 × 20 grid. The correct ball numbers depend on the chosen I/O
   bank voltages and must be read from the Lattice `LFE5UM-85F-8BG381C` datasheet.
   This document specifies **which function goes on which bank**; the EE assigns
   the specific (row, column) ball.

---

## 3. IC Support Circuits

### 3.1 ECP5-85F (U1)

#### 3.1.1 Configuration Mode

```
MODE[2:0] = 001  (Master SPI: ECP5 reads its bitstream from U3)
  MODE2 ball: 10 kOhm to GND
  MODE1 ball: 10 kOhm to GND
  MODE0 ball: 10 kOhm to VCC_3V3
```

#### 3.1.2 Configuration Interface (Bank 0, VCCIO0 = 3.3V)

| ECP5 function | Direction | Flash (U3) pin | Pull resistor | Notes |
|:---|:---:|:---|:---:|:---|
| CCLK | output | CLK | — | 10-20 MHz during config, stops after DONE |
| CSO | output | CS# | — | Active-low chip select, held high in user mode |
| MOSI/SIS1 | output | DI | — | Data to flash |
| MISO/SIS0 | input | DO | — | Data from flash |
| PROGRAM# | input | — | 10 kOhm pull-up to 3.3V | Also driven by RP2350 GPIO for remote reconfig |
| DONE | open-drain | — | 10 kOhm pull-up to 3.3V + green LED | High = configuration complete |
| INIT# | open-drain | — | 10 kOhm pull-up to 3.3V | High = FPGA ready for config |

**Ball numbers:** EE to assign from Lattice datasheet, Bank 0 fixed-function pins.

#### 3.1.3 Slave-SPI Configuration (RP2350 -> ECP5)

For RP2350-pushed bitstream loading (used during firmware updates or
pre-production debugging), a second set of GPIOs connects to the ECP5's
slave-SPI port:

| Signal | RP2350 GPIO | ECP5 function | Series R | Notes |
|:---|:---:|:---|:---:|:---|
| FPGA_CCLK | GPx (TBD) | CCLK | 22 ohm | Clock during slave config, tri-state after DONE |
| FPGA_MOSI | GPx (TBD) | MOSI/SIS1 | 22 ohm | Bitstream data |
| FPGA_MISO | GPx (TBD) | MISO/SIS0 | 33 ohm | Status/CRC |
| FPGA_CS# | GPx (TBD) | CS#/CSIN | — | Active-low |
| FPGA_PROGRAM# | GPx (TBD) | PROGRAM# | — | Push-pull, overrides pull-up |

The RP2350 must also monitor DONE and INIT# through spare GPIOs to detect
configuration success/failure.

#### 3.1.4 JTAG (Bank 5, VCCIO5 = 3.3V)

Bit-banged by the RP2350 PIO subsystem. Same pin order as the proven RP2040
DirtyJTAG adapter:

| JTAG signal | RP2350 PIO GPIO | ECP5 ball | Notes |
|:---|:---:|:---|:---:|
| TCK | GPx (TBD) | TCK | Clock, ~1 MHz |
| TDI | GPx (TBD) | TDI | Data to FPGA |
| TDO | GPx (TBD) | TDO | Data from FPGA |
| TMS | GPx (TBD) | TMS | State machine control |

Pin order for firmware compatibility: `GPIO0=TDI, GPIO1=TMS, GPIO2=TCK, GPIO3=TDO`.

**Ball numbers:** EE to assign from Lattice datasheet. Use dedicated JTAG pins on Bank 5.

#### 3.1.5 Clock Input

| Ref | Value | ECP5 pin type | I/O bank | Notes |
|:---|:---:|:---|:---:|:---|
| Y2 | 50 MHz | GPLL-capable input | Bank 2 or Bank 5 | 50 MHz oscillator module, 3.3V, 3225 package |

Y2 is a **canned oscillator module** (part ECS-5032MV-500), not a crystal.
It requires VCC = 3.3V and GND connections, plus a 100 nF decoupling cap
adjacent to its VCC pin.

**Ball numbers:** EE to assign from Lattice datasheet. Use a clock-capable
GPLL input on Bank 2 or Bank 5.

#### 3.1.6 I/O Bank Voltage Map

| Bank | VCCIO | Signals |
|:---:|:---:|:---|
| 0 | 3.3V | Configuration flash interface, MODE straps, PROGRAM#, DONE, INIT# |
| 1 | 1.8V | Optional: PLL reference, SDRAM (if fitted in future revision) |
| 2 | 3.3V | 50 MHz clock input |
| 3 | 3.3V | SPI southbridge bus |
| 4 | 3.3V | PIO parallel data bus |
| 5 | 3.3V | JTAG, status LEDs, DIP switch, test points |

All I/O standards: `LVCMOS33`.

#### 3.1.7 Decoupling Network (VCC_CORE, 1.1V)

Simulated target impedance: **Z_PDN < 0.15 Ohm from 1 kHz to 10 MHz**.
Verified with ngspice (`tools/pdn_analyze.py`).

| Cap value | Qty | Package | ESL target | Placement |
|:---|:---:|:---:|:---:|:---|
| 22 µF | 2 | 0805 | 0.5 nH | Within 10 mm of BGA power balls |
| 4.7 µF | 2 | 0603 | 0.4 nH (0.15 Ohm ESR) | Within 5 mm, deliberate higher ESR for damping |
| 100 nF | 4 | 0402 | 0.3-0.6 nH (spread) | Bottom layer under BGA, staggered via length |
| 10 nF | 6 | 0402 | 0.3-0.8 nH (spread) | Bottom layer under BGA, staggered via length |
| 1 nF | 2 | 0402 | 0.3-0.6 nH (spread) | Bottom layer under BGA |

Spread ESL by using different via stub lengths or trace lengths to the via
— this staggers the SRFs and prevents stacked anti-resonance peaks. The PDN
simulation uses 0.3/0.5/0.8 nH groups.

**Anti-resonance management:** The worst peak is 0.226 Ohm at 95 MHz, which is
within the relaxed 1.0 Ohm target for the VHF band (>50 MHz). No additional
damping required.

---

### 3.2 RP2350 (U2)

#### 3.2.1 Power

| Pin | Voltage | Notes |
|:---|:---:|:---|
| VDD_IO (pins 23, 50, 59) | 3.3 V | I/O supply |
| VDD_CORE (pins 31, 41, 51, 60) | 3.3 V | Core supply (internal LDO from 3.3V) |
| VDD_USB (pin 34) | 3.3 V | USB PHY supply |
| VDD_ADC (pin 43) | 3.3 V | ADC analog supply, via ferrite bead |
| VREF_ADC (pin 42) | 3.3 V | ADC voltage reference |

All 3.3 V pins require 100 nF decoupling adjacent to the pin, plus one
10 µF bulk cap shared per supply group.

#### 3.2.2 USB (Single Debug Port)

| Signal | RP2350 pin | USB-C (J1) pin | Series R | Notes |
|:---|:---:|:---:|:---:|:---|
| USB_D+ | 36 | DP (J1-6) | 27 ohm | Series resistor within 5 mm of RP2350 |
| USB_D- | 37 | DN (J1-7) | 27 ohm | Series resistor within 5 mm of RP2350 |
| VBUS | 35 | VBUS (J1-4,9) | — | 5 V input |
| GPIO24 | 38 | VBUS via divider | 2 × 10 kOhm | VBUS detect: 5V → 2.5 V at GPIO24 |

**USB-C connector:** GCT USB4110-GF-A (16-pin, through-hole). CC1 and CC2
pins must have 5.1 kOhm pull-down resistors to GND for 5 V / 3 A
source current advertisement.

#### 3.2.3 Crystal

| Pin | Component | Value | Notes |
|:---|:---|:---:|:---|
| XI (pin 48) | Crystal Y1 + load cap | 12 MHz + 18 pF to GND | 12 MHz parallel-cut, CL=20pF, ±50 ppm |
| XO (pin 49) | Crystal Y1 + load cap | 12 MHz + 18 pF to GND | |

Y1 = ECS-120-20-30B-TR (3225 package, NOT an oscillator).
Load caps = 18 pF ±5% COG/NP0 0402. Place within 5 mm of XI/XO pins.
Keep trace length from crystal to XI/XO under 10 mm. No other signals
cross the crystal routing.

#### 3.2.4 Boot Mode and Reset

| Signal | RP2350 pin | Circuit | Purpose |
|:---|:---:|:---|:---|
| GPIO8 (BOOT) | 29 | 10 kOhm pull-up to 3.3V + tactile switch to GND | Hold low at power-on for UF2 mass-storage mode |
| RUN | 30 | 10 kOhm pull-up to 3.3V + optional tactile switch to GND | Hard-reset RP2350 |

SW1 = BOOT button. SW2 = RUN button. Both are 6 × 6 mm through-hole tactile
switches (TE FSM4JH or equivalent).

#### 3.2.5 Debug Header (SWD, Optional)

| Signal | RP2350 pin | Test point |
|:---|:---:|:---|
| SWCLK | 21 | TP_SWCLK |
| SWDIO | 22 | TP_SWDIO |
| GND | — | TP_GND_DEBUG |

Not required for normal operation — firmware can always be loaded via UF2
over USB. Included for firmware developers who want to use a debug probe.

#### 3.2.6 ADC Reference

```
VCC_3V3 → ferrite bead BLM18PG221SN1 (220 Ohm @ 100 MHz) → VREF_ADC pin 42
                                                              │
                                                         10 µF 0805 to GND
                                                              │
                                                         100 nF 0402 to GND
```

Keep the ferrite bead and caps within 5 mm of pin 42. No switching
regulators or digital traces near this circuit.

---

## 4. Bus Lane Interconnects

### 4.1 SPI Southbridge (Bank 3, LVCMOS33)

| Signal | RP2350 GPIO | ECP5 Bank 3 ball | Series R | Pull | Notes |
|:---|:---:|:---|:---:|:---:|:---|
| SPI_CS# | GP1 | **EE assign** | — | 10 kOhm to 3.3V | Driven low by RP2350 for each transaction |
| SPI_SCK | GP2 | **EE assign** | 22 ohm near RP2350 | — | Use a clock-capable input ball on ECP5 |
| SPI_MOSI | GP3 | **EE assign** | 22 ohm near RP2350 | — | |
| SPI_MISO | GP0 | **EE assign** | 33 ohm near ECP5 | — | RP2350 input; series R at source (ECP5) |

**Protocol:** SPI mode 0 (CPOL=0, CPHA=0), 2 MHz bench / 12 MHz target.
**Bank voltage:** VCCIO3 = 3.3 V.
**Routing:** Match SCK and MOSI trace length within ±2 mm. Keep total trace
length under 60 mm.

### 4.2 PIO Parallel Bus (Bank 4, LVCMOS33)

Eight-bit half-duplex parallel transport for high-throughput RPLU table
hydration and result streaming.

| Signal | RP2350 GPIO | ECP5 Bank 4 ball | Series R | Direction | Notes |
|:---|:---:|:---|:---:|:---:|:---|
| PIO_D0 | GP4 | **EE assign** | 22 ohm | Bidir | Contiguous GPIO block |
| PIO_D1 | GP5 | **EE assign** | 22 ohm | Bidir | |
| PIO_D2 | GP6 | **EE assign** | 22 ohm | Bidir | |
| PIO_D3 | GP7 | **EE assign** | 22 ohm | Bidir | |
| PIO_D4 | GP8 | **EE assign** | 22 ohm | Bidir | Shared with BOOT — ensure pull-up doesn't conflict |
| PIO_D5 | GP9 | **EE assign** | 22 ohm | Bidir | |
| PIO_D6 | GP14 | **EE assign** | 22 ohm | Bidir | |
| PIO_D7 | GP15 | **EE assign** | 22 ohm | Bidir | |
| PIO_STROBE | GP16 | **EE assign** | 22 ohm | RP2350 -> ECP5 | Data valid strobe |
| PIO_READY | GP17 | **EE assign** | 22 ohm | ECP5 -> RP2350 | FPGA ready for next word |
| PIO_DIR | GP18 | **EE assign** | 22 ohm | RP2350 -> ECP5 | 1 = ECP5 drives data bus |

**Timing budget (12 MHz):** Setup margin > 76 ns, hold margin > 0 ns.
Verified with `tools/pio_timing_budget.py` at 40 mm trace length.

**Routing constraints:**
- DATA[7:0] must have matched skew < 0.5 ns across all 8 lanes
- Use ground guard traces between adjacent data lanes
- 22 ohm series resistors within 5 mm of RP2350 GPIO pins
- Do not route PIO bus near the 50 MHz oscillator or switching regulators

**Note on PIO_D4 (GP8):** This pin also serves as the BOOT mode select.
The 10 kOhm pull-up on BOOT will weakly hold this line high; the RP2350
PIO must drive against it. If this causes issues, move PIO_D4 to a
different GPIO and assign a dedicated BOOT pin.

### 4.3 microSD Card (RP2350 SPI1)

| Signal | RP2350 GPIO | microSD pin | Pull-up | Notes |
|:---|:---:|:---:|:---:|:---|
| SD_CLK | GP10 | CLK | — | 400 kHz init, 8 MHz after |
| SD_CMD | GP11 | CMD | 10 kOhm to 3.3V | |
| SD_DAT0 | GP12 | DAT0/MISO | 10 kOhm to 3.3V | |
| SD_CS# | GP13 | DAT3/CS# | 10 kOhm to 3.3V | |

**Connector:** J2 = 112A-TAAR-R03 (push-push, through-hole).
**Routing:** Keep trace length under 60 mm. Add 22 ohm series resistor on
SD_CLK near RP2350 if required for EMI.

### 4.4 Configuration Flash (U3 — ECP5 Master SPI)

See Section 3.1.2. The W25Q128JVSQ on U3 connects ONLY to the ECP5
configuration port. The RP2350 does not access this flash directly —
it pushes new bitstreams through the slave-SPI configuration path instead.

### 4.5 RPLU Table Flash (U4 — RP2350 SPI0)

U4 is a W25Q128JVSQ on the RP2350's SPI0 bus. It is independent of the
ECP5 configuration flash and shares the same physical SPI0 pins as the
southbridge link (CS# on a separate RP2350 GPIO for chip-select
demultiplexing).

| Signal | RP2350 GPIO | U4 pin | Notes |
|:---|:---:|:---:|:---|
| RPLU_CS# | GP19 (tentative) | CS# | Separate CS from southbridge CS# |
| RPLU_SCK | GP2 (shared) | CLK | Shared with SPI_SCK — same bus |
| RPLU_MOSI | GP3 (shared) | DI | Shared |
| RPLU_MISO | GP0 (shared) | DO | Shared |

If the shared bus causes timing issues (capacitive loading from two
devices), make RPLU_CS# a dedicated SPI bus on different RP2350 GPIOs.

---

## 5. Power Architecture

### 5.1 Rail Summary

| Rail | Regulator | Voltage | Max I | Ripple target | Typical load |
|:---|:---|:---:|:---:|:---:|:---:|
| VCC_CORE | U6 = TPS62082 (buck) | 1.1 V | 2.0 A | < 10 mV pk-pk | 800 mA |
| VCC_3V3 | U5 = AP2112K-3.3 (LDO) | 3.3 V | 600 mA | < 30 mV pk-pk | 250 mA |
| VCC_1V8 | U7 = TPS62232 (buck) | 1.8 V | 500 mA | < 20 mV pk-pk | 100 mA |
| VCC_PLL | U8 = LP5907-2.5 (LDO) | 2.5 V | 250 mA | < 5 mV pk-pk | 20 mA |

### 5.2 Power Tree

```
USB-C (5 V / 3 A)
  │
  ├─► U5 (AP2112K-3.3) ──── 3.3 V ──┬── VCC_3V3 (ECP5 banks 0,2,3,4,5)
  │       LDO, 600 mA                ├── VCC_3V3 (RP2350 VDD_IO, VDD_CORE, VDD_USB, VDD_ADC)
  │                                  ├── VCC_3V3 (microSD pull-ups, flash VCC)
  │                                  └── VCC_3V3 (LEDs, DIP switch, test points)
  │
  ├─► U6 (TPS62082) ──── 1.1 V ──── VCC_CORE (ECP5 core)
  │       Buck, 2 MHz, 2 A
  │
  ├─► U7 (TPS62232) ──── 1.8 V ──── VCC_1V8 (ECP5 Bank 1)
  │       Buck, 2 MHz, 500 mA
  │
  └─► U8 (LP5907-2.5) ── 2.5 V ──── VCC_PLL (ECP5 PLL supply)
          LDO, low-noise, 250 mA      via ferrite bead BLM18PG221SN1
```

### 5.3 Sequencing

The RP2350 GPIO line `FPGA_PROGRAM#` must hold the ECP5 `PROGRAM#` pin low
until all rails are stable. Sequence:

1. USB-C connected → 5 V present
2. U5 (3.3 V LDO) ramps → RP2350 powers on
3. RP2350 firmware starts, asserts FPGA_PROGRAM# = low (holding ECP5 in reset)
4. U6 (1.1 V buck) and U7 (1.8 V buck) ramp
5. RP2350 waits 10 ms (all rails settled)
6. RP2350 de-asserts FPGA_PROGRAM# → ECP5 begins configuration read from U3

If TPS3808G33 (or similar) supervisor is preferred over firmware-based
sequencing, connect its RESET# output to ECP5 PROGRAM#. Configure the
supervisor to assert reset until both VCC_CORE and VCC_3V3 are above
their thresholds.

### 5.4 Regulator BOM

| Ref | Part | Type | Package | Input | Output | Max I |
|:---|:---|:---|:---|:---:|:---:|:---:|
| U5 | AP2112K-3.3 | LDO | SOT-23-5 | 5 V USB | 3.3 V | 600 mA |
| U6 | TPS62082 | Sync buck | QFN-8 3×3 | 5 V USB | 1.1 V | 2.0 A |
| U7 | TPS62232 | Sync buck | QFN-8 3×3 | 5 V USB | 1.8 V | 500 mA |
| U8 | LP5907-2.5 | LDO | SOT-23-5 | 3.3 V | 2.5 V | 250 mA |

### 5.5 PDN Simulation Results

From `tools/pdn_analyze.py` (ngspice):

| Band | Worst Z | Target | Status |
|:---|:---:|:---:|:---:|
| 1 kHz – 10 MHz | 0.028 Ohm @ 10 MHz | 0.15 Ohm | **PASS** |
| 10 MHz – 50 MHz | 0.091 Ohm @ 63 MHz | 0.50 Ohm | **PASS** |
| 50 MHz – 100 MHz | 0.226 Ohm @ 95 MHz | 1.00 Ohm | **PASS** |

All 501 simulated data points pass per-band targets. CSV output saved to
`build/pdn_z11.csv`.

### 5.6 Physical PDN Constraints

1. **VCC_CORE plane (In1.Cu):** Dedicated inner layer. No splits or cutouts
   under the FPGA. Minimum copper thickness 35 µm (1 oz).
2. **GND plane (In2.Cu):** Dedicated inner layer. Complete solid plane.
3. **Via-in-pad:** 100 nF 0402 caps on bottom layer directly opposite BGA
   power vias. Use 0.3 mm via-in-pad with filled/capped vias.
4. **Bulk caps:** 22 µF 0805 within 10 mm of the BGA power ball array.
5. **Via stitching:** GND vias within 0.5 mm of every power via.
6. **PLL isolation:** VCC_PLL uses a dedicated ferrite bead
   (BLM18PG221SN1, 220 Ohm @ 100 MHz) with 4.7 µF + 100 nF on the FPGA side.

---

## 6. Evaluation Circuits

### 6.1 Status LEDs

| LED | Colour | Driven by | Series R | Signal | Meaning |
|:---|:---:|:---:|:---:|:---|:---|
| LED_DONE | Green | ECP5 DONE (pull-up to 3.3V) | 1 kOhm | DONE high = configured | FPGA bitstream loaded successfully |
| LED_PWR | Green | VCC_3V3 rail | 1 kOhm | Always on when powered | Board powered |
| LED_ACT | Red | RP2350 GPIO | 330 Ohm | RP2350 toggles | Heartbeat / activity indicator |

All LEDs: 0603 package, connected cathode to signal, anode to VCC_3V3
(active-low drive).

### 6.2 User Inputs

| Item | Connection | Function |
|:---|:---|:---|
| SW1 (BOOT) | RP2350 GPIO8 to GND via tactile switch | Hold during USB plug-in for UF2 mode |
| SW2 (RUN) | RP2350 RUN to GND via tactile switch | Hard-reset RP2350 |
| SW3 (MODE) | 4-position DIP switch, each pole to RP2350 GPIO + 10 kOhm pull-up | Evaluation mode select (firmware-defined) |

### 6.3 Test Points

| TP | Signal | Connector type | Use |
|:---|:---|:---|:---|
| TP_VCC_CORE | VCC_CORE (1.1 V) | 1 mm test point | Scope probe for PDN measurement |
| TP_VCC_3V3 | VCC_3V3 | 1 mm test point | I/O voltage verification |
| TP_GND | GND | 1 mm test point | Scope ground reference |
| TP_SPI_CS | SPI_CS# | 1 mm test point | SPI protocol analysis |
| TP_SPI_SCK | SPI_SCK | 1 mm test point | SPI clock measurement |
| TP_PIO_STB | PIO_STROBE | 1 mm test point | PIO bus timing measurement |

Add a 6-pin header (J4) that breaks out SPI and PIO signals for
oscilloscope hookup with ground-spring accessories:

| J4 pin | Signal |
|:---:|:---|
| 1 | SPI_SCK |
| 2 | GND |
| 3 | SPI_MOSI |
| 4 | PIO_STROBE |
| 5 | PIO_READY |
| 6 | GND |

---

## 7. PCB Constraints

### 7.1 Stackup (Recommended)

| Layer | Type | Material | Thickness | Notes |
|:---:|:---|:---|:---:|:---|
| Top (F.Cu) | Signal + components | 1 oz copper | 35 µm | All ICs, series R, LEDs, buttons |
| Inner 1 (In1.Cu) | VCC_CORE plane | 1 oz copper | 35 µm | No splits. Dedicated 1.1V. |
| Inner 2 (In2.Cu) | GND plane | 1 oz copper | 35 µm | No splits. Continuous reference. |
| Bottom (B.Cu) | Signal + decoupling | 1 oz copper | 35 µm | Decoupling caps under BGA, test points |

**Dielectric:** 1.6 mm total thickness. 0.2 mm prepreg between In1.Cu and
In2.Cu for plane capacitance. ε_r ≈ 4.2-4.5 (FR4). The 50 ohm microstrip
width on outer layers is approximately 0.16 mm with this stackup; confirm
with fab house.

### 7.2 Board Outline

Hexagonal profile, 60° isotropic boundary. Circumradius = 55 mm.
Vertices centered at (X=150, Y=100) mm in the KiCad workspace.

The hexagon is defined in `tools/gen_kicad_layout.py` via:
```python
for i in range(6):
    angle = i * 60 + 30  # flat-top hexagon
    vertex = (150 + 55 * cos(angle), 100 + 55 * sin(angle))
```

**Fab note:** Request tab routing with mouse-bites for depaneling.
V-scoring is not compatible with a hexagonal outline.

### 7.3 Fiducial Marks

Three asymmetric fiducials at radius 45 mm, angles −90°, 30°, and 150°
from center. Required for pick-and-place machine optical registration.

### 7.4 Clearance Rules (KiCad Custom DRC)

Add these rules in `Board Setup → Custom Rules`:

```lisp
(rule "Hexagonal Boundary Keepout"
    (constraint edge_clearance (min 0.5mm))
    (condition "A.Type == 'Track' && A.Layer == 'F.Cu'"))

(rule "Radial Parallel Crosstalk Prevention"
    (constraint clearance (min 0.4mm))
    (condition "A.NetClass == 'Synergetic_Bus' && B.NetClass == 'Synergetic_Bus'"))
```

### 7.5 Grounding

- **No isolated copper islands.** All copper pours must be connected to GND
  via at least one via. Floating copper acts as an antenna.
- **Via stitching:** GND vias every 5 mm across the board, especially around
  the perimeter of the hexagonal outline.
- **Solid GND under PLL:** No other signals on the layer directly beneath
  the VCC_PLL filter circuit.

---

## 8. Bill of Materials

Complete BOM with DigiKey PNs: `hardware/pcb/spu13_ecp5_carrier_bom.csv`

### Key Parts

| Qty | Value | Footprint | Designators | Purpose |
|:---:|:---|:---|:---|---|
| 1 | LFE5UM-85F-8BG381C | CABGA381 | U1 | SPU-13 FPGA (EE assigns balls) |
| 1 | RP2350-LQFN60 | QFN-60 | U2 | Southbridge + single USB-C debug |
| 2 | W25Q128JVSQ | SOIC-8 | U3, U4 | Config flash + RPLU table flash (independent buses) |
| 1 | TPS62082 | QFN-8 | U6 | 1.1 V buck for VCC_CORE |
| 1 | AP2112K-3.3 | SOT-23-5 | U5 | 3.3 V LDO |
| 1 | TPS62232 | QFN-8 | U7 | 1.8 V buck |
| 1 | LP5907-2.5 | SOT-23-5 | U8 | 2.5 V low-noise LDO for PLL |
| 1 | ECS-120-20-30B-TR | 3225-4 | Y1 | 12 MHz crystal for RP2350 (NOT oscillator) |
| 1 | ECS-5032MV-500 | 3225-4 | Y2 | 50 MHz oscillator for ECP5 |
| 2 | 18 pF COG 0402 | 0402 | C13 | RP2350 crystal load caps |
| 2 | 27 ohm 0402 | 0402 | R6 | USB D+/D- series termination |
| 11 | 22 ohm 0402 | 0402 | R4 | PIO/SPI series termination |
| 2 | 33 ohm 0402 | 0402 | R5 | MISO/CS series termination |
| 2 | Tactile switch 6×6 | THT | SW1, SW2 | BOOT + RUN |
| 1 | DIP switch 4pos | SMD | SW3 | Eval mode select |
| 1 | BLM18PG221SN1 | 0603 | L1 | Ferrite bead for PLL |
| 1 | USB4110-GF-A | USB-C 16-pin | J1 | Single debug USB-C |
| 1 | 112A-TAAR-R03 | microSD | J2 | SD card slot |
| 3 | LED 0603 | 0603 | LED1-3 | DONE (green), PWR (green), ACT (red) |
| 6 | Test point 1 mm | THT | TP1-6 | Scope probe points |

**Note:** The FT2232HL is intentionally omitted. All debug functions are
handled by the RP2350's native USB interface.

---

## 9. Open Items for EE

These must be resolved before the board can be sent to fabrication:

### 9.1 ECP5 Ball Assignments — resolved

`hardware/boards/ecp5_85k/spu_ecp5_85k.cst` now carries real CABGA381 ball
coordinates for every signal (clock, SPI southbridge, PIO bus, config flash,
JTAG, configuration straps/status) — no `# TBD by EE` lines remain. EE should
verify these against the datasheet rather than assign from scratch. The ECP5
family datasheet is at
`FPGA_DS_02012_2_4_ECP5_ECP5G_Family_Data_Sheet-1022822.pdf` in the repo root;
the Lattice hardware checklist is at
`FPGA-TN-02038-2-0-ECP5-and-ECP5-5G-Hardware-Checklist.pdf`. Note the RP2350-side
GPIO assignments in §3.1.3/§3.1.4 (`GPx (TBD)`) are a separate, still-open item
— they are RP2350 pin choices, not ECP5 ball assignments, and are unaffected
by this fix.

| Interface | Bank | ECP5 ball(s) | Source |
|:---|:---:|:---|:---|
| 50 MHz clock (GPLL input) | 7 | A4 | CSV row 6, PL11A (ULC_GPLL0T_IN) |
| SPI southbridge (CS/SCK/MOSI/MISO) | 3 | U18, U16, U19, T18 | CSV rows 150-161 |
| PIO parallel bus (D0-D7, STB, RDY, DIR) | 6 | G2, H2, F1, G1, J4, J5, J3, K3, K2, J1, H1 | CSV rows 78-100 |
| JTAG (TCK/TDI/TDO/TMS) | 40 | T5, R5, V4, U5 | CSV rows 210-214 |
| Config flash (CS/CLK/MISO/MOSI) | 8 | T2, U3, V2, W2 | CSV rows 192-201 (PB13A, CCLK, PB11A, PB11B) |
| Config straps (MODE[2:0]) | 8 | U4, T4, R4 | CSV rows 205-208 |
| Config status (PROGRAM#/DONE/INIT#) | 8 | W3, Y3, V3 | CSV rows 199-204 |

### 9.2 Hardware Checklist Verification (from TN02038)

The Lattice hardware checklist is at `FPGA-TN-02038-2-0-ECP5-and-ECP5-5G-Hardware-Checklist.pdf`
in the repo root. Run through these items against our current design:

| Checklist section | Our design | Verify against PDF |
|:---|:---|:---|
| Power supply sequencing | RP2350 holds PROGRAM# low until rails stable (Section 5.3) | Confirm minimum ramp rate and POR thresholds |
| VCC_CORE decoupling | 2×22µF + 2×4.7µF + 4×100nF + 6×10nF + 2×1nF (Section 3.1.7) | Confirm Lattice-recommended count per rail |
| VCC_IO decoupling | 1×22µF + 1×4.7µF + 4×100nF per bank voltage | Confirm per-bank requirement |
| CCLK termination | No series R specified | Checklist may require series R for overshoot |
| PROGRAM# pull-up | 10 kOhm to 3.3V | Confirm value matches checklist |
| DONE pull-up | 10 kOhm to 3.3V + LED | Confirm value |
| INIT# pull-up | 10 kOhm to 3.3V | Confirm value |
| MODE resistor tolerance | 10 kOhm ±5% | Confirm tolerance requirement |
| JTAG connector | None (RP2350 PIO bit-bang via fly-wires) | Checklist may recommend a header |
| PCB stackup | 4-layer, 0.2 mm prepreg (Section 7.1) | Confirm Lattice minimum layer count |
| Unused I/O termination | Not specified | Checklist likely requires pull-up/pull-down |

If any item contradicts our design, update `docs/ee_handoff.md` and
`hardware/docs/ecp5_oshwa_carrier_spec.md` before handing off to the EE.

### 9.3 Stackup Confirmation (Medium Priority)

Confirm with the fab house (JLCPCB, PCBWay, etc.) that the assumed 0.2 mm
prepreg thickness between In1.Cu and In2.Cu is available in their standard
4-layer FR4 stackup. If not, re-run `tools/pdn_analyze.py` with the actual
dielectric thickness to verify PDN impedance.

### 9.4 USB-C CC Resistor Sizing (Medium Priority)

The GCT USB4110-GF-A connector requires two 5.1 kOhm resistors on CC1 and
CC2 to ground to advertise 5 V / 3 A capability. Confirm resistor values
with the USB-C specification if a different current capability is desired.

### 9.5 Thermal (Low Priority)

The TPS62082 buck converter dissipates approximately 0.5 W at full load.
Ensure adequate copper area on the VCC_CORE plane (In1.Cu) for heat
spreading. The AP2112K LDO dissipates approximately 1 W worst-case
(5V → 3.3V @ 600 mA) — add thermal vias under its exposed pad.

---

## 10. Reference Documents

| Reference | Location | Contents |
|:---|:---|---|
| ECP5 family datasheet | `FPGA_DS_02012_2_4_ECP5_ECP5G_Family_Data_Sheet-1022822.pdf` | CABGA381 ball map, DC characteristics, power rails (repo root) |
| ECP5 hardware checklist | `FPGA-TN-02038-2-0-ECP5-and-ECP5-5G-Hardware-Checklist.pdf` | Lattice validation checklist for decoupling, configuration, PCB (repo root) |
| ECP5-85F build script | `hardware/boards/ecp5_85k/build_ecp5_85k.sh` | Yosys + nextpnr-ecp5 synthesis, P&R, bitstream for CABGA381 |
| ECP5-85F pin constraints | `hardware/boards/ecp5_85k/spu_ecp5_85k.cst` | Physical pin assignments (placeholder — fill from datasheet) |
| ECP5-85F top-level Verilog | `hardware/boards/ecp5_85k/spu_ecp5_top.v` | Module ports matching this spec |
| Carrier board spec | `hardware/docs/ecp5_oshwa_carrier_spec.md` | Full architectural specification |
| Power tree | `hardware/docs/power_tree.md` | Detailed regulator analysis and selection |
| PDN simulation | `tools/pdn_analyze.py` | ngspice-based PDN impedance analysis |
| PDN netlist | `tools/pdn_simulation.cir` | SPICE netlist for VCC_CORE decoupling |
| PIO timing | `tools/pio_timing_budget.py` | Setup/hold margin calculator |
| PCB generator | `tools/gen_kicad_layout.py` | KiCad 10 board outline + component placement |
| Schematic generator | `tools/gen_kicad_schematic.py` | KiCad 10 annotated power-tree schematic |
| KiCad PCB | `hardware/pcb/spu13_ecp5_carrier.kicad_pcb` | Hex board outline with placed components |
| KiCad schematic | `hardware/pcb/spu13_ecp5_carrier.kicad_sch` | Annotated reference diagram |
| BOM | `hardware/pcb/spu13_ecp5_carrier_bom.csv` | Full BOM with DigiKey part numbers |
| Gerbers | `build/gerbers/` | Concept Gerber outputs (visual review only) |
| OSHWA application | `docs/oshwa_application.md` | Self-certification draft |
| SPI protocol | `docs/SOUTHBRIDGE_SPI_PROTOCOL.md` | Complete command set reference |
| Bring-up guide | `docs/build_and_bringup_guide.md` | Toolchain setup and board targets |
| Lattice ECP5 family datasheet | Lattice Semiconductor | CABGA381 ball map (external) |
| Lattice ECP5 hardware checklist | `FPGA-TN-02038-2-0-ECP5-and-ECP5-5G-Hardware-Checklist.pdf` | Decoupling, configuration, PCB rules (repo root) |
| ECP5-85K build target | `hardware/boards/ecp5_85k/` | Build script, top-level Verilog, pin constraints for CABGA381 |
| RP2350 datasheet | Raspberry Pi Foundation | QFN-60 pin functions (external) |
