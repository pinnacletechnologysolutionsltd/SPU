# Engineering Contract: Frozen T1H Scalar-Diagnostic Visual Replay

**Contract ID:** `GPU-T1H-VISUAL-REPLAY-2026-10-07`
**Date:** 2026-10-07
**Owner:** John Curley
**Status:** **DRAFT — NOT RATIFIED; HARDWARE HALTED**
**Preparation authority:** Offline source review, runner preparation, and offline checks only.

## 1. Objective and evidence boundary

After explicit ratification, perform one bounded operator-observed replay of
the retained T1H scalar-diagnostic image using frozen scenes A/B/C/A. The
replay records stable lock, the grayscale scene changes, and whether the
historically reported purple edge fringe is visible. It does not change RTL,
build an image, capture analyzer data, or determine the fringe's cause.

The owner reports no visual limitation currently visible. This is a current
operator report; it does not replace the historical report of a purple fringe
in `docs/hardware_evidence.md` §3.13 or close the unresolved H1 audit. The
operator must report the fringe's presence or absence during this replay.
Neither outcome alone diagnoses the signal path. No analyzer capture is
authorized; the prior stop on analyzer captures remains in force.

The historical result remains: the monitor showed black/white scalar changes
for B and C and returned to A; A/C had an observed eight-pixel translation;
the purple edge shimmer was photographed; the underfilled analyzer capture
missed the edge. This contract is a fresh visual replay, not a claim of exact
physical pixels, FPGA receipt, or H1 closure.

## 2. Frozen identities

| Item | Frozen identity |
|---|---|
| Board | QMTech Wukong XC7A100T-FGG676; expected JTAG IDCODE `0x3631093` |
| T1H artifact | `build/spu_a7_100t_GPUVGA_T1H_DIAG_B1_S1.bit`; SHA-256 `ec600abe73e847f0846bff5429813cc6913a343b235e215cab5298ebb5d126dd` |
| T1G recovery artifact | `build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit`; SHA-256 `e16dc6992c60de99d9f5d9a5cc10c3aff99a245b5f5da6035887f2c92cb68fa5` |
| UART | Original CH340 by-id endpoint from the runbook; 115200 baud, 8N1 |
| T1H A | `fixtures/gpu_t1h_scene_a_wire_151b.hex`; text SHA-256 `93a4baf336ec166e69c802ecaeee43383810ad48b5597940229f83eff81db062`; wire SHA-256 `656e4583753bd86d37b9fe0480cf6fa493e4f475232fb89271ae4bf5559ad3e3` |
| T1H B | `fixtures/gpu_t1h_scene_b_wire_151b.hex`; text SHA-256 `6f913e4715f458d4caf70865649f7aff466520b46fc7366c2589c0a4e256dca5`; wire SHA-256 `3858256dd7999634cf997afdf40318c16bf4d87a731b340148b31d1c49aed70a` |
| T1H C | `fixtures/gpu_t1h_scene_c_wire_151b.hex`; text SHA-256 `df43e881a888ff96df09aab448f7c686d0367209ffcc6ae8e3d3060de573ee74`; wire SHA-256 `f9415dcf3143604e25fa4591e49646d9cb446e28e81f87a1f3d771869cfb27d9` |
| T1G recovery loader | `tools/load_gpu_t1g_sram.py`; SHA-256 `cdb904f8ee258b24ca5845ea15169873496f9c7d4f49021f697993b0544145e2` |
| T1G recovery sender | `tools/send_gpu_t1g_scene.py`; SHA-256 `8fa0e1c7f46a1e9b59aaf95a86829b607a5f88481febc1f70517ed98143e1024` |
| T1G recovery runner | `tools/run_gpu_t1g_demo.py`; SHA-256 `dfe0c9332e3cb062c1ed18ec55425bba53564500d7f6d9bde9258f174419b241` |
| T1G recovery A | `fixtures/gpu_t1f_scene_wire_127b.hex`; SHA-256 `abf881178c4384f9210575aa2992c784cb6e19fcd10f149b81631e39591c8fda` |
| T1G recovery B | `fixtures/gpu_t1f_coverage_scene_wire_127b.hex`; SHA-256 `80bb103e43e1fc06a98e1d03166a673b35ea4e70c1c2b5fd34ff2caf177fb607` |
| T1G recovery C | `fixtures/gpu_t1g_scene_c_wire_127b.hex`; SHA-256 `5aad8b1b1954875ea78fb11192d94a19652e027aea8f33e1656ec950b50abca5` |
| Loader candidate | `tools/load_gpu_t1h_sram.py`; SHA-256 `494d47f8be85d5ed4be3105b92d9ce861a73ddd823c6bf7d178742fdeba3c74d` |
| Sender candidate | `tools/send_gpu_t1h_scene.py`; SHA-256 `3e397752add1b73b559010fbe44a1849c646a211748819515d12634a20b7d142` |
| Runner candidate | `tools/run_gpu_t1h_demo.py`; SHA-256 `b2019bfb6c8fcbf5908e5b9d3b376ab30d31175787e689f3ae95b76b56343f9a` |

The bitstream is the frozen replay identity. Its historical build checkout was
dirty and the complete build-time patch was not retained; exact source
reconstruction is unavailable. No rebuild is in scope. The offline
source/profile comparison is recorded in
`build/gpu_evaluation/t1g_t1h_offline_qualification_20261007/source_compare.md`.
Recheck every artifact and tool hash and freeze them in the ratification record
immediately before any future execution. A mismatch blocks launch.

Visual references are the historical photo
`build/t1h_gpu_attributes_20260923/h1_scalar_threshold_photo.jpeg` (SHA-256
`a0afe136711a6acd02cd91c000b9c394663f6fbebb161b5dba7a3f06a07c757d`) and the
scene expectations in the historical scalar contract and §3.13 evidence entry.
The diagnostic displays scalar bit 14 as black/white. A must match the A
reference; B and C must each visibly change from the preceding scene; final A
must return to the A reference. Record the fringe as seen, not seen, or
indeterminate.

## 3. Authority and limits

This draft does not authorize hardware access. After ratification, it permits
one T1H SRAM load and one A/B/C/A replay. It also reserves one conditional T1G
SRAM recovery load and one frozen T1G A/B/C/A/B/C sequence, only if the T1H
attempt does not pass, the operator reports the board safe and ready, and the
target ID remains correct. Recovery is part of this contract, not an
unbudgeted cleanup operation.

The maximum campaign budget after ratification is two SRAM loads, ten scene
transactions (four T1H, up to six T1G), 30 minutes per load-plus-run operation,
and 60 minutes aggregate. Each operation uses one shared monotonic deadline
anchored at its first JTAG detect. A consumed load attempt is not repeated.
There are no flash writes, synthesis, builds, resets beyond the frozen loader,
power cycles, pin/cable/monitor changes, analyzer captures, alternate images,
fixture changes, packet retries, or automatic recovery.

Do not run any command in §5 until the owner records explicit ratification,
approved hashes, operator readiness, and the selected by-id endpoint in this
contract's execution record. A changed identity or unavailable qualified host
context blocks launch.

## 4. Bounded transport and stop rules

Each T1H transaction is exactly 151 bytes, starts with `A5`, and is sent at
115200 8N1. The sender opens one UART handle for A/B/C/A, continues a positive
short write only from its unwritten suffix, never restarts a packet, and stops
on any write error. Before each packet, the runner requires at least 185
seconds remaining: the five-second transaction bound plus the full
180-second observation window. It applies a one-second guard before this
reserve check. One killable worker enforces a five-second bound across writes,
`tcdrain`, and the 20 ms post-drain delay. Expiry kills and reaps the worker,
records confirmed partial progress or unknown device-write state, and
prevents later writes. This is a host stop bound, not a hardware delivery
guarantee. Keep the three-second inter-scene dwell and 31.1 ms minimum
start-to-start interval. The runner records completion of the 20 ms delay,
each start-to-start gap, and each inter-scene dwell; it stops if required
pacing evidence is absent or below its bound.

The runner requires a fresh ordinal/scene-specific operator reply after each
completed host write and drain. Each reply is capped at 180 seconds and the
shared deadline. No response is not confirmation. Initial stable-lock
confirmation is also capped at 180 seconds. The sixth T1G observation is not
applicable here; T1H PASS requires all four T1H observations durably recorded
before the runner emits PASS.

Stop the current operation on loader failure, IDCODE mismatch, lock loss,
wrong scene, sender failure, deadline expiry, ambiguous/unconfirmed
observation, or unexplained hardware behavior. Preserve the evidence. Do not
send a later scene after a failed transport or missed observation. Conditional
T1G recovery may be used only within the reserved budget and after explicit
operator readiness; if the board is unsafe or the target identity is
uncertain, halt without recovery.

## 5. Execution commands (inactive until ratification)

Create a fresh evidence directory and verify identities offline first:

```bash
RUN_DIR=build/gpu_evaluation/t1h_visual_replay_20261007/campaign_01
mkdir -p "$RUN_DIR"
sha256sum \
  build/spu_a7_100t_GPUVGA_T1H_DIAG_B1_S1.bit \
  build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit \
  tools/load_gpu_t1g_sram.py tools/send_gpu_t1g_scene.py \
  tools/run_gpu_t1g_demo.py \
  fixtures/gpu_t1f_scene_wire_127b.hex \
  fixtures/gpu_t1f_coverage_scene_wire_127b.hex \
  fixtures/gpu_t1g_scene_c_wire_127b.hex \
  tools/load_gpu_t1h_sram.py tools/send_gpu_t1h_scene.py \
  tools/run_gpu_t1h_demo.py \
  fixtures/gpu_t1h_scene_a_wire_151b.hex \
  fixtures/gpu_t1h_scene_b_wire_151b.hex \
  fixtures/gpu_t1h_scene_c_wire_151b.hex
```

After fresh operator readiness and ratification, execute one T1H operation in
the approved host context. `--attempt-limit-seconds` is shared by the loader
and runner; do not start a second timer:

```bash
python3 tools/load_gpu_t1h_sram.py \
  --attempt 1 --attempt-limit-seconds 1800 \
  --evidence-dir "$RUN_DIR/t1h_load"
python3 tools/run_gpu_t1h_demo.py --execute \
  --observation-timeout-seconds 180 \
  --send-drain-bound-seconds 5 \
  --port /dev/serial/by-id/REPLACE_WITH_RATIFIED_CH340_ID \
  --load-evidence-dir "$RUN_DIR/t1h_load" \
  --evidence-dir "$RUN_DIR/t1h_demo"
```

Run the T1G recovery only when its §3 trigger is met and the operator confirms
readiness. Use fresh directories and the existing frozen T1G loader/runner:

```bash
python3 tools/load_gpu_t1g_sram.py \
  --attempt 1 --attempt-limit-seconds 1800 \
  --evidence-dir "$RUN_DIR/t1g_recovery_load"
python3 tools/run_gpu_t1g_demo.py --execute \
  --observation-timeout-seconds 180 \
  --send-drain-bound-seconds 5 \
  --port /dev/serial/by-id/REPLACE_WITH_RATIFIED_CH340_ID \
  --load-evidence-dir "$RUN_DIR/t1g_recovery_load" \
  --evidence-dir "$RUN_DIR/t1g_recovery_demo"
```

Inspect exactly one terminal marker per loader/runner directory and preserve
the JSON records, per-packet transcripts, stdout/stderr, and operator
observations. Do not infer FPGA receipt from host write/drain completion.

## 6. Offline preparation and verification record

The candidate tools are separate from the T1G tools. They do not alter an
image, UART bytes, fixture, pacing, or loader command. Offline checks executed
on 2026-10-07:

```bash
python3 -m unittest software.tests.test_gpu_t1h_sender \
  software.tests.test_gpu_t1h_sram_loader \
  software.tests.test_gpu_t1h_demo_runner
python3 software/tests/test_gpu_t1h_attribute.py
python3 tools/send_gpu_t1h_scene.py --scene A --validate-only
python3 tools/send_gpu_t1h_scene.py --scene B --validate-only
python3 tools/send_gpu_t1h_scene.py --scene C --validate-only
python3 tools/run_gpu_t1h_demo.py --help
python3 tools/load_gpu_t1h_sram.py --help
```

**Result:** 26 focused host-tool tests passed; the oracle passed 40,000 active
pixels and 715 focused edge samples; all fixture validations reported the
frozen 151-byte lengths and hashes; both CLI help commands exited zero. Tests
cover partial suffix writes, write/drain timeout termination, transcript
preservation, loader markers, shared monotonic deadline reuse, operator gates,
the per-send 185-second reserve, required post-drain delay, start-to-start
pacing, dwell recording, and stop-before-later-send behavior. These are
offline results only. No UART,
JTAG, USB probe, bitstream load, or monitor interaction occurred.

Repository state was dirty at preparation time (HEAD
`4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`); unrelated pre-existing changes
were left untouched. Hashes above are preparation identities, not ratification.
Before launch, run `git diff --check` on the contract and candidate paths and
refresh all hashes. Do not perform the full repository gate as an implicit
hardware authorization.

## 7. Outcomes and claim limits

**PASS — bounded visual replay:** T1H load passes with expected IDCODE and all
DONE flags; stable lock is confirmed; four 151-byte transactions have
successful drains and the recorded 20 ms post-drain delay. Each send had at
least the five-second transaction bound plus the full 180-second observation
window remaining before transmission. All start-to-start gaps are at least
31.1 ms and each inter-scene dwell is at least three seconds. The operator
explicitly confirms A, B, C, and return-to-A references with transitions; all
records fall within the shared deadline. Record fringe status independently.
PASS demonstrates operator-observed
scalar-threshold scene switching on this frozen image only. It does not close
the purple-fringe cause, establish exact pixel values, or prove FPGA receipt.

**INCOMPLETE:** observation timeout, operator interruption, or deadline
expiry prevents all required confirmations. Record the last completed
transaction and last confirmed scene separately.

**FAIL / HALT:** load/transport failure, ID mismatch, lost lock, wrong scene,
unexplained behavior, or identity drift. Preserve evidence and use only the
explicitly budgeted conditional T1G recovery. Further work requires a new
owner decision.

## 8. Ratification record (not yet completed)

Owner instruction and timestamp: **PENDING**
Approved contract and T1G/T1H tool and fixture hashes: **PENDING**
Fresh artifact/fixture identity check: **PENDING**
Approved host namespace and UART by-id path: **PENDING**
Operator readiness and unchanged wiring/monitor: **PENDING**
Attempt/aggregate budget acknowledged: **PENDING**
Hardware status: **HALTED**
