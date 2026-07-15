# FPGA Board Scaling Strategy

Date: 2026-07-05

This document defines the practical FPGA ladder for SPU-13 development. The
goal is to keep bring-up moving on available boards while reserving the larger
targets for the full concurrent suite.

## Core Decision

Use the Tang Primer 25K as the primary component-proof board.

The 25K does not need to run every SPU-13 subsystem at once. Its job is to prove
each subsystem with deterministic traces:

- QLDI / Quadray register hydration
- ROTC / six-step rational rotation
- SOM BMU classification
- RPLU Morse lookup and runtime update
- SDRAM hydration on a replacement board
- UART / visual telemetry frames
- GPU raster and audio proof slices

The larger boards become necessary when those components must run concurrently
with fewer compile-time exclusions.

## Board Roles

| Board | Role | Use It For | Avoid Using It For |
|---|---|---|---|
| Tang Primer 25K | Primary closed-regression probe target | Component proofs, silicon traces, RPLU/SOM/ROTC/Lucas/neuro slice probes, RP2350 SPI southbridge | Full concurrent suite — LUT budget too tight |
| Wukong Artix-7 100T | Artix silicon-evidence and constrained integration | LUCAS/SU3/ROBOTICS/RPLU2CORE/RPLU2PADE J11 proofs, shared-multiplier baseline, lean RPLU2 live-evaluator | Full concurrent live RPLU2 plus all sidecars/safety at once |
| Colorlight i9 (ECP5-45F) | Open-toolchain ECP5 portability | Routed lean RPLU2 ECP5 proof, SDRAM/Ethernet experiments, cheap warm spare | Full concurrent core — current RPLU2 probe already uses 72/72 DSPs |
| Kintex-7 K7-480T PCIe (YZCA-00338) | Full-integration + PCIe proof | Full concurrent SPU-13/RPLU2/sidecar/safety images, PCIe host interface, 4GB DDR3 SDRAM | Early bring-up — wait for closed Artix ladder and a suitable host PC |
| Raspberry Pi Pico 2 | RP2350 transport reference | PIO transport, cleaner southbridge wiring, repeatable USB/SPI/JTAG experiments | Treating transport speed as a reason to disturb the current known-good Wukong J11 proof |

## Acquisition Order

The practical order is:

1. **Raspberry Pi Pico 2 first.** It is the cheapest useful upgrade and reduces
   wiring friction for RP2350 PIO transport without changing the FPGA evidence
   path.
2. **Colorlight i9 next.** It is the best low-cost open-toolchain portability
   target while the custom ECP5-85K evaluator remains EE/funding dependent.
   Use it to prove a lean ECP5 subset, not the full concurrent SPU-13 suite.
3. **Kintex-7 last by default.** The used PCIe card is attractive for full
   integration, but it also requires a suitable host PC, power budget, cooling,
   constraint discovery, and higher bring-up risk. Move it earlier only if a
   verified card appears cheaply enough to treat as a gamble.

This order does not block the papers: current Tang and Wukong evidence is
already sufficient for the central SPU-13, RPLU v2, Lucas, and SU3 preprints.

## Tang Primer 25K

This remains the near-term board. The project already has extensive 25K scripts,
tests, and hardware evidence. The replacement board should be used first for:

1. SPI flash and RPLU pack proof.
2. SDRAM hydration proof.
3. ROTC silicon trace.
4. SOM_CLASSIFY silicon trace.
5. Runtime RPLU material update.
6. Visual telemetry frame output.

The full rotor core has already pushed the 25K near the edge, so the 25K should
be treated as a modular proof platform. Build small, explicit bitstreams for
each subsystem instead of chasing one oversized image.

## iCESugar Pro / ECP5

iCESugar Pro is interesting because it gives the project an ECP5 portability
target with SDRAM, flash, USB CDC/JTAG, display-capable I/O, and a fully open
Yosys/nextpnr flow.

Use it if the project needs:

- proof that SPU-13 is not locked to Gowin
- a display-heavy deterministic visual board
- SDRAM experiments without depending on the damaged Tang 25K
- a public-friendly open-toolchain demo target

Repository note: the current `hardware/boards/icesugar/` target is the older
iCE40UP5K iCESugar v1.5 class, not iCESugar Pro. If iCESugar Pro is selected,
add a dedicated `hardware/boards/icesugar_pro/` ECP5 target rather than
overloading the existing iCE40 target name.

Good first iCESugar Pro subsets:

- Bresenham-killer GPU raster slice
- SOM BMU visual map emitter
- RPLU lookup subset with flash-backed tables
- UART/USB visual telemetry bridge
- SDRAM smoke test and trace capture

## Colorlight i9 / ECP5-45F

The Colorlight i9 is now the preferred low-cost ECP5 portability board. It has
enough capacity for a lean SPU-13/RPLU2 subset, and the current RPLU2 probe now
synthesizes, routes, and packs with the open ECP5 flow. It is still not
equivalent to the Artix tree:

- `hardware/boards/ecp5_85k/spu_ecp5_top.v` is still an integration placeholder.
- The southbridge parser/result path must be wired before J11-style smoke tests
  can be repeated.
- The current i9 RPLU2 probe consumes 72/72 `MULT18X18D` cells, so the i9 has
  useful LUT headroom but no DSP headroom for Lucas/SU3/safety sidecars.
- The flash-clock path is still a configuration-clock/USRMCLK issue, not a
  normal unconstrained user-I/O problem.

Measured i9 RPLU2 probe, 2026-07-06:

| Metric | Result |
|---|---:|
| Total LUT4 before packing | 6,881 / 43,848 (15%) |
| TRELLIS_COMB after packing | 7,271 / 43,848 (16%) |
| TRELLIS_FF | 1,967 / 43,848 (4%) |
| MULT18X18D | 72 / 72 (100%) |
| DP16KD | 0 / 108 |
| Timing | 44.05 MHz max core clock, PASS at 25 MHz |

Recommended i9 milestone:

1. Flash the current RPLU2 probe when physical hardware is available.
2. Confirm clock/LED/programming smoke before adding more I/O.
3. Add SPI status and QR commit readback.
4. Compare ECP5 resource/timing against the cleaned Artix `RPLU2PADE` baseline:
   20,277 Artix slice LUTs, 6,678 FFs, 72 DSP48E1, 0 BRAM, 36.54 MHz
   post-route `clk_fast` in the 2 MHz bench image.

## Tang Mega 138K

Tang Mega 138K is the correct target for the full complementary suite. It should
not be required before the 25K component proofs are done.

Use it when the project is ready to integrate:

- multiple SPU-13 sectors
- full SOM/RPLU/ROTC concurrent pipeline
- visual maps and GPU raster path
- anharmonic Morse audio path
- large flash/RAM-backed table sets
- memory-tier arbitration experiments
- public demo images that show the whole processor as a system

The repository already has a `hardware/boards/gowin_mega/` skeleton. That should
remain a later integration target until the smaller proofs are trace-clean.

## Custom KiCad Boards

Do not start with a full custom BGA FPGA board. That is a manufacturing project,
not a bring-up shortcut.

Recommended hardware sequence:

1. Dev-kit v0: existing commercial FPGA boards plus PMODs, display bridge, and
   pre-flashed RPLU SPI flash.
2. Dev-kit v0.1: custom KiCad carrier board around a known FPGA module or dev
   board. Include display connector, RP2040/RP2350 bridge, SPI flash socket,
   UART/USB debug, PMODs, power rails, test pads, and clear labels.
3. Dev-kit v1: production open carrier board once the telemetry ABI and boot
   procedure are stable.
4. Dev-kit v2: custom FPGA board only after paid beta evidence, assembly quotes,
   failure data, and support requirements are known.

This keeps the first public kit buildable and serviceable while still moving
toward OSHWA certification.

## Public Kit Strategy

The first public kit should be a deterministic robotics / geometry kit, not a
claim that one small board runs every possible SPU-13 subsystem.

Minimum public kit proof:

- bootable bitstream from source
- pre-flashed RPLU periodic pack
- deterministic UART/USB telemetry
- visual SOM/RPLU/Davis/rotor host renderer
- one robotics trace: commanded path, injected error, inverse correction,
  corrected path
- one GPU/raster visual trace
- one Morse/RPLU sonification or material lookup trace
- clear known-limitations page

The kit can then be sold as an open deterministic processor development kit,
with larger boards documented as expansion targets.

## Immediate Actions

1. Finish Tang 25K component bring-up on the replacement board.
2. Keep all new demos trace-first: VM, RTL, FPGA, then visual replay.
3. Rebuild the six-step rational robotics kinematics harness — see `docs/rotc_robotics_bringup_plan.md`.
4. Prove SOM BMU classifier in simulation and silicon — see `docs/som_bringup_plan.md`.
5. Add a host visual renderer for SOM/RPLU/Davis/rotor frames.
6. Add `hardware/boards/icesugar_pro/` only if an iCESugar Pro is purchased.
7. Keep `hardware/boards/gowin_mega/` as the full-suite integration target.
8. Draft KiCad carrier requirements after the visual telemetry ABI stabilizes.

## References

- Tang Mega 138K Dock documentation:
  https://wiki.sipeed.com/hardware/en/tang/tang-mega-138k/mega-138k.html
- iCESugar Pro repository:
  https://github.com/wuxx/icesugar-pro
- Commercialization roadmap:
  `docs/commercialization_and_development_roadmap.md`
- Visual SOM devboard plan:
  `docs/archive/legacy/visual_som_devboard_plan.md`
- SOM bring-up plan:
  `docs/som_bringup_plan.md`
- ROTC/Robotics bring-up plan:
  `docs/rotc_robotics_bringup_plan.md`
