# Neuro-Safe Sidecar Plan

Date: 2026-06-30

This track turns the Tang 25K sidecar idea into an auditable hardware feature:
a deterministic epoch controller lets a small digital spiking field propose a
token vector, while algebraic guard logic decides whether the proposal can
commit.

This does not make SPU-13 a neuromorphic processor. The SPU-13 role is the
deterministic guard and commit boundary around event-driven or adaptive
proposal engines. See `docs/SPU13_IDENTITY_AND_BOUNDARIES.md` for the canonical
architecture boundary.

## Current RTL And Tang Probe Proof

Module: `hardware/rtl/core/spu13/spu13_neuro_epoch_sidecar.v`
Adapter: `hardware/rtl/core/spu13/spu13_neuro_sidecar_adapter.v`

Verified by:

- `hardware/tests/spu13/spu13_neuro_epoch_sidecar_tb.v`
- `hardware/tests/spu13/spu13_tang25k_neuro_guard_probe_tb.v`
- `hardware/tests/spu13/spu13_neuro_sidecar_adapter_tb.v`
- `hardware/tests/spu13/spu13_tang25k_neuro_sidecar_probe_tb.v`

Focused regression: `TB_FILTER=neuro python3 run_all_tests.py`

Tang probe: `hardware/boards/tang_primer_25k/spu13_tang25k_neuro_guard_probe.v`
Adapter probe:
`hardware/boards/tang_primer_25k/spu13_tang25k_neuro_sidecar_probe.v`

Build: `bash build_25k_spu13_neuro_guard_probe.sh`
Adapter build: `bash build_25k_spu13_neuro_sidecar_probe.sh`

The current block proves the bounded version of the architecture:

- Fixed epoch length, configured by `EPOCH_CYCLES`.
- Synchronous digital leaky-integrate-and-fire updates.
- Hard clamp of all membrane state at the epoch boundary.
- Spike counter projection into `a+b*phi` over `Z[phi]/L_p`.
- Lucas norm check `a^2 + ab - b^2 mod L_p`.
- Fallback commit when the norm mismatches or a token counter saturates.

This is deliberately not an asynchronous fabric proof. The first hardware
target should stay synchronous so timing, reset, replay, and fault telemetry are
boring.

The standalone Tang 25K probe now routes, packages, and SRAM-loads:

- 5,016 LUT4 / 358 DFF with `synth_gowin -noalu`.
- 0 BRAM / 0 DSP / 0 ALU carry cells.
- 33.27 MHz post-route max frequency at the 12 MHz probe target.
- Bitstream: `build/tang_primer_25k_spu13_neuro_guard_probe.fs`.
- Captured UART after SRAM load:
  `N:P T:4 P:003/003 K:009 C:007/008 E:00`.

The `-noalu` setting is intentional for this Tang regression image. The first
compact ALU-mapped image produced the correct proposal vector but reported an
incorrect norm on hardware; the no-ALU image matches RTL simulation and the
board UART signature above.

The SPI-visible Tang adapter probe is also hardware-verified:

- 4,013 LUT4 / 380 DFF with no BRAM, no DSP, and no ALU carry cells.
- 99.53 MHz post-route max frequency at the 12 MHz probe target.
- Bitstream: `build/tang_primer_25k_spu13_neuro_sidecar_probe.fs`.
- Captured UART after SRAM load: `N:P T:3 E:00`.

This adapter self-drives the command opcodes that will be exposed through the
southbridge: `0xE0` (`NEURO_CFG`), `0xE1` (`NEURO_START`), `0xE2`
(`NEURO_SPIKE`), and `0xE3` (`NEURO_READ`). The proof covers accept/readback,
reject/fallback, and saturated-counter overflow fallback.

## What Is Not Claimed Yet

- No external RP2350 master has driven these neuro opcodes through the full
  shared southbridge shell yet; the Tang adapter probe is self-driven.
- No actuator-safe quadray guard is attached yet.
- The Lucas norm protects the phinary token vector only; physical quadray
  updates still need Davis/Quadray/RPLU2 guard logic before driving motors or
  other external effects.

## Bring-Up Path

1. Keep the RTL proof in the generic test suite.
2. Keep the Tang 25K `neuro_guard_probe` in the split-build regression ladder.
3. Keep the Tang 25K `neuro_sidecar_probe` in the split-build regression
   ladder for SPI-visible epoch start, threshold/weight load, expected norm,
   fallback vector, spike injection, and commit readback.
4. Promote the adapter to an Artix `NEURO_SAFE` spin after JTAG, clock/reset,
   SPI status, QLDI/QSUB, RPLU2, and Lucas sidecar smoke tests are stable.
5. Add quadray/Davis guard composition before any spatial or actuator-facing
   commit path.

Tang 25K remains the probe/regression board. Wukong Artix-7 remains the
integrated system target.
