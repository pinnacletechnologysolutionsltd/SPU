# Wukong GPU bring-up runbook

Use this procedure on the QMTech Wukong Artix-7 100T. The operational
recovery baseline is the retained September 23 T1G image. It was reloaded on
2026-10-06; the operator observed red-left/green-right inverted triangles
with stable lock, then visible B and C scene changes in two A/B/C cycles.
This is operator-observed visual evidence, not pixel capture or FPGA receipt
telemetry. The September 6 static image loaded but produced a blank monitor in
that recovery session; it is not the operational recovery baseline.

On October 7, attempt 06 loaded T1G and completed six host writes, but the
cycle 2 C observation was not received before its deadline. Attempt 07 loaded
T1G, but the post-load lock response arrived after the 180-second gate; no
UART was opened and no scene was sent. Both remain INCOMPLETE.

Attempt 08 passed the bounded two-cycle A/B/C visual acceptance sequence with
explicit operator confirmations and stable lock. All six 127-byte host writes
and drains completed with the recorded 20 ms post-drain delay, 31.1 ms minimum
start interval, and three-second inter-scene dwell. It finished before the
shared 30-minute deadline. The campaign stopped after PASS; further hardware
work requires a new owner contract. See the campaign closeout and evidence
ledger §3.37. This is operator-observed scene switching, not physical pixel
equality or measured FPGA receipt.

## Frozen baseline

```text
Board       QMTech Wukong XC7A100T-FGG676; JTAG IDCODE 0x3631093
Bitstream   build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit
SHA-256     e16dc6992c60de99d9f5d9a5cc10c3aff99a245b5f5da6035887f2c92cb68fa5
Source      build/t1f_clean_qualification_20260922, commit a64d87c7ae0d96b44d8178c20f2421376a975ac0
Pixel clock 50 MHz oscillator divided by two: 25 MHz
VGA         R=G8, G=G7, B=G5, HSYNC=D5/J10-4, VSYNC=E5/J10-10
            G6/J10-7 is unused by this image
UART        CH340, 115200 baud, 8N1; use its /dev/serial/by-id path
Packets     A, B, C; 127 bytes each, begin with A5
Scene A     red-left/green-right inverted triangles; stable signal lock
Scene B/C   visible image changes from the preceding scene; lock stays stable
```

The retained sender source is
`build/t1f_clean_qualification_20260922/build/t1g_h1_20260923/send_sequence.py`
(SHA-256 `f3f4d8c4eabaed5e149689cd84dea25771ffbdd7cc2db9058aecc1b5f3cbee60`).
For one packet, use `tools/send_gpu_t1g_scene.py`: it verifies the frozen
fixture hashes, completes positive partial writes, records partial progress on
transmission errors, and refuses to overwrite a transcript. For the complete
demo, use `tools/run_gpu_t1g_demo.py` as described below.

## Reference procedure — inactive without a new hardware contract

Create a fresh run directory for each campaign. Change the example ID before
running it.

```bash
RUN_DIR=build/gpu_campaign/t1g_replay_YYYYMMDD
ATTEMPT=01
mkdir -p "$RUN_DIR/attempt_$ATTEMPT"
sha256sum \
  build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit \
  build/t1f_clean_qualification_20260922/build/t1g_h1_20260923/send_sequence.py \
  tools/send_gpu_t1g_scene.py \
  fixtures/gpu_t1f_scene_wire_127b.hex \
  fixtures/gpu_t1f_coverage_scene_wire_127b.hex \
  fixtures/gpu_t1g_scene_c_wire_127b.hex
git -C build/t1f_clean_qualification_20260922 status --short
git -C build/t1f_clean_qualification_20260922 rev-parse HEAD
ls -l /dev/serial/by-id
```

Confirm the original monitor and VGA harness are connected as listed above,
the CH340 by-id path is the GPU UART, the board is powered, and no analyzer
lead is loading a VGA or UART signal. After a host restart, wait for USB
enumeration and verify the adapter is present before beginning the bounded
attempt. The `john` account is a member of `uucp`; a host login process should
therefore have effective `uucp` access to the `root:uucp` mode-0660 node. The
workspace agent sandbox may omit that supplementary group or may not retain
the host device node. In that case, do not retry from the sandbox: run the
hardware command in the authorized host context. The sequence manifest records
its effective groups, node identity, permissions, and any UART-open failure.
Record operator, UTC time, monitor input, and wiring map. If the retained
source checkout is dirty or its commit differs, stop and record that before
using it to interpret the image.

The workspace agent sandbox does not inherit the host `uucp` group and does
not consistently expose host `/dev` nodes. Execute the following physical
command in the approved host context, outside that sandbox. It verifies the
frozen artifact, detects and requires the Wukong IDCODE, then runs the exact
SRAM-only load command. It retains the full command output and exit result so
a missed interactive tool session cannot turn a completed load into an
unclassified attempt:

```bash
python3 tools/load_gpu_t1g_sram.py \
  --attempt "$ATTEMPT" \
  --attempt-limit-seconds 1800 \
  --evidence-dir "$RUN_DIR/attempt_$ATTEMPT/programming_01"
```

Require exactly one terminal marker in that evidence directory: `COMPLETE`,
`FAILED`, or `TIMEOUT`. Only `COMPLETE` means the command exited zero and all
three DONE flags were present. No marker means unavailable; do not infer a
result from the log, elapsed time, or a closed agent session. Never add `-f`
or use a flash command.

Observe the monitor and explicitly confirm stable lock and a visible image
within 180 seconds after loading and before UART opens. If lock is absent or
confirmation times out, stop. Identify the CH340 from `ls -l
/dev/serial/by-id`; use its stable by-id path. The one-command runner sends
A/B/C twice with explicit ordinal-labelled observation gates and three-second
dwell after each confirmation. Observe throughout. A should show red-left and
green-right inverted triangles; B and C should visibly change the image from
the preceding scene while lock remains stable. Cycle 2 A must match A; no
visible C-to-A transition is required.

```bash
python3 tools/run_gpu_t1g_demo.py --execute \
  --observation-timeout-seconds 180 \
  --send-drain-bound-seconds 5 \
  --port /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 \
  --load-evidence-dir "$RUN_DIR/attempt_$ATTEMPT/programming_01" \
  --evidence-dir "$RUN_DIR/attempt_$ATTEMPT/t1g_demo_01"
```

The loader records its first hardware-action monotonic timestamp, absolute
1800-second deadline and host boot ID. The runner validates and uses that exact
deadline; it does not start a new allowance. It checks before UART open and
before every packet. Each write/drain/post-drain transaction has an enforced
five-second worker bound. Positive short writes continue only from the
unwritten suffix; the packet is never restarted and accepted bytes are never
replayed. The sender waits 20 ms after `tcdrain`; the runner enforces the
31.1 ms minimum start-to-start interval and three-second scene dwell. These
timeouts are stop policies, not delivery guarantees.

The runner refuses an existing evidence directory, validates the frozen
fixtures, opens and configures the CH340 once for the complete sequence, and
retains one transcript plus stdout/stderr per send in `t1g_demo_01/`. Holding
one descriptor avoids repeated open/close line-state changes. A missing or
inaccessible node is recorded as a terminal `FAILED` manifest before any
packet write. A disconnect during a packet preserves the confirmed partial
byte count and stops the sequence; it never switches to another device node.
It records each send as `UART_OPEN_FAILURE_ZERO_BYTES`,
`ZERO_BYTE_WRITE_FAILURE`, `PARTIAL_TRANSMISSION`,
`FULL_PACKET_WRITTEN_DRAIN_FAILED`, or `COMPLETED_HOST_WRITE`. It stops on the
first sender failure. `HOST_SENDS_COMPLETE` records host writes only; it does
not prove FPGA receipt, CRC acceptance, bank activation, or visible output.
Save operator, lock and A/B/C observations in a separate
`operator_observation.json` beside `sequence.json`.

## First-failure recovery — inactive without an authorizing contract

Stop at the first failed boundary. Preserve command output, artifact hash,
transcript and operator observation. The table is diagnostic guidance only;
each recovery operation, especially a reload or rollback, requires an active
contract that specifies the exact action and budget. Change one cause at a
time.

| First failure | Next action |
|---|---|
| Wrong or absent JTAG ID | Check board power and JTAG connection; retry detection once within budget. Do not load or send UART. |
| SRAM load fails or DONE flags are absent | Preserve the log; correct the identified host/JTAG issue, then use one bounded reload. Never write flash. |
| Load passes but VGA has no lock | Check monitor input and the frozen J10 DAC harness/pin map. Do not send scene packets without lock. |
| Lock is stable but A is absent | Check the by-id CH340 endpoint and packet transcript. Choose a measurement that distinguishes FPGA receipt, activation and rendering. |
| A works but B/C does not visibly change | Keep image and packet hashes fixed; record the first failing scene. Do not infer FPGA receipt from `tcdrain`. |
| Candidate image fails | Reload this exact T1G hash, send A/B/C, and confirm recovery before another candidate attempt. |

Do not add analyzer leads, reset, power cycle, wiring change, new image or
packet format unless the active campaign explicitly budgets and authorizes
that action. Stop on smoke, unusual heat, unstable power, unknown pin identity,
repeated loss of JTAG, flash-write requirement or exhausted budget.

Store readiness, wiring, command output, source/image/tool/fixture hashes,
transcripts, observations and failures under the fresh campaign directory.
Mark each boundary `PASS`, `FAIL` or `NOT MEASURED`. Report operator display
evidence separately from simulation, captured pixels and internal telemetry.
When both A/B/C cycles meet the campaign criteria, record `COMPLETE` and stop;
unused attempt or send budget does not authorize extra experiments.
Historical T1G evidence is in [`docs/hardware_evidence.md`](hardware_evidence.md)
§3.12; the October 6 recovery replay is in §3.36. Its raw records are in
`build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/`.

## T1H visual replay — H1 remains on hold

T1G-to-T1H protocol and profile differences, the retained source provenance
limit, and the fresh offline oracle result are recorded in
`build/gpu_evaluation/t1g_t1h_offline_qualification_20261007/source_compare.md`.
The current check `python3 software/tests/test_gpu_t1h_attribute.py` passed
40,000 active pixels and 715 focused edge samples. This is simulation evidence
from the current dirty checkout, not a rebuild or proof of the historical
T1H artifact's exact source identity.

T1H uses 151-byte transactions and adds per-vertex scalar interpolation. Its
diagnostic image makes the scalar bit-14 threshold visible as black and white.
The earlier physical purple edge fringe remains unexplained; the historical
analyzer capture missed the edge, and the owner's stop on further analyzer
captures remains in force. The owner-ratified visual-replay contract and
T1H-specific offline loader, sender and runner are recorded in
`spu_strategy/contract_gpu_t1h_visual_replay_2026-10-07.md`. The bounded
A/B/C/A replay passed: stable lock, expected grayscale-threshold scene
changes, completed host writes/drains, 20 ms post-drain delays, and required
pacing were recorded. The operator did not see the historical purple fringe
during this replay. Its historical observation remains valid and its cause
remains unresolved, so **T1H H1 remains HOLD**. The conditional T1G recovery
was not used; the campaign stopped after PASS. No further T1H or T1G hardware
operation is authorized by this completed campaign. Full evidence is in
`build/gpu_evaluation/t1h_visual_replay_20261007/campaign_01/`, including
`campaign_closeout.md`. CPU arithmetic and normalization remain the main
development priority.
