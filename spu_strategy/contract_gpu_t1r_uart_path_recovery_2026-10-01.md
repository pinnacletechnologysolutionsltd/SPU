# Engineering Contract: T1r CH340 UART Path Recovery

**Date:** 2026-10-01  
**Contract ID:** `GPU-T1R-UART-PATH-RECOVERY-2026-10-01`  
**Status:** HALTED — conditional UART attempt failed before port open; attempt consumed  
**Owner:** John Curley

## 0. Objective and boundary

Resolve the disappeared CH340 device path after the authorized T1r SRAM load and, only if a unique expected CH340 endpoint is visible, send the existing frozen A/B/C/return-A sequence once. This is a UART-path recovery only. Do not reload the FPGA, reset or reconnect USB, alter wiring, rebuild, change source, or modify packets.

The prior UART command is consumed and failed before port open with zero transmissions. This contract permits one new UART command only. A successful sender transcript establishes host writes and `tcdrain` completion to the identified CH340; it does not establish FPGA acceptance or visual output.

## 1. Frozen inputs

| Item | Value |
|---|---|
| SRAM-loaded bitstream SHA-256 | `5df8ac43e5e6c10dc8a8a6b6a369ee2c44b7e73df9e11149f2b30e9f044523d7` |
| Sender | `tools/send_gpu_t1r_scaled_visibility.py` |
| Sender SHA-256 | `b53d567e254790da7e35269159752523b8a1226b6b646693d5377291008a77f9` |
| Expected UART bridge | CH340, USB VID:PID `1a86:7523` |
| Preferred device path | `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` |
| Frozen frame lengths | Four ordered packets, 187 bytes each |
| Packet SHA-256, A/B/C/return-A | `3719a5925da386fbd14e1ad1ca38139e5f4b68defdbce3e22a9fc8a5daa8ab58`, `43dd87f2bdfd0de0aeaaed13693f446099b6c21688c208659992efdbf6a03bd2`, `71c04abf252893262b7eaed6a2649fd1e3a9abe52a6e008eb3d95dfed7e81f37`, `3719a5925da386fbd14e1ad1ca38139e5f4b68defdbce3e22a9fc8a5daa8ab58` |
| Prior failure transcript | `build/gpu/t1r_palette_pair_20261001/hardware_recovery_01/sequence_02.json` |

The already-authorized SRAM-load evidence is `build/gpu/t1r_palette_pair_20261001/hardware_recovery_01/program_02.log`. This contract authorizes no additional SRAM action. Keep the board powered and leave its configuration undisturbed while performing this UART recovery.

## 2. Read-only endpoint preflight

Create the new evidence directory only if absent. Save output and exit statuses to `build/gpu/t1r_palette_pair_20261001/uart_path_recovery_01/preflight.txt`. Run these read-only checks once, in order:

```bash
test ! -e build/gpu/t1r_palette_pair_20261001/uart_path_recovery_01
mkdir -p build/gpu/t1r_palette_pair_20261001/uart_path_recovery_01
lsusb -d 1a86:7523
ls -l /dev/serial/by-id/
ls -l /dev/ttyUSB*
sha256sum build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit
sha256sum tools/send_gpu_t1r_scaled_visibility.py
python3 tools/send_gpu_t1r_scaled_visibility.py --dry-run
```

If `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` exists, resolve it with `readlink -f` and use that exact path. If it does not exist, use `udevadm info --query=property --name=<candidate>` on each enumerated `/dev/ttyUSB*` candidate and accept only exactly one device reporting `ID_VENDOR_ID=1a86` and `ID_MODEL_ID=7523`. Record the chosen path and command output. A missing, duplicate, or ambiguous CH340 halts before UART transmission. Do not use another USB serial adapter.

Require the bitstream and sender hashes to match §1, the dry-run packet hashes to match §1, and the sole selected endpoint to identify as the CH340. The endpoint preflight sends no bytes. If any requirement fails, stop; the UART attempt remains unlaunched, but no alternate probe, reset, reconnect, or device substitution is permitted under this contract.

## 3. Single conditional UART attempt

After §2 passes, record `git status --short`, select the one verified path, verify the transcript destination is absent, then run exactly once with that path substituted for `<verified-port>`:

```bash
timeout 60s python3 tools/send_gpu_t1r_scaled_visibility.py --send \
  --port <verified-port> \
  --dwell-seconds 5 \
  --transcript build/gpu/t1r_palette_pair_20261001/uart_path_recovery_01/sequence_03.json
```

The slot is consumed when this command launches, regardless of outcome. Require exit 0, four ordered full writes of 187 bytes, four successful `tcdrain` completions, the hashes in §1, and identical A/return-A bytes. On any failure, stop without retry. Preserve and hash the transcript.

## 4. Closeout

If transport passes, ask the operator to report A, B, C, and return-A visibility separately. Record only operator-observed output; do not infer pixel equality or byte-level FPGA acceptance. If no transmission occurs or visibility is absent, record that result accurately. Update `docs/hardware_evidence.md` and this contract with the evidence hashes, then stop. D4 P1b remains deferred.

| Claim | Current state |
|---|---|
| T1r route and SRAM load | PASS |
| Prior UART command | FAIL before open; zero transmissions; slot consumed |
| CH340 endpoint recovery preflight | PASS at check time — `1a86:7523`, by-id path resolved to `/dev/ttyUSB0` |
| New UART attempt | FAIL before port open — path disappeared between preflight and sender open; zero transmissions; slot consumed |
| T1r transport / scaled visibility | NOT PROVEN |
| D4 P1b | DEFERRED |

## 5. Recovery closeout

The read-only inventory found one CH340 (`1a86:7523`), `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` linked to `/dev/ttyUSB0`, and the frozen hashes and packet/oracle dry-run matched. Preflight record: `build/gpu/t1r_palette_pair_20261001/uart_path_recovery_01/preflight.txt`, SHA-256 `535f726f1d9de7cbb8b9ecb8d85d1f987502de38220c0c13bf826c4a33563bd0`.

The single authorized sender invocation then exited 1 before opening the endpoint, with `FileNotFoundError` for the same by-id path. Transcript: `build/gpu/t1r_palette_pair_20261001/uart_path_recovery_01/sequence_03.json`, SHA-256 `3f111c7c0c8745e745cd8a96b3ddb860936229b97bbc84158304908c1d7cd0dc`; it records status `failed` and zero transmissions. No retry, reconnect, USB reset, or additional probe was performed. This contract's UART attempt is consumed and T1r host transport and visibility remain unproven.

## 6. Stop rules

- No SRAM reload, USB reset, unplug/replug, board reset, wiring change, or port substitution outside the unique VID:PID rule above.
- Stop if the endpoint is absent, duplicated, or not identified as the CH340.
- The sender attempt is consumed. Any further hardware work requires another owner-authorized contract.
