# Engineering Contract: T1q Scaled Visibility Replay

**Date:** 2026-10-01  
**Contract ID:** `GPU-T1Q-SCALED-VISIBILITY-REPLAY-2026-10-01`  
**Status:** `UART TRANSPORT PASS; A/B/C/RETURN-A VISUAL PASS (OPERATOR-OBSERVED)`  
**Owner:** John Curley  
**Spec Author:** Codex

## 1. Objective and scope

Replay the existing oracle-checked 4x-scaled T1q A/B/C/return-A sequence once
so the operator can observe its transitions. Do not reload or alter the
currently loaded FPGA bitstream. Do not change geometry, tables, selectors,
packet order, UART framing, or dwell. Claim host-to-CH340 transport only from
the transcript; record visual behavior only from operator observation.

## 2. Frozen inputs

| Item | Value |
|---|---|
| Bitstream SHA-256 | `c2458086d6efcc323f70039dce87754ae6ff8bcf8012aed2e1404862332a728d` |
| Sender SHA-256 | `c6b9274ed5f594dfb7befdbd8e46c826a99bc0e80feb52fbc7729884c6c86859` |
| Derived wire SHA-256 | `1b6b066639da98f914f3e8512150656631dd7a55e18b6a1f65b9b7f222ca66df` |
| UART | `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`, 115200 8N1 |
| Tables | A `00000000`; B `0F0F0F0F`; C `06060606`; return A `00000000` |
| Selectors | `CCCCCCCC` in every packet |
| Dwell | Five seconds between packets |
| Transcript | `build/gpu/t1q_truth_table_20261001/scaled_visibility/sequence_02.json` |

Require four 183-byte packets and exact A/return-A packet identity. Their
hashes and the 38,561-pixel oracle coverage are frozen in
`contract_gpu_t1q_scaled_visibility_2026-10-01.md`.

## 3. Preconditions and budget

Run from the repository root:

```bash
test -e /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0
test -f build/gpu/t1q_truth_table_20261001/scaled_visibility/sequence_01.json
test ! -e build/gpu/t1q_truth_table_20261001/scaled_visibility/sequence_02.json
sha256sum build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.bit tools/send_gpu_t1q_scaled_visibility.py
python3 tools/send_gpu_t1q_scaled_visibility.py --dry-run
```

Require hashes and dry-run oracle/packet results to match §2 and the frozen
scaled-visibility contract. Stop on any mismatch.

Owner authorization is one UART replay attempt, with a 60-second per-attempt
and cumulative limit. The attempt is consumed on any outcome. Do not retry,
reconnect, reprogram, or change packets under this authorization.

## 4. Replay

Send exactly once:

```bash
timeout 60s python3 tools/send_gpu_t1q_scaled_visibility.py --send \
  --port /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 \
  --dwell-seconds 5 \
  --transcript build/gpu/t1q_truth_table_20261001/scaled_visibility/sequence_02.json
```

Require exit 0. Audit four ordered full writes, frozen packet hashes, one
`tcdrain` completion per packet, and exact return-A equality. Record the
transcript SHA-256. Stop on any failure.

## 5. Interpretation and stop rule

Ask whether the operator saw the blue A image, yellow B, XOR C, and return to
the same blue A. Do not infer scene activation from host transport. This
contract authorizes no additional hardware action; a negative or ambiguous
observation requires a separate receive/commit diagnostic contract.

## 6. Replay result

The single replay completed within the 60-second limit with exit 0. Transcript
audit passed for four ordered 183-byte writes, frozen packet hashes, four
`tcdrain` completions, and exact A/return-A identity. Transcript SHA-256:
`5c2598430ad47079d61bf387a9fc2dd30ef1c0e762cfe599aa504ebfbe8c4bf9`.
The operator confirmed seeing the yellow B state, the XOR C state, and the
return to blue A. This closes the bounded scaled A/B/C/return-A visual gate as
`PASS (operator-observed, visual-only)`. No raw VGA capture or exact physical
pixel comparison was made. FPGA receipt/activation is supported by these
observed state changes, but byte-level receipt and per-pixel equivalence were
not directly measured.
