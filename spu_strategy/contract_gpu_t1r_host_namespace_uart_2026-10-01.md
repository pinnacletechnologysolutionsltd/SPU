# Engineering Contract: T1r Host-Namespace UART Sequence

**Date:** 2026-10-01  
**Contract ID:** `GPU-T1R-HOST-NAMESPACE-UART-2026-10-01`  
**Status:** HALTED — operator confirmed board power-off; recorded SRAM configuration invalidated; sender NOT RUN  
**Owner:** John Curley

## 0. Objective

Use the already SRAM-loaded T1r bitstream to make one frozen A/B/C/return-A UART attempt from the approved host execution context, where the CH340 endpoint is visible. The default sandbox context cannot see `/dev/ttyUSB0`; the approved host context can. This attempt tests the same sender and packet sequence in the context that has the device node.

The comparison is recorded at `build/gpu/t1r_palette_pair_20261001/execution_context_compare_01.txt`. It found default mount namespace `4026533125` with the by-id path and tty node absent, versus host mount namespace `4026531832` with the same by-id path resolving to `/dev/ttyUSB0`, character device major 188/minor 0, and USB `1a86:7523`. This strongly supports an execution-namespace visibility explanation for the prior `FileNotFoundError`; it does not establish UART transport.

## 1. Frozen inputs and limits

| Item | Frozen value |
|---|---|
| SRAM-loaded bitstream | `build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit` |
| Bitstream SHA-256 | `5df8ac43e5e6c10dc8a8a6b6a369ee2c44b7e73df9e11149f2b30e9f044523d7` |
| Sender | `tools/send_gpu_t1r_scaled_visibility.py` |
| Sender SHA-256 | `b53d567e254790da7e35269159752523b8a1226b6b646693d5377291008a77f9` |
| Expected host endpoint | `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` → `/dev/ttyUSB0` |
| UART | 115200 baud, 8N1; four 187-byte packets; 5-second dwell |
| Packet hashes | A `3719a5925da386fbd14e1ad1ca38139e5f4b68defdbce3e22a9fc8a5daa8ab58`; B `43dd87f2bdfd0de0aeaaed13693f446099b6c21688c208659992efdbf6a03bd2`; C `71c04abf252893262b7eaed6a2649fd1e3a9abe52a6e008eb3d95dfed7e81f37`; return-A equals A |
| Attempts | 1 sender invocation maximum |
| Timeout / cumulative budget | 60 seconds / 60 seconds |
| Transcript | `build/gpu/t1r_palette_pair_20261001/host_uart_01/sequence_04.json` |

No FPGA reload is included. Before sender launch, obtain and record operator confirmation that the board has remained powered and its SRAM configuration has not been invalidated since the successful load recorded in `docs/hardware_evidence.md` §3.26 (`build/gpu/t1r_palette_pair_20261001/hardware_recovery_01/program_02.log`). If continuity is uncertain or the condition is not met, halt; do not reload under this contract. On 2026-10-02 the operator reported: "No, it was turned off." Continuity is LOST; this contract is HALTED before sender launch.

## 2. Host-context preflight

Create `build/gpu/t1r_palette_pair_20261001/host_uart_01/` only if absent. Run these checks in the same approved host execution context intended for the sender, preserving complete output and exit statuses in `preflight.txt`:

```bash
python3 -c 'import os; p="/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"; print("mount_ns",os.readlink("/proc/self/ns/mnt")); print("by_id_exists",os.path.lexists(p)); print("by_id_realpath",os.path.realpath(p)); print("tty_exists",os.path.exists("/dev/ttyUSB0")); print("tty_stat",os.stat("/dev/ttyUSB0") if os.path.exists("/dev/ttyUSB0") else "MISSING")'
udevadm info --query=property --name=/dev/ttyUSB0
sha256sum build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit
sha256sum tools/send_gpu_t1r_scaled_visibility.py
python3 tools/send_gpu_t1r_scaled_visibility.py --dry-run
```

Require the by-id path to exist and resolve to `/dev/ttyUSB0`, udev properties to identify USB VID:PID `1a86:7523` with driver `ch341`, hashes to match §1, and dry-run packet hashes/oracle to match §1 and the frozen scaled-scene contract. The host mount namespace must differ from the recorded default sandbox namespace and match the approved host context. Any mismatch halts before sender launch.

## 3. One host-context send

After explicit owner authorization, preflight passes, and the §1 continuity and §4 observer-readiness confirmations are recorded, require the transcript destination to be absent and run the existing sender once in the same approved host context:

```bash
timeout 60s python3 tools/send_gpu_t1r_scaled_visibility.py --send \
  --port /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 \
  --dwell-seconds 5 \
  --transcript build/gpu/t1r_palette_pair_20261001/host_uart_01/sequence_04.json
```

The attempt slot is consumed when the sender launches, regardless of outcome. If using a sandboxed command interface, request host-context execution approval for this exact command; do not fall back to the sandboxed namespace. Require exit 0, four ordered full 187-byte writes, four successful `tcdrain` completions, exact packet hashes, and byte-identical initial/return-A packets. On any failure, stop without retry. Record the transcript SHA-256.

## 4. Observation and stop rules

Before sender launch, confirm the operator is ready to observe the complete A → B → C → return-A sequence and record each state separately. Collect the report afterward. If any state was missed or uncertain, record visibility as inconclusive; do not retry under this contract.

A visual pass requires all four broad states and return to A by observation. This remains operator-observed evidence, not exact physical pixel comparison or FPGA packet-acceptance proof.

- Do not reload FPGA SRAM, reset/power-cycle the board, reset/reconnect USB, move cables, alter source, or substitute another endpoint.
- Stop before send if the host-context preflight fails.
- Stop before send if power/SRAM continuity is uncertain or invalidated, or operator readiness is unconfirmed.
- Stop after the one sender outcome. The attempt is consumed on any result.
- Keep D4 P1b deferred.

| Claim | Current state |
|---|---|
| T1r route / SRAM load | PASS |
| Sandbox/host namespace mismatch | CONFIRMED by read-only metadata comparison |
| Prior sandbox UART attempts | FAIL before open; zero transmissions |
| New host-context UART attempt | NOT RUN — halted before launch on confirmed power-off |
| T1r UART transport / visibility | NOT PROVEN |
| D4 P1b | DEFERRED |

This contract is HALTED. The prior load remains historical evidence only. A new SRAM load is scoped by `contract_gpu_t1r_power_cycle_sram_reload_2026-10-02.md`; it does not activate this UART contract.
