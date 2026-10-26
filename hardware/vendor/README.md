# hardware/vendor — FPGA Vendor Primitives

This directory contains FPGA-family-specific primitives and vendor-optimised
modules. Nothing in `hardware/common/rtl/` depends on files here.

## Structure

```
vendor/
  gowin/    Gowin Semiconductor (GW1N, GW2A, GW5A)
  ice40/    Lattice iCE40 simulation stubs
```

## gowin/

| File | Purpose |
|------|---------|
| `gowin_bsram.v` | GW1N-9C SDPB block RAM wrapper |
| `spu_surd_mul_gowin.v` | Q(√3) surd multiplier using Gowin DSP blocks |
| `spu_alu_gowin.v` | Parallel 13-axis ALU using Gowin DSP (alternative to the portable TDM ALU) |

**Note:** `gowin_mult18.v` remains in `hardware/common/rtl/prim/` because it
has a `DEVICE="SIM"` fallback path (pure inferred multiply) used by
`davis_gate_dsp.v` during simulation and for non-Gowin synthesis targets.
It is a multi-target DSP wrapper, not a Gowin-only primitive.

## ice40/

| File | Purpose |
|------|---------|
| `SB_HFOSC.v` | Simulation stub for the iCE40 internal HF oscillator primitive |

## Porting to a new FPGA family

1. Create `vendor/<family>/` directory.
2. Add a `<family>_mult18.v` (or equivalent) that matches the `gowin_mult18`
   port signature — see `hardware/common/rtl/prim/gowin_mult18.v` for the
   interface contract.
3. Set `DEVICE="<family>"` on `davis_gate_dsp` in your board top-level.
4. Add the new vendor path to `run_all_tests.py` include dirs.

The `hardware/common/rtl/` tree compiles with DEVICE="SIM" on any toolchain
without any vendor files.
