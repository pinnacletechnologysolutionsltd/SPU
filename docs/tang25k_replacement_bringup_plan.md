# Tang Primer 25K Bring-Up Plan

Date: 2026-06-29 (updated)

The Tang Primer 25K FPGA board is healthy and is the primary bring-up and
subsystem-regression target. The original SDRAM module (W9825G6KH) has a
DQ[10] fault and has been retired — this was an external module fault, not
an FPGA or dock issue. The Wukong Artix-7 path is prepared for full RPLU2 +
Lucas MAC integration when the board is on the bench. The RP2040 and RP2350
remain active bench hardware for firmware, UART/JTAG, and SPI southbridge.

## Current Bench Work

The 25K serves as a subsystem regression target. Each probe is a
self-contained bitstream proving one aspect of the architecture:

| Probe | MATH | RPLU_V2 | LUTs | Proves |
|---|---|---|---|---|
| `southbridge_link` | 0 | 0 | ~350 | SPI protocol validation |
| `math_probe` | 1 | 0 | ~4,000 | ROTC, Davis, rotor |
| `rplu2_arith_probe` | 0 | 1 | ~6,282 | QLDI, QSUB, RPLU2 config |
| `lucas_mac_probe` | 0 | 0 | ~200 | PSCALE zero-drift |

1. Keep all split-build probes buildable:

   ```sh
   bash build_25k_spu13_math_probe.sh
   bash build_25k_spu13_southbridge_link.sh
   bash build_25k_spu13_rplu2_arith_probe.sh
   bash build_25k_spu13_lucas_mac_probe.sh
   ```

3. Keep the RP firmware images buildable:

   ```sh
   cmake -S hardware/rp2350 -B build/rp2350_modules_check -G Ninja \
     -DPICO_SDK_PATH="$PICO_SDK_PATH"
   ninja -C build/rp2350_modules_check \
     rp2350_uart_injector rp2350_spu_diag rp2350_spu_interface
   ```

4. Keep Piranha/Whisper PIO disabled for normal RP2350 builds. Enable them
   only in a scoped bench build after checking the pins with a scope or logic
   analyzer.

5. Use the RP2040 as a DirtyJTAG/programmer/debug pod. Do not fold JTAG, UART,
   SPI southbridge, SD, and sensors into one RP role until each lane has passed
   independently.

## Replacement Board Arrival Sequence

The first pass should avoid persistent FPGA flash writes. Load bitstreams into
FPGA SRAM until the board passes JTAG, UART, RPLU, and SDRAM checks.

### 1. Physical and USB Smoke

1. Inspect headers, dock seating, jumpers, and any add-on wiring. Start with no
   RP/sensor wiring attached.
2. Use the known-good USB 2.0 path for the Sipeed bridge.
3. Confirm the board appears:

   ```sh
   openFPGALoader --scan-usb
   ```

### 2. SRAM-Load the Active Math Probe

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

### 3. RPLU Flash-Load Proof

Use the proven RPLU probe artifact first:

```sh
tools/probe_tang25k_rplu_flash.py
```

Expected proof lines:

```text
B:D0EF4018 A:C
R:D28003FF A:D
R:00000803 A:E
R:<checksum> A:F
```

The checksum is read automatically from `build/rplu_metrics/` or
`build/rplu_boot_chords.bin` when present. See `docs/rplu_bringup_guard.md`
for the detailed decode.

### 4. RPLU + Math Probe

After the RPLU-only proof passes, load the RPLU+math artifact:

```sh
tools/probe_tang25k_rplu_flash.py \
  --bitstream build/tang_primer_25k_spu13_rplu_math_probe.fs
```

This confirms the flash-loaded RPLU table is being addressed by live SPU-13
math data, not only by the isolated boot/probe path.

### 5. SDRAM Proof on the Replacement Board

The damaged board requires a DQ mask. The replacement board should be tested
unmasked before accepting the dock/SDRAM path as healthy.

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

### 6. Silicon Feature Probes

Once config, UART, RPLU, and SDRAM are clean:

1. Run the ROTC/robotics silicon plan in `docs/rotc_robotics_bringup_plan.md`.
2. Run the SOM/BMU silicon plan in `docs/som_bringup_plan.md`.
3. Keep captures tied to the VM/RTL golden traces under `build/`.

### 7. RP2350 Southbridge Wiring

Only after the FPGA-side 25K baseline is stable:

1. Wire RP2350 UART injector to the proven `periph_rx` path and shared ground.
2. Use `rp2350_spu_diag.uf2` for SPI read-only commands after a Tang 25K top
   exposes `spu_spi_slave`.
3. Add `chord` writes, then RPLU hydration writes.
4. Add SD-card packs later through `spu_storage`; today the compiled fallback
   defaults in `hardware/rp_common/rplu_default_tables.h` are the only
   implemented RP-side table source.

## Board Role

The Tang 25K board is healthy. The retired SDRAM module means SDRAM-dependent tests are deferred to Wukong. The 25K remains useful for:

- RPLU flash image/probe regression.
- RP2350 UART injector testing against the known `B3` input path.
- RP2040 DirtyJTAG and USB enumeration practice.
- Risky PMOD/header wiring.
- SPI/diagnostic firmware work before connecting the replacement board.

Do not use the damaged board to certify unmasked SDRAM behavior. Its DQ[10]
fault makes it a controlled regression target, not a clean memory reference.

## Decision Gates

- No persistent `openFPGALoader -f` writes until SRAM-loaded smoke passes.
- No SD-card or RP-side SPI-flash dependency in first FPGA bring-up.
- No Whisper/Piranha PIO connection to FPGA until scoped on the RP board.
- No full southbridge boot dependency until JTAG, UART, SPI read-only, SPI
  write, and RPLU hydration have each passed separately.
- No Wukong hardware work until the Wukong board is physically present.

## Current Cleanup Item

The active root-level 25K build is `build_25k_spu13_math_probe.sh`. Several
older RPLU/SDRAM rebuild scripts and matching synthesis files are currently
under `hardware/boards/archive/`. Existing `build/*.fs` artifacts are enough
for first replacement-board proof, but fresh RPLU/SDRAM rebuilds should restore
or modernize those archived scripts before they are treated as canonical.
