# Engineering Contract: T1d two-address static readback qualification

**Date:** 2026-10-05  
**Contract ID:** `contract_gpu_t1d_readback_transaction_qualification_2026-10-05.md`  
**Status:** CLOSED — attempt 1 static subset matched; stopped after PASS; two slots unused; full snapshot/GPU root cause unestablished.  
**Roles:** Spec Author, Halt-and-Flag Implementer and Integration Auditor:
local executor; operator supplies authorization, readiness and observations.

## 1. Commands and scoped files

```bash
python3 -B build/gpu_evaluation/t1d_readback_qualification_20261005/draft_01/check_qualification.py
# Only after explicit new approval, stdin JSON as specified in §4:
python3 -B build/gpu_evaluation/t1d_readback_qualification_20261005/draft_01/activate.py
# Only after complete current readiness, host namespace, once:
timeout 60s python3 -B build/gpu_evaluation/t1d_readback_qualification_20261005/draft_01/qualify_static.py
# Capture the operator reply verbatim in the bound stdin JSON in §5:
python3 -B build/gpu_evaluation/t1d_readback_qualification_20261005/draft_01/record_operator.py
# Review the completed attempt using stdin JSON; set the actual attempt number:
python3 -B build/gpu_evaluation/t1d_readback_qualification_20261005/draft_01/review_attempt.py --attempt 1
```

Modify only this draft, prospective helpers/evidence in its named build bundle,
offline retained-journal review in campaign-02 `readback_transaction_review_01/`,
and appended entries in [the hardware evidence ledger](../docs/hardware_evidence.md).
Preserve every previous campaign, failure, authorization, runtime seal and
exhausted stop. Do not execute another bank/depth campaign under this draft.

## 2. Retained transaction and limits

Use campaign-02 attempt-03 journal SHA-256
`d71f7de029c0402c91d9badd0daa0fb5dad91ab4920ac3e75ea7c6cade790ff8`.
The adjacent successful `0x2071F` and rejected `0x2079F` transactions have
identical 52-word requests except FAR word index 15. Each received 202 words
through 201 32-bit scans and a final 31-bit scan plus checked exit bit.
Native USB status/lengths and recorded word assembly agree. All 808 FDRO
body response bytes of the rejected read are zero before Python conversion;
the complete assembled frame is also zero. IR captures around it remain 0x35.
The successful preceding data frame has 42 distinct words.

Classify HOST_JOURNAL_TRANSACTION_CONSISTENT_DEVICE_RETURNED_ZERO_FDRO;
"device" here identifies the USB adapter response, not measured FPGA TDO.
This audit does not establish actual TAP execution, physical TCK/TDO, adapter
firmware identity, FAR delivery, live bitstream identity or GPU internal state.
Earlier bank-bit/depth mismatches remain unconfirmed diagnostic leads.

Eight falsifiable retained-journal checks pass. Evidence:
campaign-02 `readback_transaction_review_01/{extract_transaction.py,
check_review.py,review.json,focused_checks.json,preceding_good.jsonl,
rejected.jsonl}`. No native USB was opened for this review.

## 3. Frozen qualification and invariants

Owner authorizes "Authorized, 3 attempts." at executor receipt
2026-10-05T09:11:50Z. Amend the prepared proposal prospectively to **three
attempts maximum, 120 seconds per attempt, 360 seconds cumulative reserved**,
one foreground subprocess per attempt capped at 60 seconds, native USB capped
at 45 seconds. The previous three slots remain exhausted. Reserve each new
slot before native access; a launched slot counts regardless of its outcome.
No hidden retry, fourth attempt or timeout extension.

Read `[0x2071F, 0x2079F]` twice in that order, at most four reads, exactly
202 words each. Discard 101 pipeline words and compare only the 101 data words'
declared immutable controls. Freeze 114 controls for 0x2071F and 107 for
0x2079F, 221 total. Exclude captured FF/ZINI and ECC interpretation. No GCAPTURE
or state decoding. Preserve the existing 32-bit FDRO receive implementation,
checked TAP sequence and 1 MHz frequency request; actual TCK is unmeasured.
Loaded adapter firmware identity is unestablished; do not infer DMA cause.

Pin DirtyJTAG VID:PID 1209:c0ca, serial CB81353DCE678119 and one revision-1
Artix-7 device, raw IDCODE 0x13631093, normalized 0x03631093. Require host
namespace `mnt:[4026531832]` and actual checked native access. Never infer
adapter accessibility from sysfs alone. No UART access is needed.

Permit only the retained CFG_IN/CFG_OUT/BYPASS register-read sequence and
RCRC(7), RCFG(4), DESYNC(13). No GCAPTURE, RCAP, GRESTORE, JSHUTDOWN, WCFG,
FDRI, security or FPGA clock-setting writes; no adapter reset/firmware change,
FPGA load/reset/power cycle, wiring change, RTL change, bitstream substitution,
packet transmission or A/B acceptance change.

Log native OUT/IN bytes, return status, lengths, scan bits and frame candidates.
After DESYNC, validate every candidate before issuing another request. Stop
immediately on transport/status/control failure, preserve the candidate and
release/close the adapter; no recovery command or repeated rejected read.
Read known startup/status brackets before and after the complete read set;
a guard failure stops before the next bracket, which remains NOT_REACHED.

## 4. Approval, readiness and activation

Campaign identifier: `t1d_two_address_readback_qualification_20261005`.
Preserve the earlier single-attempt draft in
`before_three_attempt_amendment_01/`. The new authorization applies only to
this qualification, prospectively. Record it in `owner_authorization_received.json`
and `authorization.json`; do not inherit campaign-02 approval or readiness.

After explicit new approval, supply `activate.py` stdin JSON with exactly
the campaign identifier, `approved: true`, verbatim `owner_reply`, aware
`received_utc`, and these integer limits: max_attempts 3, cumulative_seconds 360, attempt_seconds 120,
subprocess_seconds 60, native_seconds 45, max_reads 4, passes 2,
captures_issued 0, uart_packets 0. Reject boolean substitutes, altered limits,
future receipt times, non-draft activation and failed helper checks.

Before execution, record `operator_readiness.json` with the same campaign ID,
raw owner reply, aware `recorded_utc`, powered/wiring_unchanged/
configuration_unchanged/signal_lock all true, and the current `image` text.
Require its age 0..300 seconds at launch. Preserve any contextual interpretation
of a short reply; do not manufacture independently restated conditions.
Approval persists; refresh only readiness when expired or setup changes.

Verify every runtime/dependency/projection SHA-256 before activation and launch.
Require the declared `timeout 60s` parent and host namespace. Lock the campaign,
reserve once before native access. Record each reservation, copied source bytes,
runtime seal, readiness, authorization, journal, result, observation and review
separately under `attempt_01/`, `attempt_02/` and `attempt_03/`. Preserve the
per-attempt copy before any prospective helper correction. Disable physical
execution after every read set until review. A killed subprocess without durable terminal evidence is unavailable;
record external TIMEOUT/exit 124 without reusing the slot or inferring success.

## 5. Operator report and interpretation

Request a monitor observation immediately after terminal measurement. The stdin
schema is campaign_id, integer attempt 1..3, phase `after-read`, aware observed_utc,
verbatim report, boolean signal_lock, boolean image_changed_since_previous_phase
and operator_intervention text. Accept the phase gate only for a COMPLETE
measurement, stable lock, unchanged image, no intervention and observation/
receipt within 60 seconds of completion and within the 120-second deadline.
Reject future/stale observations for the gate. Preserve late reports as
LATE_OBSERVATION_ONLY; they cannot repair invalid readback or establish causal
probe noninterference. The pending campaign-02 monitor report belongs to its
earlier attempt, not this campaign.

If all four reads match 221 controls and both passes agree, classify
STATIC_TWO_ADDRESS_CONTROLS_MATCH only. This establishes that selected static
reads worked under the tested conditions; it does not qualify GCAPTURE or a
complete snapshot, clear arithmetic, establish GPU acceptance or authorize a
later bank/depth campaign. Stop this test after a passing static qualification;
leave remaining slots unused. A failed control/transport bracket is an inconclusive
readback result. Compare failure position, raw USB bytes and address with the
retained transaction; do not assign a cause from correlation alone.

For a failed measurement, `review_attempt.py` must require a reviewed diagnosis
and a specific local correction-evidence file before setting proceed true.
Correct and focus-check the actual cause before retrying. A review without
correction evidence cannot enable another launch. Retained addresses, FPGA
commands, packet count and limits remain frozen; a prohibited scope change
requires a new contract. Before another allowed slot, require current readiness
and passing sealed helper checks. A pass, exhausted budget or stop decision
sets hardware execution false. Late/missing monitor evidence cannot authorize
a retry or erase the measurement result.

## 6. Verification and stop

The amended worker passes 70 offline checks: exact 32/64 TAP traces and frame
data, four-read limits, zero/ones contradictions, transport failure stops,
forbidden commands, inactive/exhausted/bad approval and stale readiness
refusals, report binding/types/expiry/lock/intervention, separate attempt/source
archives, preserved failed evidence, refusal of unreviewed/blind repeats,
reviewed corrected retry and stopping after qualification. Native USB opened: zero.
The local checker initially used an incorrect campaign-root path during
preparation; correct it offline before checks/sealing. No slot was consumed.

```bash
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/hardware_evidence.md spu_strategy/contract_gpu_t1d_readback_transaction_qualification_2026-10-05.md spu_strategy/contract_gpu_t1d_bank_depth_diagnosis_2026-10-05.md
```

No full RTL regression or synthesis claim is made. RTL, bitstream and arithmetic
inputs are unchanged. The earlier 53-check draft remains archived. Corrected
an incomplete fake projection fixture and reused mock-parent stream during
offline amendment checks before the 70-check PASS; no device access occurred.
Review all prospective helpers before activation. Stop
after qualification or three consumed attempts, or immediately if implementation review reveals a
contradiction or execution requires changing the prohibited scope.

## 7. Attempt 1: static subset PASS and campaign stop

Owner directly confirms "Powered, unchanged, stable lock, same image; ready now"
at executor receipt 2026-10-05T09:20:51Z. The measurement runs
09:20:51.639604Z–09:21:01.238404Z, COMPLETE/exit 0, about 9.60 seconds.
Read order is 0x2071F, 0x2079F, 0x2071F, 0x2079F. All 221 static controls
match both passes; zero unstable/mismatched bits, repeated full frames identical.
Data frames have 42 distinct words at 0x2071F and 44 at 0x2079F. IR stays
0x35 and STAT stays 0x401079fc. Both final brackets and USB cleanup complete.
No GCAPTURE, UART, FPGA load/reset or recovery is sent.

Classify STATIC_TWO_ADDRESS_CONTROLS_MATCH. The previously rejected address is
readable for this static test; the all-zero failure does not recur in these
four reads. This does not isolate transaction history, capture dependence,
adapter/physical timing or live image identity, or qualify full FF snapshots.
Earlier bank/depth leads and the GPU root cause remain unconfirmed.

The immediate post-measurement operator report is unavailable at closure;
the 60-second window expires without a phase-gate PASS. Preserve any subsequent
report as context, late when expired, without repairing readback or asserting
probe noninterference. The COMPLETE measurement and its static subset result
are separate from this unestablished operator gate.

`review_attempt.py` records proceed false. Manifest state STATIC_SUBSET_QUALIFIED,
hardware execution false; one slot used, two unused, 120 seconds reserved
within the approved 360-second maximum. Stop after the qualified subset; do
not spend the remaining slots on repeats or another bank/depth campaign.
Evidence: `attempt_01/{reservation.json,authorization.json,operator_readiness.json,
runtime_hashes.json,executed_sources/,transport.jsonl,result.json,analysis.json,
review.json}` under the named qualification bundle.

Owner later reports "Image is identical to last." at executor receipt
2026-10-05T09:25:04Z. Preserve it in `attempt_01/operator_late.json` as
LATE_OBSERVATION_ONLY: unchanged image context, received outside the report
window/deadline. Observation time, current lock and intervention were not
independently supplied. Do not satisfy the expired gate or infer causal
noninterference. No new hardware action is authorized by this observation.
