# Engineering Contract: T1d A → B → B → A static frame fingerprints

**Date:** 2026-10-05  
**Status:** CLOSED — attempt 1 sequence PASS and timely operator gate PASS; two slots unused; hardware execution disabled.  
**Campaign:** `t1d_address_fingerprint_20261005`  
**Roles:** local executor drafts, implements and audits; owner authorizes and
reports board readiness/display observations. No delegated agent work.

## 1. Commands and scope

```bash
python3 -B build/gpu_evaluation/t1d_address_fingerprint_20261005/draft_01/check_qualification.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/hardware_evidence.md spu_strategy/contract_gpu_t1d_address_fingerprint_2026-10-05.md
# Only after explicit new approval; supply the bound stdin JSON in §4:
python3 -B build/gpu_evaluation/t1d_address_fingerprint_20261005/draft_01/activate.py
# Only after fresh readiness and checked host execution context:
timeout 60s python3 -B build/gpu_evaluation/t1d_address_fingerprint_20261005/draft_01/qualify_static.py
# Supply the bound observation stdin JSON in §5:
python3 -B build/gpu_evaluation/t1d_address_fingerprint_20261005/draft_01/record_operator.py
# Supply the review stdin JSON in §6; use the actual completed attempt number:
python3 -B build/gpu_evaluation/t1d_address_fingerprint_20261005/draft_01/review_attempt.py --attempt 1
```

Modify this contract, prospective helpers/evidence under the named bundle and
appended hardware-ledger entries. Extend copies of retained checked workers.
Preserve all earlier campaigns, failures, authorizations, seals and unused
slots. No RTL, firmware, bitstream, wiring or arithmetic changes.

## 2. Frozen experiment and acceptance

Read exactly `[0x217A1, 0x217A2, 0x217A2, 0x217A1]`. The first two reads have
pass_index 0, the last two pass_index 1. Each request uses the retained 52-word
RCRC/RCFG/FAR/FDRO sequence: only the FAR data word changes. Request 202 words,
discard 101 pipeline words and validate all 128 projected static bits for
that address in the 101 data words. Freeze 256 bits total; 56 shared positions
have opposing expectations. Both addresses include zero and one expectations.
Compare their repeated static values after all four candidates pass.

Use the hash-pinned PNR/FASM/frames/device-database projection from campaign-01
attempt-03. Those selected LUT INIT bits matched in both retained passes.
Verify provenance input hashes at activation and launch. Include the frozen
disk bitstream hash `52d45da0743c326f1700b4efa7fa0187523ea6e456948f274e2cc276ccd7b914`.
Disk hashes and selected controls do not establish full live image identity.
Exclude captured FF/ZINI, ECC and mutable RAM/SRL interpretation.

Record all native OUT/IN bytes, status, lengths, scan bits and complete frame
candidates. Send the retained DESYNC after a completed receive; validate and
log the candidate before any next read. Stop on the first extent, transport,
startup or static contradiction. Preserve replies and release/close USB; no
recovery or repeated rejected read. Final status brackets remain NOT_REACHED
when a guard stops before them. Compare a saved rejected frame with both
fingerprints offline; an alternate match is a diagnostic lead, not a cause.

Keep 32-bit FDRO receive chunks, checked TAP transitions and the 1 MHz request;
physical TCK is unmeasured. Pin DirtyJTAG 1209:c0ca, serial CB81353DCE678119,
raw target IDCODE 0x13631093/normalized 0x03631093, revision 1. Require native
host namespace `mnt:[4026531832]` and checked actual adapter access.

Permit only retained CFG_IN/CFG_OUT/BYPASS, STAT/CTL0 reads and
RCRC(7)/RCFG(4)/DESYNC(13). No FAR echo assertion: recorded CTL0=0x501 has
FARSRC=0. No new FAR/CMD register read, MASK/CTL0 write, capture, reset,
JSHUTDOWN, GRESTORE, WCFG/FDRI, UART packet, load, adapter reset or firmware
change. No FPGA clock or security setting change.

## 3. Freshness limit and offline review

Reject fixtures with swapped fingerprints, stale replies from the other
address, all-zero/all-one data, invalid frame word extent and truncated raw
replies. Exercise failure at each of the four positions and mutation of every
projected bit. Require preservation of the rejected candidate and no subsequent
frame request. Keep falsifiable launch/report/budget/archive/retry checks.

A byte-identical stale B response at B → B is observationally indistinguishable
from a fresh static B response. Explicitly exercise and record that limitation;
do not claim universal stale-response rejection or freshness from USB success,
host sequence labels, identical data or healthy IR. Adding a device freshness
tag would require a different, separately reviewed experiment.

The retained 32/64-bit mock comparison must produce identical TAP edge traces,
clock counts and frame data for this sequence. Check projection separation and
each fingerprint's zeros/ones. No native USB may open during offline checks.
Seal every flat helper, projection, provenance and passing focused report
in runtime_hashes.json after checks; preserve executed sources before access.

## 4. Proposed budget, approval and readiness

Propose **three attempts maximum, 120 seconds per attempt, 360 seconds
cumulative reserved**. Each has one foreground subprocess capped at 60 seconds,
native USB capped at 45 seconds, at most four static reads, zero captures,
zero UART packets and zero loads. This draft does not activate that budget.
The prior campaign's two unused slots remain unused and cannot be reassigned.

Activation stdin requires campaign_id, approved true, verbatim owner_reply,
timezone-aware received_utc and exact non-boolean integer limits:
max_attempts 3, cumulative_seconds 360, attempt_seconds 120,
subprocess_seconds 60, native_seconds 45, max_reads 4, passes 2,
captures_issued 0, uart_packets 0. Refuse future receipt, changed limits,
non-draft activation, failed checks or changed sealed inputs.

Before each launch, save operator_readiness.json bound to this campaign with
verbatim owner reply, aware recorded_utc, powered/wiring_unchanged/
configuration_unchanged/signal_lock true and current image text. Require age
0..300 seconds. Authorization persists; refresh readiness after expiry or
setup change. Preserve contextual interpretation of short replies explicitly.

Lock the campaign and reserve each slot before native access. Archive source
bytes, seal, authorization and readiness under attempt_NN/. A launched slot
counts regardless of COMPLETE, FAILED, TIMEOUT or unavailable result. Never
infer success from elapsed time or logs without durable terminal evidence.
On an external exit 124, preserve TIMEOUT separately; do not reset accounting.
An unavailable result leaves execution disabled by the RUNNING-state guard;
review/account for it before any prospective amendment. No hidden retries.

## 5. Operator observations

Request an observation immediately after terminal measurement. Record stdin
campaign_id, non-boolean integer attempt 1..3, phase `after-read`, aware
observed_utc, verbatim report, boolean signal_lock, boolean
image_changed_since_previous_phase and operator_intervention text.

Accept the phase gate only for COMPLETE, stable lock, unchanged image, no
intervention and observation/receipt within 60 seconds of completion and the
120-second attempt deadline. Refuse future/invalid timestamps and binding/type
errors. Preserve expired reports as LATE_OBSERVATION_ONLY; they cannot repair
a rejected frame or establish causal probe noninterference.

## 6. Review and stop

Disable execution after every attempt until review. A four-read PASS qualifies
only these static controls under this sequence; stop and leave remaining slots
unused. Do not qualify a long snapshot, scene banks, prepared depth, UART,
electrical timing, arithmetic or the display. Root cause remains NOT_ESTABLISHED.

For a failed attempt, review_attempt.py requires a diagnosis and a specific
local correction-evidence file before proceed true. Correct and focus-check
the cause before retrying; a failure alone does not authorize another launch.
Do not amend executed copies or erase earlier failures. A qualified result,
stop decision or three consumed slots closes physical execution. Renew approval
for changed scope, larger budget or timeout. No blind retry or fourth attempt.

## 7. Preparation review recorded

417 offline checks PASS, native USB opened zero. Checks cover A,B,B,A, all
256 projected-bit mutations, 56 opposing positions, swapped/other-address
stale and uniform frames at every position, raw/frame truncation, identical
stale B limitation, full 32/64-bit TAP trace agreement, launch refusals,
operator expiry/binding, separate attempt archives, diagnosed corrected retries
and native deadline accounting as TIMEOUT. Reuse retained transport helpers;
new fixture module is 135 lines, all helpers stay below 150 lines.

22 helper/data/report files are sealed. Verify original worker copies and
projection input hashes; earlier files remain unchanged. Execute the sealed
draft worker to confirm refusal before reservation/native access:
`ValueError: Draft or inactive qualification`, exit 1. This expected refusal
does not consume a slot. Manifest remains DRAFT_NOT_AUTHORIZED, execution
false, attempts_used 0, three proposed slots available. No authorization or
operator readiness is inherited or manufactured. No hardware test occurred.

Documentation audit and whitespace gates apply to this diagnostic-helper
preparation; RTL, arithmetic and shared regression infrastructure are unchanged.
No full repository, synthesis, waveform or physical qualification claim is made.

## 8. Authorization, attempt 1 and closeout

Owner replies "Authorized and ready." to the combined three-attempt/readiness
question; executor records receipt 2026-10-05T19:16:12Z. Preserve the raw reply
and explicit contextual interpretation of powered, unchanged wiring/configuration,
stable lock and same image; these conditions were accepted in context, not
independently restated. Activate the proposed frozen budget. Approval and
readiness are copied into attempt_01/ before native access.

Attempt 1 runs 19:16:40.147985Z–19:16:49.731953Z, COMPLETE/exit 0, about
9.58 seconds. Order is exactly A,B,B,A. All 256 selected static bits match
across both observations, zero mismatches/unstable bits. Repeated full data
frames are identical. Each frame contradicts the other address's fingerprint
at exactly 56 positions. Data frames have 42 distinct words for A and 48 for B.
IR stays 0x35, STAT 0x401079fc, CTL0 0x501. Native bulk errors zero; release,
close and exit complete. All 22 archived helper/data/report files match the
attempt seal. No capture, UART, load, reset or recovery command was sent.

Owner reports "Stable lock; same image; no intervention — observed now".
The bound report is recorded at 19:17:37.783229Z, within 60 seconds and the
attempt deadline; accepted_for_phase_gate true. This is observed unchanged
display context, not causal probe noninterference or GPU display acceptance.

Review records proceed false, measurement_qualified true and operator_gate
true. Manifest STATIC_SUBSET_QUALIFIED, execution false, one slot used, two
unused, 120 seconds reserved within the approved 360-second total. Stop after
PASS; do not reuse the two slots for a repeat or longer snapshot experiment.
Classify STATIC_FOUR_READ_FINGERPRINT_SEQUENCE_MATCH only. Root cause remains
NOT_ESTABLISHED; identical stale B and longer transaction-history failures
remain outside this qualification.

Evidence: attempt_01/{reservation.json,authorization.json,operator_readiness.json,
runtime_hashes.json,executed_sources/,transport.jsonl,result.json,analysis.json,
operator_after_read.json,review.json}. Journal SHA-256
`2127be1ed3ff9bee785fef53503bcba275ea6d2e1729e7fd01296272b7d9eb62`.
The initial offline summary attempted len() on integer mismatch counts and
raised TypeError before creating output. Correct the summary to use counts;
record that local correction in analysis.json. No worker/source change or
hardware retry occurred.
