# SPU-13 Bench Metrics & Southbridge Adapter — Rev B Specification

**Status:** Rev B safety design update.  The existing Rev A PCB must not be
ordered.  Breadboard-verify the power-ready interlock in §2.1 first, then
capture that proven circuit in the KiCad schematic and lay out a new PCB.
**Scope:** 2-layer, hand-solderable, all-through-hole/module carrier board.
**License:** CERN-OHL-W-2.0 (this directory), docs CC0 1.0.
**Role:** First OSHWA-certifiable SPU-13 board; permanent bench replacement for
jumper-wire SPI southbridge hookups; in-line power metering for the paper
metrics program.

Rev A deliberately contained no bare ICs.  Rev B makes one safety exception:
the J2 interlock uses a bus-switch IC and a micropower comparator.  This is
not optional convenience circuitry: it prevents a powered Pico from driving
an unpowered FPGA through its I/O clamp diodes.  The board remains otherwise
a socketed-module carrier for wiring, termination, pullups, and metering.

---

## 1. Block Diagram

```
   5V IN (screw term / USB-C PD breakout fp)
        │
   [PWR LED + R]  ← on INPUT side: excluded from measurement
        │
   INA226 module ── I2C0 (GP8/GP9) ──┐
   VIN+ ─shunt─ VIN-    ALERT→GP15   │
        │                            │
   5V OUT (screw term + USB-A fp)    │
        → powers target FPGA board   │
                                     │
  ┌──────────────────────────────────┴─┐
  │  Raspberry Pi Pico 2 (socketed)    │
  │                                    │
  │ GP16-19 ──[100R]──[PGOOD / Ioff]── J11/PMOD SPI hdr
  │                   (10k on CS#)     ├── to Tang 25K southbridge /
  │                                     │   Wukong J11
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

### 2.1 Southbridge SPI → J11/PMOD header (J2), power-ready interlocked

Source: `hardware/rp2350/rp2350_su3_j11_smoke.c:49-58`, `rp2350_spu_diag.c`,
`rp2350_spu_arithmetic_test.c` (identical in all).

| Signal | Pico 2 GPIO | Pico pin | Series R | Pull | J2 pin |
|---|---|---|---|---|---|
| SPI_MISO | GP16 | 21 | 100 Ω (near header) | — | 3 |
| SPI_CS#  | GP17 | 22 | 100 Ω (near Pico) | 10 kΩ → 3V3 | 1 |
| SPI_SCK  | GP18 | 24 | 100 Ω (near Pico) | — | 4 |
| SPI_MOSI | GP19 | 25 | 100 Ω (near Pico) | — | 2 |
| 3V3 (sense/ref only) | — | 36 | — | — | 6 |
| GND | — | 23 | — | — | 5 |

J2 = 1x6 male 2.54 mm header (plus an optional parallel 2x6 PMOD-pattern
footprint, unpopulated). The CS# pullup guarantees idle-high during Pico
reboot — required by the FPGA-side SPI deadman timer.

**Series R raised 33 Ω → 100 Ω 2026-07-13 (Gemini finding, post A7 Wukong
J11 damage):** the original 33 Ω was sized for signal termination, not fault
current. `hardware/rp2040/`/`rp2350/` bring-up on the Wukong A7 confirmed via
multimeter that J11 CS/SCK/MOSI (all three are Pico-driven outputs into the
FPGA) took permanent I/O damage from sustained backfeed while the FPGA board
was unpowered but the Pico stayed powered and driving — 33 Ω limits that
fault current to ~100 mA (3.3 V / 33 Ω), which is high enough to stress an
unpowered pin's clamp diodes over a long/repeated exposure. 100 Ω caps it at
~33 mA, a meaningfully safer margin, at the cost of slightly softer edges at
these boards' ≤2 MHz SPI rates — a non-issue at this frequency. Applied to
all four J2 lines (including MISO, an FPGA output) for symmetric protection
in case wiring roles ever get swapped. J3's flash-PMOD resistors stay at
33 Ω: that link never crosses an independent power domain (flash chip has no
board of its own to be "unpowered"), so it isn't exposed to this failure
mode.

#### Mandatory Rev B interlock

All four J2 signals shall pass through **U1, SN74CBTLV3125** (or a documented,
pin-compatible substitute explicitly rated for `Ioff` / powered-off
protection).  It is a four-channel bidirectional FET bus switch, so it safely
covers the three Pico-to-FPGA drivers and FPGA-to-Pico MISO without assigning a
fixed direction.  Its four active-low OE pins are tied together as `J2_OE_N`.

`J2_OE_N` is pulled up to **Pico 3V3** with 10 kΩ, so the safe default is all
four signals disconnected.  U2, a Pico-3V3-powered open-drain comparator with
an independent/fail-safe input (prototype: **TLV3011B**), pulls `J2_OE_N` low
only after `TARGET_3V3_SENSE` crosses the qualified-on threshold.  Use its
1.242 V reference with a 137 kΩ / 100 kΩ divider from J2-6 for a nominal
2.94 V rising threshold.  Provide a 1 MΩ hysteresis footprint (DNP until the
breadboard test sets the falling threshold); target 2.75–2.85 V falling.

U1 and U2 are both powered from Pico 3V3.  This deliberately avoids powering
any safety logic from the target.  U1's `Ioff` rating is required to keep the
J2 side high impedance if the Pico itself is unpowered; U2's fail-safe input is
required so a powered target cannot back-power the Pico through the sense path.
Retain the four 100 Ω resistors between the Pico and U1 as secondary
fault-current limiting / signal damping.  They are no longer the primary
protection mechanism.

**J2 pin 6 is `TARGET_3V3_SENSE`, not a rail tie.** It goes only to U2 through
the high-impedance divider; it must never connect to Pico pin 36, Pico 3V3, or
any other adapter supply rail.  The target FPGA board is never powered from
the Pico's 3V3 regulator.

Breadboard acceptance, before PCB layout:

1. With Pico powered and target 3V3 absent, add a temporary 10 kΩ pull-down
   to each U1 target-side pin. All four pins must stay below 100 mV while the
   Pico drives the corresponding source-side signals.
2. Ramp target sense from 0 to 3.3 V. `J2_OE_N` must stay high below the chosen
   falling threshold and go low only above the qualified-on threshold.
3. With target power removed while the Pico continues to issue SPI traffic,
   target-side CS#/SCK/MOSI must remain high impedance and the target rail must
   not rise measurably through the interface.
4. With both domains powered, run the existing 2 MHz southbridge smoke test.
5. Repeat steps 1–3 with Pico unpowered and target powered, validating U1's
   powered-off isolation in the opposite direction.

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

**Corrected 2026-07-09 (found during KiCad capture):** J3 is a 6-pin
connector and has no WP#/HOLD# pins — a prior draft of this section
claimed the adapter provides WP#/HOLD# pullups, which is not physically
possible with this connector and was never implemented. Per
`rp2040_flash_pmod.c`'s own comment ("the flash breakout must pull /WP
and /HOLD high. Most 6-pin W25Q PMODs do"), Rev A instead **relies on
the breakout module's own onboard WP#/HOLD# pullups** — true of the
common 6-pin W25Q PMOD style this connector targets. This is a real
constraint, not a cosmetic note: **a bare W25Q chip on a
no-pullup breakout will not work on this board** — verify the specific
module has onboard WP#/HOLD# pullups (nearly all do) before relying on
it. A future Rev B could widen J3 to 8 pins to add these pullups
directly; out of scope for Rev A.

> *Conflict note:* GP4/GP5 are shared between the flash-PMOD role (MISO/CS)
> and the southbridge FPGA-UART role (TX/RX, §2.4). The two roles are never
> active in the same firmware image, but J3 and J4 must not be cabled
> simultaneously. **Corrected 2026-07-09 (found during KiCad capture):** a
> single 3-pin jumper can only select one-of-two destinations for *one*
> signal — switching GP4 *and* GP5 together as a matched pair needs two
> poles. JP2 is therefore a **2×3 (6-pin) shorting-jumper block**: two
> independent 3-pin groups (common=GPx, position A=J3 role, position
> B=J4 role) side by side, moved together with two shunts. BOM corrected
> to 6 pins, still one reference designator. Silkscreen: "FLASH ⟷ UART —
> pick one", with the two shunts clearly grouped so they're moved as a
> pair, not independently.

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

### 2.5 INA226 module socket (J6) and metering path

Rev A upgraded INA219 → INA226 (2026-07-08): 16-bit ADC (vs 12), hardware
averaging up to 1024 samples, and an ALERT/conversion-ready pin — cleaner
idle-vs-active deltas for the paper power tables at ~NZ$2 extra. Logger:
`tools/bench_metrics/ina226_logger.py` (`ina219_logger.py` retained for
breadboard use of existing INA219 stock).

| Signal | Pico 2 GPIO | Pico pin | J6/module pin |
|---|---|---|---|
| I2C0 SDA | GP8 | 11 | SDA |
| I2C0 SCL | GP9 | 12 | SCL |
| ALERT (conversion ready) | GP15 | 20 | ALE/ALERT |
| 3V3 | — | 36 | VCC |
| GND | — | 13 | GND |
| VIN+ | — | — | screw terminal T1 (5V IN) |
| VIN− | — | — | screw terminal T2 (5V OUT) + USB-A fp J7 |

Stock module shunt is 0.1 Ω (R100): ±0.8 A usable range at the INA226's
±81.92 mV shunt limit, ~0.1 mA-class resolution, 50 mV drop at 500 mA —
fine for every board in the fleet (Tang 25K, Wukong, Colorlight i9 all
draw well under 0.8 A at 5 V; a board that exceeds it saturates the shunt
reading, it doesn't break). **Listing caution:** INA226 modules ship with
either R100 or R010 shunts — order the R100 variant and verify the shunt
marking on arrival. Module carries its own I2C pullups. ALERT lets the
conversion-ready signal gate sampling windows in later logger versions;
v1 polls and leaves it unconfigured.

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

| Ref | Part | Qty | Est. NZD | MPN / listing | Notes |
|---|---|---|---|---|---|
| A1 | Raspberry Pi Pico 2 | 1 | 12 | official RPi Pico 2 (SC1631) | Socketed, 2× 1x20 female headers. Pico 1 (SC0915) also fits (flash-PMOD role). |
| A2 | INA226 breakout module | 1 | 7 | Generic "INA226 I2C 36V" breakout, **R100 (0.1 Ω) shunt** — sold widely under this description on AliExpress/Amazon; 6-pin: VCC,GND,SCL,SDA,ALERT,+ one NC/A0. **Verify shunt marking (R100, not R010) on arrival before trusting readings.** | I2C + ALERT |
| A3 | microSD SPI breakout module | 1 | 4 | Generic "Micro SD Card SPI breakout, 3.3V, 6-pin" (HW-125-style footprint, no onboard level shifter) — pin order printed on the module silkscreen as 3V3 CS MOSI CLK MISO GND; confirm against the specific listing before socketing. | 6-pin, 3V3-native |
| J1 | 2-pin 5.08 mm screw terminal, THT | 2 | 2 | Generic 5.08mm pitch 2-pin terminal block (e.g. Phoenix-style clone, KF128-2P) | T1 5V IN, T2 5V OUT |
| J7 | USB-A female THT jack | 1 | 2 | Generic USB-A Type-A female, through-hole, 4-pin | Metered power out |
| J1b | USB-C 5V breakout module fp | 0–1 | 3 | Generic USB-C PD trigger/breakout board footprint (unpopulated default) | Optional alternative input |
| J2–J4, J8 | 2.54 mm male headers | ~40 pins | 2 | Generic breakaway pin header strip | |
| JP2 | 2×3 shrouded header + 2× jumper shunt | 1 | 0.5 | Generic 2.54mm 2x3 header + 2× 2.54mm jumper shunts | GP4/GP5: FLASH ⟷ UART select, both poles moved together |
| R | 100 Ω 1/4 W THT | 4 | 0.5 | Generic carbon/metal film, 5% or better | J2 SPI-to-FPGA series (MISO/CS/SCK/MOSI) — fault-current-limiting value, see §2.1 note |
| U1 | SN74CBTLV3125PW | 1 | 2 | TI or pin-compatible `Ioff`-rated 4-channel bidirectional bus switch | Mandatory J2 isolation; TSSOP-14 |
| U2 | TLV3011BIDBVR | 1 | 2 | TI micropower open-drain comparator | Pico-powered `TARGET_3V3_SENSE` supervisor; SOT-23-6 |
| R | 10 kΩ, 137 kΩ, 100 kΩ | 3 | 0.5 | 1% metal-film preferred | U1 OE pull-up and U2 2.94 V sense divider |
| R | 1 MΩ | 1 | 0.2 | 1% metal-film; mark DNP on first PCB | Optional U2 hysteresis, populate after breadboard characterization |
| R | 33 Ω 1/4 W THT | 5 | 1 | Generic carbon/metal film, 5% or better | J3 flash-PMOD series termination (4) +1 spare |
| R | 10 kΩ 1/4 W THT | 3 | 0.5 | Generic carbon/metal film, 5% or better | SPI_CS# + FLASH_CS# pullups (2, WP#/HOLD# pullups removed per §2.2 correction — not physically possible on the 6-pin J3), +1 spare |
| R | 1 kΩ 1/4 W THT | 2 | 0.5 | Generic carbon/metal film, 5% or better | LED series |
| LED | 3 mm THT, green + red | 2 | 0.5 | Generic 3mm THT LED | PWR (input side), ACT (GP14) |
| PCB | 2-layer, ~80×60 mm, HASL | 5 pcs | 15 | Any prototype fab (JLCPCB/PCBWay) | |
| | **Total** | | **~NZ$52** | | including 5 spare PCBs |

**Listing discipline:** every "generic" line above is a widely-available part
category, not a single-source dependency — any listing matching the stated
pin count/pitch/pinout works. The two that need physical verification before
first power-up regardless of listing: A2's shunt marking (R100 vs R010) and
A3's pin order (confirm against the specific board's silkscreen, since 6-pin
microSD breakouts do occasionally ship in a mirrored order).

## 5. Layout guidance

- 2 layers; bottom = ground pour, top = signal + 5V metering trace.
- Metering path (T1 → INA226 VIN+ → VIN− → T2/J7) in ≥2 mm trace, kept away
  from SPI. Everything else is ≤2 MHz digital — routing is uncritical.
- Keep each SPI group's traces together; grounds interleaved on J8 as tabled.
- Place U1 immediately behind J2, with short grouped SPI traces; leave the
  100 Ω resistors on the Pico side of U1. Place U2 and its divider by J2-6,
  away from SCK. Label the target-side U1 nets `TARGET_SPI_*`, never `SPI_*`.
- Add labelled test pads for `TARGET_3V3_SENSE`, `J2_OE_N`, and all four
  target-side SPI nets; these make the interlock acceptance test possible
  without touching a connector pin.
- Hex/IVM silkscreen motif welcome; keep the outline rectangular in Rev B.
- Mounting: 4× M3 holes.

## 6. Bring-up & test plan (uses only existing repo firmware)

1. **Continuity:** every table row above, before any module is socketed.
2. **Meter sanity:** Pico 2 + INA226 + 47 Ω/5 W resistor on T2 → expect
   ~106 mA ±5% at 5.0 V via `tools/bench_metrics/ina226_logger.py`
   (startup ID check must report TI manufacturer/die ID before trusting
   readings).
3. **Interlock qualification:** complete the five tests in §2.1 with a bench
   supply and meter/scope before attaching any FPGA. Record the measured
   rising/falling thresholds and only then populate R16 if hysteresis needs
   adjustment.
4. **Southbridge smoke:** `rp2350_spu_diag` UF2, J2 → Tang 25K
   `southbridge_link` probe → expect 0xAC status responses (known-good
   baseline from `docs/SOUTHBRIDGE_SPI_PROTOCOL.md`).
5. **Flash PMOD:** `rp2040_flash_pmod.uf2` on a Pico 1 in the same socket,
   JP2 → FLASH; `tools/rp2040_flash_pmod.py --port <tty> id` must report
   `JEDEC: EF4018` on a known-good W25Q PMOD.
6. **SD path:** SD hydration regression via `spu_sd` firmware on J5.
7. **First real metrics run:** Tang 25K probe ladder power table — idle vs.
   active for each silicon-verified probe, logged to CSV. This table feeds
   the central paper §Power and Timing.

## 7. Rev B layout / tapeout handoff

The project owner may hand-layout the board as far as practical, then engage
an EE student or other qualified reviewer to complete and review the tapeout.
The reviewer is not expected to redesign the board's role: this specification,
the breadboard interlock proof, and the proven firmware pin map are the design
inputs. Their job is to turn them into a safe, manufacturable, reproducible
KiCad design.

### Non-negotiable electrical requirements

- J2's CS#, SCK, MOSI, and MISO each pass through the hardware
  power-ready/`Ioff` interlock in §2.1; none may bypass it for convenience.
- J2-6 is `TARGET_3V3_SENSE` only. It shall not connect directly to Pico 3V3,
  Pico pin 36, or an adapter power rail.
- Retain the four 100 Ω Pico-side J2 series resistors after U1 is added.
- Provide labelled test pads for target sense, `J2_OE_N`, and both sides of
  each SPI channel, so backfeed and signal-integrity checks are repeatable.
- Keep the INA226 5 V metering path physically and electrically distinct from
  J2 SPI routing. Maintain the specified wide 5 V trace and a continuous,
  low-impedance ground return under the SPI group.

### Required review and tapeout deliverables

- KiCad schematic and PCB with symbols, footprints, net names, and values
  matching this spec; the active interlock must be present in the actual
  netlist, not only in a note or BOM.
- Electrical Rules Check and Design Rules Check reports, with every remaining
  warning either fixed or documented with a specific rationale.
- Fabrication package: Gerbers, drill files, board outline, stack-up, and
  fabrication drawing; provide pick-and-place and assembly drawings if an
  assembler will be used.
- Public BOM with manufacturer part numbers, distributor alternatives where
  sensible, DNP markings, and the exact U1/U2 qualified parts.
- A short assembly/inspection note covering polarity, Pico/module orientation,
  J2 pin 1 orientation, and the target-power safety rule.

### Required acceptance evidence

Before any board is treated as a stable southbridge fixture, retain the
breadboard/assembled-board results for: target-off with Pico-on; Pico-off with
target-on; power-threshold and hysteresis measurements; and the existing 2 MHz
southbridge smoke test. After those pass, collect the INA226 CSV power table
for the supported probe ladder. These artifacts are both the first metrics
capture dataset and the electrical evidence supporting OSHWA self-certification.

## 8. OSHWA mapping

| OSHWA requirement | This board |
|---|---|
| Original design files | KiCad project in this directory (to be captured from this spec) |
| Public BOM | §4, with MPN column to be added at capture time |
| Open license | CERN-OHL-W-2.0 |
| Docs to build/modify | This spec + assembly notes at capture |
| No proprietary blobs | All firmware already MIT in-repo |

Certification target: after Rev B is assembled, its design files and
manufacturing package are published, and the §6/§7 acceptance evidence passes.

## 9. Later candidates (explicitly NOT in Rev B scope)

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
