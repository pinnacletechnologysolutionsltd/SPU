# Engineering Contract: T1d snapshot frame qualification

**Date:** 2026-10-06  
**Campaign:** `t1d_snapshot_qualification_20261006`  
**Status:** SNAPSHOT_STATIC_CONTROLS_QUALIFIED, CLOSED — attempt 2 COMPLETE with all 56 frames and static controls passing; timely display observation accepted. Two of three slots reserved; one slot closed unused. Runtime freshness, GPU cause and acceptance remain unestablished.  
**Roles:** local executor drafts, reviews and audits; owner approves a new
bounded physical budget and supplies current readiness/observations.

## 1. Commands and scope

```bash
# Offline review only; create once, refuse overwrite:
python3 -B build/gpu_evaluation/t1d_snapshot_qualification_20261006/review_01/review_inputs.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/hardware_evidence.md spu_strategy/contract_gpu_t1d_snapshot_qualification_2026-10-06.md
```

Modify this draft, its named build evidence and appended ledger records only.
Preserve all prior contracts, workers, source seals, attempts and authorizations.
No budget activation or hardware attempt is released until §7's checks/review.
Read `review_01/review.json` after the review command creates it; do not repeat.

## 2. Pre-execution flaw and minimal correction

At initial review the retained snapshot projection covered 48 FARs and 1667 runtime bits. Its frame
guard for FAR 0x2151F contains seven controls, all expecting 1. Consequently
an all-one data frame satisfies that guard. Known readback anomalies include
uniform data; guard coverage cannot be assumed sufficient from nonzero count.

The review HALTED under AGENTS.md §2. The authorized correction is recorded
in §6. Add at least one source-proven immutable expected-zero
control for this FAR using the frozen FASM/frames/placement/database inputs.
Do not infer an unlisted bit is zero, use a mutable FF/captured state bit,
alter old projections or weaken the existing expected-one controls.
Require both expected values {0,1} in every planned capture frame's guard.
Record feature-to-FAR/word/bit derivation and source hashes before accepting
the correction. Validate uniform zero/one rejection and every selected-bit
mutation before implementing or releasing a physical snapshot worker.
Do not claim any earlier physical read at this FAR actually returned all ones.

## 3. Qualified predecessor and its limits

[Hardware evidence §3.35.28](../docs/hardware_evidence.md) records 64 successful
CMD checkpoints and 64 static reads under the amended sequence. Every CMD
reply was raw 0x4; all selected static controls matched. The changed transaction
split, USB calls and timing were not isolated as causes of the earlier failure.
Root cause remains NOT_ESTABLISHED.

No timely monitor report was received; display acceptance/noninterference is
unestablished. The predecessor is closed after PASS, with one closed unused
slot. That slot and its readiness/authorization cannot fund this new campaign.
Require a separately reviewed contract, new owner-approved frozen physical
budget and current readiness before physical execution. Do not ask for these
until the guard correction, prospective helper review and checks are concrete.

## 4. Prospective measurement constraints after correction

Extend checked worker copies using the CMD checkpoint before each FAR/FDRO
request. Every captured candidate must match all declared static controls
before another frame request. On first contradiction preserve raw replies and
candidate, close native access and reject the entire snapshot. No partial bank,
descriptor or depth interpretation. Do not reread a rejected frame.

Retain one addressed 202-word reply with 101 pipeline words discarded and
32-bit receive chunks. Hash-pin target/adapter identity, 1 MHz request and
retained bitstream/placement/FASM/database sources; actual TCK and loaded
adapter firmware remain unmeasured. No UART, reload, power cycle, reset, wiring,
RTL, bitstream, acceptance-criteria or configuration clock/security writes.
GCAPTURE needs explicit scope approval in the eventual physical contract;
the static-only predecessor did not authorize it.

First qualify the complete captured frame set. Passing static controls is
necessary but cannot alone establish capture freshness, timing, polarity or
coherent operand association. Review capture-clock/single-shot settings and
both polarity decodes separately. Keep each unmet runtime condition explicit;
do not promote initial configuration cells or old snapshots to current state.
The retained reduced projection excludes final prepared coefficients/fracs;
do not claim they have been measured without a separately reviewed extension.

Record timezone-aware observed_utc, campaign/attempt/phase and receipt time for
before/after JTAG reports. Define and freeze report ages/deadlines with the new
budget; missing/late reports remain context only. Stable monitor observations
do not establish causality or repair invalid captured frames.

## 5. Initial release hold and evidence (historical)

At initial review physical budget, exact capture/read schedule, worker release
and offline job budget were NOT SET. Keep execution disabled. Resolve §2 before drafting those
implementation steps; §6 now records that correction. Reuse prior
passed gates only where inputs remain unchanged. Apply detached execution to
new deterministic checks expected to exceed 60 seconds under AGENTS.md §4.2.

Evidence: `build/gpu_evaluation/t1d_snapshot_qualification_20261006/review_01/`
`{review_inputs.py,review.json}`. The review verifies retained source hashes,
guard coverage and closed predecessor state without native USB access.
Guard review is offline evidence, not a snapshot or GPU diagnosis.

## 6. Authorized guard repair and focused checks

```bash
# Both commands already completed; exclusive evidence output refuses overwrite:
python3 -B build/gpu_evaluation/t1d_snapshot_qualification_20261006/repair_01/derive_guard.py
python3 -B build/gpu_evaluation/t1d_snapshot_qualification_20261006/repair_01/check_repair.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/hardware_evidence.md spu_strategy/contract_gpu_t1d_snapshot_qualification_2026-10-06.md
```

Owner reply "Authorized repair." permits this offline correction. Preserve
`review_01/` and all original projections/helpers. Create new prospective
`repair_01/{projection.json,frame_guards.json,proof.json}` only. Runtime groups,
1667 mapped bits, 48 capture FARs, polarity, limits and old controls are unchanged.

Use enabled FASM feature CLBLL_L_X42Y186.SLICEL_X1.AFFMUX.O6. Its pinned
CLBLL_L.SLICEL_X1.AFFMUX.O6 database encoding is
`30_04 !31_00 !31_01 !31_02`. Tilegrid segment base 0x21500, offset 73,
36 minor frames and two words maps token !31_00 to FAR 0x2151F, data word 73,
bit 0, expected 0. Frozen frame word is 0x00308218. Verify all four feature
tokens against frozen frames, not merely the selected zero. The selected mux
configuration bit is absent from the runtime projection and is not ZINI/live FF
state. Hash-pin original sources, database, feature mapping and derivation.

Append this one guard to both new lists: projection static guards 2835→2836,
full frame guards 2851→2852. The full list covers 49 FARs: the 48 capture FARs
plus one retained baseline FAR. Every guard FAR now has both expected values.
Require prospective worker preflight to call
`guard_coverage.validate_guard_coverage(declared_fars, frame_guards)` before
native access. It rejects missing zero/one coverage, malformed/non-integer or
boolean fields, duplicate locations/FARs, undeclared FARs and ECC word 50.
At repair closeout this helper was prepared; a snapshot worker was not yet implemented or released.

3165 focused checks PASS with no native USB or physical slot. Reproduce the
old all-one acceptance at 0x2151F, reject it with the repaired guard, accept
frozen-frame static controls, reject both uniform payloads and extent errors
at all 49 guard FARs, and reject every selected-bit mutation across 2852
controls. Remove every FAR's zero controls to falsify coverage validation;
reject duplicates/empty sets and malformed fields. Verify both prospective
lists preserve old entries and the runtime projection is otherwise unchanged.
Use the hash-verified validator archived by the qualified predecessor.

Record `repair_01/{focused_checks.json,proof.json,guard_coverage.py,doc_gates.json}`.
Only §2's uniform-frame guard gap is repaired. Capture freshness/clock/polarity,
operand association, display noninterference and GPU cause remain unqualified.
Do not reinterpret earlier snapshots or reopen the closed static campaign.
At repair closeout the new physical/offline job budgets and exact worker
remained NOT SET. §7 records subsequent authorization and preparation.

## 7. New owner authorization, frozen schedule and release checks

```bash
# One new deterministic check job, timeout 600 seconds; no native USB:
tools/run_detached_job.sh \
  --output build/gpu_evaluation/t1d_snapshot_qualification_20261006/offline_check_01 \
  --timeout 600 --notify-desktop -- \
  python3 -B build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/check_snapshot.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/hardware_evidence.md spu_strategy/contract_gpu_t1d_snapshot_qualification_2026-10-06.md

# Later, only after checks, source review/seal and host access preflight:
python3 -B build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/activate.py \
  < build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/activation_input.json
python3 -B build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/record_readiness.py \
  < build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/readiness_input.json
timeout 210s python3 -B build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/qualify_snapshot.py

# Promptly record the operator's actual observation; never fabricate its UTC:
python3 -B build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/record_operator.py \
  < build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/operator_input.json
```

Bind raw owner reply "Authorized 3 tries, ready and powered." and receipt UTC
in `owner_authorization_received_01.json`. Interpret this as authorization for
the proposed snapshot qualification, including at most one necessary GCAPTURE
per attempt. It does not authorize UART, reload, FPGA reset or runtime decoding.
Preserve the short readiness statement; it omits a current image report and
does not remain fresh while preparation continues. Do not reopen prior budgets.

Freeze three new physical attempts, 270 seconds each, 810 seconds cumulative,
external subprocess 210 seconds and native USB activity 180 seconds. Retain
these prior time caps conservatively; the owner did not separately restate the
numeric caps. Each launched attempt consumes one slot and reserves 270 seconds
regardless of terminal result. Host checks and offline repair consume no slot.
The offline check has one 600-second job; no timeout extension or blind relaunch.
After LAUNCHED record unit/evidence and end the turn under AGENTS.md §4.2.

Freeze each attempt's sequence in `draft_01/plan.json`: target ID/IR/STAT/CTL0/
COR0 checks, static A→B→B→A, one GCAPTURE, all 48 capture FARs once, static
A→B→B→A, then final STAT/IR. A=0x217A1, B=0x217A2. Total 56 addressed reads;
every read requires a passing CMD checkpoint before FAR/FDRO. Keep 32-bit FDRO
chunks and exact 202-word extent. Reject the first command/transport/status/
extent/control mismatch; no subsequent request or rejected-frame reread.
DESYNC at the end of a completed frame transaction precedes static validation.
No recovery command after a rejected candidate, and no runtime interpretation.

Copy the qualified amended static workers; extend small helpers in `draft_01/`.
Filter repaired controls to all 48 capture FARs and add predecessor A/B controls:
3092 controls across exactly 50 read FARs. Preserve repaired runtime mapping,
1667 bits, polarity and the old sources. Require complete plan/guard/source
validation before native access. Retain identity pins and 1 MHz request; actual
TCK and loaded adapter firmware remain unmeasured. Read COR0 without modifying
it; reject single-shot bit 23 set or reserved startup-clock value 3. Never send
RCAP, GRESTORE, JSHUTDOWN or configuration clock/security writes. Normal TAP
protocol reset is allowed; FPGA reset/power cycle is outside scope.

Validate full 56-read TAP model, 32/64 receive equivalence and one-capture limit;
inject failures before/within/after capture, uniform zero/one data, truncated
CMD/FDRO, all 3092 selected-bit mutations, extent/coverage/plan defects and
unsupported COR0 settings. Require first-failure stop, exact accounting,
cleanup, activation refusal, checked correction before retry and closure after
PASS. Bind before readiness to campaign, next attempt, phase before-snapshot,
timezone-aware observed_utc, receipt UTC, powered/unchanged setup, stable lock
and current image. Reject receipt more than 60 seconds after observation;
launch must be within 300 seconds of observation. Preserve each readiness input.
Bind post-report to phase after-snapshot, campaign and actual attempt. Require
both observation and receipt within 60 seconds of measurement completion and
before the attempt's 270-second deadline. Preserve late reports as context only.

Keep manifest DRAFT_NOT_RELEASED/execution false until exactly one COMPLETE
terminal marker, focused_checks PASS, independent source review and runtime
seal. The supplied input files for later activation/readiness/operator commands
must contain reviewed real approvals/observations; they are not placeholder
permission to execute. Confirm actual native adapter access before physical
reservation. Seal all used helpers/data and provenance; archive executed
sources and raw USB replies separately for each attempt.

Classify a full pass CAPTURE_FRAME_SET_STATIC_CONTROLS_MATCH with snapshot
validity STATIC_CONTROLS_QUALIFIED_RUNTIME_FRESHNESS_UNESTABLISHED. Static
controls qualify these frame reads only. Capture freshness, coherent operands,
polarity, display noninterference and GPU cause remain NOT_ESTABLISHED. Reject
the entire snapshot on failure; prior partial bank/depth leads remain unconfirmed.
After failure diagnose and validate a specific correction before another slot;
preserve its evidence. After PASS close the campaign without repeating; after
three attempts stop. Changes to wiring, RTL, bitstream identity, scope or
acceptance criteria require a separate owner decision.

## 8. Completed offline release review

Read `offline_check_01/{COMPLETE,result.json,exit_status,stdout.log,stderr.log}`:
exactly one terminal marker COMPLETE, exit 0, 182 seconds within the frozen
600-second cap. Full suite records 3415 checks PASS, native USB opened false,
zero physical attempts, 56 modeled frame reads, one capture and exact 32/64
TMS/TDI trace agreement across 476280 clocks. Do not infer physical timing.

Verify all preparation/provenance hashes unchanged. Record
`draft_01/{source_review_01.json,release_review_01.json,runtime_hashes.json}`;
seal 23 helpers, five fixed data/result inputs and the frozen disk bitstream.
Host adapter open/claim/release/close preflight completes without bulk commands
or TAP clocks. Activate using the retained owner approval; manifest ACTIVE_READY,
zero slots used/three available, 810 seconds unreserved. Activation authorizes
no launch without fresh bound readiness. No current monitor observation exists
for this attempt yet. Earlier readiness has expired; request setup/image status
under §7 before physical execution. Do not ask again for the approved budget.

Offline model PASS does not qualify physical snapshots, capture freshness,
runtime operands or the GPU. Preserve all prior invalid captures and missing
operator reports without promoting their bank/depth leads to established faults.

## 9. Attempt 1 failed before capture; preserve the rejection

```bash
# Read-only retained evidence; no hardware access or retry:
cat build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/attempt_01/result.json
cat build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/attempt_01/diagnosis_refinement_02.json
cat build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/attempt_01/raw_ir_replay_check.json
```

Bind owner reply "Ready," contextually to the preceding setup/image question;
record that the full powered/unchanged/lock/image statement was inferred from
the affirmative response, not separately enumerated. Readiness recorded at
2026-10-06T02:03:45.728046Z. Attempt 1 runs 02:04:07.244077Z–02:04:23.002155Z,
15.76 seconds, FAILED/exit 1. Reserve one slot/270 seconds; leave two slots and
540 seconds available. Preserve manifest AWAITING_REVIEW/execution false.

Four CMD checkpoints return 0x4. First three A/B/B static transactions pass.
Fourth A transaction returns all 202 words, then the CFG_IN scan for DESYNC
returns 0x3f, violating mandatory IR low bits 01. DESYNC is not transmitted;
normal fourth-frame validation does not complete. Reconstruct those 202 words
from the journal for forensic triage only; 54 of 128 A controls disagree and
80 of 128 B controls disagree. The fourth return is neither qualified A nor B.
No global bit offset in [-64,64] satisfies all A controls. Preserve this failed
static transaction without any captured-runtime interpretation.

Raw native five-bit reply f8 plus final GETSIG 08 decodes to six ones/0x3f;
prior same outgoing IR scan packets decode to 0x35. Four focused offline replay
checks pass and confirm rejection before interpreting startup flags. USB bulk
errors zero, interface release/close/exit complete, all 29 executed archives
match the seal. Adapter execution, clock/signal delivery, TDO sampling and target
TAP causes remain open. Generic DJTAG2 INFO does not identify loaded firmware;
local candidate firmware source inspection cannot establish its live identity.

No GCAPTURE was attempted, no UART/reload/FPGA reset sent. Post-report "Stable
lock; same image; no intervention — observed now" is recorded at 02:05:59.383211Z,
after the 02:05:23.002155Z deadline. Preserve LATE_OBSERVATION_ONLY; operator
gate false. No earlier precise observation/receipt time was supplied. The report
does not repair rejected readback or establish causal noninterference.

Preserve the failed initial transaction-slicing assertion; it wrote no diagnosis.
`diagnosis_refinement_02.json` corrects the earlier analysis file's inferred
failure position: rejection occurs after fourth FDRO receive, before DESYNC,
not before FAR/FDRO. Keep both historical files. Require a diagnosed, focused-
checked correction before retry; do not relax guards or blindly repeat the same
procedure. This failure does not establish a GPU bank/depth or UART fault.

## 10. Authorized prospective transport correction; retain two slots

```bash
# Completed focused check evidence; read only:
cat build/gpu_evaluation/t1d_snapshot_qualification_20261006/transport_repair_01/transport_focused_checks_01.json

# One additional deterministic repair check, 600 seconds; no native adapter:
tools/run_detached_job.sh \
  --output build/gpu_evaluation/t1d_snapshot_qualification_20261006/transport_repair_offline_check_01 \
  --timeout 600 --notify-desktop -- \
  python3 -B build/gpu_evaluation/t1d_snapshot_qualification_20261006/transport_repair_01/check_snapshot.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/hardware_evidence.md spu_strategy/contract_gpu_t1d_snapshot_qualification_2026-10-06.md
```

Record latest owner reply "Authorized." prospectively in
`owner_authorization_received_03.json`. Interpret it as approval to prepare and
validate the proposed host correction, including one new offline repair job
capped at 600 seconds. No physical budget increase or longer time limit is
inferred. Keep the same campaign and failed attempt 1, one slot consumed/two
remaining; active manifest AWAITING_REVIEW/execution false. Do not activate the
preparation bundle, copy campaign counters or ask again for the existing budget.

Copy checked helpers/data to `transport_repair_01/`. Change only host scan
packet splitting and journal sync scheduling; preserve pins, 1 MHz request,
logical TMS/TDI sequence, clock counts, 56-read plan, 48 capture FARs, 3092
static controls, CMD/IR/status rejection criteria, one-capture limit, native
180/external 210/attempt 270/cumulative 810-second bounds. No FPGA/adapter
firmware change, clock/security register write, UART, reload or wiring action.

The failed path depends on partial-byte bulk transfers, including five IR bits
and 31 bits before the final explicit scan-exit clock. Change `Wire.shift` to
bulk-transfer only multiples of eight bits and use existing per-clock SETSIG/
GETSIG commands for the remainder and exit bit. Preserve exact bit order and
the same logical rising edges. This removes partial-byte bulk handling from
the host path; it does not prove that handling caused the physical failure.
Physical waveform/timing and actual loaded adapter executable remain unknown.

Flush every journal record to the OS. Sync outgoing command intent before the
native write, every incoming raw result before returning to the decoder, halt,
capture intent/completion and frame candidates; sync all remaining records on
close. Derived decoded records are covered by the next durable boundary.
Preserve all raw replies and the first-failure stop. Do not promise performance
from this change; the physical limits are unchanged. Old per-record syncs added
host overhead but are not established as the cause of corruption.

390 focused checks PASS without native access: all widths 2..64, with and
without scan exit, compare old/new data, exact TMS/TDI traces and clocks. Full
56-read snapshots agree under the bit model, and every new bulk shift is byte
aligned. A deliberately injected bad partial-byte return trips the old guard;
the new path does not invoke that injected branch. This fixture is synthetic,
not evidence about actual firmware or electrical behavior. Journal fixtures
verify intent precedes native write, raw result is synced before decode,
derived records avoid redundant sync and capture/candidate/halt/close remain
durable. Record `transport_focused_checks_01.json`; full amended suite pending.

After LAUNCHED record unit/evidence and end the turn. Later accept only exactly
one COMPLETE/exit 0 marker with full focused PASS, unchanged frozen inputs and
reviewed correction evidence. Preserve active worker/seal in a separate archive
before promoting tested helpers; leave attempt 1 archives untouched. Seal the
amended runtime set and use the retained reviewer to release the next existing
slot with a specific correction record. This is qualification of a corrected
measurement method, not a claim that the physical cause is repaired. Require
fresh setup/image readiness after release and confirm native adapter access
before attempt 2. No retry or physical command is released by preparation.

## 11. Completed transaction audit and amended release

```bash
# Audit completed once; read retained result, do not overwrite:
cat build/gpu_evaluation/t1d_snapshot_qualification_20261006/transaction_audit_01/result.json
cat build/gpu_evaluation/t1d_snapshot_qualification_20261006/transport_repair_offline_check_01/result.json
cat build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/transport_amendment_release_01.json
```

Independent command decoding audits 2533 native transfers and 1266 paired
replies. Expected byte counts match actual native lengths; no incomplete call,
unbound reply, overlap or decoder-to-reply mismatch is found. Five checks PASS,
including short/missing/duplicate reply rejection. Last successful B frame and
failed A frame have identical outgoing prefixes except the intended FAR word;
the failed prefix has 292 packets, good transaction 299 because failure stops
before closing DESYNC words. Equal-length stale/incorrect data inside the
adapter or FPGA cannot be excluded; host logs lack transaction IDs on replies.
This audit qualifies logged host pairing, not physical response freshness.

Exactly one COMPLETE/exit 0 marker is present for transport repair validation,
2026-10-06T02:18:27Z–02:19:23Z, 56 seconds within 600. Full suite records
3806 checks PASS, no native USB and no physical slot. Preserve all preparation
hashes and original active worker/seal under `draft_01/before_transport_repair_01/`;
leave attempt 1's executed archives untouched. Promote tested helpers/data and
seal 30 inputs. Retained reviewer releases the existing next slot at
02:22:52.211139Z: REVIEWED_NEXT_ATTEMPT/execution true, one used/two remaining,
270 of 810 seconds reserved. Cause and operator gate remain unestablished.

Native host access check 02 completes at 02:23:53.101587Z without bulk JTAG
commands or TAP clocks. Attempt 2 must use this amended path at the unchanged
1 MHz request and all prior physical caps/guards. Require fresh attempt-bound
setup/image readiness under §7 before launch. Do not treat the earlier readiness
or latest authorization as a fresh board/display observation.

## 12. Conditional lower-clock comparison within final existing slot

```bash
# Candidate is prepared, not active or permitted for physical execution:
cat build/gpu_evaluation/t1d_snapshot_qualification_20261006/lower_clock_candidate_01/focused_checks.json
```

Latest owner authorization covers the transaction audit and a conditional
bounded lower-clock comparison. Retain its wording/context in receipt 04.
Freeze candidate request 100 kHz, compared with attempt 2's 1 MHz request,
under the same amended helper method. Do not compare clock causality against
attempt 1's different packet/sync method. Actual TCK remains UNMEASURED.
No new slot or timeout is authorized; reserve only existing final attempt 3
if attempt 2 fails and review identifies timing comparison as relevant to an
invalid IR/static-return signature. Permission/access failure, unsupported
configuration or time exhaustion alone does not justify this substitution.

Candidate `dirty_protocol.py` changes only the frequency command to
`02 00 64 00` and request log to 100000 Hz. Seven offline checks PASS: returned
modeled data, exact TMS/TDI and 476280 clocks match the 1 MHz baseline; only
one outgoing packet differs (`02 03 e8 00` versus `02 00 64 00`). Pin both
source hashes. Preserve the initial formatter error; it wrote no success file
and the corrected model probe is recorded separately in focused evidence.

Keep the candidate outside the active runtime set. Before conditional use,
review attempt 2's raw evidence, confirm frozen inputs and gates remain relevant,
preserve its executed sources and baseline helper, seal the selected candidate
prospectively, record explicit correction/comparison review and obtain fresh
readiness. Keep 56 reads/48 capture FARs, static rejection, one-capture cap,
native 180/external 210/attempt 270/cumulative 810 seconds unchanged.
Stop on first contradiction and after PASS; after final slot close/report.
A single lower-requested-clock PASS does not establish timing causality or
actual physical clock reduction, runtime freshness, GPU cause or acceptance.

## 13. Attempt 2 pass and closeout

```bash
# Retained qualification record and promptly recorded monitor report:
cat build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/attempt_02/managed_terminal.json
cat build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/attempt_02/operator_after_read.json
cat build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/attempt_02/review.json
```

Attempt 2 COMPLETE/exit 0 at 02:27:25.403349Z after 58.69 seconds under
external/native/attempt limits. All 56 addressed frames have 56 passing CMD
checkpoints; four static ABBA reads before and after, 48 captured reads and the
single GCAPTURE complete. All 3092 declared controls match. All 30 executed
inputs match their seal. No UART, new bitstream load or FPGA reset. Classify
CAPTURE_FRAME_SET_STATIC_CONTROLS_MATCH and
STATIC_CONTROLS_QUALIFIED_RUNTIME_FRESHNESS_UNESTABLISHED.

Owner report "Stable lock; same image; no intervention — observed now" is
recorded 02:28:06.793223Z, within 60 seconds. Operator phase gate passes for
that reported observation. Preserve its exact scope: it does not prove causal
probe noninterference or validate captured runtime operands.

Close after PASS: two attempts used/540 seconds reserved of 810, one remaining
slot closed unused. Do not execute the prepared 100 kHz candidate; its condition
was an attempt 2 failure with a relevant IR/static-return signature. Do not
decode bank/depth/runtime fields or infer GPU cause from the passing static
controls. A separate review must qualify capture freshness and coherent runtime
operand association before interpreting captured GPU state.

Evidence: `build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/attempt_02/`
`{result.json,managed_terminal.json,transport.jsonl,executed_sources/,
operator_readiness.json,operator_after_read.json,review.json}`. Journal SHA-256:
`c07aa5b5b87232d72cde8bda037ff6b3360cde9f55f73c42c02fc954cd0c5aa0`.
Manifest state SNAPSHOT_STATIC_CONTROLS_QUALIFIED, execution false, slots used 2,
remaining 1 closed. Previous attempt 1 stays FAILED and fully preserved.
