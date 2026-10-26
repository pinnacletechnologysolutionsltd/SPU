# Engineering Contract: T1r SRAM Programming Recovery and Conditional UART Sequence

**Date:** 2026-10-01  
**Contract ID:** `GPU-T1R-PROGRAMMING-RECOVERY-2026-10-01`  
**Status:** HALTED — SRAM recovery PASS; conditional UART attempt failed before write; attempt budget consumed  
**Owner:** John Curley  
**Spec Author:** Codex  
**Halt-and-Flag Implementer:** Codex  
**Integration Auditor:** hardware transcript and operator report audit

## 0. Objective and evidence boundary

Recover from the single failed T1r SRAM-programming attempt by checking the programmer/USB/JTAG path without changing the design or frozen inputs, then permit exactly one additional SRAM programming attempt. If and only if SRAM programming passes, permit the one frozen T1r A/B/C/return-A UART sequence.

The prior attempt remains consumed and failed at JTAG initialization. The recovery attempt is a distinct, newly authorized slot. This contract does not authorize a new build, bitstream substitution, source change, flash programming, reset, cable reseat, UART retry, or receiver diagnosis.

Keep these claims separate:

1. `openFPGALoader` SRAM completion establishes loading the exact named bitstream into volatile FPGA SRAM.
2. The sender transcript establishes full host writes and `tcdrain` completion to the CH340 path.
3. An operator report establishes only whether the broad palette states were visibly observed.

None establishes FPGA packet acceptance or exact physical pixel equality.

## 1. Frozen identities and historical failure

| Item | Frozen value |
|---|---|
| Bitstream | `build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit` |
| Bitstream SHA-256 | `5df8ac43e5e6c10dc8a8a6b6a369ee2c44b7e73df9e11149f2b30e9f044523d7` |
| Sender | `tools/send_gpu_t1r_scaled_visibility.py` |
| Sender SHA-256 | `b53d567e254790da7e35269159752523b8a1226b6b646693d5377291008a77f9` |
| Geometry fixture | `fixtures/gpu_t1i_scene_a_wire_175b.hex` |
| Fixture SHA-256 | `079a14b7fa4565c86e82311d571ab1b70099e96e598eededa7e8bffa5a0f4143` |
| Expected FPGA | Xilinx Artix-7 XC7A100T, recognized model `xc7a100` |
| Expected JTAG IDCODE | `0x03631093` (decimal identity; leading-zero formatting may vary) |
| Expected JTAG IR length | 6 |
| UART path | `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` |
| Previous programming log | `build/gpu/t1r_palette_pair_20261001/hardware/program_01.log` |
| Previous log SHA-256 | `b5f391ce29bad0bbfbf7c22f56aa945c9c577dd7348d108051801b3ef129f6e0` |
| Previous result | exit 1; `empty`, `libusb init failed`, `JTAG init failed with: std::exception` |

The prior SRAM attempt is not retried or reclassified. Its programmer failure is infrastructure evidence only and says nothing about T1r logic. Frozen packet hashes, geometry oracle, palette layout, and visual expectations are carried forward unchanged from `contract_gpu_t1r_hardware_scaled_visibility_2026-10-01.md` §§1–2. Require the existing `hardware/preflight.txt` to record the original static preflight PASS.

## 2. Read-only preflight

Run all checks once, in order, before the recovery programming attempt. Save complete stdout/stderr and command exit statuses to the new evidence directory `build/gpu/t1r_palette_pair_20261001/hardware_recovery_01/preflight.txt`. These commands must not program, reset, reconnect, or transmit UART data.

```bash
test ! -e build/gpu/t1r_palette_pair_20261001/hardware_recovery_01
mkdir -p build/gpu/t1r_palette_pair_20261001/hardware_recovery_01
openFPGALoader --scan-usb
openFPGALoader -c dirtyJtag --freq 1000000 --detect -v
sha256sum build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit
sha256sum tools/send_gpu_t1r_scaled_visibility.py
sha256sum fixtures/gpu_t1i_scene_a_wire_175b.hex
test -e /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0
readlink -f /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0
python3 tools/send_gpu_t1r_scaled_visibility.py --dry-run
test -f build/gpu/t1r_palette_pair_20261001/hardware/preflight.txt
```

Preflight PASS requires all of the following:

- USB scan identifies the DirtyJTAG adapter as visible to `openFPGALoader`.
- Read-only JTAG detection finds exactly one Xilinx `xc7a100` device, IDCODE `0x03631093`, IR length 6. No SRAM action is part of detection.
- All three hashes match §1 and the existing scaled packet/oracle dry-run matches the frozen values in the prior contract: four 187-byte packets; A/return-A byte-identical; hashes `3719a5925da386fbd14e1ad1ca38139e5f4b68defdbce3e22a9fc8a5daa8ab58`, `43dd87f2bdfd0de0aeaaed13693f446099b6c21688c208659992efdbf6a03bd2`, `71c04abf252893262b7eaed6a2649fd1e3a9abe52a6e008eb3d95dfed7e81f37`, and the A hash again.
- The CH340 path exists and resolves to its current device node. This checks availability only; no port is opened and no bytes are sent.
- The original static preflight record remains present and contains the final preflight PASS; do not overwrite it.

Capture each command's full output and exit status in `preflight.txt`. Stop immediately on a nonzero status. The output directory must be absent before this contract's evidence is created; never overwrite or append to prior attempt evidence.

Any missing device, scan/detect error, unexpected or multiple JTAG devices, IDCODE/model/IR mismatch, hash mismatch, dry-run mismatch, or unavailable UART path halts this contract before programming. Do not repair wiring, reflash DirtyJTAG, run alternate probes, or spend the programming slot after a failed preflight. Preflight failure does not consume the one recovery programming attempt, but requires renewed authorization to change the setup or probe plan.

## 3. Frozen attempt budget and order

| Action | Maximum attempts | Per-attempt timeout | Cumulative budget |
|---|---:|---:|---:|
| SRAM programming recovery | 1 | 120 s | 120 s |
| UART A/B/C/return-A sequence, only after SRAM PASS | 1 | 60 s | 60 s |

The SRAM slot is consumed once the programming command launches, for every outcome. If it fails, times out, becomes unavailable, or lacks the required completion signature, stop; do not send UART. If UART launches, its slot is consumed on any outcome; do not retransmit. No retry, cable reseat, USB reset, board reset, flash write, limit increase, or alternate method is authorized.

## 4. Single SRAM recovery attempt

Only after §2 passes, record `git status --short`, append the completed preflight output and hashes, and run this exact command once:

```bash
set -o pipefail
timeout 120s openFPGALoader -c dirtyJtag --freq 1000000 \
  build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit \
  2>&1 | tee build/gpu/t1r_palette_pair_20261001/hardware_recovery_01/program_02.log
```

SRAM PASS requires exit 0 and programmer output confirming `Load SRAM 100%`, `isc_done 1`, `init 1`, and `done 1`. Record the log SHA-256 and command status. Any other result is a consumed failure/inconclusive outcome; stop with UART NOT RUN.

## 5. Conditional UART sequence

Run this exact command once only after SRAM PASS:

```bash
timeout 60s python3 tools/send_gpu_t1r_scaled_visibility.py --send \
  --port /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 \
  --dwell-seconds 5 \
  --transcript build/gpu/t1r_palette_pair_20261001/hardware_recovery_01/sequence_02.json
```

Require exit 0 and audit four ordered 187-byte full writes, the frozen packet hashes in §2, four successful `tcdrain` completions, and byte-identical A/return-A. Record transcript SHA-256. A transport failure stops the campaign without retransmission. This transcript is host-to-CH340 delivery evidence only.

## 6. Operator observation and closeout

If and only if the UART command completes, record the operator's separate observation for A, B, C, and return A. A visual PASS requires all four broad states to be observed and return A to match A by observation. Do not claim exact physical pixel equality or FPGA packet acceptance.

Store recovery artifacts only under `build/gpu/t1r_palette_pair_20261001/hardware_recovery_01/`; preserve the prior attempt untouched. Update `docs/hardware_evidence.md` only with claims supported by this recovery's durable logs/transcript and operator report. Update this contract with the result and stop. D4 P1b remains deferred; no D4 software or RTL work is included.

| Evidence claim | Current state |
|---|---|
| T1r focused functional / repository / Padé / route gates | PASS |
| First T1r SRAM attempt | FAIL — consumed; JTAG initialization failure |
| Recovery USB/JTAG preflight | PASS — DirtyJTAG visible; one XC7A100T, IDCODE `0x03631093`, IR length 6; frozen hashes and oracle match |
| Recovery SRAM programming | PASS — exit 0; 100%; `isc_done 1`, `init 1`, `done 1` |
| Recovery UART transport | FAIL — sender could not open the now-missing frozen by-id path; zero transmissions |
| Scaled palette visibility | NOT RUN |
| Exact physical pixel equality / persistent flash | NOT MEASURED / NOT RUN |
| D4 P1b | DEFERRED |

## 7. Recovery closeout

The read-only USB scan found DirtyJTAG (`1209:c0ca`, serial `CB81353DCE678119`). JTAG detection found one Xilinx `xc7a100`, IDCODE `0x3631093` (same IDCODE as `0x03631093`), IR length 6. The bitstream, sender, and fixture hashes matched §1. The oracle dry-run passed; the original static preflight record remains a PASS. Recovery preflight: `build/gpu/t1r_palette_pair_20261001/hardware_recovery_01/preflight.txt`, SHA-256 `dc009507fd7035e83d25d8d906b5cb4dc8685014dee99ccee3d25319f39f668b`.

The single authorized SRAM recovery command exited 0, reached 100%, and reported `isc_done 1`, `init 1`, and `done 1`. Log: `build/gpu/t1r_palette_pair_20261001/hardware_recovery_01/program_02.log`, SHA-256 `da4130eb31e500564a5b017544b128b144754cbc9fef33ce1238c3da42996605`. This establishes SRAM loading of the frozen bitstream.

The conditional UART command was launched once and exited 1 before opening the serial device: `FileNotFoundError` for `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`. Transcript `build/gpu/t1r_palette_pair_20261001/hardware_recovery_01/sequence_02.json` has status `failed`, zero transmissions, SHA-256 `3f111c7c0c8745e745cd8a96b3ddb860936229b97bbc84158304908c1d7cd0dc`. The UART slot is consumed. No reconnect, resend, or further hardware probe was performed. There is no scaled-visibility observation.

## 8. Stop conditions

- Stop before programming on any preflight failure or identity mismatch.
- Stop after any programming failure, timeout, missing completion signature, or unavailable result; UART must remain unrun.
- Stop after any UART failure; no resend.
- Do not infer results without preserved output and exit status.
- Do not change source, profile, bitstream, packet definitions, board wiring, or tooling under this contract.
- The authorized attempt budget is consumed. No further hardware action is authorized by this contract.
