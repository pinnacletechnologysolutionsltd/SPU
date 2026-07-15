# Tang Primer 25K Regression Plan

Date: 2026-07-01 (updated)

The Tang Primer 25K FPGA board is healthy and remains the subsystem-regression
and risky-wiring target. It is no longer the primary full-core integration
target. The original SDRAM module (W9825G6KH) has a DQ[10] fault and has been
retired; this was an external module fault, not an FPGA or dock issue.

The Wukong Artix-7 100T path is now the primary Artix silicon-evidence and
constrained integration target. Full concurrent RPLU2 + Lucas MAC + sidecar
integration belongs on an Artix-7 200T / Kintex-class board. The RP2040 and
RP2350 remain active bench hardware for firmware, UART/JTAG, and SPI
southbridge work.

## Bring-Up Closeout

Status as of 2026-07-01: Tang Primer 25K bring-up is complete for the intended
regression-board role. The board enumerates through the Sipeed FTDI2232 bridge,
accepts SRAM loads through `openFPGALoader -b tangprimer25k`, and has a closed
split-probe ladder for southbridge SPI, RPLU2 arithmetic, Lucas fast paths,
ROTC, six-step robotics, SOM/BMU, and neuro-safe sidecar checks.

Final closeout checks:

| Check | Result |
|---|---|
| USB/JTAG scan | `openFPGALoader --scan-usb` sees `SIPEED 2025030317 USB Debugger` |
| Feature bitstreams present | Southbridge, RPLU2 arithmetic, Lucas, ROTC, six-step, SOM/BMU, neuro guard, and neuro adapter `.fs` images are in `build/` |
| Final UART soak | 40-second `/dev/ttyUSB2` capture from `six_step_probe` stayed on `KIN:P P:5 E:00` |

Do not expand the Tang role into full concurrent SPU-13 integration. The 25K is
now a closed regression ladder and risky-wiring bench target. Full RPLU2 +
Lucas + wider safety integration moves to Wukong Artix-7.

## Current Bench Work

The 25K serves as a subsystem regression target. Each probe is a
self-contained bitstream proving one aspect of the architecture:

| Probe | MATH | RPLU_V2 | LUTs | Proves |
|---|---|---|---|---|
| `southbridge_spi_probe` | 0 | 0 | 1,861 LUT4 | SPI electrical/protocol smoke without core |
| `southbridge_link` | 0 | 0 | 4,054 LUT4 | SPI protocol validation with dormant core attached |
| `math_probe` | 1 | 0 | ~4,000 | ROTC, Davis, rotor |
| `rplu2_arith_probe` | 0 | 1 | 9,211 LUT4 | QLDI, QSUB, RPLU2 config, CRC-8 writes, ECC regfile |
| `lucas_mac_probe` | 0 | 0 | 696 LUT4 | PSCALE/PCHIRAL zero-drift |
| `rotc_probe` | 0 | 0 | 13,352 LUT4 | Corrected ROTC 0-5 trace and period closure |
| `six_step_probe` | 0 | 0 | 13,576 LUT4 | Period-6 six-step robotics closure and inverse recovery |
| `som_bmu_probe` | 0 | 0 | 13,189 LUT4 | Weighted SOM/BMU classification and cluster reduction |
| `neuro_guard_probe` | 0 | 0 | 5,016 LUT4 | Fixed-epoch neuro guard, Lucas norm admission, fallback |
| `neuro_sidecar_probe` | 0 | 0 | 4,013 LUT4 | SPI-visible neuro adapter opcodes, readback, overflow fallback |

2026-06-30 southbridge result: both split southbridge probes were rebuilt after
hardening the RP CRC helper and the FPGA `0xA5` write receiver. The SPI-only
probe reports `status raw=25 A5 00 00`; manual `rplu` advances `cfgtele` to
count 1; and SD hydration advances count 0 to 16 with checksum `0x3A0AB5E9`.
The core-attached probe reports `status raw=13 A5 00 00` and passes the same
manual write and SD hydration checks. Keep these as the first two Tang
regression rungs before loading math or RPLU2 images.

2026-06-30 neuro sidecar adapter result: `build_25k_spu13_neuro_sidecar_probe.sh`
routes at 4,013 LUT4 / 380 DFF, no BRAM, no DSP, no ALU carry cells, and
99.53 MHz post-route max frequency at the 12 MHz target. SRAM load reports
stable UART `N:P T:3 E:00`, proving the self-driven `0xE0` config, `0xE1`
start, `0xE2` spike, and `0xE3` QR readback adapter path.

2026-06-30 Lucas fast-path result: `build_25k_spu13_lucas_mac_probe.sh`
routes at 696 LUT4 / 216 DFF / 416 ALU, no BRAM, no DSP, and 126.50 MHz
post-route max frequency at the 12 MHz target. SRAM load reports stable UART
`LUCAS:P`, proving PSCALE, PCHIRAL, and a 100-period PSCALE zero-drift
marathon. This is a `FAST_ONLY=1` Tang proof; PMUL/PINV silicon coverage remains
separate.

2026-06-30 ROTC result: `build_25k_spu13_rotc_probe.sh` routes at
13,352 LUT4 / 1,036 DFF / 1,044 ALU, no BRAM, no DSP, and 73.07 MHz post-route
max frequency at the 12 MHz target. SRAM load reports stable UART
`ROTC:P A:5 E:00`, proving corrected ROTC angles 0-5 on the canonical VM/RTL
trace vector plus period closure for all non-identity angles.

2026-07-01 six-step robotics result: `build_25k_spu13_six_step_probe.sh`
routes at 13,576 LUT4 / 1,518 DFF / 1,024 ALU, no BRAM, no DSP, and 77.25 MHz
post-route max frequency at the 12 MHz target. SRAM load reports stable UART
`KIN:P P:5 E:00`, proving period-6 six-step forward kinematics, angle-4
inverse recovery per phase, early-closure rejection, and exact phase-5 closure.

2026-06-30 SOM/BMU result: `build_25k_spu13_som_bmu_probe.sh` routes at
13,189 LUT4 / 959 DFF / 1,130 ALU, no BRAM, no DSP, and 84.75 MHz post-route
max frequency at the 12 MHz target. SRAM load reports stable UART
`SOM:P T:2 B:6 E:00`, proving two weighted seven-node SOM/BMU oracle scenarios
and cluster reduction in silicon.

1. Keep all split-build probes buildable:

   ```sh
   bash build_25k_southbridge_spi_probe.sh
   bash build_25k_spu13_southbridge_link.sh
   bash build_25k_spu13_math_probe.sh
   bash build_25k_spu13_rplu2_arith_probe.sh
   bash build_25k_spu13_lucas_mac_probe.sh
   bash build_25k_spu13_rotc_probe.sh
   bash build_25k_spu13_six_step_probe.sh
   bash build_25k_spu13_som_bmu_probe.sh
   bash build_25k_spu13_neuro_guard_probe.sh
   bash build_25k_spu13_neuro_sidecar_probe.sh
   ```

2. Keep the RP firmware images buildable:

   ```sh
   cmake -S hardware/rp2350 -B build/rp2350_modules_check -G Ninja \
     -DPICO_SDK_PATH="$PICO_SDK_PATH"
   ninja -C build/rp2350_modules_check \
     rp2350_uart_injector rp2350_spu_diag rp2350_spu_interface
   ```

3. Keep Piranha/Whisper PIO disabled for normal RP2350 builds. Enable them
   only in a scoped bench build after checking the pins with a scope or logic
   analyzer.

4. Use the RP2040 as a DirtyJTAG/programmer/debug pod. Do not fold JTAG, UART,
   SPI southbridge, SD, and sensors into one RP role until each lane has passed
   independently.

## Optional Fresh-Board Sanity Sequence

If a fresh Tang 25K is used, keep it as a sanity/regression board. The first
pass should avoid persistent FPGA flash writes. Load bitstreams into FPGA SRAM
until the board passes JTAG, UART, RPLU, and any SDRAM checks that still matter
for regression.

### 1. Physical and USB Smoke

1. Inspect headers, dock seating, jumpers, and any add-on wiring. Start with no
   RP/sensor wiring attached.
2. Use the known-good USB 2.0 path for the Sipeed bridge.
3. Confirm the board appears:

   ```sh
   openFPGALoader --scan-usb
   ```

### 2. SRAM-Load the SPI-Only Smoke Probe

Build and SRAM-load the minimal SPI-only 25K probe:

```sh
bash build_25k_southbridge_spi_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_southbridge_spi_probe.fs
```

This checks FPGA configuration, reset, the J4 SPI electrical path, and the
`spu_spi_slave` protocol without instantiating the SPU-13 core.

Do not use `-f` here. `-f` writes persistent configuration flash and should
wait until the SRAM-loaded image has passed.

### 3. SRAM-Load the Core-Attached Southbridge Probe

Build and SRAM-load the southbridge image with the dormant SPU-13 core attached:

```sh
bash build_25k_spu13_southbridge_link.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_southbridge_link.fs
```

This proves the same SPI path remains healthy when the real board top and core
integration shell are present.

### 4. SRAM-Load the Active Math Probe

Build and SRAM-load the active root-level 25K probe:

```sh
bash build_25k_spu13_math_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_math_probe.fs
```

Open the FTDI UART at 115200 baud and capture the math/HEX telemetry. This
checks FPGA configuration, clock/reset, UART TX, QLDI, rotor/Davis math, and
the basic sequencer path before any external memory is involved.

Do not use `-f` here. `-f` writes persistent configuration flash and should
wait until the SRAM-loaded image has passed.

### 5. RPLU Flash-Load Proof

Use the proven RPLU probe artifact first:

```sh
tools/probe_tang25k_rplu_flash.py
```

Expected proof lines:

```text
B:D0EF4018 A:C
R:D28003FF A:D
R:00000095 A:E
R:<checksum> A:F
```

The checksum is read automatically from `build/rplu_metrics/` or
`build/rplu_boot_chords.bin` when present. See `docs/archive/legacy/rplu_bringup_guard.md`
for the detailed decode.

### 6. RPLU + Math Probe

After the RPLU-only proof passes, load the RPLU+math artifact:

```sh
tools/probe_tang25k_rplu_flash.py \
  --bitstream build/tang_primer_25k_spu13_rplu_math_probe.fs
```

This confirms the flash-loaded RPLU table is being addressed by live SPU-13
math data, not only by the isolated boot/probe path.

### 7. SDRAM Proof on a Fresh Board

The damaged SDRAM module requires a DQ mask. A fresh board/module should be
tested unmasked before accepting the dock/SDRAM path as healthy.

Start with an SDRAM-only or RPLU+math+SDRAM artifact, then move to the full
probe once the low-level memory check is clean:

```sh
tools/probe_tang25k_rplu_flash.py \
  --bitstream build/tang_primer_25k_spu13_rplu_full_probe.fs \
  --expect-sdram-selftest
```

Expected full-probe SDRAM values on a healthy board:

```text
endpoints: 0x5D005D33
checksum:  0x0012E92E
```

If DQ[10] or any other bit fails on the replacement board, treat it as a new
hardware fault and stop before using SDRAM as a bring-up dependency.

### 8. Silicon Feature Probes

For repeated regression, use SRAM loads and check the following known-good
feature signatures:

1. SRAM-load `build/tang_primer_25k_spu13_rotc_probe.fs`; this is
   hardware-verified with UART `ROTC:P A:5 E:00`.
2. SRAM-load `build/tang_primer_25k_spu13_six_step_probe.fs`; this is
   hardware-verified with UART `KIN:P P:5 E:00`.
3. Continue the remaining generalized robotics work in
   `docs/rotc_robotics_bringup_plan.md` only when it is part of a new feature
   target, not basic Tang bring-up.
4. SRAM-load `build/tang_primer_25k_spu13_som_bmu_probe.fs`; this is
   hardware-verified with UART `SOM:P T:2 B:6 E:00`.
5. SRAM-load `build/tang_primer_25k_spu13_lucas_mac_probe.fs`; this is
   hardware-verified with UART `LUCAS:P`.
6. SRAM-load `build/tang_primer_25k_spu13_neuro_guard_probe.fs`; this is
   hardware-verified with UART `N:P T:4 P:003/003 K:009 C:007/008 E:00`.
7. SRAM-load `build/tang_primer_25k_spu13_neuro_sidecar_probe.fs`; this is
   hardware-verified with UART `N:P T:3 E:00`.
8. Keep captures tied to the VM/RTL golden traces under `build/`.

### 9. RP2350 Southbridge Wiring

Only after the FPGA-side 25K baseline is stable:

1. Wire RP2350 UART injector to the proven `periph_rx` path and shared ground.
2. Use `rp2350_spu_diag.uf2` for SPI read-only commands after a Tang 25K top
   exposes `spu_spi_slave`.
3. Add `chord` writes, then RPLU hydration writes.
4. Add SD-card packs later through `spu_storage`; today the compiled fallback
   defaults in `hardware/rp_common/rplu_default_tables.h` are the only
   implemented RP-side table source.

## Board Role

The Tang 25K board is healthy. The retired SDRAM module means SDRAM-dependent
integration tests are deferred to Wukong. The 25K remains useful for:

- Southbridge SPI and RP2350 regression.
- QLDI/QSUB/QR commit readback smoke tests.
- RPLU2 table hydration regression.
- Small math/Lucas/neuro/ROTC/robotics/SOM probe bitstreams.
- RP2350 UART injector testing against the known `B3` input path.
- RP2040 DirtyJTAG and USB enumeration practice.
- Risky PMOD/header wiring.
- SPI/diagnostic firmware work before connecting Wukong.

The 25K should not be used for full concurrent RPLU2 integration, publication
area claims for the final core, or architecture decisions driven by LUT
starvation.

Do not use the damaged board to certify unmasked SDRAM behavior. Its DQ[10]
fault makes it a controlled regression target, not a clean memory reference.

## Decision Gates

- No persistent `openFPGALoader -f` writes until SRAM-loaded smoke passes.
- No SD-card or RP-side SPI-flash dependency in first FPGA bring-up.
- No Whisper/Piranha PIO connection to FPGA until scoped on the RP board.
- No full southbridge boot dependency until JTAG, UART, SPI read-only, SPI
  write, and RPLU hydration have each passed separately.
- No persistent Wukong configuration-flash writes until SRAM-loaded JTAG, reset,
  UART, and southbridge smoke tests pass.

## Closeout Boundary

No open Tang board bring-up blocker remains. Remaining open items are explicitly
not Tang bring-up gates:

- Unmasked SDRAM confidence requires a fresh SDRAM module or a different board.
- Full concurrent RPLU2 + Lucas + safety integration belongs on Artix-7.
- Generalized robotics FK/IK, RPLU trajectory correction, and live actuator
  loops are feature work.
- PMUL/PINV silicon capture is an Artix-7 or future dedicated Tang PMUL/PINV
  probe task.
