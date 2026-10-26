# Engineering Contract: T1r Correlated CH340/UART Attempt

**Date:** 2026-10-01  
**Contract ID:** `GPU-T1R-CORRELATED-UART-DIAGNOSTIC-2026-10-01`  
**Status:** SUPERSEDED — host/sandbox mount-namespace mismatch demonstrated by read-only comparison  
**Owner:** John Curley  
**Spec Author:** Codex

## 0. Objective and claim boundary

Observe USB, udev, kernel, and tty-node state continuously across one future frozen T1r UART sequence. The event monitor and endpoint sampler must already be active before sender launch, so disappearance during port open or transmission is time-correlated with kernel/udev events.

This tranche authorizes at most one sender invocation, conditional on a unique expected CH340 being present before launch. It does not authorize FPGA reload, USB reset, device reset, cable movement, reconnection, wiring changes, alternate serial adapters, retries, or another passive-only capture. Successful sender evidence is host-to-CH340 transport only. It does not establish FPGA packet acceptance or visual output.

## 1. Frozen hardware and software inputs

| Item | Frozen value |
|---|---|
| SRAM-loaded bitstream SHA-256 | `5df8ac43e5e6c10dc8a8a6b6a369ee2c44b7e73df9e11149f2b30e9f044523d7` |
| Sender | `tools/send_gpu_t1r_scaled_visibility.py` |
| Sender SHA-256 | `b53d567e254790da7e35269159752523b8a1226b6b646693d5377291008a77f9` |
| USB bridge | CH340, VID:PID `1a86:7523`, kernel driver `ch341` |
| Preferred endpoint | `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` |
| Frozen sequence | A/B/C/return-A, four 187-byte packets, 115200 8N1, five-second dwell |
| Packet hashes | A `3719a5925da386fbd14e1ad1ca38139e5f4b68defdbce3e22a9fc8a5daa8ab58`; B `43dd87f2bdfd0de0aeaaed13693f446099b6c21688c208659992efdbf6a03bd2`; C `71c04abf252893262b7eaed6a2649fd1e3a9abe52a6e008eb3d95dfed7e81f37`; return-A equals A |
| Prior recovery artifact | `build/gpu/t1r_palette_pair_20261001/hardware_recovery_01/program_02.log` |

## 2. One-shot campaign budget

| Action | Maximum | Limit |
|---|---:|---:|
| Correlated observation window | 1 | 75 seconds total: 5-second baseline, sender window up to 60 seconds, 10-second post-window |
| Sender invocation | 1 | 60 seconds, cumulative 60 seconds |

The sender slot is consumed once launched, regardless of exit result or whether any byte is written. If prelaunch validation fails, do not launch the sender. If the observer exits, fails, or cannot prove it is active before sender launch, do not launch the sender. No retry or repeat capture is allowed.

## 3. Required correlated capture tool

Before hardware access, implement one focused helper:

```text
tools/capture_gpu_t1r_correlated_uart.py
```

The helper must remain below 150 lines and must:

1. Verify the frozen bitstream and sender hashes in §1 and run the sender's existing `--dry-run`; verify the four frozen packet hashes.
2. Identify exactly one present CH340 with VID:PID `1a86:7523`, driver `ch341`, and a tty endpoint. Prefer the frozen by-id path. If it has changed, accept a `/dev/ttyUSB*` candidate only when udev properties prove the same VID:PID and exactly one candidate exists. Record the chosen endpoint. A missing or ambiguous device halts before sender launch.
3. Start `udevadm monitor --kernel --udev --property` and collect a kernel log snapshot immediately before the attempt. Record UTC wall-clock timestamps and monotonic timestamps.
4. Sample the preferred by-id link, resolved node existence, and tty node identity at 100 ms intervals from five seconds before sender launch until ten seconds after sender completion, or until the 75-second total window expires. Record missing-link intervals as explicit samples.
5. Launch the existing sender exactly once as a child process with the §1 endpoint, `--dwell-seconds 5`, the 60-second timeout, and a new transcript path. The helper must not import or modify sender packet logic.
6. Keep the udev monitor and sampler active during the sender process and post-window. Capture a second kernel log snapshot and all process exit statuses. Stop its own observer processes after the single window; it must not reset or signal any USB device.
7. Preserve separate `preflight.json`, `node_samples.jsonl`, `udev_monitor.log`, `kernel_before.log`, `kernel_after.log`, and sender `sequence_03.json` under `build/gpu/t1r_palette_pair_20261001/correlated_uart_01/`. Refuse to overwrite any existing output. Emit SHA-256 hashes for every artifact in `manifest.sha256`.
8. Return a nonzero overall status if prelaunch validation fails, if the observer is not confirmed active before sender launch, or if artifact writing/hash generation fails. Preserve the sender's own result separately; never retry it.

Run only the following non-hardware checks after implementing the helper:

```bash
python3 -m py_compile tools/capture_gpu_t1r_correlated_uart.py
python3 tools/capture_gpu_t1r_correlated_uart.py --dry-run
sha256sum tools/capture_gpu_t1r_correlated_uart.py
```

Freeze the helper SHA-256 in this contract and in `preflight.json` before any hardware invocation. Any helper or input hash mismatch halts before the sender.

## 4. Authorized invocation after separate approval

After the helper, its source hash, inputs, and output directory are frozen and this contract is explicitly authorized, run exactly once:

```bash
python3 tools/capture_gpu_t1r_correlated_uart.py \
  --port /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 \
  --sample-ms 100 \
  --baseline-seconds 5 \
  --sender-timeout-seconds 60 \
  --post-seconds 10 \
  --output build/gpu/t1r_palette_pair_20261001/correlated_uart_01
```

The helper may select a uniquely identified `/dev/ttyUSB*` endpoint only under the rule in §3, while recording that exact choice before sender launch. Do not rerun the invocation for any outcome.

## 5. Evidence interpretation

- A kernel USB disconnect/add event with matching timestamps and topology supports USB disconnect/re-enumeration. It does not identify what initiated it.
- A stable USB device with tty-node removal/re-add supports driver or udev node churn.
- A disappearing symlink with a continuously present tty node and no USB/udev event suggests a path-management or observation-boundary issue; it does not prove sender behavior caused it.
- Stable path and no events throughout this attempt means only that the earlier failure was not reproduced.
- Link event timestamps to the sender's recorded start/end timestamps. Do not infer JTAG causality absent overlapping event evidence.
- If all four writes and drains pass, report host-to-CH340 transport only. Visual behavior requires a separate operator observation; pixel equality and FPGA packet acceptance remain unmeasured.

## 6. Current status and stop rules

| Claim | State |
|---|---|
| T1r route / SRAM load | PASS |
| CH340 stable during prior passive 45-second window | PASS for that interval |
| Earlier sender-open disappearance | Intermittent; cause unresolved |
| UART transport / scaled visibility | NOT PROVEN |
| Correlated attempt | NOT RUN |
| D4 P1b | DEFERRED |

- Stop after the single correlated attempt or prelaunch failure.
- Never reset/reconnect USB, move cables, reload FPGA, or retry under this contract.
- Preserve the existing failed transcripts and passive diagnostic unchanged.
- Update `docs/hardware_evidence.md` with supported evidence only; leave visibility unclaimed without an operator report.
- This draft was superseded before helper implementation or hardware action. The read-only context comparison is recorded in `build/gpu/t1r_palette_pair_20261001/execution_context_compare_01.txt`: the default sandbox was in mount namespace `4026533125` and could not see either serial path, while the approved host context was in mount namespace `4026531832` and saw `/dev/ttyUSB0` and the frozen by-id link. Do not implement or run this correlated helper unless a later contract requires it.
