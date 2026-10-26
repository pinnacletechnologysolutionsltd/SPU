# Engineering Contract: T1d bank and depth diagnosis, campaign 02

**Date:** 2026-10-05  
**Contract ID:** `contract_gpu_t1d_bank_depth_diagnosis_2026-10-05.md`  
**Status:** CLOSED — all three slots consumed; static subset matched, full snapshot rejected; root cause not established; no further physical execution authorized.  
**Roles:** Spec Author: Codex; Halt-and-Flag Implementer: local executor;
Integration Auditor: local executor and operator. These are functional roles;
no separate agents are required.

## 1. Objective and scope

Prepare the commands in §4, qualify readback, then compare two identical A
transmissions using captured raw banks, dispatcher inputs and depth results.
Record whether the raw-bank and arithmetic mismatches recur together or
separately. Report a specific measurement failure when reliable capture cannot
be established. Do not assign a transport or arithmetic root cause from widths
or a bank-state bit flip alone.

Modify only this contract, prospective campaign helpers/evidence under
`build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/`, and new
entries in `docs/hardware_evidence.md` after execution. Keep helper modules
single purpose, normally 50–150 lines. Preserve all campaign-01 workers,
results, authorizations, failures and the exhausted hardware stop.

The owner's request, "Okay, let's draft a new contract with 3 attempts.",
authorized the draft. The later reply "Authorized and ready. Please begin."
approves this scope prospectively. Preserve both statements; the new approval
does not reopen an old budget. Obtain current operator readiness before
physical execution and preserve the initial readiness reply separately.

## 2. Frozen evidence, inputs and constraints

Read [hardware evidence §§3.35.9–3.35.12](../docs/hardware_evidence.md) and
[the preceding contract §§18–18.7](contract_gpu_t1d_reload_after_operator_reset_2026-10-05.md).
Pin campaign-01 `byte_44_review.json`, attempt-02 `decoded_capture.json` and
`projection.json`, attempt-01 `projection.json`, attempt-03 `projection.json`
and raw anomalous frames, and `readback_guard_repair_01/` before copying any
worker. Hash every copied dependency, placement/database input and oracle.

Record these existing observations without promoting them to root causes:

| Observation | Established limit |
|---|---|
| Packet byte 44: expected `0x0F`, raw bank `0x0B`, XOR `0x04` | D2 maps to scene bit 346, green b1 bit 14; no UART waveform was captured |
| Green b1: expected −480, captured −16864 | Captured raw-bank state; corruption origin unestablished |
| Corrupted-descriptor oracle Sa/Sb/Sc: −1472000 / −6641600 / 986240000 | These disagree with captured shared sums −1488384 / −274968271552 / −16193629184 |
| Specified arithmetic widths fit these inputs | Physical arithmetic, timing and operand histories remain unqualified |
| Final read returned two constant, contradictory frame payloads | COMPLETE command status did not establish valid measurement data |
| Operator reported interlaced, truncated green after the final read | Probe noninterference and causality remain unestablished |

Freeze the following paths and SHA-256 values:

```text
52d45da0743c326f1700b4efa7fa0187523ea6e456948f274e2cc276ccd7b914  build/d3_physical_diag_20260921/spu_a7_100t_GPUVGA_T1D_DIAG_S1.bit
d59390661dac131151b03f70aee9c3a0cf02d26ba4cb6c94ded9ecad707f67a5  build/spu_a7_100t_GPUVGA_T1D_DIAG_S1.json
9dd28baf323e120a50b623fb50cf19b74a770fa519163541538deba502edfdb0  build/spu_a7_100t_GPUVGA_T1D_DIAG_S1.json.pnr.json
2ac300d9fd5b83dec0a216d4e99342208a5672b501f93f2cb90f054f29a8be2a  build/spu_a7_100t_GPUVGA_T1D_DIAG_S1.json.pnr.fasm
621dcbec34c5ca09f34302a03dd26c1ec1d992dd64f450d946f7de26810b0859  tools/send_gpu_t1d_vertex_ab.py
aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee  build/gpu_evaluation/s1_t1d_scene_20261004/run_01/scene_packet.bin
```

Keep the present configured board powered. No FPGA load, reset, power cycle,
flash write, wiring change, RTL change, bitstream substitution, baud change,
packet mutation, B transmission or A/B acceptance change is permitted.
The frozen bit file identifies the retained design; its hash alone does not
establish the complete live configuration identity.

Pin DirtyJTAG VID:PID `1209:c0ca`, serial `CB81353DCE678119`, and exactly one
Artix-7 100T chain device, normalized IDCODE `0x03631093`. Pin CH340 VID:PID
`1a86:7523`, serial identity `1a86_USB_Serial`, endpoint
`/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`, UART 115200 8N1.
Resolve actual paths by identity; record namespace and permissions. Separate
sysfs visibility from actual adapter access. Physical JTAG access consumes
a slot, including programmer detection; do not probe during host preflight.

Permit only the previously checked CFG_IN/CFG_OUT/BYPASS register-read
sequence and RCRC(7), RCFG(4), DESYNC(13), plus at most one GCAPTURE(12) per
attempt. Forbid GRESTORE, RCAP, JSHUTDOWN, WCFG, FDRI and security/clock-setting
writes. GCAPTURE stores FF state in configuration cells; do not claim it is
physically nonintrusive. No recovery commands follow a transport failure.

## 3. Three-attempt budget and default procedure

Reserve **three attempts maximum, 360 seconds per attempt, 1080 seconds
cumulative reserved**. The deadline starts at `begin`, before any device is
opened, and includes operator waits and pauses between stages. Limit each
UART send to 10 seconds, each measurement subprocess to 180 seconds and its
native USB activity to 160 seconds. Allow at most 60 seconds for each requested
before-capture and after-capture report, bounded by the attempt deadline.
No deadline extension or hidden retry is allowed.

| Attempt | UART | JTAG plan | Required comparison |
|---|---|---|---|
| 1 | None | Two static passes over the union of attempt-01's 13 FARs and anomaly FARs `0x20b9f`, `0x2141b`; then one capture over attempt-02's 60 FARs | Readback validity, baseline banks/selector/dispatcher/prepared state |
| 2 | A once | One capture over the same 60 FARs | Changed bank, exact payload, settled prepared coefficients versus the descriptor actually captured |
| 3 | Identical A once | One capture over the same 60 FARs | Opposite-bank transition, repeated packet equality, depth comparison across the two sends |

Attempt 1 permits at most 90 addressed frame reads (at most 15 static FARs
twice plus 60 capture FARs once). Attempts 2 and 3 permit at most 60 reads
each. Every read has exactly 202 words: discard 101 pipeline/dummy words and
retain 101 data words. These scheduled passes are consistency measurements;
never reread a rejected frame inside the same attempt.

Use attempt-02's frozen 55-group/2017-bit capture projection and its 3324
static controls, including both complete 504-bit raw banks, selector, loader
status, prepared-control generations/state, all 24 latched descriptor fields,
dispatcher state/unit/pending/start, math state/sums/reciprocal, and both sets
of prepared coefficients and fractional scales. Preserve both polarity decodes.
Derive static guards for the additional baseline FARs from retained placement,
FASM and database evidence; freeze them before launch.

Proceed to a UART attempt only after the preceding baseline has valid readback,
stable operator-reported signal and no unexplained post-measurement image
change. If either identical send fails to produce a settled commit/generation
transition, stop the pair and classify incomplete; do not send again.
Measure the selector instead of assuming which bank each packet activates.

After an infrastructure failure, permit prospective helper/host repairs and
use a remaining slot for a corrected readback-only measurement. Record the
specific cause/correction, revised commands/projection and focused checks first.
Do not issue UART until a valid baseline is established. Such a substitution
uses one of the same three slots and can leave the identical-A comparison
incomplete. Routine corrections require no renewed permission after scope
approval; changes to prohibited scope or budget require a new contract.

## 4. Command-first preparation and physical stages

**Prepared interfaces (see §9):** create `prepare_campaign.py`,
`check_campaign.py`, `review_attempt.py` and each attempt's `run_checked.py`,
`record_operator.py` and `analyze_result.py` in the new bundle. Install the
bootstrap preparation/check helpers first; preparation creates the child
workers and checks validate them before physical stages are enabled.
Preparation must refuse existing campaign state, attempt directories, evidence
or any bootstrap-file hash mismatch, and must never modify an old worker.
Extend new copies of the retained checked workers where practical, with small
changes for the frame guard, campaign reservation, sender evidence path and
operator reports. Record each copy's provenance and diff; avoid replacing the
checked transport or adding a general framework.

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/prepare_campaign.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/check_campaign.py
```

`prepare_campaign.py` must freeze commands, projections, dependencies, source
hashes, exact transport allowlist and oracle inputs. It must default to
`DRAFT_NOT_AUTHORIZED`, with physical execution disabled. It may create the
new campaign's child files only; its own installation is an offline step.
Set the immutable campaign identifier in its manifest to
`t1d_bank_depth_diagnosis_campaign_02_2026-10-05`.

After approval, record authorization and fresh readiness verbatim, with UTC
timestamps. Readiness must explicitly cover powered board, unchanged wiring
and configuration, current image and signal lock. Require readiness age at
most 300 seconds at each physical stage; renew readiness only when it expires
or the setup changes. Readiness does not extend an attempt deadline.

Execute stages in the host namespace. For attempt 1:

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/attempt_01/run_checked.py begin
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/attempt_01/run_checked.py capture
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/attempt_01/record_operator.py --phase after-capture --stdin-json
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/attempt_01/analyze_result.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/review_attempt.py --attempt 1
```

For the default attempt 2, `begin` reserves the slot then transmits A once.
Collect the display report before JTAG so packet and probe effects can be
reported separately:

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/attempt_02/run_checked.py begin
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/attempt_02/record_operator.py --phase before-capture --stdin-json
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/attempt_02/run_checked.py capture
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/attempt_02/record_operator.py --phase after-capture --stdin-json
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/attempt_02/analyze_result.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/review_attempt.py --attempt 2
```

For the default attempt 3:

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/attempt_03/run_checked.py begin
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/attempt_03/record_operator.py --phase before-capture --stdin-json
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/attempt_03/run_checked.py capture
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/attempt_03/record_operator.py --phase after-capture --stdin-json
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/attempt_03/analyze_result.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/review_attempt.py --attempt 3
```

`record_operator.py` accepts a JSON object on stdin with these required fields:

| Field | Required value/type |
|---|---|
| `campaign_id` | Exact identifier from the immutable campaign manifest |
| `attempt` | Non-boolean integer matching the reserved attempt, 1–3 |
| `phase` | `before-capture` or `after-capture`, matching `--phase` and the pending stage |
| `observed_utc` | ISO 8601 timestamp with an explicit timezone (`Z` or numeric UTC offset); normalize to UTC |
| `report` | Verbatim operator text |
| `signal_lock` | Boolean |
| `image_changed_since_previous_phase` | Boolean |
| `operator_intervention` | Verbatim operator text |

Timestamp acceptance at receipt using the executor's UTC clock as
`recorded_utc`. Require **0 <= recorded_utc − observed_utc <= 60 seconds**;
reject missing/invalid/naive timestamps, future observations and older reports.
The observation and receipt must both fall within the pending phase's
60-second window and the attempt's absolute deadline. For `before-capture`,
that window starts at the successful UART stage's completion after drain and
the 100 ms wait; for `after-capture`, it starts at the measurement subprocess's
completion. Reject observations from before the relevant stage completed.
Use persisted stage timestamps, not report arrival, to establish these windows.

Verify campaign/attempt/phase against the manifest, reservation and stage
record; reject a cross-campaign, cross-attempt, wrong-phase, duplicate or
out-of-order report. Store the original input, normalized `observed_utc`,
`recorded_utc`, stage identity and acceptance decision together. Preserve
rejected reports as evidence without satisfying an observation gate. Never
restamp an old observation or infer its time from a photo's file metadata.

Recheck the accepted `before-capture` report's age (at most 60 seconds) and
the attempt deadline immediately before JTAG starts. Historical reports
accepted on time remain historical evidence when analyzed later; do not
reclassify them as expired solely because analysis happens later.
Reject missing fields and wrong types. Preserve explicit uncertainty as a
failed readiness/observation gate; never fill in an answer for the operator.
Report capture comparison separately from operator observations. Photos are
optional.

Lock the campaign during reservations and physical stages. `begin` consumes a
slot once and persists its absolute deadline before opening UART or USB.
`capture` requires that same reservation and can execute once only. Direct
workers require a live reservation/token and frozen hashes. Reject duplicate,
concurrent, out-of-order, unreviewed-predecessor or exhausted launches. Any
stage failure closes the attempt; a terminal attempt cannot be resumed.

Preserve the sender's single write/drain/100 ms wait semantics. Make a local
prospective sender copy with only evidence-path binding changed; record its
diff/hash and run focused sender checks. The original sender's hard-coded
transcript path must not be bypassed or overwritten. No short-write retries.

## 5. Required preparation checks and verification

Run the following offline commands on new copies before any device access:

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/check_campaign.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_gpu_t1d_bank_depth_diagnosis_2026-10-05.md docs/hardware_evidence.md
```

Require falsifiable checks for all of the following:

- Missing approval/readiness, stale readiness, wrong namespace/device/hash,
  duplicate launch, direct-worker bypass, concurrency, slot exhaustion,
  expired stages/reports and unavailable terminal outcomes.
- Operator timestamp parsing with `Z` and numeric offsets, missing/naive/
  invalid/future timestamps, the inclusive 60-second age limit and rejection
  beyond it, observations preceding stage completion or outside the phase/
  attempt deadline, freshness at capture launch, and unchanged validity of
  historical reports. Check exact campaign/attempt/phase binding, boolean
  attempt rejection, duplicate reports and preservation of rejected inputs.
- No device opens during preparation, checks, analysis or host discovery;
  exactly zero/two maximum campaign UART sends and no forbidden commands.
- Sender evidence binding, one exact 64-byte A write, drain, partial write,
  blocked drain, exception and timeout with no retransmission.
- Per-frame extent/FAR/word validation, boolean-word rejection and static
  controls. Reject both recorded anomalous payloads before another frame.
  Adapt the guard to the capture projection's `static_guards`; do not compare
  live ZINI state with initial bitstream values as static data.
- Persist candidate words and native journal before semantic rejection.
  Integrate the prospective frame guard into every addressed read, halt on
  any static-control mismatch, and forbid a second read after rejection.
- Legitimate constant payloads are accepted only when consistent with the
  declared controls; never reject arbitrary data merely for being constant.
- Both polarity decodes, raw bit 346/byte 44 reconstruction, state/generation
  settling, signed widths, exact malformed-descriptor oracle and preservation
  of the inactive bank after each single commit.
- Replay previously recorded transport without native USB; prove exact
  command counts, failure stops and forbidden-command rejection in mocks.

Reuse passed software gates only with unchanged relevant inputs and recorded
hashes. A helper correction requires focused checks for that correction.
Use AGENTS.md's applicable scope gates before declaring implementation complete;
RTL/shared verification changes require its full gates and a scope amendment.
No synthesis or full regression result establishes display acceptance.
For deterministic jobs exceeding 60 seconds, use `tools/run_detached_job.sh`
with a frozen budget and end the agent turn after LAUNCHED. Physical interactive
measurements use managed foreground execution with the same durable evidence.

## 6. Interpretation and evidence

For each attempt persist the reservation, commands, timestamps, readiness,
runtime/input hashes, UART transcript if any, native USB journal, candidate
frames including rejected data, brackets, terminal marker, comparison and
verbatim before/after reports. Process exit zero is `COMPLETE`, not a claim of
measurement or rendering PASS. Missing or contradictory terminal records
are `UNAVAILABLE`; failed/expired launches remain consumed.

Before comparing depth, require settled loader/prepared/dispatcher/math states,
matching result generations and identified active descriptor/unit. Derive
both prepared results from the actual latched descriptors using the pinned
finite-width device oracle. Compare shared accumulators only when the captured
unit/state establishes their operand association; otherwise mark that comparison
`NOT ESTABLISHED`. An idle snapshot does not reveal intermediate timing history.
GCAPTURE does not establish an atomic snapshot across clock domains; require
settled state and record that limitation with every decoded comparison.

Use these outcome labels independently:

| Claim | Evidence required |
|---|---|
| `READBACK_VALID` | Exact checked transfers, extent/alignment, matching projected static controls and unambiguous supported polarity |
| `RAW_BANK_MATCH` / `RAW_BANK_MISMATCH` | Complete bank bytes, measured selector/commit transition and exact packet comparison |
| `DEPTH_MATCH` / `DEPTH_MISMATCH` | Settled, associated descriptor/results versus the pinned finite-width oracle |
| `BANK_DEPENDENT_REPRODUCTION` | Two valid identical sends/captures with measured opposite-bank activation and repeatable bank-specific difference |
| `PROBE_DISTURBANCE_REPORTED` | Operator image/lock change between before-capture and after-capture reports; cause unestablished |
| `INCOMPLETE` / `INCONCLUSIVE` | Missing settling, invalid readback, absent observation, timeout or insufficient remaining slots |

Even a clean two-bank result does not prove UART electrical integrity or clear
all physical arithmetic/timing. Keep root cause `NOT_ESTABLISHED` unless the
new evidence distinguishes a specific failing boundary. A stable bank-specific
mismatch is a localization result, not proof of UART noise. No A/B visual
acceptance is possible here because B is not transmitted.

Append new results to `docs/hardware_evidence.md` with exact evidence paths;
do not rewrite earlier outcomes. Close after the third slot or an earlier
campaign stop, preserve unused slots as unused, and summarize the specific
next repair or missing measurement. A fourth launch is forbidden.

## 7. Stop conditions

Halt and flag contradictory specs or unfalsifiable guards before execution.
Stop the current attempt on transport/extent/semantic failure, unhealthy
startup/security brackets, ambiguous polarity, uncommitted/unstable state,
missing report or deadline expiry. No blind retry or recovery operation.

Stop the campaign on lost monitor lock, unexplained image change after JTAG,
operator intervention affecting setup, exhausted slots, or required wiring,
RTL, bitstream, protocol, clock or acceptance changes. Retain the observation
without attributing it to JTAG automatically. Physical scope beyond this
contract requires a new reviewed authorization and readiness.

## 8. Historical draft review status

Pinned bitstream, synthesis, placement, FASM, sender and A packet hashes were
rechecked while drafting and match §2. New helpers, focused helper checks,
campaign activation, current readiness and physical execution are `NOT RUN`.
This contract proposes three new slots; it records no new physical result.

The documentation audit was executed. Its tracked-corpus findings remain
outside this draft (24 link, 31 claim, one stale-total, 118 orphan and one
superseded-status finding); exit zero is not a clean-corpus claim. The new
untracked draft was also audited directly for links, claims, stale totals and
contradictions, with no findings. Whitespace inspection found no unexpected
trailing whitespace; `git diff --check` was run, but omits untracked files.
Planned helper/hardware commands are not executable evidence and remain unrun.

## 9. Authorization and prospective helper review

Owner approval "Authorized and ready. Please begin." is recorded in
`diagnosis_campaign_02/authorization.json` at 2026-10-05T06:45:17.774411Z.
The initial readiness reply is preserved separately. Preparation outlasted its
300-second validity; current image/lock also need an explicit report. Renew
readiness under §4, retaining the existing scope approval.

Prospective helpers and three attempt directories are prepared in the new
bundle. `provenance.json`, literal patches and `runtime_hashes.json` preserve
retained source identities and the amended workers. The native transport,
TAP serialization and capture projection are copied from campaign 01.
Frame validation is inserted after candidate journaling/DESYNC and before
the next frame; attempt 1 adds the frozen two static passes before GCAPTURE.
No old worker or physical result is modified.

Pre-execution replay halted on an incorrect assumption that math-state idle
was zero. `state_encoding_review.json` records the correction: retained
`spu_depth_math.state` is 16-bit one-hot, with bit 0 driven by the sole FDPE
preset FF and the other 15 bits by FDCE clear FFs. The retained RTL reset
state is S_IDLE; require synthesized idle `0x0001`. This is a decoder/helper
correction, with no RTL or bitstream change. Preserve the initial failed
assumption and earlier runtime seals.

`check_campaign.py` passes 156 focused checks, including 12 existing sender
tests applied to the two prospective sender copies, operator age/binding and
duplicate-report gates, direct-worker/reservation guards, forbidden command
and transport-error stops, frame rejection, finite-width oracle association
and one-hot settling. `recorded_replay.stdout.txt` records 10939 exact USB
exchanges replayed offline through the amended capture worker with identical
raw capture output; no native USB is opened during these checks.

Read-only host discovery finds DirtyJTAG serial CB81353DCE678119 and the
pinned CH340 ttyUSB0 path in the host namespace, with required node/serial
permissions. `host_discovery_offline.json` explicitly records actual adapter
access as NOT_TESTED; that access occurs only inside a reserved attempt.
Attempts used: zero; remaining: three. No JTAG, UART, reload or reset has run.

## 10. Attempt 1: rejected constant-zero capture frame

Owner readiness reply "Ready and powered. Proceed." was recorded at
2026-10-05T07:25:35Z. The executor interpreted ready/proceed as contextual
confirmation of the preceding powered/unchanged/stable-lock/same-image request.
The exact reply explicitly restated only readiness and power; the remaining
conditions/image were not individually restated. Preserve that limitation in
`operator_readiness.json`, rather than claiming an independent monitor report.

The slot was reserved at 07:26:56.882227Z with deadline 07:32:56.882227Z.
The measurement ran 07:27:06.551932Z–07:28:00.307008Z, terminal FAILED/exit 1,
inside the 180-second measurement limit. Both static passes completed (30
reads); the guard validated four subsequent snapshot frames after one GCAPTURE.
The fifth snapshot candidate, FAR `0x0B9F`, contained 101 all-zero data words
and contradicted 29 of its 76 pinned static controls. Candidate words were
journaled after DESYNC, then the guard halted before another frame or recovery.
No final status bracket was reached. Native cleanup released the adapter.

Classify `INCONCLUSIVE_READBACK_DATA_ANOMALY`. A complete payload does not
establish valid data or changing FPGA configuration. The partial snapshot
does not establish fresh bank contents, operand association or depth results.
No UART packet, FPGA load, reset or wiring change was commanded. Root cause
and display acceptance remain NOT_ESTABLISHED. Request the current display
report separately; absence/late arrival must not establish noninterference.

Record evidence in campaign-02 `attempt_01/{reservation.json,
read_capture.py.started.json,read_capture.py.result.json,managed_result.json,
capture_result.json,transport.jsonl,analysis.json,failure_review.json}`.
Used slots: one; remaining: two; reserved cumulative budget: 360 seconds.
State: `ATTEMPT_1_FAILED_REPAIR_REQUIRED`; hardware execution disabled.
Preserve all attempted workers/runtime hashes. Do not repeat the failed capture
or transmit A until a specific diagnosed correction or permitted diagnostic
amendment is reviewed. The remaining slots do not authorize blind retries.

### 10.1 Later display report

Owner replies "Stable lock; same image — observed now" at executor receipt
2026-10-05T07:34:31Z, outside both the 60-second after-capture window and
attempt deadline. Preserve it in `attempt_01/operator_after_failure.json` as
`LATE_OBSERVATION_ONLY`: current stable lock and unchanged image are reported,
but the reply cannot satisfy the expired phase gate or reopen attempt 1.
Operator intervention was not explicitly reported; do not assert its absence.

## 11. Reviewed adaptive attempt 2: static32 receive-path comparison

Use §3's prospective helper/diagnostic-amendment allowance within the existing
three-slot authorization. Attempt 2 is now read-only; no A or GCAPTURE is sent.
The original identical-A pair is INCOMPLETE. Attempt 3 remains unprepared;
do not execute the original attempt-02/03 UART commands under this amendment.

Failure review: the zero-data frame had normal IR capture `0x35` immediately
before and after. Local pico-dirtyJtag source `pio_jtag.c` selects DMA when
byte_length > 4 and otherwise polling; the retained host reads FDRO in 64-bit
chunks. Prepare a comparison using 32-bit FDRO receive chunks with the same
FPGA words, TMS/TDI trace, frequency request and total TCK count. Loaded adapter
firmware identity and DMA causality are NOT_ESTABLISHED. This is a conditional
path comparison, not an established root-cause repair.

Freeze `static32/attempt_02/static_projection.json`: FARs `0x0B1F` (preceding
valid capture frame), `0x0B9F` (current failed frame), `0x20B9F`, `0x2141B`
(prior anomalous addresses), two planned passes, eight reads maximum,
202 words each. Compare declared immutable controls only; exclude ZINI/ECC.
One checked connection, no GCAPTURE, UART, reload, reset or recovery. Keep
360-second attempt, 180-second subprocess and 160-second native caps unchanged.
The 64-bit ID-chain scan is retained; this change applies to FDRO receive
chunks only. Halt on the first invalid frame, with candidate journaling before
validation. Do not repeat a rejected frame.

Preserve all attempted workers and the original runtime seal. The adaptive
manager/guards are separate copies; original shared workers are verified against
their executed hashes. New modules and projections are sealed prospectively.

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/check_static32.py
# After fresh readiness, host namespace, once each:
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/static32/attempt_02/run_checked.py begin
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/static32/attempt_02/run_checked.py capture
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/static32/attempt_02/record_operator.py --phase after-capture --stdin-json
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/static32/attempt_02/analyze_result.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/review_static32.py
```

Seventeen offline checks pass: exact TMS/TDI traces, 67318 clocks and frame data
are equal across mocked 32/64 receive paths; unsafe commands, transport failures
and zero/ones contradictions halt. Record checks, source provenance, patches,
runtime hashes and exact mode in the adaptive bundle. Require passing adaptive
checks and the reviewed first failure before reserving slot 2. Skip the UART/
before-capture gate only for this pinned read-only mode; after-capture timing
and report binding remain unchanged. Activation/readiness do not enlarge the
budget. A static subset PASS does not establish full captured-state validity,
DMA causality, bank/depth correctness or GPU acceptance.

Seven additional offline launch checks pass in
`static32/attempt_02/adaptive_launch_checks.json`: the amended begin stage
reserves slot 2 without UART, rejects duplicate launches and requires the
pinned mode, checks and worker token. No hardware was opened by those checks.
The prospective runtime seal includes these results and the new copies;
executed attempt-01 workers still match their original hashes. Scope approval
persists; readiness must be refreshed before physical launch.

### 11.1 Attempt 2 result and late operator observation

Owner confirms "Powered, unchanged, stable lock, same image; ready now" at
executor receipt 2026-10-05T07:56:02Z. Reserve slot 2 at 07:56:20.741536Z,
deadline 08:02:20.741536Z. Measurement completes 07:56:29.746791Z–
07:56:50.388873Z, exit 0/COMPLETE. All eight planned static reads pass;
271 projected controls match both passes with zero unstable/mismatched bits,
and the repeated full frames are identical. IR stays 0x35; STAT stays
0x401079fc. No GCAPTURE, UART, reload or reset is sent. Classification:
STATIC_READ32_CONTROLS_MATCH. Loaded adapter firmware, DMA causality, full
snapshot validity and bank/depth correctness remain NOT_ESTABLISHED.

Owner replies "Same as before. Authorized." at executor receipt 07:59:42Z.
Preserve it as LATE_OBSERVATION_ONLY in `static32/attempt_02/operator_late.json`.
It reports unchanged display context but does not independently restate lock
or intervention. The expired 60-second gate is not satisfied or extended.
The measurement subprocess remains COMPLETE; the managed attempt is FAILED
for the late operator gate. Its reviewed result permits preparing the final
readback diagnostic under §3, with fresh readiness before any physical action.
Used slots: two; remaining: one; cumulative reserved budget: 720 seconds.

## 12. Reviewed adaptive attempt 3: reduced inputs/sums snapshot

Use the remaining existing slot for `snapshot32/attempt_03/`; keep the
360/180/160-second limits and 60-second report windows unchanged. No UART,
reload, reset or clock-setting change. At most one GCAPTURE and 56 frame reads:
two static passes over the same four FARs as §11, then one pass over 48 FARs
containing both complete raw banks, all 24 latched edge/depth fields, loader/
dispatcher/preparation settling controls, generations, math state, retained
sums and reciprocal state. Freeze the reduced 1667-bit projection and pinned
static controls. Final prepared coefficients/fracs are excluded; do not claim
their values or an A/B/identical-A transition from this campaign.

The specific amendment extends the statically qualified 32-bit FDRO receive
path to a guarded snapshot. Keep the checked TAP command sequence and native
cleanup. Journal each candidate after DESYNC and reject before the next frame
if a static control disagrees. No recovery or repeat follows a rejected frame.
Preserve every attempted worker; new final manager/guards/worker are separate
copies and all new dependencies are sealed prospectively.

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/check_final32.py
# After current complete readiness, host namespace, once each:
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/snapshot32/attempt_03/run_checked.py begin
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/snapshot32/attempt_03/run_checked.py capture
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/snapshot32/attempt_03/record_operator.py --phase after-capture --stdin-json
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/snapshot32/attempt_03/analyze_result.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/review_final32.py
```

Forty-seven offline checks pass: retained TAP/failure mock, exact scheduled
reads and one capture, forbidden-command stops, malformed/duplicate frame
rejection, both polarity decodes, settled-generation controls, recorded bank
bit 346 and sum mismatch replay, and final reservation without UART or duplicate
launch. The first offline check exposed an old projection path in the check
adapter; correct it prospectively and rerun before sealing. No hardware slot
is consumed by these checks.

Interpret sums only when quiet state, matching generations and unique settled
polarity qualify the snapshot. Compare latched descriptors with the measured
active raw bank before associating retained shared sums with active_unit.
Any failed association remains NOT_ESTABLISHED. One asynchronous snapshot
does not establish operand history or physical arithmetic/transport cause.
Close the campaign after attempt 3 regardless of result; no fourth action or
longer timeout is permitted under this authorization.

### 12.1 Final attempt result and campaign stop

Owner replies "Confirmed." to the complete final readiness question at
executor receipt 2026-10-05T08:17:25Z. Record its contextual confirmation of
power, unchanged wiring/configuration, stable lock and same image; individual
conditions were not independently restated in the raw reply. Preserve the
previous readiness separately.

Reserve final slot at 08:17:26.842978Z, deadline 08:23:26.842978Z. Measurement
runs 08:17:34.844679Z–08:18:42.357197Z, exit 1/FAILED, within its 180-second
limit. Both static passes complete all eight reads. One GCAPTURE is issued.
Eighteen captured frames pass pinned controls; candidate 19, FAR `0x2079F`,
contains 101 all-zero data words and contradicts 50 of 107 selected controls.
Its dummy frame is also all zero. Preserve the candidate after DESYNC; halt
before any further frame or recovery. IR captures around the failed read stay
0x35; no final STAT/IR bracket is reached. Native USB release/close/exit run.

Classify INCONCLUSIVE_READBACK_DATA_ANOMALY. A partial snapshot is not decoded
as fresh bank, latched-input or depth evidence. Changing FDRO chunks to 32 bits
alone did not qualify the full snapshot. Adapter firmware identity, DMA cause,
live configuration identity, operand association, physical arithmetic and GPU
root cause remain NOT_ESTABLISHED. No UART, FPGA load, reset or recovery was
commanded. The identical-A comparison remains INCOMPLETE_NO_PACKETS_SENT.
Request the current display report separately; none is established at closure.

Preserve `snapshot32/attempt_03/{reservation.json,read_capture.py.result.json,
capture_result.json,transport.jsonl,failure_analysis.json,managed_result.json,
review.json}` and prior runtime seals. Campaign state is CAMPAIGN_EXHAUSTED,
three used slots, zero remaining, 1080 seconds cumulatively reserved and
hardware execution disabled. Actual measured subprocess durations total
about 141.91 seconds across the three slots; unused time cannot authorize a
fourth action. Report this specific readback failure before proposing another
physical campaign.

## 13. Offline transaction audit and diagnostic confidence

Keep the campaign exhausted. Audit the retained attempt-03 transaction offline
in `readback_transaction_review_01/`. The adjacent successful FAR 0x2071F and
failed FAR 0x2079F have exact retained 52-word requests differing only at FAR
word index 15. Each has 202 correctly assembled 32-bit words; the failed
FDRO body's 808 native USB response bytes are already zero before Python
conversion. Native status/length checks and IR captures agree with the log.
Eight falsifiable audit checks pass without native access.

This localizes the recorded zeros upstream of Python word assembly. It does
not identify the physical TDO source, adapter execution, actual clocks, FAR
delivery or live configuration identity. Earlier bank-bit/depth mismatches
remain unconfirmed diagnostic leads, not established GPU hardware faults.
Some successful reads do not qualify the incomplete snapshot.

Prepare a separate, inactive two-address static qualification draft; do not
reopen this budget or execute another bank/depth campaign. Preserve the pending
monitor observation as context if received, late when outside the window;
it cannot repair the snapshot or establish causal probe noninterference.
