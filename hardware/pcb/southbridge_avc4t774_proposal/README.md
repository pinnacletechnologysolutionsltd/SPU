# Rev 1 SPI interface: SN74AVC4T774 candidate comparison

**Status: unqualified KiCad prototype; NOT FOR FPGA CONNECTION OR FINAL FABRICATION.**
The [prototype schematic](southbridge_avc4t774.kicad_sch), local symbol library
and KiCad project capture the proposal below. The three-translator candidate
remains intact at its [review revision](https://github.com/pinnacletechnologysolutionsltd/SPU/tree/c03c18334e88bbb2e4d76a3be8d68dd71e65f36c/hardware/pcb/southbridge_rev1_candidate).
The [electrical review](ELECTRICAL_REVIEW.md) retains the safety HOLD for
partial-rail and transition behavior. Schematic capture and standalone dummy-load
validation are authorized; no electrical testing has been performed.

KiCad 10.0.8 ERC reports zero violations. The exported netlist was checked against
the pin table and passive wiring below. ERC power flags represent external bench
supplies, not evidence of real rail availability. U1 uses a project-local symbol;
its pin numbers were checked against TI Rev I. U1 has the KiCad PW-compatible
TSSOP-16 footprint assigned, but actual package fit, socket orientation, parts,
board layout and operation remain unverified. J1 and J2 socket pins 1–20 map to
Pico module pins 1,3,...,39 and 2,4,...,40 respectively. J3 pins follow the table
below. Do not use the footprint assignments as fabrication approval.

## Purpose and comparison

Protect the dedicated Pico 2 ↔ Wukong SPI interface against the agreed power
conditions, while using fewer translator packages. Powered-off isolation,
brownout safety and reliable SPI are acceptance requirements to be established,
not properties demonstrated by this proposal.

| Item | Existing candidate at c03c183 | This alternative |
|---|---|---|
| SPI translation | one SN74LVC2T45 plus two SN74LVC1T45 | one SN74AVC4T774PWR, PW/TSSOP-16 |
| Direction | fixed by wiring | one fixed DIR per channel |
| Default-disable control | no shared OE or power-valid interlock | one OE pulled high; Pico GPIO may pull low |
| Independently detects target brownout | no | **no** |
| Rail connections | Pico 3V3 and target bank 3V3 separate; common ground | same; VCCA Pico, VCCB actual target bank rail |
| Series damping | four 100 Ω starting values | four 33 Ω starting values, subject to measurement |
| Validation | recorded ERC and netlist consistency; no electrical bench qualification | KiCad capture and ERC/netlist check; no bench result |
| Fabrication status | draft; not for fabrication | draft; not for fabrication |

Fewer packages do not establish lower total cost or equivalent protection. Both
alternatives leave partial-rail behaviour unqualified. The older comparator/
bus-switch Rev B and its power-ready requirements are a separate design.

## Proposed U1 pin mapping

Use [TI SN74AVC4T774PWR, PW 16-pin TSSOP](https://www.ti.com/product/SN74AVC4T774/part-details/SN74AVC4T774PWR),
[SCES693I Rev I, sections 4, 7 and 8](https://www.ti.com/lit/gpn/sn74avc4t774).
A-side and control pins reference VCCA. DIR high selects A→B; DIR low selects
B→A; OE high disables all outputs. Pin numbers below are **PW package only**.
Check the KiCad symbol and footprint against the manufacturer pinout before capture.

| U1 pin | Function | Proposed connection |
|---:|---|---|
| 1 | DIR1 | Pico 3V3 (A→B SCK) |
| 2 | DIR2 | Pico 3V3 (A→B MOSI) |
| 3 | A1 | Pico SCK, GP18 / module pin 24 |
| 4 | A2 | Pico MOSI, GP19 / module pin 25 |
| 5 | A3 | Pico CS#, GP17 / module pin 22 |
| 6 | A4 | Pico MISO, GP16 / module pin 21, through output resistor |
| 7 | DIR3 | Pico 3V3 (A→B CS#) |
| 8 | DIR4 | GND (B→A MISO) |
| 9 | OE# | Pico GPIO, provisional GP2 / module pin 4; 10 kΩ pull-up to Pico 3V3 |
| 10 | GND | shared signal ground |
| 11 | B4 | target MISO input, target connector pin 3 |
| 12 | B3 | target CS# via 33 Ω output resistor, target connector pin 1 |
| 13 | B2 | target MOSI via 33 Ω output resistor, target connector pin 2 |
| 14 | B1 | target SCK via 33 Ω output resistor, target connector pin 4 |
| 15 | VCCB | target bank 3V3 via target connector pin 6 |
| 16 | VCCA | Pico pin 36 3V3(OUT) |

Target connector pin 5 is GND. This follows the old candidate's generic J2
assignment; verify the actual board, bank rail and physical connector orientation
independently before any connection. The 33 Ω MISO output resistor is between A4
and Pico GP16. Place all four output resistors close to U1 outputs. Values are
initial placeholders, not verified signal-integrity or current-limit values.
The Pico GPIO allocation is proposed, not implemented firmware; confirm pin 4
is free in the chosen Pico 2 firmware and pinout before use.

## Proposed passive connections and test access

- 100 nF ceramic from VCCA to GND and another 100 nF from VCCB to GND, close to
  their respective pins with short return paths. Values, ratings and layout need
  review; rail inrush and external loads are not characterized.
- 10 kΩ from OE# to VCCA. Pico GPIO provisionally drives low only to enable;
  use input/high impedance to disable. Confirm reset state, GPIO behavior and
  pull-up/sink limits. This GPIO must never connect to VCCB or an FPGA signal.
- Pico-side input defaults: 10 kΩ from A1 SCK and A2 MOSI to GND, 10 kΩ from
  A3 CS# to VCCA. Target-side input B4 MISO has 10 kΩ to GND. These define
  undriven translator inputs, subject to source loading and power-state review.
- Target-side CS# after its series resistor has 10 kΩ to VCCB; target-side SCK
  and MOSI after their resistors each have 10 kΩ to GND. Pico-side MISO after
  its resistor has 10 kΩ to GND. These are starting idle pulls, not a proof of
  no back-power. Assess combined current and target inputs in every power state.
- Test points: VCCA, VCCB, GND, OE#, and each SPI line on each side of U1.
  The previous debug header and AUX signals are not implicitly included in this
  SPI-only proposal; any later debug paths require a separate complete audit.
- No target-voltage sense net, divider, analogue input or extra cross-board signal
  is specified. Sense-circuit choice, pin rating, clamp/injection current, safe
  behavior when Pico is unpowered, measurement accuracy and response latency are
  unresolved. Do not infer that software can determine target power state.

## OE and power states

TI recommends pulling OE high and not enabling until **both rails are fully
ramped and stable** ([datasheet §8.3](https://www.ti.com/lit/gpn/sn74avc4t774)).
The pull-up and GPIO support deliberate enable but do not enforce this condition
when Wukong starts independently or unexpectedly browns out. A fixed Pico delay
is insufficient. Default Pico reset/input state also needs verification. GPIO
firmware is not designed or tested here.

| Case | Required result | Evidence / current disposition |
|---|---|---|
| Either board fully off | No damaging back-power through any connected path | TI specifies high impedance when either VCC is **at GND** and Ioff; whole-board leakage, floating rail and every connected path remain unmeasured. **OPEN**. |
| Both supplies stable | OE can be asserted low and intended SPI operates correctly | Mapping is proposed; the means to establish target stability, operating rate, voltage thresholds and timing margins are **OPEN**. |
| Either rail brownout or fast loss | No damaging excursions; communication may fail | No power-valid enforcement, response-time guarantee, or complete partial-rail guarantee is established. **HOLD** pending analysis and dummy-load tests; GPIO polling cannot guarantee immediate disable. |

No hot plugging is permitted in the proposed operating envelope: both boards
are de-energized and discharged before cable insertion/removal. Common ground
is required during operation. A normal connector does not guarantee ground-first
mating. Power-off isolation is not galvanic isolation or protection against
miswiring, excess voltage, ESD, injected current or peripheral/debug bypasses.

## Proposed acceptance evidence, not test authorization

Before choosing hardware limits or connecting the real FPGA, identify exact
Pico and FPGA bank/device revisions and their pin, rail and injection-current
limits; verify J11-12 actually tracks the intended VCCO rail and is suitable as
a supply; define the maximum intended SPI frequency, cable, instruments and
numeric pass/fail thresholds. Audit every inter-board path including grounds,
UART, reset, USB, analyser, debug and any future rail-sense or peripheral link.
The single-master, single-target topology and actively driven MISO mean the MISO
line is not assumed shareable with other SPI targets.

In the authorized standalone dummy-load setup, with current-limited supplies and
no FPGA, examine both rails powered/off, either rail at zero and floating, inputs
high/low, slow and fast transitions in both directions, partial rails and target
loss during traffic. Record rail voltage, per-path current and waveform excursions
against the previously chosen endpoint limits. A 1 kΩ load is one measurement
condition: V/1 kΩ reports current through that resistor only; account for meter
resolution, other loads and alternate paths. After electrical acceptance, verify
SPI after both possible startup/restart orders at the defined rate and loads.

Review alternatives for controlled OE and safe target-rail knowledge. Add a
hardware power-valid mechanism only if the requirements and evidence call for it;
no option is qualified merely by naming it. Keep the existing candidate until
this comparison and schematic review are complete. No PCB layout, fabrication, programming or live FPGA connection is authorized by this document. The owner authorized bounded standalone dummy-load tests after schematic review; actual hardware and test equipment are required.
