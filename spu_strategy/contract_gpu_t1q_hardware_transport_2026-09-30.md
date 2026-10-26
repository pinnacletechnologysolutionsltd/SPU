# Engineering Contract: T1q SRAM Programming and UART Transport

**Date:** 2026-09-30  
**Contract ID:** `GPU-T1Q-HARDWARE-TRANSPORT-2026-09-30`  
**Status:** `COMPLETE; SRAM PROGRAMMING PASS; UART TRANSPORT PASS`  
**Owner:** John Curley  
**Spec Author:** Codex  
**Halt-and-Flag Implementer:** Codex  
**Integration Auditor:** transcript audit plus owner evidence review

## 0. Objective and evidence boundary

Program the routed T1q Q1 bitstream into FPGA SRAM, then send one frozen
four-packet A/B/C/return-A scene sequence to the CH340 UART. This contract
establishes only the named SRAM load and host-to-UART transport if their
transcripts meet the gates below. It does not establish packet acceptance,
display response, physical pixel equality, or persistent configuration flash.

No SRAM programming or UART transmission is authorized while this document is
in `DRAFT`. After owner authorization, execute the ordered steps below once.
Do not repeat programming or transmission under this budget. The owner
authorized this contract on 2026-09-30.

## 1. Frozen artifact and packet definition

Use the routed T1q Q1 artifact from the completed route recovery:

| Item | Frozen value |
|---|---|
| Bitstream | `build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.bit` |
| Bitstream SHA-256 | `c2458086d6efcc323f70039dce87754ae6ff8bcf8012aed2e1404862332a728d` |
| Route evidence | `build/gpu/t1q_truth_table_20260929/build_seed1/run_02/` |
| Pixel timing | `36.92 MHz PASS` against `25.00 MHz` |
| Geometry source | `fixtures/gpu_t1i_scene_a_wire_175b.hex` |
| Decoded geometry SHA-256 | `8077acb3efbb92756fdee4c137500417e32f6f3664784c3b21f150c398d0dae9` |
| UART | `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` |
| Framing | `115200 baud, 8 data bits, no parity, 1 stop bit` |

The geometry source is exactly 175 bytes and begins with `A5`. Append the four
T1q table bytes at wire offsets `175..178`, followed by four selector bytes at
`179..182`, for a total wire length of 183 bytes. Use selector tuple
`[CC, CC, CC, CC]` for every scene, holding geometry and predicate selection
constant while changing only truth tables.

| Scene | Table bytes | Expected logic |
|---|---|---|
| A | `[00, 00, 00, 00]` | Constant false |
| B | `[0F, 0F, 0F, 0F]` | Constant true on valid winning fragments |
| C | `[06, 06, 06, 06]` | XOR of selected predicate bits |
| Return A | `[00, 00, 00, 00]` | Byte-identical to initial A |

Invalid or uncovered fragments remain black. Valid false/true retain the
T1q blue/yellow color mapping. The table high nibble is zero in every packet.
The sequence is transport evidence; these expected colors are design
semantics, not a visual pass criterion in this contract.

## 2. Halt-and-flag review

1. **Artifact identity:** stop if the bitstream or geometry SHA-256 differs.
   Do not rebuild, retag, or substitute an artifact under this budget.
2. **Packet layout:** stop if the fixture is not 175 bytes, a packet is not
   183 bytes, the table bytes do not occupy wire offsets `175..178`, or
   selector bytes do not occupy `179..182`.
3. **Transport scope:** a successful write and `tcdrain` establish only
   host-to-CH340 delivery. They do not establish that the FPGA accepted or
   rendered a packet.
4. **Visual scope:** no camera capture or operator visual gate is defined.
   Do not claim a visible transition or pixel-level match from this contract.
5. **Persistence:** use SRAM programming only. Do not write configuration
   flash.

## 3. Preconditions and bounded budget

From the repository root, first run:

```bash
test -f build/gpu/t1q_truth_table_20260929/build_seed1/run_02/COMPLETE
test ! -e build/gpu/t1q_truth_table_20260929/build_seed1/run_02/FAILED
test ! -e build/gpu/t1q_truth_table_20260929/build_seed1/run_02/TIMEOUT
python3 -c 'import json; p="build/gpu/t1q_truth_table_20260929/build_seed1/run_02/result.json"; d=json.load(open(p)); assert d["exit_code"] == 0, d'
test -f build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.bit
test -e /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0
sha256sum build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.bit
python3 -c 'import hashlib,pathlib; b=bytes.fromhex(pathlib.Path("fixtures/gpu_t1i_scene_a_wire_175b.hex").read_text()); assert len(b)==175 and b[0]==0xA5 and hashlib.sha256(b).hexdigest()=="8077acb3efbb92756fdee4c137500417e32f6f3664784c3b21f150c398d0dae9"'
test ! -e build/gpu/t1q_truth_table_20260930/hardware/program_01.log
test ! -e build/gpu/t1q_truth_table_20260930/hardware/sequence_01.json
```

Require the two hashes to match §1 and require the completed route evidence to
contain exactly one `COMPLETE` marker paired with exit 0. Stop if any
precondition fails.

The frozen campaign budget is:

| Action | Maximum attempts | Per-attempt limit | Cumulative limit |
|---|---:|---:|---:|
| SRAM programming | 1 | 120 s | 120 s |
| Four-packet UART sequence | 1 | 60 s | 60 s |

Launching an action consumes its slot regardless of outcome. Do not retry,
increase a limit, reset/reconnect the board, or substitute another artifact
without a renewed owner authorization.

## 4. Execution sequence after authorization

### 4.1 Static packet preflight

Implement `tools/send_gpu_t1q_sequence.py` as a focused sender. Pin the fixture
and bitstream hashes in the script; refuse altered inputs, an existing
transcript, short writes, or any packet that violates the layout in §1. The
sender must support `--dry-run` and `--send`, set 115200 8N1, require complete
writes and `tcdrain`, wait five seconds between packets, and write a transcript
with ordered packet hashes, byte counts, drain completion, and monotonic
timings. Ensure return-A is byte-identical to A. Do not add visual assertions.

Run the static checks before touching hardware:

```bash
python3 -m py_compile tools/send_gpu_t1q_sequence.py
python3 tools/send_gpu_t1q_sequence.py --dry-run
git diff --check
```

Require the sender to report four 183-byte packets with the table and selector
bytes specified in §1. Stop if the preflight fails.

### 4.2 SRAM programming

Launch exactly once and preserve the complete console transcript:

```bash
mkdir -p build/gpu/t1q_truth_table_20260930/hardware
set -o pipefail
timeout 120s openFPGALoader -c dirtyJtag --freq 1000000 \
  build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.bit \
  2>&1 | tee build/gpu/t1q_truth_table_20260930/hardware/program_01.log
```

Require exit 0, `Load SRAM 100.00%`, and reported `isc_done 1`, `init 1`, and
`done 1`. Record the transcript SHA-256. On any other result, stop; do not
transmit UART packets under this contract.

### 4.3 UART transport

Only after §4.2 passes, send exactly once:

```bash
timeout 60s python3 tools/send_gpu_t1q_sequence.py --send \
  --port /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 \
  --dwell-seconds 5 \
  --transcript build/gpu/t1q_truth_table_20260930/hardware/sequence_01.json
```

Require exit 0 and audit the transcript for four ordered complete writes,
183 bytes per packet, table values matching §1, selector tuple `CCCCCCCC`,
`tcdrain_completed=true` for each packet, and exact A/return-A hash equality.
Record the transcript SHA-256. Stop on any mismatch; no retransmission is
authorized.

## 5. Result reporting and stop rules

Report the two claims independently:

- **SRAM programming:** PASS only when the exact bitstream hash was loaded and
  the programmer transcript meets §4.2. Persistent flash remains `NOT RUN`.
- **UART transport:** PASS only when the transcript meets §4.3. FPGA packet
  acceptance, display response, visual transition, and physical pixel match
  remain `NOT MEASURED`.

Stop on a changed hash, missing device, failed programming, missing or
malformed transcript, short write, failed drain, or any packet mismatch. A
failed or interrupted action consumes its slot. Any visual qualification,
repeat, or changed sequence requires a separate contract and frozen budget.

## 6. Authorization and preflight record

Owner authorization was received on 2026-09-30. An initial device-path check
in the restricted execution namespace returned exit 1. A host-shell
read-only check then found CH340 `1a86:7523`; the frozen path resolved to
`/dev/ttyUSB0`. The complete host-shell preflight passed: the route has its
sole `COMPLETE` marker and exit 0, bitstream and decoded fixture hashes match
§1, and output/transcript paths are absent.

The sender static preflight passed on 2026-09-30: `py_compile`, `--dry-run`,
and `git diff --check` returned exit 0. The dry-run reported four 183-byte
packets with tables `00000000`, `0F0F0F0F`, `06060606`, `00000000`, selector
tuple `CCCCCCCC`, and identical A/return-A SHA-256
`a37d33e9c98f3c0dc16f3a92670fd47c49bc98163618119c3b02cf493d37e521`.
No hardware attempt had been launched at this point.

The single SRAM programming attempt then completed within its 120-second
limit. The exact bitstream was loaded with exit 0; the transcript contains
`Load SRAM: 100.00%`, `isc_done 1`, `init 1`, and `done 1`. Transcript SHA-256:
`da4130eb31e500564a5b017544b128b144754cbc9fef33ce1238c3da42996605`.
Persistent configuration flash was not written.

The single UART sequence completed within its 60-second limit. Its ordered
transcript audit passed for four full 183-byte writes, table values and
selectors from §1, `tcdrain` completion on every packet, and exact A/return-A
packet identity. Transcript SHA-256:
`f5621af9dcc54f7e0db422de00a26346889fe31278aa0bca9a9eda7a3ce48d15`.
Packet hashes were A/return-A `a37d33e9c98f3c0dc16f3a92670fd47c49bc98163618119c3b02cf493d37e521`,
B `5f13a6f1a776bd98acfd02cb51df10f32ed671c5437f3e4b820c95a9105c0330`, and
C `aa48aeca133c5b2f0e126248b6e8fe192ecb05b62db5df836d430cbd4f382188`.
These records establish host-to-CH340 transport only. FPGA packet acceptance,
display response, visual transition, and physical pixel match remain
`NOT MEASURED`.
