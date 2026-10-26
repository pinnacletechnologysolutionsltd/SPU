# Colorlight i9 (ECP5-45K) Feasibility Study

**Date:** 2026-07-06
**Evaluation:** Can Colorlight i9 become a useful SPU-13/RPLU2 ECP5 target?

## Executive Summary

**Answer: feasible as a lean open-toolchain ECP5 target, but not yet
hardware-proven.**

The Colorlight i9 now has a routed SPU-13/RPLU2 resource/timing probe using
Yosys, nextpnr-ecp5, and ecppack. The result is strong enough to justify buying
or using an i9 as a low-cost ECP5 portability board, but it is not a silicon
bring-up result until a physical module is flashed and smoke-tested.

The important constraint is DSP, not LUTs. The current RPLU2 probe consumes
every ECP5 multiplier block that nextpnr exposes for this 45K-class target.

## Measured Build

Commands:

```bash
bash hardware/boards/colorlight_i9/build_colorlight_i9_rplu2.sh synth
bash hardware/boards/colorlight_i9/build_colorlight_i9_rplu2.sh pnr
bash hardware/boards/colorlight_i9/build_colorlight_i9_rplu2.sh bitstream
```

Measured on 2026-07-06:

| Resource | Result |
|---|---:|
| Logic LUT4 | 3,477 |
| Carry LUT4 | 3,404 |
| Total LUT4 before packing | 6,881 / 43,848 (15%) |
| TRELLIS_COMB after packing | 7,271 / 43,848 (16%) |
| TRELLIS_FF | 1,967 / 43,848 (4%) |
| DP16KD BRAM | 0 / 108 |
| MULT18X18D DSP | 72 / 72 (100%) |
| Core timing | 44.05 MHz max, PASS at 25 MHz |
| Packaged bitstream | `build/spu_colorlight_i9_rplu2_top.bit` (297 KiB) |

P&R routing completed normally. Router time was about 426 seconds, which is
useful evidence in itself: the design fits and closes timing, but it is already
DSP-saturated and nontrivial to route.

## Practical Verdict

Use Colorlight i9 for:

- open ECP5 portability proof
- lean RPLU2/SPU-13 resource and timing experiments
- LED/clock/SPI smoke tests once the board arrives
- comparing ECP5 timing against the Artix-7 RPLU2PADE baseline

Do not use Colorlight i9 for:

- full concurrent SPU-13 plus Lucas/SU3/neuro/safety sidecars
- claims requiring DSP headroom
- board-level evidence until physical flash/smoke testing is complete

## Current Caveats

- The current i9 `.lpf` constrains the active probe I/O and allows one
  unconstrained flash-clock-style signal for P&R metrics.
- ECP5 configuration flash SCK/CCLK is not treated as an ordinary user I/O by
  this open-flow probe; a proper USRMCLK/configuration-clock path should be
  added before relying on on-board flash access.
- SPI southbridge readback is not yet the primary i9 proof path. First hardware
  smoke should be clock/LED/JTAG or programming-path validation.
- Physical Colorlight board revisions may differ from the community v7.2
  pinout. Verify the actual board before flashing.

## Recommendation

Colorlight i9 is worth acquiring after the Pico 2 if budget allows. It gives a
cheap, open-toolchain ECP5 proof target. The custom ECP5-85F board remains the
proper funded/EE-designed evaluator path, and Artix/Kintex remain the better
targets for full concurrent arithmetic integration.
