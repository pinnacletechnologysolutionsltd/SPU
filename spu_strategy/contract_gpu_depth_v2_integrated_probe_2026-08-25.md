**Status:** COMPLETE — measured 2026-08-25

# Integrated Probe: Coverage + Depth-v2 + Reciprocal, Full Design

## Result
`build_25k_spu13_gpu_depth_v2_probe.sh` — spu_dual_raster (coverage,
tested) + spu_depth_dispatch (dispatcher, both units) + spu_reciprocal_core
+ spu_shared_mult35 (40x17) + two spu_attr_stepper instances, all in one
synthesis, not summed from separate probes:

| Resource | Used | Total | % |
|---|---|---|---|
| LUT4 | **9,635** | 23,040 | **41.8%** |
| ALU | 1,570 | 17,280 | 9.1% |
| DFF | 2,314 | 23,040 | 10.0% |
| DSP | 0 | 28 each | 0% |

Max frequency (final line): **44.54 MHz**, clean route. **13,405 LUT4
(58.2%) headroom.** Bitstream packaged, not flashed — area measurement,
not a silicon claim.

## What this resolves
The depth-v2 shared-multiplier architecture contract's §6 flagged the
FSM control logic, 256-entry ROM, and leading-one detector as
unmeasured on top of the isolated multiplier number. They're included
here: raster (1,317) + full depth-v2 subsystem (~8,318) = 9,635. The
subsystem costs more than "one multiplier" alone (3,532 at the earlier,
too-small 35x17 sizing) but the design still fits with substantial
margin. **No separate go/no-go question remains for Tang 25K capacity.**

## What this does NOT establish
- Not silicon-verified — synthesis/PNR only.
- No video PMOD exists on either target board in this repo (Tang 25K's
  .cst has no VGA/HDMI pins; A7's HDMI outputs are stubbed to zero in
  every existing top-level) — this was never a blocker for this
  measurement, since it's area-only, not a working display.
- The 44.54 MHz Fmax is this specific probe's stimulus pattern; real
  triangle-setup timing (multiple triangles/frame, real host cadence)
  is untested — throughput math in the shared-multiplier-arch contract
  §5 (~165ns/triangle setup) remains a reasoned estimate, not measured.

Related: `contract_gpu_depth_v2_shared_multiplier_arch_2026-08-25.md`,
`contract_gpu_raster_synth_probe_2026-08-25.md`,
`contract_gpu_mult35_corrected_probe_2026-08-25.md`.
