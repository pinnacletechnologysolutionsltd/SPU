# SN74AVC4T774 Rev 1: focused electrical review

**Scope update:** The owner authorized unqualified schematic capture and bounded standalone dummy-load tests. The HOLD below remains in force for electrical qualification and connection to the real FPGA; the original review records its findings at the time it was written.

**Disposition: HOLD for electrical safety; preferred candidate retained.** The
PW pin mapping checks out. TI's powered-off specification supports the
fully grounded-supply case for the IC under its stated conditions. It does not
establish whole-board safety through every floating, partial or transitioning
rail. GPIO-controlled OE and the proposed passives therefore **cannot yet be
accepted** as satisfying independent-sequencing safety. A target-rail monitor
or supervisor is not proven necessary, and neither is it proven unnecessary:
compare the required operating envelope with the missing evidence before adding
parts. No schematic, layout, hardware or firmware was changed and no test ran.

Reviewed: proposed [pin-level design](README.md), previous public three-translator
candidate at `c03c183`, TI [SN74AVC4T774 datasheet Rev I](https://www.ti.com/lit/gpn/sn74avc4t774)
and [PW ordering record](https://www.ti.com/product/SN74AVC4T774/part-details/SN74AVC4T774PWR),
[Raspberry Pi Pico 2 pinout](https://datasheets.raspberrypi.com/pico/Pico-2-Pinout.pdf),
[AMD Artix-7 DS181](https://docs.amd.com/v/u/en-US/ds181_Artix_7_Data_Sheet),
and local Wukong V03 schematic PDF SHA-256 `bec53e6201c5c47a7059ce5b5af86e0f3a48535ebdf5643af7583171f7331aee`.
These are source and paper checks, not an independent electrical certification.

## Pin and supply verification

TI's PW TSSOP-16 mapping is: 1 DIR1, 2 DIR2, 3 A1, 4 A2, 5 A3, 6 A4,
7 DIR3, 8 DIR4, 9 OE, 10 GND, 11 B4, 12 B3, 13 B2, 14 B1, 15 VCCB,
16 VCCA. The proposal matches it. A and all DIR/OE controls reference VCCA;
B references VCCB. With OE low, DIR high gives A→B and low gives B→A. Thus
DIR1–3 high for SCK/MOSI/CS and DIR4 low for MISO match the intended directions.
OE high disables outputs; both input circuits remain active. PW and PWR identify
the same PW package; PWR denotes an ordering/packaging variant. The Pico module
pinout confirms GP16/17/18/19 at 21/22/24/25 and provisional GP2 at 4, with
3V3(OUT) at 36. GP2 availability, reset behavior and actual firmware remain
unverified. KiCad symbol-to-footprint mapping has not been checked because no
candidate schematic exists.

## Powered, off and transition cases

- **Fully grounded VCC:** TI states either VCC at ground puts both ports in
  high impedance. Rev I §5.5 specifies Ioff for A or B ports, VI or VO 0–3.6 V,
  with one supply exactly 0 V and the other 0–3.6 V: ±5 µA maximum over
  −40 to 85 °C (±1 µA maximum at 25 °C). These are IC port leakage test
  conditions, not total system current, zero leakage, floating-supply evidence,
  non-SPI-path evidence, or a direct current limit on an FPGA input. Check the
  full table and supply-current rows when designing a measurement.
- **Below recommended range:** §5.3 recommends VCCA and VCCB 1.1–3.6 V for
  operation, with condition-dependent VIH/VIL and switching limits. A rail at
  0.1–1.1 V is neither the exactly grounded Ioff condition nor generally within
  recommended operation. The isolated-at-ground statement alone does not prove
  a cutoff threshold, output voltage/current envelope, or damage-free interface
  throughout that interval. A fully floating rail is a different test condition.
- **Startup/shutdown:** §8.3 requires OE pulled up to VCCA and not enabled until
  both rails are fully ramped and stable. The example with GPIO does not itself
  establish independent target-rail sensing. With Pico running and OE asserted
  low, Wukong rail loss need not be detected by the Pico; whether port behavior
  during the fall stays inside every endpoint limit is **not established**.
  The same concern applies to Pico-rail fall while the target remains powered,
  reset, slow ramps, and floating VCC. TI's powered-off promise is useful but
  does not by itself show a complete brownout trajectory.

AMD DS181's general Artix-7 I/O absolute maximum table gives V_IN up to VCCO +
0.55 V, with notes and other applicable limits. This is a **damage stress limit**,
not an operating target or permitted injection-current budget. It illustrates
why a high signal with the target rail down needs attention. Verify the actual
bank, pin, I/O standard, full notes and Wukong circuit before deriving a numerical
acceptance threshold. Corresponding Pico 2/RP2350 power-off and injection limits
also remain to be extracted for the actual configuration; do not assume the
translator's Ioff rating is an endpoint limit.

## OE, sensing and requirements

A 10 kΩ pull-up to VCCA and GP2 controlled as input/high-Z for disable or low
for enable is consistent with the control concept in TI's SPI example; with
VCCA 3.3 V it draws approximately 0.33 mA while held low. This does not verify
GPIO reset/high-impedance state, sink capability, OE noise margin or safe
behaviour if GP2 is misconfigured as output-high. Those require pin/firmware
review. A pull-up is not a target-supply detector: with VCCA high and OE low,
a target brownout can occur without any control change. It also cannot certify
sudden transitions merely because it starts disabled.

**Rail knowledge is necessary to implement TI's 'enable only after both stable'
instruction; a particular sensing circuit or supervisor IC is not established as
necessary.** An externally confirmed, controlled power sequence can provide
operational knowledge for a restricted manual test, but does not automatically
cover independent loss/restart or prove the wider safety requirement. GPIO/ADC
monitoring could support orderly operation if designed and validated, but must
not add an unpowered GPIO backfeed path; its latency and failure modes do not
by themselves guarantee fast-loss protection. The simplest candidate remains
OE pull-up + controlled GPIO, subject to evidence. If it fails a safety criterion,
evaluate the least-complex suitable mitigation, including hardware gating; none
is assumed sufficient without its own analysis and test.

## Passive and inter-board path audit

| Path | Proposed handling | Finding / gap |
|---|---|---|
| SCK, MOSI, CS | A→B through IC; 33 Ω at B outputs | No direct rail-to-rail resistor, but OE asserted during partial VCCB is uncharacterized. 33 Ω is damping, not protection: ideal 3.3 V/33 Ω is 100 mA before source impedance and clamps; no actual fault current is inferred. |
| MISO | B→A; 33 Ω at A output | Input source may be driven or unpowered; IC off leakage, powered-target outputs, Pico input limits and transitions need measurement. With OE enabled, MISO is actively driven at A; not a shared bus. |
| CS idle pulls | 10 kΩ from Pico CS to VCCA and target CS to VCCB | Each is local to its own rail; no intentional passive VCCA↔VCCB resistor. If J2-6 does not track the FPGA bank, the target pull can drive a differently powered FPGA pin. Confirm rail identity and powered-off tracking. |
| SCK/MOSI/MISO pulls | 10 kΩ local pull-downs; 10 kΩ MISO on target and Pico sides | No intentional positive cross-rail pull. Driven 3.3 V into one 10 kΩ pull-down gives about 0.33 mA per resistor, excluding tolerances and other loads. Actual GPIO low/high levels and aggregate current need checking. |
| OE and DIR | OE pull-up/GP2; DIR1–3 to VCCA, DIR4 to ground | Local to Pico domain. Direct GP2 wire is not an inter-board rail sense; verify startup and powered-off pin characteristics. |
| VCCB sense/supply wire | J2-6 connected to target bank 3V3 for U1 VCCB, target CS pull and bypass capacitor | It is a **real supply path**, not passive high-impedance sensing. Rail shorts, disconnected pin, floating rail, capacitance/inrush, unpowered FPGA bank, and connector current must be examined. VCCA and VCCB are not intentionally tied. |
| Ground and connector | J2-5 common ground; no hot-plug | Ground is a return path, not galvanic isolation. Broken ground, reverse cable and insertion with power present are outside the proposed operating envelope and not demonstrated safe. |
| USB, UART, reset, flash/JTAG, debug/AUX, analyser, peripherals | None specified as an additional Pico↔Wukong link in this proposal; Pico and Wukong can each have independent USB/JTAG connections | Separate USB hosts, cable shields, external instruments or future signals can create return, ground or powered paths. The existing candidate's J3 exposes target SPI plus direct Pico GPIO and grounds; it is **not included** here and must be audited before reuse. Board-level non-SPI wiring has not been inventoried physically. |
| Extra voltage sensing | None connected | Any future divider, ADC or other sense connection becomes a new cross-domain path; evaluate input clamp/injection and Pico-off/target-on cases before choosing it. |

The local V03 PDF shows J11 pins 7/8/9/10 as BANK35 J4/G4/B4/B5,
11 as ground and 12 as 3V3; J11 6 is also marked 3V3. The existing candidate
uses this lower-row signal mapping. The schematic is not a measurement: actual
board revision, orientation, rail continuity, rail behavior with FPGA unpowered,
physical damage and connected cable paths remain unverified. The previous board
incident does not identify the fault mechanism of this proposed circuit.

## Bounded dummy-load test proposal — not performed or authorized here

First freeze an owner-reviewed test procedure: actual component and board
identities, current-limited supplies, grounds and isolation, instrument limits,
per-path measurement, maximum excursion/current and duration criteria drawn
from endpoint specifications, cable/load model, exact ramp parameters and stop
conditions. A test instrument capable of holding or backfeeding a rail must be
characterized. No real FPGA/Pico connections during the first stage.

One bounded first-stage matrix for a single translator assembly is:

1. Two independently current-limited 3.3 V sources and dummy GPIO/FPGA loads;
   test four stable supply combinations, including each side driven while the
   opposite rail is clamped to 0 V. Exercise each SPI input high and low, first
   with OE disabled then, in permitted conditions, enabled.
2. Repeat each one-sided-power case with the opposite rail **disconnected**,
   not merely clamped, and measure that rail's voltage with a documented high-Z
   instrument. Repeat with a known 1 kΩ load; V/1 kΩ is only that load's current.
3. With only safe dummy endpoints, capture both rails, OE and each output during
   both startup and shutdown orders; include one predefined slow and one fast
   ramp, target loss while enabled, and recovery. Three repetitions per named
   condition are a starting bound, not a statistical qualification. Record
   actual ramp rates, capacitance, worst excursions and instrument bandwidth.
4. Compare every channel and rail against the frozen endpoint limits and stop on
   any excursion, unexpected current or unresolved measurement. If results are
   ambiguous, do not infer a pass or connect the real boards. Testing can reveal
   a failure or support only the tested conditions; it cannot prove all parts,
   temperatures, ramp shapes, faulty cables or lifetime conditions safe.
5. Only after electrical review and authorization, evaluate normal SPI and
   restart behavior at a specified rate with appropriate loads. No hardware
   mitigation or GPIO algorithm is declared adequate solely by this paper review.

No measured current, scope trace, ERC, netlist or physical result was produced.
