# Engineering Contract: T1r CH340 USB/Serial Disappearance Diagnosis

**Date:** 2026-10-01  
**Contract ID:** `GPU-T1R-USB-SERIAL-DIAGNOSTIC-2026-10-01`  
**Status:** COMPLETE — passive capture finished; prior CH340 path loss not reproduced  
**Owner:** John Curley  
**Spec Author:** Codex

## 0. Objective and boundary

Determine whether USB enumeration, udev, kernel TTY registration, or device-node visibility changes explain why the CH340 path disappeared between preflight and sender open. This is a passive diagnostic tranche only.

Do not run the T1r sender, open the serial port, transmit bytes, program FPGA SRAM, reset or power-cycle the board, reset USB, unplug or reconnect cables, change wiring, or substitute a serial adapter. Do not induce a disconnect. No T1r transport or visibility claim can result from this diagnostic.

Prior evidence remains unchanged: T1r SRAM programming passed, two UART sender invocations failed before opening the CH340 path with zero transmissions, and the path was visible during each immediate preflight. The frozen device is USB VID:PID `1a86:7523`; the expected by-id path is `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`.

## 1. Frozen capture budget and artifacts

| Action | Maximum | Limit |
|---|---:|---:|
| Passive capture campaign | 1 | 45 seconds of udev monitoring |

Store outputs under the new directory `build/gpu/t1r_palette_pair_20261001/usb_serial_diagnostic_01/`. Require the directory to be absent before launch; never overwrite prior evidence. Record UTC timestamps and exit status for each command. Expected artifacts:

- `before.txt`: timestamp, USB inventory, by-id links, ttyUSB nodes, and available CH340 udev properties.
- `udev_monitor.txt`: kernel and udev events with property records during the fixed observation window.
- `kernel_before.txt` and `kernel_after.txt`: recent kernel messages, preferably with journal timestamps.
- `after.txt`: timestamp and the same USB/by-id/tty/property inventory as `before.txt`.

## 2. Read-only capture commands

Run once in order, without intervening hardware or port actions:

```bash
test ! -e build/gpu/t1r_palette_pair_20261001/usb_serial_diagnostic_01
mkdir -p build/gpu/t1r_palette_pair_20261001/usb_serial_diagnostic_01
date -u --iso-8601=ns
lsusb
ls -l /dev/serial/by-id/
ls -l /dev/ttyUSB*
```

Capture the first command block's full output and exit statuses in `before.txt`. For each currently present `/dev/ttyUSB*` node, run and record:

```bash
udevadm info --query=property --name=<present-ttyUSB-node>
```

Capture recent kernel messages before monitoring:

```bash
journalctl -k --no-pager -o short-iso -n 300
```

If `journalctl` is unavailable or denied, record its failure and make one read-only fallback capture:

```bash
dmesg --ctime --level=err,warn,notice
```

Then start the event monitor exactly once:

```bash
timeout 45s udevadm monitor --kernel --udev --property
```

Record the monitor's complete output and status in `udev_monitor.txt`. Exit 124 after the full 45-second window is the expected observation-window completion. Any earlier exit is recorded as an incomplete capture; do not restart it.

Immediately after monitoring, capture `date -u --iso-8601=ns`, `lsusb`, `ls -l /dev/serial/by-id/`, `ls -l /dev/ttyUSB*`, and available `udevadm info --query=property --name=<present-ttyUSB-node>` output in `after.txt`. Capture recent kernel messages again using the same `journalctl` command, or the same `dmesg` fallback if journal access failed, in `kernel_after.txt`. Hash every artifact with `sha256sum` and record the hashes in `manifest.sha256`.

Inventory commands may return nonzero if a directory or matching tty node is absent; preserve that status and output as evidence. Do not treat an absent device as permission to inspect another adapter or change the bench setup.

## 3. Interpretation rules

- A kernel disconnect followed by a new USB add and tty add supports physical/logical USB disconnect and re-enumeration; it does not identify the initiating cause by itself.
- USB remains enumerated while the tty node is removed or re-added supports a driver/udev TTY registration transition.
- A changed USB bus/device address with the same VID:PID and serial identity supports re-enumeration.
- A stable 45-second capture shows only that no event was observed in that window; it does not explain the earlier disappearance.
- Correlation with JTAG/programming requires event timestamps overlapping the preserved SRAM-programming interval. Do not infer causality from sequence alone.
- Missing or permission-denied kernel logs are reported as unavailable; do not escalate privileges or alter system configuration under this contract.

No result from this contract authorizes a sender retry. A new UART attempt requires a separate contract and owner authorization after interpreting this capture.

## 4. Stop conditions and current evidence

- Stop at the end of the one capture, including an incomplete monitor result.
- Do not run a sender, open `/dev/ttyUSB*`, reset/reconnect USB, program the FPGA, or change wiring.
- Do not repeat or extend the capture window under this contract.
- D4 P1b remains deferred.

| Claim | Current state |
|---|---|
| T1r route / SRAM load | PASS |
| CH340 present at UART preflight | PASS at two preflight instants |
| CH340 path present at sender open | FAIL at two attempts; zero transmissions each |
| CH340 during passive capture | Present before and after as `/dev/ttyUSB0`; same udev identity |
| udev events in 45-second window | None observed |
| Recent kernel USB event | Disconnect at port `1-1.1`; distinct from CH340 port `1-1.4` |
| Disconnect/re-enumeration mechanism | UNRESOLVED — CH340 failure not reproduced; no causal link established |
| T1r UART transport / scaled visibility | NOT PROVEN |
| D4 P1b | DEFERRED |

## 5. Capture closeout

The one 45-second passive capture completed. The CH340 (`1a86:7523`, driver `ch341`) appeared before and after at USB path `1-1.4`, with `/dev/ttyUSB0` and the same by-id link. Its udev properties matched, including `USEC_INITIALIZED=17052731`. `udevadm monitor --kernel --udev --property` emitted only its start banner and no events; `timeout` status 124 marks the planned full-window completion.

The last 300 kernel messages were unchanged between before and after snapshots. They include `2026-10-01T23:29:32+13:00 ... usb 1-1.1: USB disconnect, device number 3`, two seconds before the before-snapshot at `2026-10-01T10:29:34Z`. That is port `1-1.1`, while the CH340 is on port `1-1.4`; it does not identify a CH340 disconnect and no cause is inferred. The prior disappearing-path event was not reproduced, so the reason remains unknown.

Evidence directory: `build/gpu/t1r_palette_pair_20261001/usb_serial_diagnostic_01/`. Artifact SHA-256 values are recorded in `manifest.sha256`. No sender, serial-port open, FPGA programming, USB reset, cable action, or retry occurred. This capture authorizes no further action.
