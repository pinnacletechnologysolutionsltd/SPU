# Engineering Contract: T1r SRAM Load, UART Transport, and Scaled Palette Visibility

**Date:** 2026-10-01  
**Contract ID:** `GPU-T1R-HARDWARE-SCALED-VISIBILITY-2026-10-01`  
**Status:** HALTED — single SRAM programming attempt failed; UART action not run  
**Owner:** John Curley  
**Spec Author:** Codex  
**Halt-and-Flag Implementer:** Codex  
**Integration Auditor:** programmer/UART transcript audit and owner visual report

## 0. Objective and evidence boundary

Use the routed T1r Q1 bitstream for one ordered SRAM load and one scaled A/B/C/return-A packet sequence. The sequence applies T1r's four per-primitive false/true palette pairs to the broad T1q visibility geometry.

The evidence claims are separate:

1. A successful programmer transcript establishes loading the exact bitstream into FPGA SRAM.
2. A successful sender transcript establishes four full host writes and `tcdrain` completions to the named CH340 UART.
3. The operator's report establishes only whether the broad A/B/C/return-A palette changes were visibly observed.

This contract does not prove byte-level FPGA packet acceptance, exact physical pixel correspondence, persistent flash programming, or arbitrary T1r scenes. It authorizes no receiver diagnostics or retries.

## 1. Frozen route artifact and inputs

| Item | Frozen value |
|---|---|
| Bitstream | `build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit` |
| Bitstream SHA-256 | `5df8ac43e5e6c10dc8a8a6b6a369ee2c44b7e73df9e11149f2b30e9f044523d7` |
| Route evidence | `build/gpu/t1r_palette_pair_20261001/build_seed1/run_01/` |
| Route result | exactly one `COMPLETE`, exit 0, 1,018 seconds |
| Final routed pixel clock | `clk_pixel` = 35.73 MHz, PASS at 25.00 MHz |
| Geometry source | `fixtures/gpu_t1i_scene_a_wire_175b.hex` |
| Geometry source file SHA-256 | `079a14b7fa4565c86e82311d571ab1b70099e96e598eededa7e8bffa5a0f4143` |
| Decoded 175-byte source wire SHA-256 | `8077acb3efbb92756fdee4c137500417e32f6f3664784c3b21f150c398d0dae9` |
| Derived scaled geometry wire | SHA-256 `1b6b066639da98f914f3e8512150656631dd7a55e18b6a1f65b9b7f222ca66df` |
| UART | `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` |
| UART framing | 115200 baud, 8 data bits, no parity, 1 stop bit |
| Inter-packet dwell | 5 seconds |

Before hardware access, require the route evidence to contain exactly one `COMPLETE` marker, no other terminal marker, and `result.json` exit code 0. Verify the bitstream hash above and require the UART path to resolve to a present device. Do not rebuild, re-tag, or substitute a bitstream.

## 2. Frozen scaled scene and palette sequence

Derive the scaled geometry from the frozen 175-byte fixture by multiplying each of its twelve signed 32-bit edge constants by exactly four. Keep every other geometry, depth, and U/V byte unchanged. Reject signed overflow. The derived 175-byte geometry wire must match the hash in §1. The independent 640×480 T1i oracle must reproduce:

| Measure | Frozen value |
|---|---:|
| Valid pixels | 38,561 |
| Winner pixels, lanes 0..3 | `[11964, 11723, 7635, 7239]` |
| Bounds | x=40..280, y=40..360 |
| A→B changed pixels | 38,561 |
| B→C changed pixels | 11,389 |
| C→A changed pixels | 27,172 |
| XOR outcomes on each lane in C | both 0 and 1 |

Use the palette byte encoding from the T1r Q1 contract: bits `[2:0]` are outcome-0 RGB, bits `[5:3]` are outcome-1 RGB, and bits `[7:6]` are zero. The lane-ordered palette suffix is fixed at `1C 2A 31 07`:

| Lane | Outcome 0 RGB | Outcome 1 RGB | Palette byte |
|---:|---:|---:|---:|
| 0 | `001` | `110` | `1C` |
| 1 | `010` | `101` | `2A` |
| 2 | `100` | `011` | `31` |
| 3 | `111` | `000` | `07` |

Construct each complete 187-byte wire frame as:

```text
wire bytes 0..174: scaled geometry (175 bytes, starts with A5)
wire bytes 175..178: four truth-table bytes, primitive 0..3
wire bytes 179..182: four selector bytes, primitive 0..3
wire bytes 183..186: four T1r palette-pair bytes, primitive 0..3
```

The exact ordered packets are:

| State | Truth tables | Selectors | Palettes | Packet SHA-256 |
|---|---|---|---|---|
| A | `00 00 00 00` | `CC CC CC CC` | `1C 2A 31 07` | `3719a5925da386fbd14e1ad1ca38139e5f4b68defdbce3e22a9fc8a5daa8ab58` |
| B | `0F 0F 0F 0F` | `CC CC CC CC` | `1C 2A 31 07` | `43dd87f2bdfd0de0aeaaed13693f446099b6c21688c208659992efdbf6a03bd2` |
| C | `06 06 06 06` | `CC CC CC CC` | `1C 2A 31 07` | `71c04abf252893262b7eaed6a2649fd1e3a9abe52a6e008eb3d95dfed7e81f37` |
| Return A | `00 00 00 00` | `CC CC CC CC` | `1C 2A 31 07` | `3719a5925da386fbd14e1ad1ca38139e5f4b68defdbce3e22a9fc8a5daa8ab58` |

Require both outcomes on every lane, all four winning lane IDs, overlap coverage, uncovered pixels, the frozen transition counts, four 187-byte frames, and exact A/return-A byte identity. Any oracle or packet-hash mismatch halts before hardware access.

## 3. Bounded budget and stop rules

The authorized campaign, if approved, contains exactly these ordered actions:

| Action | Maximum attempts | Per-attempt limit | Cumulative limit |
|---|---:|---:|---:|
| SRAM programming | 1 | 120 seconds | 120 seconds |
| Four-packet UART sequence, only after SRAM PASS | 1 | 60 seconds | 60 seconds |

Launching an action consumes its slot regardless of outcome. Do not retry, reconnect, reset the board, change the packet sequence, program flash, or increase a limit. If SRAM programming does not pass, stop without UART traffic. If UART transport fails, stop without retransmission. If the operator sees no broad output or an ambiguous transition, record that result and stop; receiver/commit diagnostics require another contract.

## 4. Static preflight and sender

Create `tools/send_gpu_t1r_scaled_visibility.py` as a focused sender. It must pin the fixture and T1r bitstream hashes, derive the scaled geometry, run the independent T1i oracle over the complete frame, verify every coverage/color/transition/packet value in §2, refuse transcript overwrite, and support `--dry-run` and `--send`. In send mode it must configure the exact UART framing in §1, require one complete 187-byte write and one successful `tcdrain` per packet, preserve packet order, and wait five seconds between packets. Record packet hashes, byte counts, drain results, and per-packet monotonic timings in JSON. Do not alter the existing T1q sender.

The implemented sender passed `py_compile` and its frozen oracle/packet dry-run. Its SHA-256 is `b53d567e254790da7e35269159752523b8a1226b6b646693d5377291008a77f9`; the complete preflight record is `build/gpu/t1r_palette_pair_20261001/hardware/preflight.txt`. Two earlier dry-run implementation defects were caught and preserved in `preflight_attempt_01_failed.txt` and `preflight_attempt_02_failed.txt`. They were corrected before hardware access; the final preflight passed, and the source must remain at this frozen hash.

Before programming, run the complete preflight below once and stop on any mismatch:

```bash
test -f build/gpu/t1r_palette_pair_20261001/build_seed1/run_01/COMPLETE
test ! -e build/gpu/t1r_palette_pair_20261001/build_seed1/run_01/FAILED
test ! -e build/gpu/t1r_palette_pair_20261001/build_seed1/run_01/TIMEOUT
python3 -c 'import json; p="build/gpu/t1r_palette_pair_20261001/build_seed1/run_01/result.json"; d=json.load(open(p)); assert d["exit_code"] == 0, d'
sha256sum build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit fixtures/gpu_t1i_scene_a_wire_175b.hex
test -e /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0
python3 -m py_compile tools/send_gpu_t1r_scaled_visibility.py
python3 tools/send_gpu_t1r_scaled_visibility.py --dry-run
test ! -e build/gpu/t1r_palette_pair_20261001/hardware/program_01.log
test ! -e build/gpu/t1r_palette_pair_20261001/hardware/sequence_01.json
```

Require all hashes and dry-run outputs to match §§1–2. Save the sender source hash, preflight command output, UART device resolution, and launch-time `git status --short` in `build/gpu/t1r_palette_pair_20261001/hardware/preflight.txt`. The sender must not change after preflight. If the sender or any frozen input changes, halt and renew the contract before touching hardware.

## 5. Hardware actions after authorization

Create the evidence directory and program only FPGA SRAM, once:

```bash
mkdir -p build/gpu/t1r_palette_pair_20261001/hardware
set -o pipefail
timeout 120s openFPGALoader -c dirtyJtag --freq 1000000 \
  build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit \
  2>&1 | tee build/gpu/t1r_palette_pair_20261001/hardware/program_01.log
```

Require exit 0, `Load SRAM: 100.00%`, and `isc_done 1`, `init 1`, and `done 1`. Record the programmer transcript SHA-256. Persistent configuration flash is out of scope.

Only after SRAM programming passes, send the four frozen packets once:

```bash
timeout 60s python3 tools/send_gpu_t1r_scaled_visibility.py --send \
  --port /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 \
  --dwell-seconds 5 \
  --transcript build/gpu/t1r_palette_pair_20261001/hardware/sequence_01.json
```

Require exit 0 and an audit of four ordered 187-byte full writes, all packet hashes from §2, four successful `tcdrain` completions, exact A/return-A equality, and transcript SHA-256. Host-side writes and drains establish only delivery to the CH340.

## 6. Visual report and interpretation

After transmission, ask the operator to report separately whether they saw:

1. A, showing the four lane-specific outcome-0 palette colors over the large scene.
2. B, showing the four lane-specific outcome-1 colors.
3. C, showing the per-lane XOR mixture.
4. Return A, matching the initial A state by observation.

The oracle predicts RGB code histograms per state as follows, with bit order `R,G,B`:

| State | RGB code → pixel count |
|---|---|
| A | `001:7635`, `010:11723`, `100:11964`, `111:7239` |
| B | `000:7239`, `011:11964`, `101:11723`, `110:7635` |
| C | `000:652`, `001:651`, `010:1957`, `011:9770`, `100:2194`, `101:9766`, `110:6984`, `111:6587` |

These are oracle expectations, not physical pixel measurements. A visual PASS requires the operator to confirm all four broad states and return to A. It does not establish pixel-exact output or independent proof of byte-level packet acceptance.

## 7. Stop and handoff boundary

Record SRAM programming, host-to-CH340 transport, and operator-observed visibility as independent results. After the campaign, update `docs/hardware_evidence.md` with only the supported claims, cite the exact bitstream hash and transcript paths, and stop. D4 P1b remains owner-authorized but deferred until this hardware proof is interpreted. D4 RTL and the integrated control-plane/GPU demo remain later decisions in the owner's declared sequence.

| Evidence claim | Current state |
|---|---|
| T1r Q1 focused functional gate | PASS — recovery v2 |
| T1r repository gate | PASS |
| Mandatory Padé baseline build | PASS — `clk_fast` 39.86 MHz at 25 MHz target |
| T1r Artix-7 route | PASS — `clk_pixel` 35.73 MHz at 25 MHz target |
| T1r SRAM programming | FAIL — single authorized attempt consumed at JTAG initialization |
| T1r host-to-CH340 transport | NOT RUN |
| T1r operator-observed scaled visibility | NOT RUN |
| T1r exact physical pixel equality / persistent flash | NOT MEASURED / NOT RUN |

## 8. Hardware attempt closeout

The final static preflight passed and froze sender SHA-256 `b53d567e254790da7e35269159752523b8a1226b6b646693d5377291008a77f9` in `build/gpu/t1r_palette_pair_20261001/hardware/preflight.txt`. The single SRAM programming command was:

```bash
timeout 120s openFPGALoader -c dirtyJtag --freq 1000000 \
  build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit
```

It exited 1 immediately with `empty`, `libusb init failed`, and `JTAG init failed with: std::exception`. The captured log is `build/gpu/t1r_palette_pair_20261001/hardware/program_01.log`, SHA-256 `b5f391ce29bad0bbfbf7c22f56aa945c9c577dd7348d108051801b3ef129f6e0`. This attempt is consumed. UART sequence 01 was not run; no SRAM load or visual result is claimed. Stop here. A renewed hardware attempt requires a separate owner authorization and a new bounded contract.
