# Engineering Contract: T1d extended static readback history

**Date:** 2026-10-06  
**Status:** CLOSED, STATIC_HISTORY_QUALIFIED — attempt 2 COMPLETE; all 64 CMD checkpoints and static reads PASS. Physical execution disabled; one unused slot closed. Operator gate unestablished; report window expired.  
**Campaign:** `t1d_readback_history_20261006`  
**Roles:** local executor drafts, implements and audits; owner authorizes the
physical budget and supplies current readiness/display observations.

## 1. Commands and scope

```bash
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/hardware_evidence.md spu_strategy/contract_gpu_t1d_readback_history_2026-10-06.md
tools/run_detached_job.sh --output build/gpu_evaluation/t1d_readback_history_20261006/offline_check_01 --timeout 600 --notify-desktop -- python3 -B build/gpu_evaluation/t1d_readback_history_20261006/draft_01/check_qualification.py
# After terminal offline PASS, review and seal all helper/data/report files.
# Only after explicit approval of this new physical budget, bound stdin JSON:
python3 -B build/gpu_evaluation/t1d_readback_history_20261006/draft_01/activate.py
# Only after current readiness and checked host namespace:
timeout 210s python3 -B build/gpu_evaluation/t1d_readback_history_20261006/draft_01/qualify_static.py
python3 -B build/gpu_evaluation/t1d_readback_history_20261006/draft_01/record_operator.py
python3 -B build/gpu_evaluation/t1d_readback_history_20261006/draft_01/review_attempt.py --attempt 1
```

Modify this draft, prospective helpers/evidence in its named build bundle and
appended ledger entries. Preserve earlier campaigns, authorizations, failures,
executed sources and unused closed slots. Keep FPGA power/configuration and
wiring unchanged. No power cycle, UART, capture, reload, firmware or RTL change.

## 2. Measured baseline and frozen sequence

The predecessor's four A,B,B,A reads passed all 256 selected static bits,
each frame opposing the other fingerprint at 56 positions. Its operator
report was timely: stable lock, same image, no intervention. That campaign
closed after PASS; two unused slots cannot fund this new experiment.

Earlier retained failures occurred at read ordinals 27,35,48,55, with different
addresses and 32/64-bit receives. Static-only failures occurred at 48 and 55.
Run **64 reads in one checked connection: A,B,B,A repeated 16 times**.
A=0x217A1, B=0x217A2. This reaches beyond those recorded ordinal positions;
it does not reproduce their varying address order or prove a history cause.

Keep the existing 52-word RCRC/RCFG/FAR/FDRO request, 202-word response,
101 discarded pipeline words and 32-bit receive chunks. Validate every
candidate against all 128 pinned static bits for its requested address before
another request. Pair index i//2 is 0..31; each pair contains both addresses.
Compare all 32 observations of each static bit after 64 successful candidates.
Record full replies and full-frame repeatability separately from static validity.
Do not require unprojected/live bits to repeat or interpret live FF/ECC/RAM/SRL.

Reuse the identical hash-pinned projection, frozen PNR/FASM/frames/database
inputs and disk bitstream hash from the qualified predecessor. Check source
hashes at activation/launch; they do not establish full live image identity.
Pin DirtyJTAG VID:PID 1209:c0ca, serial CB81353DCE678119, single raw target
IDCODE 0x13631093/normalized 0x03631093 and revision 1. Require host namespace
mnt:[4026531832], actual checked native access and retained 1 MHz request;
actual physical TCK and adapter firmware build remain unmeasured.

## 3. First-failure handling and limits

Journal each native OUT/IN payload, status/length, scan and complete candidate.
After each completed receive, send retained DESYNC, preserve the candidate,
then validate. Halt on the first transport, extent, startup or static failure;
no next frame request, final status bracket or recovery after rejection.
Release/close the adapter. Compare the saved candidate with both fingerprints
offline. Native deadline expiry is TIMEOUT, not a static contradiction.

Permit only CFG_IN/CFG_OUT/BYPASS, STAT/CTL0 reads and RCRC/RCFG/DESYNC.
No additional FAR/CMD register read, MASK/CTL0 write, GCAPTURE, RCAP,
GRESTORE, JSHUTDOWN, WCFG/FDRI, reset, UART packet or reload. A direct FAR
echo is invalid under the recorded FARSRC=0 read-source setting.

Identical stale bytes remain indistinguishable from a fresh same-address
static reply. Do not claim universal stale-response rejection. A 64-read PASS
qualifies only these static controls in this sequence; it does not qualify a
long snapshot, identify a GPU fault, measure waveforms or establish display
acceptance. A failure localizes a rejected readback transaction, not its cause.

## 4. Frozen physical budget and readiness

Owner activated **three attempts, 270 seconds each, 810 seconds cumulative reserved**
as recorded in §8; the earlier proposal and preparation records are preserved.
Each uses one foreground interactive hardware subprocess capped at 210 seconds,
native access capped at 180 seconds, at most 64 reads, zero captures/UART/loads.
Predecessor frame intervals were about 2.2–2.5 seconds; use these only to size
the longer bounds, not as measured performance for 64 reads. Approval is not
inferred from authorization to prepare or an exhausted/closed older contract.

Activate only after reviewed offline PASS and sealing. Stdin approval requires
campaign_id, approved true, verbatim owner_reply, aware received_utc and exact
non-boolean integers: max_attempts 3, cumulative_seconds 810,
attempt_seconds 270, subprocess_seconds 210, native_seconds 180,
max_reads 64, passes 32, captures_issued 0, uart_packets 0. Refuse future
receipt, changed limits, failed checks, altered inputs or non-draft activation.

Before each attempt, save bound operator_readiness.json: verbatim owner reply,
aware recorded_utc, powered/wiring_unchanged/configuration_unchanged/signal_lock
true and current image text. Require age 0..300 seconds. Approval persists;
refresh only expired readiness or changed setup. Do not manufacture conditions
from an ambiguous reply; preserve any explicit contextual interpretation.

Lock and reserve a slot before native access. Copy sealed helper bytes, seal,
approval and readiness to attempt_NN/. A launched slot counts regardless of
COMPLETE/FAILED/TIMEOUT/unavailable outcome. Preserve external exit 124 as
TIMEOUT and account for interrupted/unavailable work before another launch.
No fourth attempt, hidden retry or timeout extension. Disable execution after
each attempt until review. Stop after PASS; leave remaining slots unused.
Failures require a diagnosis, a specific local correction-evidence file and
focused validation before a retry. Changed scope/budget needs new approval.

## 5. Operator report

Request a report immediately after terminal measurement. Require campaign_id,
non-boolean attempt integer 1..3, phase after-read, aware observed_utc,
verbatim report, boolean signal_lock/image_changed_since_previous_phase and
operator_intervention text. Accept the observation gate only for COMPLETE,
stable lock, unchanged image, no intervention and observation/receipt within
60 seconds of completion and the 270-second deadline. Preserve late reports
as context only; they cannot repair a rejected readback or establish causal
probe noninterference.

## 6. Offline checks, recovery and release

Use one deterministic offline check launch capped at 600 seconds; it does not
consume a physical slot. Follow AGENTS.md detached execution: record LAUNCHED
unit/evidence and end the turn. Interpret only exactly one terminal marker.
Do not repeat or extend this frozen offline limit after TIMEOUT without approval.

Check a full 64-read model and identical 32/64-bit TAP edge traces, word data
and clock counts. Fault fixtures cover swapped/other-address stale and uniform
data at positions 1,2,3,4,27,35,48,55,64, every static bit, truncated replies,
the identical-stale limit, all 64-read accounting/binding/timeout/refusal paths
and distinct attempted-source archives. Bind fixture limits to the real draft
manifest so a copied timeout error cannot hide behind a matching fake fixture.

Preliminary syntax, 64-read comparison and eight mocked activation checks pass;
no native USB opened. Corrected overlapping literal replacements in nested
timeout fields before full check launch, sealing or physical activation.
The restart interrupted preparation before this bundle existed; inspect
current state before creating it. Do not repeat the closed hardware campaign.
Reuse earlier unaffected gates; no RTL/math/shared regression infrastructure changed.

## 7. Terminal offline result and release review

Detached unit spu-offline_check_01-20261005T193747Z-219529 records exactly one
terminal marker, COMPLETE/exit 0, 2026-10-05T19:37:47Z–19:41:56Z, duration
249 seconds under the frozen 600-second limit. stdout records 498 checks PASS,
stderr empty, native USB opened false. Whole 32/64-bit TAP traces, frame data
and 532902 logical clock edges agree in the modeled 64-read experiment.

Verify helper hashes against the pre-launch checkpoint and provenance inputs
against frozen sources. All match; predecessor files remain unchanged. Seal
22 helpers/data/report files. The sealed draft worker refuses launch with
exit 1, Draft or inactive qualification, before reservation/native access.
This refusal consumes no physical slot. Evidence: draft_01/{focused_checks.json,
runtime_hashes.json,preparation_checkpoint.json,preparation_review.json};
offline_check_01/{COMPLETE,result.json,stdout.log,stderr.log,unit_name}.

At preparation closeout, manifest remained DRAFT_NOT_AUTHORIZED, execution false, attempts_used 0 and
three proposed slots. Prior generic preparation authorization does not activate
the newly frozen 270-second/810-second physical budget. Obtain approval and
current readiness through one combined prompt after this review. No physical
read, capture, UART, reload or reset had occurred at that preparation closeout.

## 8. Authorization, first failure and offline transaction review

```bash
python3 -B build/gpu_evaluation/t1d_readback_history_20261006/transaction_review_01/audit_pair.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/hardware_evidence.md spu_strategy/contract_gpu_t1d_readback_history_2026-10-06.md
```

The audit command creates evidence exclusively; it has already run and refuses
overwrite. Read its retained `review.json` instead of repeating it. No physical
retry command is released by this section.

Record owner reply "Confirmed." at 2026-10-05T19:55:15Z, bound to the combined
question stating the frozen budget and current readiness. Preserve the raw reply
and contextual readiness interpretation in the authorization/readiness receipts.
Host access check completes at 19:56:08.928503Z: pinned USB identity and native
claim/release/close pass without bulk JTAG commands, TAP clocks or a physical slot.

Attempt 1 runs 19:56:19.215522Z–19:57:14.842806Z, FAILED/exit 1, 55.63 seconds.
Twenty-two candidates validate; candidate 23 at B=0x217A2 is rejected against
44 of its 128 pinned static bits. All 202 returned words, including the 101
pipeline words, are zero. The opposite A fingerprint disagrees at 84 positions.
No next frame request or final STAT bracket occurs. IR captures before/after
the failed read are 0x35; native bulk errors are zero and USB closes. No UART,
capture, reload, reset or power cycle is sent.

Compare reads 22 and 23 with the retained transaction auditor: both request B,
both 52-word requests match, all 281 outgoing native packets match byte for
byte, and logged TDI scans/exit positions match. Read 22 has 48 distinct data
words; read 23's 808 FDRO body response bytes are already zero before Python
conversion. Recorded scans assemble exactly to the candidate words. This
failure needs no adjacent address change; the host word assembly is consistent
with the saved USB responses. Neither finding establishes adapter execution,
physical TDO, FPGA command acceptance or a causal firmware/timing defect.

Preserve `initial_failure_analysis.json`: its body-range summary included the
following 5-bit CFG_IN IR response byte a8. Final `analysis.json` filters the
202 FDRO bodies of 31/32 bits, yielding 808 all-zero bytes. This is an offline
summary correction, not a hardware/helper repair or additional attempt.

Record the owner observation verbatim: "Stable lock; same image; no intervention
— observed now", observation 19:59:43.268632Z and receipt 19:59:43.347339Z.
It arrives after the 60-second window and is LATE_OBSERVATION_ONLY. Preserve
it as display context; it cannot qualify the failed read or probe noninterference.

Keep manifest AWAITING_REVIEW, execution false, one slot consumed, two remaining,
270 seconds reserved of 810. Keep source seals and all prior receipts/failures.
`diagnostic_review.json` records the hold without an immutable retry approval.
Do not consume another slot without a specific correction, focused validation
and the existing review/readiness gates. No correction is established here;
root cause remains NOT_ESTABLISHED. Do not interpret bank/depth captures.

Evidence: `draft_01/attempt_01/` and `transaction_review_01/` under the named
campaign. Journal SHA-256:
`c8b83219ef341256285f73c19171dfaf52d17507f3dfa7b1b966563dfd601e9d`.
Physical result is recorded in hardware evidence §3.35.25.

## 9. Proposed CMD checkpoint amendment — not activated

```bash
# Offline packet calculation only; create once, refuse overwrite:
python3 -B build/gpu_evaluation/t1d_readback_history_20261006/cmd_checkpoint_proposal_01/packet_review.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_gpu_t1d_readback_history_2026-10-06.md
```

Record the subsequent owner message "Authorized and ready." as authorization
to continue diagnosis and a readiness statement. It supplies no specific
correction and does not itself replace §3's explicit CMD-read exclusion.
Keep execution false and both remaining slots unused.

Propose replacing that exclusion with one CMD register read per candidate,
after RCFG preparation and before FAR/FDRO arming. This closes a measurement
gap; it is not an established repair of the all-zero response. Obtain approval
of this scope amendment before physical execution. Preserve the existing
three-slot campaign: one consumed, two remaining, 270 seconds each, 810 total
reserved, external 210/native 180 seconds. Do not enlarge deadlines or budget.

Use sealed request words 0..13 (dummy/sync/NOOP/RCRC/NOOPs/RCFG/NOOP).
Append CMD read header 0x28008001 and two NOOP words: 17 CFG_IN words total.
Switch to CFG_OUT and consume exactly one 32-bit CMD reply. Journal raw reply
and require `(raw & 0x1f) == 4`; preserve all higher bits without interpretation.
On mismatch halt before FAR/FDRO and close native access; no recovery or retry.
On match switch to CFG_IN without TAP reset, re-sync or DESYNC. Send the
original request suffix: FAR header/address, FDRO type-1/type-2 read headers,
34 NOOPs (38 words). Receive the original 202 words, DESYNC and apply the
existing per-candidate 128-bit static guard. Never insert a register read after
FDRO has been armed. Keep original ABBA×16 order, fingerprints and 1 MHz request.

Journal the CMD checkpoint separately from frame candidates so it does not
alter candidate/slot counting. A CMD match followed by an invalid frame would
localize the rejected response after a command read consistent with RCFG;
it would not establish FAR/FDRO acceptance, physical TDO, adapter firmware,
response freshness or GPU state. A passing amended run qualifies only its
changed sequence and cannot be substituted for the original 64-read PASS.

Before releasing a worker, use prospective copies; preserve old seals and
attempt archives. Independently review the TAP continuation and packet parser;
validate CMD mismatch/zero/one/truncation, no FDRO after rejection, static guard,
transport cleanup, exact command allowlist and timeout/slot/report accounting.
Reuse earlier passed checks only where inputs are unchanged. No hardware worker
is implemented or released by this packet-layout proposal.

Primary reference: [AMD UG470 v1.17](https://docs.amd.com/api/khub/documents/FOs3lXmlcWxBhTIFxVKyGA/content),
table 5-23 (CMD read/write address 4), table 5-25 (RCFG code 4), and chapter 6
(CFG_IN/CFG_OUT register access). The document's shutdown example is not
permission to shut down this running GPU. Source facts establish the register
and packet fields; continuation correctness still requires helper review.

## 10. Approved amendment and prospective worker validation

```bash
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/hardware_evidence.md spu_strategy/contract_gpu_t1d_readback_history_2026-10-06.md
tools/run_detached_job.sh --output build/gpu_evaluation/t1d_readback_history_20261006/cmd_offline_check_01 --timeout 600 --notify-desktop -- python3 -B build/gpu_evaluation/t1d_readback_history_20261006/cmd_checkpoint_worker_01/check_qualification.py
```

Record owner reply "Approved and ready." to the explicit §9 scope question in
`scope_amendment_authorization_01.json`, recorded 2026-10-05T20:19:17.087061Z.
It approves the CMD checkpoint and retains the two remaining physical slots
and all existing physical limits. Preserve the readiness statement; refresh
bound readiness if older than §4's 300-second limit after worker validation.
The §3 CMD-read exclusion is prospectively replaced only by §9's checkpoint;
all other exclusions and previous records remain in effect.

Copy retained helpers/projection/provenance to `cmd_checkpoint_worker_01/`.
Keep the active bundle and attempt 1 archives/seals unchanged. The prospective
manifest retains consumed-slot accounting, state DRAFT_AMENDMENT_NOT_RELEASED,
execution false. It has no physical activation/readiness receipts or runtime
seal and must not be executed against hardware. Later release promotes reviewed
helper bytes into the existing campaign; never activate a second slot counter.

Implement exactly §9's split request and guard; record all CMD checkpoints
separately. Use distinct successful classification
STATIC_64_CMD_CHECKPOINT_CONTROLS_MATCH in both worker and reviewer. Keep
the operator/report, hardware deadlines, cleanup and slot rules. This corrects
the measurement's missing command-state observation, not the physical fault.

Preliminary syntax and first-CMD-zero rejection checks PASS without native USB.
The independent TAP model requires an exact 17-word preparation, one consumed
32-bit CMD reply and the exact 38-word continuation, with no TAP reset between
the consumed reply and continuation. Added fixtures reject CMD zero/all-one/
RCRC/DESYNC at ordinals 1,3,23,64 before FAR/FDRO, truncated CMD replies and
unauthorized packets; preserve high raw bits without asserting their meaning.
Retain full 64-read 32/64-bit TAP parity, static faults/bit mutations, cleanup,
launch/review/refusal, report expiry and reservation/source-archive checks.

Run one new detached offline check of the changed worker under a frozen
600-second limit, consuming zero physical slots. This is validation of new
inputs, not a repeat of the already passed original job. Preserve the original
498-check PASS. Record source hashes before launch and after the terminal result.
After LAUNCHED record unit/evidence and end the turn under AGENTS.md §4.2.
Do not release hardware, seal a PASS or authorize attempt 2 until exactly one
terminal marker and the required passing results have been reviewed. Physical
manifest remains AWAITING_REVIEW/execution false, one consumed/two remaining.

## 11. Amended worker terminal PASS and release

```bash
# Already completed; do not repeat or overwrite the retained review:
python3 -B build/gpu_evaluation/t1d_readback_history_20261006/draft_01/review_attempt.py --attempt 1 < build/gpu_evaluation/t1d_readback_history_20261006/draft_01/review_input_01.json
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/hardware_evidence.md spu_strategy/contract_gpu_t1d_readback_history_2026-10-06.md
# Following host-access PASS in the intended execution context:
timeout 210s python3 -B build/gpu_evaluation/t1d_readback_history_20261006/draft_01/qualify_static.py
```

Detached unit spu-cmd_offline_check_01-20261005T202207Z-227279 has exactly one
terminal marker COMPLETE, exit 0, 2026-10-05T20:22:07Z–20:25:42Z, duration
215 seconds under its frozen 600-second limit. stdout records 601 checks PASS,
stderr empty, native USB opened false. Modeled 32/64-bit data and complete
TMS/TDI traces agree over 543270 clock edges in the amended 64-read sequence.

Verify all prepared source hashes against the pre-launch checkpoint and all
projection provenance hashes: unchanged. Preserve the active 22-file seal,
helpers and prior readiness/state in `before_cmd_checkpoint_amendment_01/`;
attempt 1's archived executed bytes remain untouched. Promote only reviewed
prospective helper/data/report files and seal 23 files in the existing bundle.
Do not activate the prospective manifest or create another slot counter.

Record owner reply "Authorized and ready." with bound current readiness at
2026-10-05T20:27:01.090304Z. Preserve the explicit contextual interpretation:
powered, unchanged wiring/configuration and stable lock/same image from the
continuing campaign; the short reply did not separately enumerate conditions.
Approval of the scope and original physical limits persists.

Evidence `amendment_release_01.json` identifies the approved correction of a
measurement gap, source promotion, passed fixtures and unchanged slot accounting.
The sealed reviewer accepts it at 20:27:01.512200Z, state REVIEWED_NEXT_ATTEMPT,
execution true. This releases attempt 2 only while current readiness and host
access pass; it does not establish a physical repair. Attempt 1 remains FAILED,
operator gate false/late context. Stop on the next first mismatch; classify
successful amended reads distinctly, and require review before any third slot.

## 12. Attempt 2 physical result: amended static sequence PASS

```bash
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/hardware_evidence.md spu_strategy/contract_gpu_t1d_readback_history_2026-10-06.md
# Bind the pending monitor report to attempt 2 via stdin JSON, once only:
python3 -B build/gpu_evaluation/t1d_readback_history_20261006/draft_01/record_operator.py
# Close after the passing measurement; no third attempt is permitted:
python3 -B build/gpu_evaluation/t1d_readback_history_20261006/draft_01/review_attempt.py --attempt 2
```

Host access check 02 completes at 2026-10-05T20:27:55.753136Z with pinned
native open/claim/release/close, no bulk JTAG command or TAP clocks. Attempt 2
runs 20:28:02.602156Z–20:30:41.579267Z, COMPLETE/exit 0, 158.98 seconds under
the unchanged external 210/native 180/attempt 270-second bounds.

All 64 CMD replies are raw 0x4 and pass the low-five-bit RCFG guard. All 64
static candidates match their requested A/B fingerprints. The 256 projected
bits are each observed 32 times with zero unstable or mismatched positions;
repeated full data frames are identical. IR startup brackets remain 0x35,
STAT brackets 0x401079fc, CTL0 0x501. Native bulk errors zero and USB cleanup
complete. All 23 executed source archives match the runtime seal. No capture,
UART, reload, reset or power cycle occurs.

Classify STATIC_64_CMD_CHECKPOINT_CONTROLS_MATCH. Preserve first attempt's
failure and do not substitute this changed sequence for the original experiment.
The checkpoint changed transaction splitting, USB calls and timing; one PASS
cannot distinguish their causal effects or prove a physical repair. No snapshot,
GPU state, waveform, full live-image identity or reply freshness is established.
Root cause NOT_ESTABLISHED; earlier bank/depth leads remain unconfirmed.

Request the post-read monitor report immediately after completion. Its observation
and receipt must fall by 20:31:41.579267Z; otherwise preserve late context only.
Do not infer a report from pre-execution readiness. Physical PASS still requires
campaign closure and cannot fund a third repeat or a new snapshot scope.

Evidence: `draft_01/attempt_02/{reservation.json,runtime_hashes.json,
executed_sources/,result.json,analysis.json,transport.jsonl}`. Journal SHA-256:
`91bf1fbd8a03b301e83a10abf1d70c7a72958bb8213d42d70c04b37ed0259939`.
Two slots consumed, 540 seconds reserved of 810; one unused slot must remain
unused when the review closes the campaign. Hardware evidence §3.35.28.

Closeout finds no monitor report received within the observation window.
`attempt_02/operator_report_status.json` preserves that absence; do not create
a placeholder operator report or block a later genuine report. The sealed
reviewer closes after the passing measurement with operator_gate false,
state STATIC_HISTORY_QUALIFIED and hardware_execution_permitted false.
Two slots consumed/540 seconds reserved, one closed unused. A later monitor
reply is context only and cannot establish the timely operator phase gate.
