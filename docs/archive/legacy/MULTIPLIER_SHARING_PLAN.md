# M31 Multiplier Sharing: RPLU v2 Pipeline + SU(3)

Shares one `spu13_m31_multiplier` between the RPLU v2 Padé path and the SU(3)
complex multiply sidecar, eliminating the second M31 multiplier instance that a
fully integrated SU3 image would otherwise need.

## Previous Architecture

```
RPLU v2 pipeline:       SU(3) sidecar:
  u_mult_pade             u_mult      <- private M31 copy
  u_mult_inv
```

On Artix-7, one `spu13_m31_multiplier` maps to 64 DSP48E1 cells because the
logical 16-product M31 datapath is built from 32x32 products. A private SU(3)
copy would therefore add another 64 DSP48E1 cells to an integrated image.

## Shared Architecture

```
Pipeline:
  u_mult_pade   <- muxed: pipeline OR SU(3)
  u_mult_inv    <- dedicated to pipeline when live evaluator is enabled

SU(3): no private integrated multiplier; borrows the top-level shared instance.
```

The mux lives in `spu_a7_top.v`. SU3 owns the multiplier while `su3_busy` is
high; otherwise the core/RPLU Padé path owns it. The result bus fans out to both
consumers, and only the active owner sees `done`.

## Implementation

### `spu13_su3_mult.v`
- Done: external multiplier ports: `m_start`, `m_a0-3`, `m_b0-3`, `m_r0-3`,
  `m_done`, and `m_busy`.
- Done: same 4-phase TDM FSM; it now drives external signals instead of
  relying on a fixed private multiplier.

### `spu13_su3_sidecar.v`
- Done: `EXTERNAL_MULT` selects between standalone private multiplier mode and
  integrated external multiplier mode.

### `rplu_pipeline.v`
- Done: `EXTERNAL_PADE_MULT` lets the Padé multiplier be driven from the
  integration layer instead of instantiated privately.

### `spu13_core.v`
- Done: `EXTERNAL_RPLU_PADE_MULT` exposes the RPLU Padé multiplier interface to
  the Artix top-level integration.

### `spu_a7_top.v`
- Done: `SU3SHARE` spin.
- Done: one top-level `spu13_m31_multiplier`.
- Done: ownership mux between SU3 and core/RPLU Padé path.
- Done: sidecar status mux fix so `SU3SHARE` exposes SU3 progress through
  `CMD 0xAC` even though the main core is also instantiated.

## Resource Result

| Case | M31 multiplier instances | Artix-7 DSP48E1 |
|---|---:|---:|
| Standalone SU3 proof | 1 private SU3 instance | 64 |
| Integrated SU3 plus private RPLU Padé copy | 2 instances | 128 |
| `SU3SHARE` shared path | 1 shared top-level instance | 64 |

The current `SU3SHARE` routed image uses 64 DSP48E1 cells total for the shared
M31 path. Whole-image route metrics at `A7_FREQ=2 A7_CLK_DIV_LOG2=6` are 60,837
LUTX cells, 16,478 FFX cells, and 64 DSP48E1 cells.

## Status

Implemented and silicon-proven as the Artix `SU3SHARE` spin.

- Simulation: `TB_FILTER=spu13_su3 python3 run_all_tests.py` passes, and
  `spu13_spi_su3share_tb.v` passes.
- Artix build: `su3share` synth, P&R, and pack pass at the 2 MHz bring-up
  target.
- Silicon: `build/spu_a7_100t_SU3SHARE.bit` loads on Wukong Artix-7 and passes
  both `SU3_J11: PASS` and the RPLU2 config/QR regression
  (`RPLU2_J11: PASS`, `RPLU2CORE_QR: PASS`, `RPLU2CORE_QSUB: PASS`).
- Bitstream SHA-256:
  `4dff1a6e5fbbfc2f10afca0afd5ff08846727a6b0b3571eb76deb755aafb80ed`.

The current proof keeps the live RPLU2 Padé evaluator disabled
(`_R2_PIPELINE=0`). It validates the external multiplier topology and same-image
SU3/RPLU2 config coexistence. The next architectural step is enabling the live
Padé pipeline and adding explicit arbitration if SU3 and Padé requests can
overlap.
