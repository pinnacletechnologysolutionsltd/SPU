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

All four J2 signals shall pass through **U1, 74CBTLV3125PGG** (Renesas/IDT —
documented pin- and function-compatible substitute for the now-obsolete
SN74CBTLV3125PW, explicitly rated for `Ioff` / powered-off protection). It is
a four-channel bidirectional FET bus switch, so it safely covers the three
Pico-to-FPGA drivers and FPGA-to-Pico MISO without assigning a fixed
direction. Its four active-low OE pins are tied together as `J2_OE_N`.

`J2_OE_N` is pulled up to **Pico 3V3** with 10 kΩ, so the safe default is all
four signals disconnected. U2, a Pico-3V3-powered open-drain comparator with
an independent/fail-safe input (**TLV3011BIDBVR**, TI — open-drain output,
SOT-23-6; reverted 2026-07-27 from the MAX9063EUK+T substitute once LCSC
sourcing made the original part available again), pulls `J2_OE_N` low only
after `TARGET_3V3_SENSE` crosses the qualified-on threshold. Use its 1.242 V
internal reference with a **140 kΩ / 102 kΩ** divider from J2-6 —
102k/(140k+102k) × 2.9467 V = 1.242 V — for the nominal 2.94 V rising
threshold. Do not substitute **TLV3012** (push-pull output); this circuit
requires the open-drain TLV3011.

**Order the `DBV` suffix, not `DCK`.** TI ships TLV3011B in two 6-pin
packages, electrically identical and mechanically not interchangeable:

| Orderable | Suffix | Package | Pitch |
|---|---|---|---|
| **TLV3011BIDBVR** | `DBV` | **SOT-23-6** ← specified | 0.95 mm |
| TLV3011BIDCKR | `DCK` | SC70-6 | 0.65 mm |

`TLV3011BIDCKR` will *not* fit the SOT-23-6 breakout adapter this build
assumes, and SC70-6 adapters are both scarcer and materially harder to
hand-solder at 0.65 mm pitch on a ~2 × 1.25 mm body. Verified against TI's
product page 2026-07-30 after the part was nearly ordered in the wrong
package.

*Divider value note (2026-07-30).* The original 137 kΩ / 100 kΩ pair gives
2.9435 V (+0.12% of nominal); 140 kΩ / 102 kΩ gives 2.9467 V (+0.23%). Both
are E96 values and either is correct. 140k/102k was selected on sourcing
grounds when the order moved from LCSC to DigiKey. What must be preserved on
any future substitution is **both** the ratio and the total impedance:

- ratio `R_top/R_bot = 1.36715` sets the threshold
  (`V_trip = 1.242 × (1 + R_top/R_bot)`); and
- total ≈ 240 kΩ keeps the deliberately high divider impedance, and keeps the
  external hysteresis feedback resistor below sized correctly — hysteresis
  width scales with the feedback resistor *relative to* the divider
  impedance, so changing the total shifts the hysteresis band proportionally.
  140k+102k = 242 kΩ is within 2% of the original 237 kΩ; a 150k/110k pair
  would be a 10% shift.

Note that 137 kΩ, 140 kΩ and 102 kΩ are **E96 values and therefore exist only
in 1% and tighter** — they are absent from E24/5% listings, which is a common
sourcing dead end rather than a stock problem.

Do not pay for tighter than 1% here. With ±1% resistors the threshold band is
2.906–2.974 V, which dominates the ±0.23% ratio error by an order of
magnitude, and ±1% is entirely adequate for an undervoltage supervisor
tripping at ~89% of a 3.3 V nominal rail.

TLV3011B exposes an externally accessible noninverting input, so **an
external hysteresis footprint is possible and shall be provisioned on the
PCB** — a 1 MΩ-class feedback path from output back to the reference/input
node, left unpopulated unless breadboard characterization shows chatter near
the threshold. Size it from the measured chatter band.

> **Schematic captured 2026-08-11 — three corrections from the datasheets.**
> Pinouts taken from TI [SCDS037K](https://www.ti.com/lit/ds/symlink/sn74cbtlv3125.pdf)
> §4 and [SBOS300C](https://www.ti.com/lit/ds/symlink/tlv3011.pdf) Table 5-1,
> not from memory or from a web summary — one search summary returned
> "Pin 6: OUT/V+" for U2, which is wrong and would have inverted the circuit.
>
> **1. Verified polarity (U2, SOT-23-6: 1=OUT, 2=V−, 3=IN+, 4=IN−, 5=REF,
> 6=V+).** The open-drain output pulls low when IN− > IN+, so the sense
> divider drives **IN− (pin 4)** and REF drives **IN+ (pin 3)**. Target
> unpowered → IN−≈0 < IN+=1.242 V → OUT hi-Z → R13 pulls `J2_OE_N` high →
> U1 disconnected. Correct in both states. U1's sense is confirmed by
> SCDS037K Table 7-1: **OE = H → Disconnect, OE = L → A port = B port**, and
> TI explicitly recommends the OE pull-up for guaranteed Hi-Z through power
> transitions.
>
> **2. R16 alone would not work — R17 added.** REF is a low-impedance output
> (sources up to 0.5 mA) driving IN+ directly, so a 1 MΩ from OUT to IN+ is
> swamped and produces no hysteresis. Positive feedback needs a series
> resistor between REF and IN+: **R17 = 10 kΩ**, now on the board. Without
> it the escape hatch that justifies choosing TLV3011B over MAX9063 does not
> exist. Hysteresis width therefore scales against **R17**, *not* the sense
> divider — the §2.1 note above is wrong on that point. The divider's
> **ratio** still matters (it refers the band up to J2-6, ×2.3725); its
> **impedance** does not. "Preserve ≈240 kΩ total" is harmless but does not
> do what it claims.
>
> **3. TLV3011*B* already has built-in hysteresis: V_HYS = 2 / 6 / 8 mV**
> (SBOS300C, "Integrated hysteresis (B version)"). The breadboard doc's
> premise — that MAX9063 was rejected because it "offered no escape hatch if
> its fixed internal hysteresis proved too narrow", implying TLV3011B has
> none — is wrong. 6 mV typ referred through the divider is **≈14 mV at
> J2-6**, the same order as the ~13 mV this spec called possibly-inadequate
> for the MAX9063. The preference still holds because the escape hatch is
> real, but bench step 1 should start from "there is already ~14 mV", not
> "there is none".
>
> **Assembly: U1 and U2 mount on DIP breakout carriers** (decision
> 2026-08-11), not as bare SMD. Footprints `DIP-14_W7.62mm_Socket` and
> `DIP-6_W7.62mm_Socket`. This keeps the board consistent with its own
> "hand-solderable / module carrier" scope (line 6), avoids the 0.65 mm
> TSSOP-14 joint, and **replaces the four bypass-link footprints** the
> 2026-08-10 Rev A-populate decision called for: with U1 socketed, Rev A is
> populated by fitting a wire-link header in the socket and swapping it for
> the real module at Rev B. Populate the link header **or** U1, never both.
>
> ⚠ **Both carrier footprints are unverified against a physical part** — the
> adapters are not yet ordered, and SOT-23-6 breakouts ship in more than one
> DIP outline. Confirm both against the adapters actually purchased before
> gerbers. Same class of risk as the A1 Pico footprint.

*Fallback if TLV3011B is unobtainable:* **MAX9063EUK+T** (SOT-23-5, the
inverting-input part of the MAX9062/9063 pair — MAX9062 has the opposite
polarity and must not be substituted). Its 0.2 V reference requires a
140 kΩ / **10.2 kΩ** divider instead (0.2 V × (1 + 140/10.2) = 2.945 V; 10.2 kΩ
is E96). Keeping `R_top` at 140 kΩ across both options means the fallback costs
one extra value rather than two. It exposes no noninverting input, so
the hysteresis footprint is unusable and its fixed internal hysteresis
(~±0.9 mV at the sense pin) must be characterized and confirmed adequate on
the breadboard with no resistor-value fallback available.

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

> *Schematic reconciled 2026-08-11.* The KiCad capture had **not** followed
> the correction above: JP2 existed as two separate `Conn_01x03` symbols
> (`JP2A`/`JP2B`) on two `PinHeader_1x03` footprints, which would have put
> 2× 1×3 headers on the board and in the BOM instead of 1× 2×3, and let the
> two poles be placed independently — losing the matched-pair property that
> is the entire point of the 07-09 correction. Now a single
> `Conn_02x03_Odd_Even` on `PinHeader_2x03_P2.54mm_Vertical`, designator
> `JP2`, qty 1.
>
> **Pin assignment (odd/even numbering, one group per column):**
>
> | Group | Common (middle) | Position A — J3/flash | Position B — J4/UART |
> |---|---|---|---|
> | Odd column | pin 3 = `GP4` | pin 1 = `FLASH_MISO_PRE_R` | pin 5 = `UART_TX` |
> | Even column | pin 4 = `GP5` | pin 2 = `FLASH_CS_PRE_R` | pin 6 = `UART_RX` |
>
> **Shunt orientation is a silkscreen requirement, not a preference.** Each
> 3-pin group is a *column*, so both shunts bridge **along** the columns
> (1–3 or 3–5; 2–4 or 4–6) — **never across the rows** (1–2, 3–4, 5–6),
> which is the default mental model for a 2×3 block and is wrong here.
> Bridging 1–2 shorts `FLASH_MISO_PRE_R` to `FLASH_CS_PRE_R`. The 33 Ω
> series resistors (§2.2) keep that from being damaging, but it silently
> breaks flash comms and looks like a dead adapter. The silkscreen must make
> the orientation unambiguous — outline the two column groups, do not merely
> label the pins.

### 2.3 microSD module socket (J5)

Source: `hardware/rp_common/spu_sd.c:15-24` (SPI1). Socket for the common
6-pin SPI microSD breakout module.

| Signal | Pico 2 GPIO | Pico pin | J5 pin (module order: 3V3 CS MOSI CLK MISO GND) |
<!-- module order confirmed against the physical microSD breakout 2026-08-11 -->
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

**J6 module order (left to right, as printed on the module silkscreen):
`IN+ IN− VBS ALE SCL SDA GND VCC`** — read off the physical part 2026-08-11.
Confirm against the specific listing before socketing; this ordering is not
universal across INA226 breakouts.

| J6 pin | Silkscreen | Net | Pico 2 GPIO | Pico pin |
|---|---|---|---|---|
| 1 | IN+ | `V5_IN` — screw terminal T1 (5V IN) | — | — |
| 2 | IN− | `V5_OUT` — screw terminal T2 (5V OUT) + USB-A J7 | — | — |
| 3 | VBS | `V5_OUT` — **tied to IN−**, load-side bus sense | — | — |
| 4 | ALE | `INA_ALERT` (conversion ready) | GP15 | 20 |
| 5 | SCL | `I2C_SCL` | GP9 | 12 |
| 6 | SDA | `I2C_SDA` | GP8 | 11 |
| 7 | GND | `GND` | — | 13 |
| 8 | VCC | `V3V3` | — | 36 |

ALE is wired but firmware v1 polls and leaves it unconfigured — the trace
costs nothing and enables conversion-ready gating in later logger versions.

> **Corrected 2026-08-11 against the physical module — J6 is ONE 8-pin
> header.** The capture had it as two connectors, `J6` (`Conn_01x05`:
> SDA/SCL/ALERT/VCC/GND) and `J9` (`Conn_01x02`: VIN+/VIN−), and the BOM
> described the module as *"6-pin: VCC,GND,SCL,SDA,ALERT,+ one NC/A0"*.
> **All three descriptions were wrong**, in pin count, in grouping and in
> order. J9 is deleted; J6 is now a single `Conn_01x08` on
> `PinSocket_1x08_P2.54mm_Vertical`.
>
> **The old order would have destroyed the module.** The 1×05 socket was
> wired SDA/SCL/ALERT/VCC/GND against a real part that starts IN+/IN−/VBS —
> seating it would have put the 5 V metering rail onto the I²C lines. This is
> the failure the J5 row guards against by naming the module order
> explicitly; that care had not been taken for J6.
>
> **VBS was also missing entirely.** It is the bus-voltage sense input, and
> the VBUS channel is actively used (a module failed *that channel* on
> 2026-08-07). It is tied to **IN−**, matching how it was wired on the
> breadboard rig, so VBUS keeps measuring the load-side node and existing
> captures stay comparable with the frozen
> `software/datasets/ina226_coarse_monitor_v2.json` contract. **Do not
> re-point VBS** — changing the measured node silently invalidates
> cross-session comparison, and the contract has no partial-redo path.

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
| A2 | INA226 breakout module | 1 | 7 | Generic "INA226 I2C 36V" breakout, **R100 (0.1 Ω) shunt** — sold widely under this description on AliExpress/Amazon; **8-pin single header, order `IN+ IN- VBS ALE SCL SDA GND VCC`** (verified against the physical part 2026-08-11 -- the earlier "6-pin: VCC,GND,SCL,SDA,ALERT,+ NC/A0" description was wrong in count, grouping and order; see 2.5). **Verify shunt marking (R100, not R010) on arrival before trusting readings.** | I2C + ALERT |
| A3 | microSD SPI breakout module | 1 | 4 | Generic "Micro SD Card SPI breakout, 3.3V, 6-pin" (HW-125-style footprint, no onboard level shifter) — pin order printed on the module silkscreen as 3V3 CS MOSI CLK MISO GND; confirm against the specific listing before socketing. | 6-pin, 3V3-native |
| J1 | 2-pin 5.08 mm screw terminal, THT | 2 | 2 | Generic 5.08mm pitch 2-pin terminal block (e.g. Phoenix-style clone, KF128-2P) | T1 5V IN, T2 5V OUT |
| J7 | USB-A female THT jack | 1 | 2 | Generic USB-A Type-A female, through-hole, 4-pin | Metered power out |
| J1b | USB-C 5V breakout module fp | 0–1 | 3 | Generic USB-C PD trigger/breakout board footprint (unpopulated default) | Optional alternative input |
| J2–J4, J8 | 2.54 mm male headers | ~40 pins | 2 | Generic breakaway pin header strip | |
| JP2 | 2×3 shrouded header + 2× jumper shunt | 1 | 0.5 | Generic 2.54mm 2x3 header + 2× 2.54mm jumper shunts | GP4/GP5: FLASH ⟷ UART select, both poles moved together |
| R | 100 Ω 1/4 W THT | 4 | 0.5 | Generic carbon/metal film, 5% or better | J2 SPI-to-FPGA series (MISO/CS/SCK/MOSI) — fault-current-limiting value, see §2.1 note |
| U1 | 74CBTLV3125PGG | 1 | 2 | Renesas/IDT, `Ioff`-rated 4-channel bidirectional bus switch (Active; substitute for obsolete SN74CBTLV3125PW) | Mandatory J2 isolation; TSSOP-14 |
| U2 | TLV3011BID**BV**R | 1 | 2 | TI open-drain comparator, 1.242 V integrated reference. Three same-family traps: do **not** use TLV3012 (push-pull output); do **not** use TLV3011BID**CK**R (that is SC70-6, not SOT-23-6 — see note below); fallback MAX9063EUK+T needs a 10.2 kΩ bottom divider leg, not 102 kΩ | Pico-powered `TARGET_3V3_SENSE` supervisor; SOT-23-**6** |
| R | 10 kΩ, 140 kΩ, 102 kΩ | 3 | 0.5 | **1% — 140k and 102k are E96 and do not exist in 5%/E24** | U1 OE pull-up (10k) and U2 2.94 V sense divider (140k/102k for TLV3011B's 1.242 V reference → 2.9467 V; the MAX9063 fallback needs a 10.2 kΩ bottom leg, not 102 kΩ). Preserve ratio **and** ≈240 kΩ total on any substitution — divider impedance sets the external hysteresis scaling. Do not buy tighter than 1%. |
| R | 1 MΩ | 1 | 0.2 | 1% metal-film preferred | R16, U2 hysteresis feedback (OUT → IN+) — **fit only if** breadboard step 1 shows chatter near the threshold; size from the measured band. Marked DNP in the schematic. Unusable with the MAX9063 fallback |
| R | 10 kΩ | 1 | 0.1 | 5% or better | **R17, added 2026-08-11** — series REF → IN+. Without it R16 does nothing: REF sources 0.5 mA and holds IN+ regardless. Hysteresis scales against *this* resistor, not the sense divider |
| C | 100 nF | 2 | 0.2 | 50 V ceramic, THT | C1/C2, decoupling at U1 VCC and U2 V+. **Check placement before fitting R16** — chatter from missing decoupling looks identical to insufficient hysteresis |
| — | TSSOP-14 → DIP-14 breakout adapter | 1 | 3 | — | U1 carrier (assembly decision 2026-08-11). Verify outline against the part actually ordered |
| — | SOT-23-6 → DIP breakout adapter | 1 | 2 | **SOT-23-6, not SOT-23-5 or SC70-6** | U2 carrier. Ships in more than one DIP outline — **confirm before gerbers** |
| — | DIP-14 wire-link header | 1 | 0.5 | Header strip + wire | Rev A populate: bridges U1's four channels while U1 is unfitted. Fit this **or** U1, never both |
| R | 33 Ω 1/4 W THT | 5 | 1 | Generic carbon/metal film, 5% or better | J3 flash-PMOD series termination (4) +1 spare |
| R | 10 kΩ 1/4 W THT | 3 | 0.5 | Generic carbon/metal film, 5% or better | SPI_CS# + FLASH_CS# pullups (2, WP#/HOLD# pullups removed per §2.2 correction — not physically possible on the 6-pin J3), +1 spare |
| R | 1 kΩ 1/4 W THT | 1 | 0.3 | Generic carbon/metal film, 5% or better | R11, PWR LED series off 5 V — ≈2 mA with a Vf 3.0 V green. 680 Ω if brighter is wanted; aesthetic only |
| R | 330 Ω 1/4 W THT | 1 | 0.3 | Generic carbon/metal film, 5% or better | R12, ACT LED series off 3.3 V GP14 — ≈4 mA with a Vf 1.9 V red. **Not interchangeable with R11**, see LED note below |
| LED | 3 mm THT: **green** (PWR) + **red** (ACT) | 2 | 0.5 | Generic 3mm THT LED | PWR (input side, 5 V rail, any Vf); ACT (GP14, **red/amber only**) |
| C | 100 nF ceramic X7R, 50 V | 4 | 0.5 | Generic X7R 0.1 µF, THT 2.54 mm or 0603 | **Decoupling — mandatory, one per IC supply pin, placed at the pin.** U1 VCC, U2 V+, +2 spare. Was absent from Rev B until 2026-07-30; see note below |
| C | 10 µF ceramic or electrolytic, 16 V+ | 2 | 0.5 | Generic | Bulk on the Pico 3V3 rail feeding U1/U2, and on the metered 5 V output |
| PCB | 2-layer, ~80×60 mm, HASL | 5 pcs | 15 | Any prototype fab (JLCPCB/PCBWay) | |
| | **Total** | | **~NZ$53** | | including 5 spare PCBs |

**The ACT LED must be red or amber — this is an electrical constraint, not a
preference (resolved 2026-08-10).** R12 hangs off GP14 at 3.3 V. Modern InGaN
green, blue and white parts sit at Vf ≈ 3.0–3.2 V, leaving ~0.3 V of headroom
before the RP2350's own output drop at 4 mA (a further 0.1–0.3 V) is counted.
Part-to-part Vf spread is ±0.2 V, comparable to the whole budget, so the result
is not "dim but working" — it is unpredictable, varying between parts from the
same reel, with the resistor value barely influencing it. Red and amber are
AlGaInP and remain at Vf ≈ 1.9–2.1 V however modern the part, which is why the
colour is specified rather than left to stock. The PWR LED is unconstrained: it
runs off the 5 V input rail where any Vf has headroom.

Rejected alternative, recorded so it is not re-proposed: driving the ACT LED
from 5 V and sinking it with GP14. It appears to work — at Vf 3.0 V the pin is
never pulled up, because 5 − 3.3 = 1.7 V is below the forward drop — but it
places a 5 V rail one component failure away from a non-5 V-tolerant pin, the
same failure class as the J11 backfeed damage in §2.1. If only high-Vf parts are
available, fit a small NPN/MOSFET driver rather than this.

**Decoupling was missing from Rev B and is not optional.** The original BOM
listed two ICs and zero capacitors. U2 is a comparator with an integrated
reference: comparators are prone to output chatter and reference disturbance
without a local bypass, and this is materially worse on a breadboard than on a
PCB because of lead inductance. Note the interaction with the hysteresis
footprint above — **if breadboard step 1 shows chatter near the threshold, check
for a missing or badly placed 100 nF before fitting the 1 MΩ feedback
resistor.** Fitting hysteresis to suppress chatter caused by absent decoupling
would treat the symptom and leave the cause on the board.

### Breadboard bring-up tooling (not PCB BOM)

Needed to execute the breadboard acceptance steps below; none of it is
populated on the board.

| Item | Qty | Est. NZD | Notes |
|---|---|---|---|
| TSSOP-14 → DIP breakout adapter | 2 | 6 | **Required for U1** (`74CBTLV3125PGG`, TSSOP-14, 0.65 mm pitch). U1 is mandatory J2 isolation, so without this the breadboard steps cannot run at all. Two, because hand-soldering 0.65 mm pitch has a failure rate |
| SOT-23-6 → DIP breakout adapter | 2 | 4 | For U2 (`TLV3011BIDBVR`). **SOT-23-6, not SOT-23-5, and not SC70-6** |
| fx2lafw/sigrok 8-channel USB logic analyzer | 1 | 15 | 24 MHz, `fx2lafw` firmware, driven by sigrok/PulseView. This is the part J8 in §2.6 is sized for. Sourced from AliExpress/Amazon — **do not buy a Digilent or Saleae unit for this**; they cost 10–30× more for bandwidth this bench does not use (SPI runs 25 kHz–2 MHz) |

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
- **J6 placement is now doubly constrained (2026-08-11).** Consolidating the
  INA226 onto one 8-pin strip means a single connector must be reachable by
  *both* the ≥2 mm metering path from T1/T2 (pins 1–3) *and* the Pico's
  I²C/ALERT signals (pins 4–6). When these were two connectors, each could be
  placed independently — J9 by the terminal blocks, J6 by the Pico. Place J6
  first and let the terminal blocks follow it; the fat 5 V path is the
  harder of the two to route late. Note the metering trace necks down at the
  1.7 mm pads, which is expected and not a violation of the ≥2 mm rule.
- Keep each SPI group's traces together; grounds interleaved on J8 as tabled.
- Place U1 immediately behind J2, with short grouped SPI traces; leave the
  100 Ω resistors on the Pico side of U1. Place U2 and its divider by J2-6,
  away from SCK. Label the target-side U1 nets `TARGET_SPI_*`, never `SPI_*`.
- Add labelled test pads for `TARGET_3V3_SENSE`, `J2_OE_N`, and all four
  target-side SPI nets; these make the interlock acceptance test possible
  without touching a connector pin.
- Hex/IVM silkscreen motif welcome; keep the outline rectangular in Rev B.
- Mounting: 4× M3 holes.

### A1 Pico 2 footprint (created 2026-08-11)

`bench_adapter:RPi_Pico2_Module_Socketed`, in the new project library
`kicad/bench_adapter.pretty` with a `kicad/fp-lib-table`. **No Pico footprint
ships with KiCad 10** — confirmed by searching the installed libraries, not
assumed.

Geometry from the [Pico 2 datasheet](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf)
§3 / Figure 3:

| Dimension | Value | Source |
|---|---|---|
| Board | 51.0 × 21.0 mm | §3 text |
| Pin pitch | 2.54 mm | §3 text |
| Row spacing | 17.78 mm | Figure 3 |
| Pin 1 → pin 20 | 48.26 mm | Figure 3 |
| Pin 1 from top edge | **1.37 mm** | (51 − 48.26)/2 — the grid is **centred**; measured off the scaled drawing as 1.386 mm, agreeing to 0.02 mm |
| Pad / drill | 1.7 mm / 1.0 mm | matches KiCad `PinSocket_1x20_P2.54mm_Vertical` — the Pico is socketed on female headers here, not soldered down |

Numbering matches the symbol and the datasheet: pin 1 top-left, down the left
edge to 20, then 21 bottom-right up to 40 top-right. Verified 40 symbol pins
against 40 footprint pads, with pins 1/20/21/40 at the four corners.

**The Pico's own 4× Ø2.1 mounting holes are deliberately *not* in the
footprint.** The module sits above this board on sockets, so replicating them
would only consume routing area. The 4× M3 above are for the adapter board
itself and are unrelated.

⚠ **Print at 1:1 and check against the physical Pico 2 before gerbers.** The
geometry is datasheet-derived and internally consistent, but has not been
compared to a real part. The USB overhang on `F.Fab` is *indicative only* — it
was not measured; the courtyard reserves 3 mm above the board edge to cover it
conservatively. Same standing requirement as the U1/U2 carrier footprints.

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
