# Engineering Contract: T1q Scaled Visibility Diagnostic

**Date:** 2026-10-01  
**Contract ID:** `GPU-T1Q-SCALED-VISIBILITY-2026-10-01`  
**Status:** `SRAM RELOAD PASS; UART TRANSPORT PASS; SCALED VISUAL PASS ON AUTHORIZED REPLAY`  
**Owner:** John Curley  
**Spec Author:** Codex

## 1. Objective and scope

Distinguish a too-small scene from the unresolved T1q receive/commit/render
path by replaying the existing Q1 bitstream with one oracle-checked 4x-scaled
T1i geometry sequence. Preserve the four truth-table tuples and `CCCCCCCC`
selectors used previously. Do not modify RTL, rebuild, write flash, or claim
FPGA packet acceptance or exact physical pixel correspondence.

The owner authorized this bounded campaign on 2026-10-01. SRAM, transport,
and operator-observed visual outcomes are recorded in §6.

## 2. Frozen source, artifact, and expected scene

Start with the 175-byte wire in
`fixtures/gpu_t1i_scene_a_wire_175b.hex` and the Q1 bitstream
`build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.bit` (SHA-256
`c2458086d6efcc323f70039dce87754ae6ff8bcf8012aed2e1404862332a728d`).
Derive the new 175-byte wire by multiplying each of the twelve signed 32-bit
edge constants, three per lane, by exactly four. Preserve all other geometry,
depth, and U/V bytes. Reject signed 32-bit overflow.

The derived geometry wire must hash to
`1b6b066639da98f914f3e8512150656631dd7a55e18b6a1f65b9b7f222ca66df`.
The independent 640x480 T1i oracle, using selector bit 12 for both U and V,
must report:

| Measure | Frozen result |
|---|---:|
| Valid pixels | 38,561 |
| Winner counts, lanes 0..3 | `[11964, 11723, 7635, 7239]` |
| Bounds | x=40..280, y=40..360 |
| A→B changed pixels | 38,561 |
| B→C changed pixels | 11,389 |
| C→A changed pixels | 27,172 |

Append per-lane table bytes at wire offsets `175..178` and selector bytes
`CC CC CC CC` at `179..182`. The ordered table tuples are A
`00 00 00 00`, B `0F 0F 0F 0F`, C `06 06 06 06`, return A
`00 00 00 00`. Require 183 bytes per packet and byte-identical A/return A.
Expected packet SHA-256 values are:

| Packet | SHA-256 |
|---|---|
| A / return A | `3ef25319403e9d8a9f8f5dd3702377f96071a7b1a695833fe503dca45d66f44b` |
| B | `009fe91ee376144fd6a64b143e84bd80a1ec317d5a9c622ff70906a05f882eb8` |
| C | `69344794090086683633521df30e63f86423c4be60d15a9e05f6cbd6e591fad2` |

## 3. Bounded campaign and preconditions

After authorization, implement `tools/send_gpu_t1q_scaled_visibility.py` as a
focused sender that derives the scaled bytes, runs the independent oracle,
checks every frozen hash/count/bound, refuses input drift and transcript
overwrite, supports `--dry-run` and `--send`, configures 115200 8N1, requires
full writes and `tcdrain`, waits five seconds between packets, and records
monotonic per-packet timings and hashes.

Freeze one SRAM load attempt (120 seconds) and, only if it passes, one
four-packet UART attempt (60 seconds). Each launched action consumes its slot
on any outcome. No retry, reconnect, packet change, or profile change is
authorized.

Before hardware access, run:

```bash
test -f build/gpu/t1q_truth_table_20260929/build_seed1/run_02/COMPLETE
test -f build/gpu/t1q_truth_table_20260930/hardware/program_01.log
test -e /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0
test ! -e build/gpu/t1q_truth_table_20261001/scaled_visibility/program_02.log
test ! -e build/gpu/t1q_truth_table_20261001/scaled_visibility/sequence_01.json
sha256sum build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.bit
python3 -m py_compile tools/send_gpu_t1q_scaled_visibility.py
python3 tools/send_gpu_t1q_scaled_visibility.py --dry-run
git diff --check
```

Require all frozen hashes and oracle outputs to match §2; require exit 0 and
the SRAM transcript markers from the completed T1q transport contract. Stop
on any mismatch.

## 4. Hardware sequence after authorization

Create the evidence directory and load the exact existing bitstream once:

```bash
mkdir -p build/gpu/t1q_truth_table_20261001/scaled_visibility
set -o pipefail
timeout 120s openFPGALoader -c dirtyJtag --freq 1000000 \
  build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.bit \
  2>&1 | tee build/gpu/t1q_truth_table_20261001/scaled_visibility/program_02.log
```

Require exit 0, 100% SRAM load, `isc_done 1`, `init 1`, and `done 1`. Stop if
any check fails. Then send the derived sequence once:

```bash
timeout 60s python3 tools/send_gpu_t1q_scaled_visibility.py --send \
  --port /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 \
  --dwell-seconds 5 \
  --transcript build/gpu/t1q_truth_table_20261001/scaled_visibility/sequence_01.json
```

Require four ordered 183-byte writes, table tuples and selectors from §2,
four completed drains, exact A/return-A packet equality, and transcript hash
audit. The operator reports whether A/B/C transitions are visible and whether
the final image matches enlarged A. Do not infer those results from transport.

## 5. Interpretation and stop rules

If the enlarged transitions are visible, classify scene scale as a visibility
contributor and T1q broad visual behavior as operator-observed only. If stable
sync persists but no enlarged image appears, stop: packet receipt, commit,
activation, and material output remain unresolved. The next step would require
a separate receive/commit telemetry contract. No further transmission is
authorized by this budget.

## 6. Authorization and preflight record

Owner authorization was received on 2026-10-01 for exactly one reload of the
frozen T1q Q1 bitstream and one scaled A/B/C/return-A sequence under this
contract. The route marker/result, prior SRAM programming transcript, exact
UART path, artifact hash, and unused evidence paths passed preflight. The
sender's `py_compile`, dry-run oracle/hash audit, and `git diff --check`
returned exit 0. No hardware action had started at this point.

The single SRAM reload completed within the 120-second limit with exit 0.
The transcript records 100% load and `isc_done 1`, `init 1`, `done 1`;
SHA-256 `da4130eb31e500564a5b017544b128b144754cbc9fef33ce1238c3da42996605`.

The single scaled UART sequence completed within the 60-second limit with
exit 0. Transcript audit passed for all four ordered 183-byte writes, the
frozen oracle record and packet hashes, four `tcdrain` completions, and exact
A/return-A equality. Transcript SHA-256:
`73a1d126586ef6c4e7f303e82b6a37ea94934ac4692986f7d72f444bb15301d0`.
On the initial sequence the operator reported a blue triangle. The operator
later confirmed the complete yellow B, XOR C, and return-to-blue-A transitions
on the separately authorized replay below.

The owner authorized one unchanged replay under
`contract_gpu_t1q_scaled_visibility_replay_2026-10-01.md`. The operator
confirmed seeing yellow B, XOR C, and the return to blue A on that replay.
This closes the scaled A/B/C/return-A gate as operator-observed visual
evidence. It does not establish exact physical pixel correspondence.
