# FPGA Board Scaling Strategy

Date: 2026-06-17

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
| Tang Primer 25K | Primary current bring-up board | Component proofs, silicon traces, RPLU/SOM/ROTC validation, SDRAM hydration | Full all-subsystem suite at once |
| Tang Primer 20K | Gowin DDR3 portability board | DDR3 bridge development, smaller SPU-13 profiles, memory experiments | Final integrated public kit |
| iCESugar Pro / ECP5 | Portability and open-toolchain validation board | ECP5 portability, SDRAM/display/network experiments, GPU/RPLU/SOM slices | Assuming Gowin primitive parity or full SPU-13 suite |
| Tang Mega 138K | Integrated suite board | Full visual SOM, RPLU, rotor, GPU, audio, memory, and multi-sector builds | Early bring-up risk reduction |

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
  `docs/visual_som_devboard_plan.md`
- SOM bring-up plan:
  `docs/som_bringup_plan.md`
- ROTC/Robotics bring-up plan:
  `docs/rotc_robotics_bringup_plan.md`
