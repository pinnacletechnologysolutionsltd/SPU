# SPU-13 ECP5 Evaluator EE Handoff

**Status:** Draft handoff specification. Not a schematic and not fab-ready.
**Target board:** ECP5-85F/44F evaluator with RP2350 southbridge.
**Primary goal:** Build a manufacturable open-toolchain evaluator for silicon
evidence: RPLU2 table hydration, one shared M31 datapath, live Thimble-Pade
evaluation, SPI-visible golden traces, and reserved PIO parallel transport.

This document gives an electrical engineer a single starting point. Vendor
datasheets and package pin tables remain the source of truth for exact rail
names, ball assignments, decoupling, sequencing, configuration straps, and
absolute maximum ratings.

## 1. Scope Boundary

### EE owns

- ECP5/RP2350 schematic capture.
- Power tree, regulator choice, rail sequencing, reset supervision, and
  decoupling.
- ECP5 configuration flash, JTAG, oscillator, boot straps, and test points.
- RP2350 USB, boot/reset, flash, microSD, SPI fallback, and PIO bus pinout.
- PCB stackup, BGA escape, impedance/routing rules, DRC/ERC clean layout, and
  fab/assembly outputs.
- Optional SI/power test coupons if budget permits.

### EE does not own

- SPU-13 ISA semantics.
- RPLU2/Lucas/SU3 arithmetic RTL.
- Existing SPI command opcodes.
- Golden-vector oracle definitions.
- Paper claims around exact arithmetic and deterministic cycle behavior.

Board-driven pinout requests are expected, but changes to RTL behavior or
arithmetic contracts must be raised as architecture issues rather than folded
into PCB work.

## 2. Required Interfaces

| Interface | Requirement |
|---|---|
| SPI fallback/control | RP2350 master to FPGA slave, Mode 0, 3.3 V LVCMOS preferred, independent of PIO bus |
| PIO data plane | 8-bit half-duplex RP2350 PIO/DMA bus: `DATA[7:0]`, `STROBE`, `READY`, `DIR/WE` |
| JTAG | Standard ECP5 JTAG header with 3.3 V reference, keyed/polarized if practical |
| Configuration flash | Dedicated SPI/QSPI flash for ECP5 bitstream |
| RPLU table storage | Dedicated flash or microSD path controlled by RP2350 |
| USB | RP2350 USB-C or USB Micro-B for CDC/debug and firmware load |
| Test pads | `CS`, `SCK`, `MOSI`, `MISO`, `STROBE`, `READY`, `DIR/WE`, two data lines, reset, clock, all rails |

Keep SPI as a recovery path even if the PIO transport is populated. The known
bring-up flow depends on having a low-speed path that can read status and write
single commands before the high-speed bus is trusted.

## 3. Candidate Power Rails

The exact rail list must be verified against the selected ECP5 ordering code,
package, speed grade, and I/O standards. The current candidate design assumes:

| Rail | Candidate voltage | Loads | Notes |
|---|---:|---|---|
| `VCC_CORE` / ECP5 core | 1.1 V nominal | ECP5 logic fabric | Size from post-P&R estimates plus margin. Verify Lattice rail naming for chosen package. |
| `VCCAUX` | 2.5 V nominal | ECP5 auxiliary/config/PLL domains as required | Verify whether selected package splits PLL/aux rails. |
| `VCCIO_3V3` | 3.3 V | RP2350-facing banks, SPI flash, PMOD/test headers | All current southbridge links assume 3.3 V LVCMOS. |
| `VCCIO_OTHER` | TBD | Optional SDRAM/SDIO/SERDES-adjacent banks | Only add lower-voltage I/O rails when a concrete peripheral requires them. |
| `RP2350_3V3` | 3.3 V | RP2350, microSD, pullups, low-speed peripherals | May share the 3.3 V logic rail if noise and current budget are acceptable. |
| `USB_5V` / input | 5 V nominal | Regulator input | Include input protection and current budget for FPGA plus peripherals. |

Power design requirements:

- Do not drive FPGA I/O banks before their `VCCIO` rail is valid.
- Hold FPGA reset/configuration in a benign state until all required rails and
  the clock are stable.
- Provide independent measurement points for every rail.
- Add current-measurement options: zero-ohm link, current-sense resistor, or
  jumper footprint on at least input 5 V, 3.3 V logic, and ECP5 core.
- Place high-frequency decoupling at BGA power balls per vendor guidance, plus
  local bulk capacitance near each regulator and connector.
- Use solid ground and power planes. Do not split ground under clocks, SPI, PIO,
  flash, USB, or oscillator routing.

## 4. Clocking

Minimum evaluator clock target:

- One primary oscillator into an FPGA global clock-capable pin.
- 50 MHz nominal is preferred because current Artix bring-up uses a 50 MHz
  system clock model.
- LVCMOS oscillator level must match the selected ECP5 bank voltage.
- Route the oscillator trace short, direct, over continuous ground, with no
  stubs. Add series damping footprint near the oscillator output if recommended
  by the oscillator vendor.

Jitter requirement:

- No special low-jitter clock is required for the low-MHz SPI/PIO evidence path.
- If SERDES, external memory, or high-speed video is added, define those as
  separate clock-domain requirements and do not reuse this low-speed evaluator
  clock assumption.

Reset/config requirements:

- Add manual reset and RP2350-controlled reset/config lines.
- Expose FPGA `DONE`/configuration status to RP2350 and a test point or LED.
- Ensure JTAG remains usable regardless of RP2350 firmware state.

## 5. PIO Parallel Bus Timing Budget

The first PIO transport is write-first half-duplex. It prioritizes reliable
RP2350-to-FPGA table/config streaming over maximum raw bandwidth.

Target operating point:

| Item | Target |
|---|---:|
| First silicon clock | 1-2 MHz equivalent byte strobe |
| Bring-up target | 5-10 MHz byte strobe |
| Data width | 8 bits |
| Voltage | 3.3 V LVCMOS |
| Series damping | 22-47 ohm footprints near active drivers |
| PCB length match | Keep `DATA[7:0]` and `STROBE` in the same routing class; target <= 5 mm mismatch on-board |

Protocol-level timing:

- RP2350 drives `DIR/WE=write`, then drives `DATA[7:0]`.
- RP2350 waits at least one PIO cycle before asserting `STROBE`.
- FPGA captures the byte only after a synchronized `STROBE` event.
- RP2350 holds `DATA[7:0]` stable until FPGA asserts `READY`.
- RP2350 deasserts `STROBE`, then waits for `READY` to deassert before the next
  byte.

This handshake deliberately avoids tight source-synchronous setup/hold
assumptions during first silicon. The PCB should still route `DATA[7:0]` and
`STROBE` together so later faster modes have margin.

Layout requirements:

- Prefer contiguous RP2350 GPIO for `DATA[7:0]`.
- Put `STROBE`, `READY`, and `DIR/WE` physically adjacent to the data bus.
- Provide nearby ground return pins on any header/cable version.
- Avoid crossing voltage-bank boundaries on the FPGA unless the bank voltages
  are identical and explicitly documented.
- Add optional pull resistors so the bus is benign during RP2350 reset.

## 6. SPI Fallback Requirements

The SPI fallback is mandatory.

- FPGA is SPI slave, RP2350 is SPI master.
- Mode 0: CPOL=0, CPHA=0.
- Keep the known opcode model: `0xA0`, `0xA5`, `0xAC`, `0xAE`, `0xB1`.
- Route as short point-to-point signals, with series damping footprints near the
  driver side.
- Include test pads or analyzer-friendly header access.
- Keep SPI on pins separate from the parallel bus so failed PIO firmware cannot
  block recovery.

## 7. Symmetry / 12-Node Ring Constraint

The 12-node ring is an evaluator layout heuristic, not a substitute for normal
SI/PI design.

Target:

- Place the FPGA near the board center.
- Reserve a 12-node radial/ring test topology around the central FPGA region.
- Nominal radial trace length target: 25.0 mm.
- Initial tolerance target: +/- 0.5 mm for deliberately matched radial demo/test
  traces, or as tight as practical after BGA escape and DRC.

Do not compromise power integrity, clock routing, configuration routing, BGA
escape, or return paths to preserve the visual ring. Electrical correctness
wins over symmetry.

## 8. Minimum PCB Stackup

Recommended minimum: 4 layers.

Preferred stack:

1. Top signal/components
2. Solid ground plane
3. Power plane or split power pours with uninterrupted return strategy
4. Bottom signal/components

For ECP5-85F BGA escape, the EE may recommend 6 layers if fanout, rail
impedance, or routing density demands it. A 6-layer recommendation should be
treated as a cost/feasibility tradeoff, not a failure.

## 9. Deliverables

The EE deliverable is accepted only when all of the following exist:

- KiCad schematic with real ECP5, RP2350, regulators, flash, oscillator, JTAG,
  USB, headers, and test points.
- KiCad PCB with valid closed outline, routed nets, stackup notes, and design
  rules.
- ERC report with no unexplained errors.
- DRC report with no unexplained errors.
- BOM matched to schematic references and manufacturer part numbers.
- Fabrication package: Gerbers, drill files, pick-and-place, assembly drawing,
  and board render.
- Bring-up checklist: rail tests, JTAG IDCODE, configuration flash, RP2350 USB,
  SPI fallback loopback, PIO loopback, and first FPGA status read.
- Explicit list of any assumptions, substitutions, and unresolved risks.

## 10. Current Repo State To Know

- `hardware/docs/ecp5_oshwa_deliverable_audit.md` is the current readiness
  audit. It states that the KiCad package is not fab-ready.
- `hardware/docs/ecp5_oshwa_carrier_spec.md` describes the evaluator concept.
- `hardware/docs/parallel_transport_plan.md` defines SPI fallback plus PIO data
  plane intent.
- `docs/oshwa_application.md` is a draft only. It must not be submitted as a
  completed board certification until the KiCad package is real and ERC/DRC
  clean.
