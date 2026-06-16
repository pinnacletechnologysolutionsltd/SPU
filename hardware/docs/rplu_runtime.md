# RPLU runtime configuration & uploader documentation

This document summarizes the runtime chord upload paths, the binary/chord format, available host tools, and the minipro-based uploader.

## Overview
Three host-side upload paths are available to write runtime tables into the RPLU system:

- Artery FIFO (HEADER+DATA chord pairs) — used by `tools/rplu_loader.py` for offline generation and by firmware that writes into the FPGA FIFO.
- USB -> RP2350 -> FPGA — `tools/rplu_uart_uploader.py` sends two 8-byte words over RP2350 USB CDC which forwards raw bytes via SPI to the FPGA.
- SPI flash via minipro — `tools/rplu_minipro_uploader.py` builds a binary of chord pairs and may call `minipro` to write to SPI flash.
- Morse table update — `tools/rplu_morse_update.py` emits UART/SD-card chord batches or a complete MRSE flash image for the engineering material set.

## Files
- `tools/rplu_loader.py` — produce HEADER/DATA chords, two hex lines, for manual/batch use.
- `tools/rplu_uart_uploader.py` — send HEADER+DATA over USB CDC to RP2350.
- `tools/rplu_minipro_uploader.py` — produce binary and optionally flash via minipro.
- `tools/build_tang25k_j4_rplu_flash.py` — build the Tang 25K boot chord payload.
- `tools/build_morse_flash.py` — build the multi-material MRSE table image.
- `hardware/rp2350/rp2350_spu_interface.c` — RP2350 firmware: forwards USB stdio 8-byte packets to FPGA.
- `hardware/rtl/peripherals/artery/rplu_artery_decoder.v` — Artery chord parser.
- `hardware/rtl/top/spu_laminar_boot.v` — SPI flash boot chord parser.
- `hardware/rtl/common/sync/rplu_cfg_cdc.v` and `hardware/rtl/top/spu_system.v` — legacy CDC/merge plumbing for runtime writes.

## Chord / binary format
- Each record is two 64-bit big-endian words: HEADER then DATA (concatenated in the binary).
- HEADER (64-bit)
  - [63:56] OPCODE = 0xA5
  - [55:48] sel (8-bit; low 3 bits used)
  - [47:44] material ID (0..15)
  - [43:34] addr (10-bit)
  - [33] singleton flag on Artery decoder path
  - [32:0] reserved
- DATA: full 64-bit cfg payload for the selected table entry.

Engineering material IDs:

| ID | Material |
|---:|---|
| 0 | carbon |
| 1 | iron |
| 2 | aluminum |
| 3 | silicon |
| 4 | titanium |
| 5 | nickel |
| 6 | copper |
| 7 | tungsten |
| 8-15 | user-loadable / reserved |

Selector mapping (tools/rplu_loader.py):
- 0 = params
- 1 = pade_num_q32
- 2 = pade_den_q32
- 3 = pade_num_q16
- 4 = pade_den_q16
- 5 = vnorm
- 6 = vnorm_dissoc

The lightweight `rplu_skel.v` ROM path uses `sel=0` for packed `{P[31:0], Q[31:0]}` entries and `sel=1` for dissociation bits. The active `rplu_exp.v` path uses `sel=5` for normalized V table data and `sel=6` for normalized dissociation bits.

## tools/rplu_minipro_uploader.py usage
- Single chord pair (writes bin, no flash):
  python3 tools/rplu_minipro_uploader.py --sel 1 --material 0 --addr 5 --data 0x1122334455667788

- Create bin from batch of lines (loader output accepts two-line HEADER/DATA pairs):
  python3 tools/rplu_minipro_uploader.py --batch-file my_chords.txt --outfile my_chords.bin

- Build and flash with minipro (example):
  python3 tools/rplu_minipro_uploader.py --batch-file my_chords.txt --flash --chip W25Q128 --yes

- Or provide full minipro command template (must include {binfile}):
  python3 tools/rplu_minipro_uploader.py --batch-file my_chords.txt --flash --minipro-cmd "minipro -p W25Q128 -w {binfile}" --yes

Batch file formats supported by the uploader:
- Two-line hex pairs (HEADER then DATA) — produced by tools/rplu_loader.py
- Two-token lines (HEADER DATA)
- Four-token lines (sel material addr data)
- Lines starting with `#` are ignored

## Safety & notes
- The minipro path writes directly to SPI flash. Ensure the target chip & offset are correct. Do not flash unknown chips holding bootloaders or FPGA bitstreams unless intentional.
- Prefer USB→RP2350 path for iterative testing; use minipro for pre-loading persistent ROM images.
- The CDC used for fast↔piranha transfers is a single-toggle handshake suitable for sparse writes. For bulk uploads, prefer the loader/uploader tooling with checksums and offline bin writing.

## Next steps (RTL audit & strategic decisions)
- Finalize address map and whether writes broadcast or target instances.
- Add readback/ACK primitives and simulation test for USB→RP2350→FPGA path.
- Decide CDC strategy for any non-fast/piranha domains (FIFO vs toggle-handshake).
- Add CRC/ACK and retry for bulk ROM uploads.

Recommended next actions:
- Run a focused RTL audit and produce a prioritized action list.
- Add a simulation test that exercises minipro-flashed ROM contents in bootflow.


## Recent changes (2026-04-08)
- Implemented per-lane threshold for spu_tensegrity_balancer: sel==3'd0 updates threshold_reg[cfg_addr[2:0]] with signed cfg_data[15:0].
- Added cfg inputs to hardware/common/rtl/bio/spu_fluid_solver.v and forwarded to u_balancer.
- Added dec_fast_cfg_* inputs to hardware/common/rtl/core/spu13_core.v and wired them from top-level spu_system (dec_fast_cfg_* → spu13_core).
- Exposed rplu_cfg_* inputs on hardware/spu4/rtl/spu4_top.v and wired them from spu_system per-sentinel.
- Updated hardware/docs/rplu_dependency_sweep.csv and session todos to reflect these changes.
