# Engineering Contract: T1D Scene B Transport Trace
**Date:** 2026-10-06
**Contract ID:** `gpu_t1d_scene_b_transport_trace_2026-10-06`
**Status:** DRAFT — trigger-arm indication requires qualification before activation

## 1. Objective and Scope

Load the pinned T1D diagnostic image into FPGA SRAM, then trace one T1D Scene B update across these boundaries:

1. Host sends the pinned 64-byte packet.
2. FPGA diagnostic record reports accepted byte count and payload CRC.
3. FPGA diagnostic record reports scene activation and active bank.
4. Operator reports the visible result and signal lock.

Do not reset, power-cycle, capture JTAG, or send Scene A. One SRAM load of the pinned T1D diagnostic image is now in scope by the owner's direction on 2026-10-06 (“Maybe it's better if you tried to overwrite that first?”). This load replaces the current volatile FPGA configuration and can briefly blank the display; it does not write configuration flash. This is a T1D 64-byte protocol campaign. Do not use the T1R 186-byte packet procedure.

Pinned Scene B artifact:

```text
build/gpu_evaluation/t1d_vertex_ab_20261004/scene_b_01/scene_packet.bin
bytes: 64
sha256: 156ab65f14559c350bc602d4a48ee441cc2b145bfaee1a7775cde067e395a61d
expected diagnostic payload CRC16: 0xC2D3
```

The scene packet is the 64-byte T1D wire image (start token `0xA5` followed by 63 payload bytes). The sender must verify the pinned hash and send the artifact without rewriting it.

## 2. Evidence and Limits

The analyzer observes the FPGA diagnostic UART output only. It does not observe the CH340 input waveform or prove voltage margins on the input UART.

The diagnostic UART is 115200 baud, 8N1, LSB-first, driven from the 25 MHz pixel clock with 217 clocks per bit. One complete 16-byte record takes about 1.39 ms. A falling edge on the diagnostic TX line begins the record.

Known connection: analyzer D0 / probe 1 → FPGA `diag_tx` at J10-7 / G6; analyzer ground → board ground. Verify this mapping and unchanged wiring before acquisition. The CH340 UART RX is a distinct signal and is not the analyzer channel in this contract.

The expected successful activation record has a valid record CRC8 and end marker `0x7E`, record type `0x02`, flags `0x7B`, accepted count `63`, payload CRC `0xC2D3`, reason `0x02`, ready `1`, and the active bank after activation. Preserve and decode raw samples before interpreting fields. A count or CRC mismatch identifies failure at or before FPGA byte acceptance; it does not by itself identify an electrical cause.

The diagnostic sequence field is a start-attempt sequence counter, not a completed-transaction counter. Do not use it as proof of transaction completion.

## 3. Acquisition Qualification — Must Pass Before UART

### 3.1 One SRAM Load of the Diagnostic Image

After recording fresh operator readiness, verify the artifact and FPGA identity, then load exactly once:

```bash
sha256sum build/d3_physical_diag_20260921/spu_a7_100t_GPUVGA_T1D_DIAG_S1.bit
timeout 15s openFPGALoader -c dirtyJtag --freq 1000000 --detect -v
timeout 60s openFPGALoader -c dirtyJtag --freq 1000000 build/d3_physical_diag_20260921/spu_a7_100t_GPUVGA_T1D_DIAG_S1.bit
```

Require the SHA-256 to equal `52d45da0743c326f1700b4efa7fa0187523ea6e456948f274e2cc276ccd7b914`, FPGA detection to identify the expected Artix-7 100T, and programming to exit zero. The command intentionally has no flash-write option. Record complete output and timestamps. If detection or programming fails, stop; do not send UART or retry the load.

After programming, record the operator's monitor lock and image report. The programmed T1D diagnostic constraints map `diag_tx` to J10-7/G6 and VGA VSync to J10-10/E5. The existing capture showing VSync-like pulses at G6 is a lead that the earlier loaded image did not match this diagnostic pin map; it does not identify the prior bitstream by itself.

### 3.2 Idle Capture

Use the currently enumerated FX2 analyzer bus.device identifier. Do not reuse a stale identifier. Create a new evidence directory under `build/gpu_evaluation/t1d_scene_b_transport_trace_20261006/` and refuse overwrite.

First run exactly one idle acquisition, with no UART activity:

```bash
timeout 15s sigrok-cli \
  --driver fx2lafw:conn=<CURRENT_BUS.DEVICE> \
  --config samplerate=24MHz \
  --channels D0 \
  --samples 750000 \
  --output-format srzip \
  --output-file build/gpu_evaluation/t1d_scene_b_transport_trace_20261006/preflight_idle.srzip
```

The 750,000 samples represent 31.25 ms at 24 MHz. Require all of the following before proceeding:

- command exit status is zero;
- the output archive exists, opens as srzip, and contains nonempty logic data;
- returned logic data contains exactly 750,000 samples (do not infer the count from the requested limit or file size alone);
- archive metadata reports samplerate `24 MHz`, probe 1 `D0`, and unitsize `1`;
- channel D0 is high throughout the idle preflight, consistent with the UART idle level;
- record command, analyzer identity, start/end UTC, raw stdout/stderr, metadata, sample count, and SHA-256.

On any failure, mark acquisition qualification `FAIL`, stop, and do not open or write the UART port.

## 4. Trigger-Arming Gate — Current Draft Blocker

The event capture must use a falling-edge trigger on D0 and retain 750,000 post-trigger samples. The candidate invocation is:

```bash
timeout 15s sigrok-cli \
  --driver fx2lafw:conn=<CURRENT_BUS.DEVICE> \
  --config samplerate=24MHz \
  --channels D0 \
  --wait-trigger \
  --triggers D0=f \
  --samples 750000 \
  --output-format srzip \
  --output-file build/gpu_evaluation/t1d_scene_b_transport_trace_20261006/scene_b_diag_tx.srzip
```

Do not send Scene B merely because the process exists or remains running. Before this contract can become active, qualify a machine-checkable indication that this exact installed `sigrok-cli` / `fx2lafw` combination has successfully started acquisition and is armed, waiting for the D0 falling edge. Record the exact tool versions, exact indication, and an offline/mock check of the send gate. If no unambiguous indication can be established, stop before UART and revise this contract; do not replace it with a guessed sleep.

After a future activation, the worker may send the packet only after all of these guards pass: successful idle preflight, verified trigger-arm indication, fresh operator readiness, unchanged wiring/configuration, pinned packet hash, pinned USB serial identity, and a new empty result directory. The worker must record the send authorization and consume its single packet slot before opening the UART device.

The trigger capture passes only with exit status zero, a valid srzip archive, exactly 750,000 returned logic samples, and the same metadata requirements as the idle preflight. A timeout, missing trigger, malformed archive, short count, wrong rate/channel, or decode failure closes the attempt and forbids a retry under this one-packet draft.

## 5. Operator Readiness and Observation

Immediately before the event capture is armed, obtain and record a current operator report confirming:

- FPGA board powered;
- wiring and loaded configuration unchanged;
- monitor signal lock stable;
- current image description;
- operator ready to send the one Scene B packet and report the resulting image.

After the decoded result is available, obtain a timely monitor report: signal-lock state and visible image. Keep the report separate from analyzer evidence. The previous software prediction is that pixel `(100,300)` changes from red to background; a verbal whole-screen report does not establish that pixel-level result unless the operator can inspect it directly.

## 6. Result Classification

| Result | Classification |
|---|---|
| Idle acquisition gate fails | `ANALYZER_ACQUISITION_UNQUALIFIED`; no UART was sent |
| No verifiable armed indication | `TRIGGER_ARM_UNQUALIFIED`; no UART was sent |
| Capture valid; no complete valid diagnostic record | `NO_VALID_FPGA_RECEIPT_RECORD` |
| Valid record, count not 63 or CRC not `0xC2D3` | `FPGA_RECEIPT_MISMATCH` |
| Valid count/CRC, no successful activation flags/reason | `RECEIVED_NOT_ACTIVATED` |
| Valid activation record with bank; visible prediction absent | `ACTIVATED_DISPLAY_MISMATCH` |
| Valid activation record and operator reports predicted visible change | `TRACE_PASS_FOR_THIS_SINGLE_SCENE_B_UPDATE` |

None of these outcomes alone proves an electrical UART waveform defect, full GPU correctness, or silicon acceptance beyond this single recorded transaction.

## 7. Budget and Stop Conditions

This draft describes exactly one idle preflight acquisition, one event acquisition, and at most one Scene B UART packet. The preflight does not consume a hardware packet slot. A launched event acquisition consumes the single attempt even if it fails, times out, or becomes unavailable. No retry, reset, reload, alternate packet, wiring change, or altered acceptance criterion is authorized by this draft.

The owner has authorized the single SRAM load described in §3.1. The previously failed wrong-pin and corrected-pin idle captures are retained and do not substitute for a post-load D0 qualification. The post-load idle capture and Scene B event capture remain `NOT RUN`; obtain fresh operator readiness immediately before each physical stage. No additional load or UART retry is authorized by this amendment.

## 8. Required Evidence Artifacts

Save under the unique campaign directory:

- analyzer identity and version report;
- exact command lines, timestamps, raw stdout/stderr, and exit statuses;
- both srzip archives, their hashes, metadata, and verified sample counts;
- trigger-arm proof and guard decision;
- exact Scene B packet hash and UART transcript;
- raw and decoded 16-byte FPGA diagnostic record;
- operator readiness and after-run image/lock reports;
- final classification with each boundary separately marked pass, fail, or not established.
