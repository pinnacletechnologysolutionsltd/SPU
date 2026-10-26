# Engineering Contract: T1q UART Replay

**Date:** 2026-09-30  
**Contract ID:** `GPU-T1Q-UART-REPLAY-2026-09-30`  
**Status:** `UART TRANSPORT PASS; NO VISIBLE OUTPUT (OPERATOR-REPORTED)`  
**Owner:** John Curley  
**Spec Author:** Codex

## 1. Objective and evidence boundary

Replay the exact T1q A/B/C/return-A sequence once so the operator can check
the display again. Do not reprogram the FPGA or change the bitstream, fixture,
selectors, tables, packet order, baud rate, or dwell. This replay can establish
host-to-CH340 delivery only. Record any visible response separately as an
operator observation; do not claim FPGA acceptance or physical pixel match.

## 2. Frozen inputs

| Item | Value |
|---|---|
| Loaded SRAM artifact | `build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.bit` |
| Bitstream SHA-256 | `c2458086d6efcc323f70039dce87754ae6ff8bcf8012aed2e1404862332a728d` |
| Sender SHA-256 | `be0c660f8363200bbf8ec75f28c46e01a6d8958cbbaf6d4061e43499e0c9912a` |
| UART | `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` |
| Sequence | A `00000000`; B `0F0F0F0F`; C `06060606`; return A `00000000` |
| Selectors | `CCCCCCCC` for all packets |
| Framing and dwell | 115200 8N1; five seconds between packets |
| Transcript | `build/gpu/t1q_truth_table_20260930/hardware/sequence_02.json` |

The sender pins the decoded 175-byte geometry fixture. Each wire packet is
183 bytes. The final A packet is byte-identical to the first A packet.

## 3. Preconditions and budget

Run from the repository root:

```bash
test -e /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0
test -f build/gpu/t1q_truth_table_20260930/hardware/sequence_01.json
test ! -e build/gpu/t1q_truth_table_20260930/hardware/sequence_02.json
sha256sum build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.bit tools/send_gpu_t1q_sequence.py
```

Require the bitstream and sender hashes to match §2. Stop if the UART path is
absent or any frozen input differs. Do not substitute a device or reload the
FPGA under this contract.

The budget is one UART sequence attempt, maximum 60 seconds cumulative and
per attempt. The attempt is consumed on any outcome. Do not retry, reconnect,
or modify the packet sequence.

## 4. Replay

Send exactly once:

```bash
timeout 60s python3 tools/send_gpu_t1q_sequence.py --send \
  --port /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 \
  --dwell-seconds 5 \
  --transcript build/gpu/t1q_truth_table_20260930/hardware/sequence_02.json
```

Require exit 0. Audit for four ordered 183-byte writes, the frozen table and
selector bytes, one `tcdrain` completion per packet, and exact A/return-A
packet hash equality. Record the transcript SHA-256. Stop on failure or any
mismatch.

## 5. Interpretation

Report host-to-CH340 transport independently from operator observation. Ask
the operator whether the A/B/C/return-A changes are visible and whether the
final A state is visible. A negative or unclear observation does not authorize
another transmission, FPGA reprogramming, or a changed scene; those require a
new contract and budget.

## 6. Replay result

The single replay completed within the 60-second limit with exit 0. Transcript
audit passed for the ordered four 183-byte writes, frozen table and selector
bytes, four `tcdrain` completions, and exact A/return-A packet identity.
Transcript SHA-256:
`5ce5df993202bf4ddfac50ab9fea65bddba7cf1df422b637c97550e182d806e9`.
This confirms repeat host-to-CH340 transport. The operator's display
observation was: stable monitor sync, but no visible image during the replay.
FPGA packet acceptance and physical pixel behavior remain unmeasured.

## 7. Read-only diagnosis (2026-10-01)

No source-level contradiction was found in the reviewed T1q packet layout or
truth-table lookup: the loader expects 182 payload bytes after `A5`, reads
tables from payload bytes 174..177, selectors from 178..181, and commits only
after a later frame activation. The routed Q1 image was loaded successfully.

The remaining evidence gap is between host transport and rendered output.
`sequence_02.json` proves complete writes and `tcdrain` at the CH340. The
focused T1q testbench's `send_byte` task drives `scene_rx_byte` and
`scene_rx_valid` directly, so it does not exercise the board's `spu_uart_rx`
or prove hardware receipt, bank commit, or frame activation. The Q1 bitstream
was built with UART receive enabled but without `GPU_T1D_DIAG`; it has no
receive/commit telemetry output.

The Q1 fixture-sequence simulation also uses zero selector bytes for A/B/C;
its selector-`FF` endpoint check forces the selected register directly. The
hardware sender's `CCCCCCCC` selector packet therefore lacks an end-to-end
loader-to-material simulation case, even though each selector nibble value
is within the documented range.

Visibility is also a plausible confounder: the Q1 packets use the same small
175-byte geometry fixture as the earlier T1p test. That fixture covers about
2,441 of 307,200 active pixels (0.8%) in the prior oracle record. The prior
T1p 4x-scaled scene covered 38,561 pixels (12.6%) and produced operator-seen
transitions. Those T1p results do not prove T1q behavior.

Classification: unresolved hardware receive/commit/render path; small scene
visibility is a plausible but unproven contributor. Any scaled-scene send or
telemetry build needs its own owner-authorized contract and attempt budget.
