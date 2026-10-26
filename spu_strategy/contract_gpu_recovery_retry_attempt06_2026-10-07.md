# Contract: Wukong T1G Recovery Retry — Attempt 06

**Campaign:** `gpu_wukong_baseline_recovery_2026-10-06`  
**Amendment date:** 2026-10-07  
**Status:** ACTIVE for one final attempt only  
**Owner authorization:** “Let's retry. It's currently functional and stable.”

## 1. Exact commands

Run physical commands in the approved host execution context with the
original CH340 by-id node. Never run them in the restricted workspace
sandbox.

```bash
python3 tools/load_gpu_t1g_sram.py \
  --attempt 6 \
  --evidence-dir build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/attempt_06/programming_01
```

Proceed only if the loader result has exactly one `COMPLETE` terminal marker,
the expected IDCODE `0x3631093`, the frozen T1G hash, exit 0, and
`isc_done=1`, `init=1`, `done=1`. Observe stable VGA lock before UART traffic.

```bash
python3 tools/run_gpu_t1g_demo.py --execute \
  --port /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 \
  --load-evidence-dir build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/attempt_06/programming_01 \
  --evidence-dir build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/attempt_06/t1g_demo_01
```

Observe each scene and enter `PASS: <observation>` only when lock is stable
and the expected state is visible. The runner stops at its 15-minute deadline
from the first load command, including while waiting for observations. Stop at
the first unexpected image or transmission result.

## 2. Frozen budget

```text
additional attempts:                  1 (attempt 06 only)
maximum elapsed time:                 15 minutes from first JTAG detect
maximum additional cumulative time:   15 minutes
maximum SRAM loads:                   1
maximum UART scene sends:             6 (two A/B/C cycles)
maximum UART sends per attempt:       6
additional resets:                   0
additional power cycles:              0
additional wiring changes:            0
additional analyzer captures:         0
flash writes:                         0
```

This amendment uses the last attempt and SRAM-load slots of the original
campaign. It does not raise the original campaign ceilings of six attempts,
six SRAM loads, 36 UART sends, or 90 cumulative minutes. Do not start another
attempt or continue after any deadline/budget stop without a new owner
contract.

## 3. Acceptance

Require stable VGA lock and two operator-observed A/B/C cycles with the
expected Scene A image and visible B then C changes. Record each packet as
`UART_OPEN_FAILURE_ZERO_BYTES`, `ZERO_BYTE_WRITE_FAILURE`,
`PARTIAL_TRANSMISSION`, `FULL_PACKET_WRITTEN_DRAIN_FAILED`, or
`COMPLETED_HOST_WRITE`. Host writes and `tcdrain` do not prove FPGA receipt,
CRC acceptance, activation, or exact pixels.

Attempt 05 showed stable lock and a visible Scene B change, but Scene B was
sent after its expired time limit. Preserve it as out-of-budget evidence;
do not count it toward attempt 06 acceptance.
