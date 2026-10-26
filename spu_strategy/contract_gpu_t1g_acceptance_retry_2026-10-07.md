# Owner Contract: Frozen T1G Two-Cycle Visual Acceptance Retry

**Contract ID:** `GPU-T1G-ACCEPTANCE-RETRY-2026-10-07`
**Date:** 2026-10-07 (Pacific/Auckland)
**Owner:** John Curley
**Status:** RATIFIED — EXECUTION AUTHORIZED WITH LIVE READINESS GATE
**Campaign:** `gpu_wukong_baseline_recovery_20261006`
**Authorized slots:** attempts 07–09, subject to the retry eligibility rule

This document records the reconciled source review and owner's ratification.
Hardware execution is authorized only after the live readiness gate in §3.
Attempt 06 remains immutable and incomplete.

## 1. Purpose and acceptance boundary

After the implementation in §6 is frozen and this contract is ratified, perform
one fresh operator-observed A/B/C/A/B/C sequence on the exact frozen T1G image,
board, monitor, wiring, UART endpoint, and A/B/C fixtures recorded in the
identity annex. A PASS means only repeatable operator-observed scene switching
on this frozen image. It does not establish pixel equality, FPGA packet
receipt, CRC acceptance, activation telemetry, throughput, or other profiles.

The owner-supplied attempt 06 summary is corroborated by the local closeout and
sequence evidence: the frozen image loaded to SRAM; six 127-byte host writes
and `tcdrain` calls completed; operator reports confirmed stable lock and the
first cycle A/B/C, then cycle 2 A/B. Cycle 2 C has no observation. The 15-minute
deadline expired at `2026-10-07T00:07:52Z`. Attempt 06 remains incomplete.
Nothing in this draft fills its missing C observation.

## 2. Proposed bounded budget

| Item | Proposed limit after ratification |
|---|---:|
| New attempts | At most 3: 07, then conditional 08 and 09 |
| Elapsed time per attempt | 30 minutes from first hardware action, including all waits |
| Aggregate hardware time | 90 minutes |
| SRAM loads | At most 1 per attempt; no automatic loader retry |
| Scene transactions | Exactly A/B/C/A/B/C, at most 6 per attempt |
| Bytes per transaction | 127, from the frozen fixtures |
| Write/drain/post-drain transaction bound | 5 seconds, enforced by a killable worker |
| Initial lock observation | At most 180 seconds after a successful load |
| Scene observation | At most 180 seconds after completed host write and drain |
| UART pacing | At least 31.1 ms start-to-start; 20 ms after drain; 3-second scene dwell |
| Deadline extensions | None |

The five-second value is an enforced stop policy, not a claim that hardware
always completes within five seconds. It covers positive partial-write
continuation, `tcdrain()`, and the explicit 20 ms post-drain delay. If it expires,
the worker is killed, the current packet is not restarted, and the attempt
halts. If termination occurs during a write syscall, accepted device bytes may
be unknown; record the acknowledged prefix and classify the device write state
as unknown. No later packet may be sent.

An attempt is consumed immediately before the loader's first hardware command.
An offline preflight failure consumes no attempt. Partial load, write, drain,
operator interruption, or runner failure consumes the attempt. No automatic
load or packet recovery is allowed.

Each successor attempt (08 or 09) is eligible only if the immediately preceding
attempt ends from a missed/timed-out operator response or observation-only
runner fault, with no load, fixture, transport, lock, or displayed-scene
failure. The preceding runner must be terminal and the operator must explicitly
confirm readiness again. Any other failure halts the campaign and requires a
separate owner decision. Stop immediately after PASS.

## 3. Frozen execution sequence (proposed)

After ratification, use new directories only:

```text
build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/attempt_07/
build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/attempt_08/
build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/attempt_09/
```

Freeze the identity annex and candidate runner before launch. Obtain an explicit
operator-ready statement before the attempt timer starts. Invoke the loader
with the 1800-second campaign limit. Its first JTAG command records the single
monotonic start and deadline plus the host boot ID. The scene runner reads and
validates that exact deadline and boot ID; it has no independent attempt timer
to restart. Run the loader once;
require its single `COMPLETE` marker, exit 0, expected IDCODE, image hash, and
`isc_done=1`, `init=1`, `done=1`. Require timely explicit stable-lock
confirmation before opening/sending on UART. Then transmit and observe the six
ordinal-labelled scenes in order. Positive short writes may continue from the
exact unwritten byte offset within the same transaction. Never restart a
packet, replay accepted bytes, or continue after an error or deadline. Enforce
at least 31.1 ms between transaction start times, call `tcdrain()`, wait the
explicit 20 ms post-drain delay, then prompt the operator; retain the 3-second
inter-scene dwell after confirmation. A response must explicitly identify the
ordinal, cycle and scene and satisfy the scene observation table in §5. The
next packet is forbidden until the current confirmation is durable. Stale,
duplicate, missing or ambiguous replies cannot advance the sequence. Record
each confirmation and the sixth confirmation before writing PASS. Close the
UART through the frozen procedure before terminal PASS.

For cycle 2 Scene A following C, require stable lock and the expected A image.
Do not require a visible C-to-A transition.

Before each packet, ensure the remaining deadline can cover the enforced
five-second write/drain/post-drain bound and a full 180-second observation
window. The sender must terminate blocked transport work at that bound; it may
not issue a later write or restart the packet. On timeout, stop. Do not add a
return-to-A packet, diagnostic, cleanup reset, or query.

Candidate command shape, **not executable authorization**:

```bash
python3 tools/load_gpu_t1g_sram.py \
  --attempt 7 \
  --attempt-limit-seconds 1800 \
  --evidence-dir build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/attempt_07/programming_01

python3 tools/run_gpu_t1g_demo.py --execute \
  --observation-timeout-seconds 180 \
  --send-drain-bound-seconds 5 \
  --port /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 \
  --load-evidence-dir build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/attempt_07/programming_01 \
  --evidence-dir build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/attempt_07/t1g_demo_01
```

The commands are the frozen runbook entries for the authorized attempt 07.
For 08 or 09, use that attempt number and its fresh evidence directory. The
runner's deadline comes only from the loader evidence, so each pair of commands
shares one 30-minute allowance.

## 4. Reconciled decisions and evidence limits

The files named in the supplied draft are present in this workspace and were
inspected. The supplied statement that they were unavailable does not apply to
this checkout. The transport conflicts are resolved for this draft as follows:

1. **Positive short writes.** Continue only from the unwritten byte offset in
   the current packet. Never restart the packet or replay accepted bytes. The
   attempt 06 transcript had six full single-call writes; offline coverage
   exercises positive partial progress.
2. **Pacing.** Restore the parent contract's explicit 20 ms post-drain delay
   and retain its 31.1 ms minimum start-to-start interval and 3-second scene
   dwell.
3. **Bounded transport.** The candidate uses a killable worker with a
   five-second enforced limit for writes, drain and post-drain delay. This is a
   stop policy, not a delivery-time guarantee. A write timeout records the
   acknowledged prefix and marks device write state unknown; the attempt halts.
4. **C-to-A appearance.** Attempt 06 reports C visibly changed from B and
   resembled A. Cycle 2 A must match the A reference, but does not need to show
   a visible transition from C. The simulation comparison in §5 gives a
   limited fixture relationship; it is not physical pixel evidence.
5. **Programmer version reporting.** The local executable is
   `/opt/oss-cad-suite/bin/openFPGALoader`, SHA-256
   `4db258c1854017bd3587af6f4fcec3704d9590aea3beed6f0fa39e6692d2a4fa`.
`openFPGALoader --version` is unsupported by this binary. Its version string
is unverified. The executable path and hash identify the local binary for
this annex.

## 5. Identity annex — locally inspected, pending owner resolution

### Parent evidence

| Record | Path | SHA-256 |
|---|---|---|
| Parent baseline contract | `spu_strategy/contract_gpu_baseline_recovery_2026-10-06.md` | `2c6cdf8c60754a0c93a92fefab73d9fdfd5940c8b22b124cdc572445105ac3fc` |
| Attempt 06 amendment | `spu_strategy/contract_gpu_recovery_retry_attempt06_2026-10-07.md` | `4465bf4454faf31df2a7c474d5c6709bf5e11428bc98e01fee28867a0950a7c8` |
| Attempt 06 closeout | `build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/attempt_06/attempt_closeout_20261007.md` | `b518de8be756bebad84f186e6e0af2e3d70408c74ea65343a61f492dcadb9fda` |

### Frozen image and board identity

| Field | Frozen identity |
|---|---|
| Bitstream | `build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit` |
| Bitstream SHA-256 | `e16dc6992c60de99d9f5d9a5cc10c3aff99a245b5f5da6035887f2c92cb68fa5` |
| Source checkout | `build/t1f_clean_qualification_20260922`, commit `a64d87c7ae0d96b44d8178c20f2421376a975ac0`; `git status --short` was empty |
| Board / target | QMTech Wukong Artix-7 100T, XC7A100T-FGG676; JTAG IDCODE `0x3631093` |
| Display setup | Parent record: original 640×480 VGA monitor, three-resistor DAC and J10 harness; R G8, G G7, B G5, HSYNC D5, VSYNC E5, G6/J10-7 unused |
| Clock | 50 MHz oscillator; 25 MHz pixel clock |
| Loader wrapper | `tools/load_gpu_t1g_sram.py`, attempt 06 SHA-256 `8f5a7ea8370882e8e3e21550151d9468deec260a2a7d15426c037de6a7ef1c35` |
| Loader command | `timeout 15s openFPGALoader -c dirtyJtag --freq 1000000 --detect`; then `timeout 60s openFPGALoader -c dirtyJtag --freq 1000000 build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit` |
| Retry loader invocation | `python3 tools/load_gpu_t1g_sram.py --attempt 7 --attempt-limit-seconds 1800 --evidence-dir <attempt_07>/programming_01` |
| Shared deadline | First detect's monotonic start plus 1800 seconds, recorded with host boot ID; runner validates and uses the same absolute deadline |
| Programmer executable | `/opt/oss-cad-suite/bin/openFPGALoader`, SHA-256 in §4 item 5; version string unavailable |
| Load behavior | One detect and one SRAM load; no flash write; attempt 06 both exited 0 and DONE flags were all 1 |

### Scene fixtures and expected observations

| Scene | Fixture | Text SHA-256 | Wire SHA-256 | Size | Reference supported by records |
|---|---|---|---|---:|---|
| A | `fixtures/gpu_t1f_scene_wire_127b.hex` | `abf881178c4384f9210575aa2992c784cb6e19fcd10f149b81631e39591c8fda` | `78820c1f6da055a3c51eb9ec3709fe027cd1b0a2772093c6e8618a5c300dbe5f` | 127 bytes | Red-left/green-right inverted triangles; operator confirmed in attempt 06 |
| B | `fixtures/gpu_t1f_coverage_scene_wire_127b.hex` | `80bb103e43e1fc06a98e1d03166a673b35ea4e70c1c2b5fd34ff2caf177fb607` | `861783056fa024a9ac232184c493fc20e2d432f94bff80d0dc14d957ccdfee97` | 127 bytes | Visible change from A; cycle 2 described as two small triangles |
| C | `fixtures/gpu_t1g_scene_c_wire_127b.hex` | `5aad8b1b1954875ea78fb11192d94a19652e027aea8f33e1656ec950b50abca5` | `863585de89f3a827e25d12ba262f35dafab93ba05440377fd56cc0f255a3ef7b` | 127 bytes | Visible change from B; cycle 1 operator said C matched A; see §4 item 4 |

### Required visual observations

| Ordinal | Cycle | Scene | Required observation |
|---:|---:|---|---|
| 1 | 1 | A | Stable lock; displayed image matches A reference |
| 2 | 1 | B | Stable lock; visible change from A; displayed image matches B reference |
| 3 | 1 | C | Stable lock; visible change from B; C resembles A |
| 4 | 2 | A | Stable lock; displayed image matches A; no visible C-to-A transition required |
| 5 | 2 | B | Stable lock; visible change from A; displayed image matches B reference |
| 6 | 2 | C | Stable lock; visible change from B; C resembles A |

The proposed limited Scene C reference is its reported B-to-C visible
change and A-like appearance. The existing `software/tests/test_gpu_t1g_pacing.py`
rendering check was extended to compare the oracle-checked first-frame outputs
for A, B and C. At its 80×100 simulation size, it reported A/B=2459, B/C=2735,
and A/C=2259 of 8000 sampled pixels different. The first A/C difference was
at (10,10): A=`f00`, C=`000`. The generator defines C as A translated by
(8,8), which explains the A-like relationship. This supports the limited
scene references; it does not prove exact physical pixels or require a visible
C-to-A transition on the monitor.

Sequence mapping is exactly `A/B/C/A/B/C`. Every decoded wire packet begins
with `A5`; no T1D 64-byte fixture is in scope.

### UART and host identity

| Field | Attempt 06 evidence / candidate procedure |
|---|---|
| Endpoint | `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`, resolved then to `/dev/ttyUSB0` |
| Serial device | CH340 UART, device node group `uucp`, mode `0660`; readable/writable by uid 1000 `john` |
| Settings | 115200 baud, 8N1; one UART descriptor held by the runner across the sequence; a killable child performs each bounded packet transaction |
| Transport policy | Positive short writes continue only from the unwritten suffix; no packet restart/replay; 5-second enforced transaction bound; `tcdrain()` then 20 ms delay |
| Packet pacing | At least 31.1 ms between write start timestamps; 3-second scene dwell after operator confirmation |
| Attempt 06 sender | `tools/send_gpu_t1g_scene.py`, SHA-256 `5db2b336dae0da68e3e21550151d9468deec260a2a7d15426c037de6a7ef1c35` |
| Attempt 06 runner | `tools/run_gpu_t1g_demo.py`, SHA-256 `fdfda65f02828170b8f060abfbf85b315440935a12b7fa7a62ed16cb5b7f4996` |
| Observed writes | Six 127/127 writes; one write call each; `tcdrain` true; host completion only |
| Captured host context | uid 1000 `john`; UART node readable/writable; no analyzer leads recorded in attempt 06 evidence |

The exact attempt 06 command lines are in the attempt 06 amendment in the table
above. The current candidate scripts have changed since attempt 06; their
post-edit hashes and offline results must be recorded in the ratification
record. Candidate changes do not change packet contents, UART settings, or
loader command lines.

## 6. Candidate runner preparation and offline evidence

Offline-only edits were made to the loader evidence, scene sender evidence,
sequence runner, and the existing T1G rendering test. The loader records the
1800-second attempt limit, first-action monotonic anchor, absolute deadline and
host boot ID. The scene runner consumes that exact deadline; it cannot start a
new allowance. The sender runs each transaction in a killable child process,
continues positive short writes from the unwritten suffix, enforces the
five-second maximum over write/drain/post-drain delay, records every acknowledged
write count, calls `tcdrain()`, then waits 20 ms. The runner enforces the
31.1 ms start interval and 3-second scene dwell, adds a pre-UART stable-lock
gate, uses unique ordinal/cycle/scene confirmations, caps observation waits at
180 seconds, reserves the transaction bound plus observation time, and
persists observations and a terminal marker before printing PASS. A timeout
kills and reaps the transport worker and halts without sending another scene.
No hardware endpoint was opened by these checks. These are candidate changes,
not execution authorization.

Required offline checks and results are recorded in the closeout accompanying
this draft. Hardware execution remains prohibited until the candidate hashes
are frozen and the owner ratifies the contract.

Candidate hashes after preparation:

| File | SHA-256 |
|---|---|
| `tools/load_gpu_t1g_sram.py` | `cdb904f8ee258b24ca5845ea15169873496f9c7d4f49021f697993b0544145e2` |
| `tools/send_gpu_t1g_scene.py` | `8fa0e1c7f46a1e9b59aaf95a86829b607a5f88481febc1f70517ed98143e1024` |
| `tools/run_gpu_t1g_demo.py` | `dfe0c9332e3cb062c1ed18ec55425bba53564500d7f6d9bde9258f174419b241` |
| `software/tests/test_gpu_t1g_pacing.py` | `4e68a448de22e4d1ec00cd196028cec86eff0789e6a50bdc44f961232ba4f692` |

Offline check log: `spu_strategy/contract_gpu_t1g_acceptance_retry_prep_2026-10-07.md`.

## 7. Outcomes and closeout

**PASS** requires one successful frozen SRAM load, six complete 127-byte host
transactions with successful drains and post-drain delays, the required
start-to-start pacing, and six timely explicit operator confirmations of
lock, expected appearance, and the applicable transitions in §5, with annex
identities matching. The sixth observation must be durable before PASS is
written or printed.

**INCOMPLETE** covers deadline expiry, missing/timed-out confirmation, operator
interruption, or eligible observation-only runner fault. Record last
transmitted and last confirmed scenes separately.

**FAIL / HALT** covers wrong displayed state, lock loss, loader/transport error,
fixture or identity mismatch, prohibited operation, or unexplained behavior.
No successor attempt follows a failure in this category.

Retain a unique terminal marker, complete command and packet transcripts,
identities, observation journal, elapsed times, stop reason, and closeout for
every attempt. Preserve failures. Do not infer FPGA state after interruption.
The campaign ends at PASS, a blocking failure, the third consumed attempt, or
90 aggregate hardware minutes, whichever occurs first.

## 8. Ratification record

Owner instruction: “Authorized. 3 attempts.” Received 2026-10-07 00:57:37 UTC.
This explicitly ratifies attempts 07–09, a 90-minute aggregate hardware limit,
and the conditional successor-attempt rule in §2. All other listed limits and
technical identities remain frozen. Candidate script hashes and offline
results are listed in §6 and the preparation closeout. Attempt availability
and fresh operator readiness remain prelaunch checks. No hardware action is
authorized until the live readiness statement is obtained.
