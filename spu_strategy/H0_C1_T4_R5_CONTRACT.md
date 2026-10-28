# H0-C1-T4-R5 — Isolated FPGA transaction-controller prototype contract

**Disposition: REVISED FOR INDEPENDENT RE-REVIEW (R5).** Documentation repair of R4 only; R1 to R4 are preserved unchanged. It does not authorize implementation or simulation. Isolated RTL prototype, production H0-C1 and H0 ratification remain HOLD. The prescribed implementation, if separately authorized after re-review, is an isolated Verilog or SystemVerilog controller with fake engine, fake configuration sink and host testbench; it is not host software or the Artix-7 image.

**Basis and identity:** R4 contract and traces preserved unchanged as `spu_strategy/H0_C1_T4_R4_CONTRACT.md` and `spu_strategy/H0_C1_T4_R4_FROZEN_TRACES.md`; R3 contract and traces preserved unchanged as `spu_strategy/H0_C1_T4_R3_CONTRACT.md` and `spu_strategy/H0_C1_T4_R3_FROZEN_TRACES.md`; R2 contract and traces preserved unchanged as `spu_strategy/H0_C1_T4_R2_CONTRACT.md` and `spu_strategy/H0_C1_T4_R2_FROZEN_TRACES.md`; R1 contract and traces preserved unchanged as `spu_strategy/H0_C1_T4_R1_CONTRACT.md` and `spu_strategy/H0_C1_T4_R1_FROZEN_TRACES.md` (hashes in `spu_strategy/H0_C1_T4_R2_MANIFEST.txt` and `spu_strategy/H0_C1_T4_R3_MANIFEST.txt` and `spu_strategy/H0_C1_T4_R4_MANIFEST.txt` and `spu_strategy/H0_C1_T4_R5_MANIFEST.txt`); T1/T2 `6556d22422549cac6848494dd640d1c224fc124a`; source baseline `2a9a9f12760bb13fb47bcf192b66f44645f35ef9`; committed NUM-SOM-4 Phase B baseline `71c8a5a46ce920f46b6e4185c21b84ba1c610fb5` ("bounded numerical-domain guard and internal refusal", committed on `dev/next`; its regression status was not re-run for this document). Phase B code being committed does not close the H0 ratification HOLD, which concerns the transaction interface and is unaffected. T3 is uncommitted. The companion `spu_strategy/H0_C1_T4_R5_FROZEN_TRACES.md` is normative for this synthetic experiment. No repository file other than these R2 to R5 documents is changed.

## 0. Four mechanisms kept distinct

| Mechanism | Owner | Status in this experiment |
|---|---|---|
| Synthetic epoch attribution | harness tags E on fake events | Assumption: tags are truthful and unreused. Not a hardware reset detector. |
| Hardware reset observability | none here | HOLD; unmodelled. |
| Controller-side authorization invalidation | controller | Under test: it must stop granting commits for invalidated or cancelled work. |
| Sink/engine-side effect cancellation | fake sink/engine | Obligation on the fakes (they commit only on a matching grant). Whether a real sink or engine can do this is unverified. |

## 1. Scope and edge convention

One clock and one authorized test host; all inputs are stable before the rising edge; each trace row is the input at an edge and the required state after it. Synthetic reset is synchronous. There is no SPI framing, real core, ISA decode, physical reset, A31 arithmetic, FPGA build, timing claim or production-width choice. The controller owns admission, interlock, record publication and authorization; the fake engine and fake sink own their storage and MUST obey the commit gates below. The harness owns reset, stimulus, expected traces, test-only epoch tags and the observation counters. The controller does not itself execute engine or sink writes.

**No implicit schedule.** Every engine and sink event is listed explicitly in each trace row. The `t+2`/`t+3` pattern (OK: commit intent `t+2`, terminal `t+3`; DELAY: terminal `t+2`, commit intent `t+5`; REFUSE: terminal `t+3`, for issue acknowledgement at edge `t`) is only how S1, S2, R1, X1 and X5 were written; an event absent from a row does not occur.

Synthetic status: lifecycle `CONFIG` or `READY`; progress `p=0,1,2`; STAGED bit `s`; active transaction identity or NONE (`P`); transaction record `(gen,id,state,outcome,result_valid,payload)`; rejection record `(gen,kind)`; configuration-ack record `(gen,kind)`; separate unread (`uT,uR,uA`) and sticky overrun (`oT,oR,oA`) bits; sticky protocol fault `F`; fake storage `(pair,single)`; and harness-observed counters, never cleared by reset: `e` (engine effects), `sw` (granted sink mutations: stage write, pair write, single write), `acc` (acceptances), `iss` (engine issues), `rej` (rejection records), `cmp` (transaction completions published). `—` denotes absent/invalid; a prior payload may physically remain but `result_valid=0` makes it historical. At reset records are NONE, generations and serials zero, unread/overrun false, F=0, lifecycle CONFIG, p=s=0, no active work; committed fake storage, `e` and `sw` are unchanged. A successful new transaction replaces its record at acceptance and retains the same generation through completion.

## 2. Two effect owners, commit/cancel boundary, fault rules

Each fake engine or sink request is PENDING only after one acceptance acknowledgement by that fake unit. PENDING has a stable identity and payload and has not mutated committed storage. The fake unit may offer a commit intent on a later edge; it mutates storage once, atomically with a controller grant for that same still-authorized pending identity. That edge is COMMITTED and is not rolled back by later invalidation or reset; it cannot count toward a new configuration sequence until freshly re-established and acknowledged. An invalidated pending operation becomes CANCELLED; neither its later intent nor its later ack may mutate storage or advance records.

At one edge the priority is: (1) reset cancels pending work, rejects all same-edge commits and invalidates records/configuration, with reset-edge events cancelled **without** fault; (2) otherwise a failed configuration submission invalidates configuration and cancels pending sink work, so a same-edge commit intent for that work gets no grant and **no fault**; (3) otherwise valid owned events and commits are processed; (4) new acceptance is determined from pre-edge READY/busy and an independent rejection may be recorded; (5) snapshots capture pre-edge state. Existing operation completion plus a new instruction sees pre-edge busy and yields a BUSY rejection while completion proceeds.

**Separate lifetimes.** An engine transaction has two independent lifetimes. (i) The *effect* is PENDING from issue acknowledgement until its commit grant, then COMMITTED; an effect intent is matched only against a pending effect. (ii) The *transaction* is ACTIVE from acceptance until its COMPLETE record is published; a terminal is matched only against an ACTIVE transaction that has not yet received a terminal. Commit-first (S1) and terminal-first (S2) are both normal: after the commit grant the transaction remains ACTIVE awaiting its terminal, and a terminal received before the commit is retained while the effect stays pending. Publication of SUCCESS occurs when both the terminal and the effect commit have happened; a REFUSED completion requires no effect and is published at its terminal, and UNSUPPORTED is published at acceptance. A sink operation has only the pending lifetime above (PENDING to COMMITTED or CANCELLED).

**Fault rules (F sticky until reset; F=1 never changes committed storage or counters by itself).** F is set by: (a) a duplicate engine commit intent for an effect already COMMITTED; (b) any engine effect intent or sink commit intent/ack with no matching *pending* identity, an old epoch tag or an inactive/old id, on an edge that is not a reset edge and not the cancelling edge; this includes a stale sink commit after a failed-submission cancellation, and one after a reset and fresh LOW; (c) a terminal with no matching ACTIVE-and-terminal-less transaction (duplicate terminal after completion, old epoch, inactive or old id); (d) a held-valid request whose kind or payload changes without a sampled low; (e) a **contradictory terminal**: REFUSED with payload_valid=1, or SUCCESS with payload_valid=0. A contradictory terminal is discarded: the record stays EXECUTING, nothing is published, no storage changes. A faulting event itself has no effect and does not cancel or alter other pending work. While F=1 the controller (1) ignores new instruction and configuration requests (no acceptance, rejection record, issue, or sink pending) and (2) **freezes existing work**: it issues no commit grant and publishes no record update, including for previously valid pending or active work, until reset. Frozen work is not completed, cancelled-and-reported or rolled back; recovery is known reset. **F observability:** F is a harness probe signal only; it is not part of any host snapshot and the traces assert it as a testbench observation. The synthetic host sees a fault only as silence (no record update, no acknowledgement), and its required response is timeout, then UNKNOWN, then known reset. This is a prototype choice and does not establish a production status interface. Ignored requests are not host-visible outcomes.

Fake engine storage is the monotonic effect counter `e`; commit needs a matching pending transaction and a grant and increments exactly once. A `terminal` never has a grant and never changes storage. Fake sink commit needs a matching pending LOW/HIGH/SINGLE stage identity and a grant.

These are prototype semantics, not claims about a real engine or sink.

## 3. Configuration

Synthetic manifest is exactly LOW=`12`, HIGH=`34`, SINGLE=`56` in that order (hex). LOW acceptance creates a PENDING sink stage; a granted commit stores stage `(attempt,12)` and produces one STAGED record with p=0,s=1 (`sw` +1). HIGH acceptance requires that stage; its granted commit atomically writes fake pair `1234`, clears the stage, produces COMMITTED and sets p=1 (`sw` +1). SINGLE granted commit writes `56`, produces COMMITTED, sets p=2, READY (`sw` +1). Acceptance alone is not an acknowledgement and does not change `sw`.

Once any submission fails, the controller records a rejection with its kind (`BAD_FRAME`, `WRONG_ORDER`, `WRONG_VALUE`, `WRONG_TARGET`, `DUPLICATE`), cancels pending sink work and invalidates authorization, s and progress; the entire manifest is replayed. An already committed pair/single remains but cannot satisfy the new attempt. An interrupted status read is not a submission and does not invalidate configuration.

**Defined exception, tested by C2:** a *failed* configuration submission (any kind) while a sink operation is PENDING cancels that pending operation and invalidates configuration; a same-edge commit intent for it gets no grant and no fault. C2 exercises the bad-frame kind only.

**Not claimed (removed from acceptance):** a configuration submission that is *not* failed (i.e. otherwise valid) while a sink operation is pending; a configuration submission while an instruction is active; and a configuration submission while lifecycle is READY. These semantics are undefined and no trace exercises them.

## 4. Transaction and request events

`I(kind)` is a valid assertion with immutable kind and payload while high; one assertion is one request and a new request requires a sampled low edge. Repeated identical high is ignored, not replayed. A changed kind/payload while valid remains high is a violation (rule 2(d)): F=1, no new accept/reject/issue.

At admission, CONFIG yields NOT_READY before BUSY is considered. READY with an active transaction yields BUSY. Accepted UNSUPPORTED records one terminal UNSUPPORTED immediately, with no engine issue/effect/payload. Accepted `OK`, `DELAY`, `REFUSE` are issued once to the fake engine and remain active until completion. No SUCCESS publication before both a matching commit and a terminal, in either order. REFUSED/UNSUPPORTED publish no fresh result or effect.

The harness injects stale/duplicate *intent* and stale/duplicate *terminal* in separate cases (each ending in reset), so each defect has its own detection point.

## 5. Epoch, identity, record freshness

The trusted harness provides an 8-bit epoch token E, starting at 1 and changing to an unused value after each known synthetic reset; every fake event is tagged with its issue-time E. At most 200 resets per experiment. Controller decisions are correct only given faithful, unreused tags and the units' commit-gate obligations. An old event mislabeled with the exact current `(E,txid)` is observationally indistinguishable from a valid one; the controller is NOT required to detect it (trace L1 documents this assumption limit and is not stale-rejection coverage).

The controller allocates a synthetic 8-bit transaction id monotonically from 1 per epoch, at most 200 admissions per epoch. Configuration request and attempt ids follow the same bounded rule. Within one epoch an old id never matches a new request. These are test-only tags, not production widths.

Transaction, rejection and configuration-ack records each use independent 2-bit generations, initially 0, incremented modulo 4 at creation of each record (first event gen 1). Completion updates the accepted transaction record without incrementing its generation or its serial. A record event creates an unread record; a replacement while unread sets that channel's sticky overrun. Transaction acceptance makes EXECUTING unread; terminal update of the same identity is not a replacement. A second transaction acceptance after a completed unacknowledged one sets `oT`. The prototype continues recording rejections while `oR` is set (synthetic diagnostics, not host permission). Overrun forces the host to treat the result as UNKNOWN and recover; ordinary ack cannot clear it. Reset clears all.

A snapshot captures pre-edge state and mints one fresh one-shot capability `cap` per channel (synthetic monotonic 16-bit, fewer than 200 per epoch); each channel has its own serial (distinct 16-bit replacement number, at most 200 per channel per epoch). A later record replacement on a channel invalidates that channel's captured caps, even if the 2-bit generation wraps to the same value. A transaction terminal update likewise invalidates caps that captured its EXECUTING state. `ACK(channel,cap)` clears unread only if the cap is valid for that channel, the current serial still matches, no overrun is set, and for transactions the record is terminal; otherwise it is inert (**an inert ack does not set F and does not consume the cap**). Snapshot interruption invalidates its response/caps and changes no other state; an interruption on the same edge as an ack makes that ack inert. Simultaneous snapshot/record update captures pre-edge values and the replacement invalidates the just-captured cap for the updated channel.

Traces never hold more than two unconsumed caps per channel; behavior beyond two (eviction) is **not claimed**. Re-use of a consumed cap is not independently observable (any later record changes the serial), and is **not claimed**. Stale-cap behavior across a 2-bit wrap is verified on the rejection channel (X9) and by terminal-update invalidation on the transaction channel (X1); the config-ack channel's wrap behavior is **not claimed**. Any overrun, ambiguous observation or timeout requires known-reset recovery.

## 6. Verification and negative controls

The companion traces define all inputs and every required selected state after each edge from explicit initial state; omitted events are absent. Fixtures Z and Q are loaded by the harness, not produced by the design under test. The companion file is the independent expectation source, written before any controller. Verify full specified state, storage, grants and counters at every row; undefined historical payload bits are not compared. Each intentional violation lists expected F and its reset clearing.

**Acceptance-invariant coverage (each invariant has a discriminating test; mutation IDs are in the traces):**

| Invariant | Cases | Mutations |
|---|---|---|
| STAGED is not COMMITTED/READY | C1 | M01 |
| Failed submission invalidates, forces replay (all five kinds) | C2, C5a–d | M02, M29–M32 |
| Interrupted read is not a failed write | C3 | M05 |
| Sink cancellation / no stale or unauthorized write | C2, C4, X4 | M03, M04, M13 |
| Commit gates publication (either order); terminal after commit is not a fault | S1, S2 | M06, M35 |
| Refusal carries no historical payload; UNSUPPORTED not issued; NOT_READY | R1, U1, N1 | M07, M33, M34 |
| Busy coincident with completion | X1 | M08 |
| Duplicate effect and duplicate terminal detected independently | X2a, X2b | M09, M10 |
| Cancelled work cannot act after reset (effect, terminal separately) | X3a, X3b | M11, M12, M14 |
| Contradictory terminal is a fault | X10a, X10b | M27, M28 |
| Overrun per channel (R, T, A) | X6, X16, C6 | M15, M16, M22, M23 |
| Capability invalidation and serial vs wrap (T channel: X1; R channel: X9) | X1, X9, X8 | M17, M18, M36, M21 |
| Ack of EXECUTING is inert | X11 | M24 |
| F blocks new requests and freezes existing engine and sink work | X12, C2, C7 | M25, M26, M37, M38 |
| Held valid not replayed; payload change faults | X7, X7b | M19, M20 |
| Generation wrap with serialized host (per-block cumulative counters frozen) | X5 | — (positive) |
| Assumption limit (mistagged event) | L1 | none, by design |

**Mutation rule.** Each negative control is one deliberately defective variant that compiles, runs the same traces, and MUST fail the single assertion named for it at the named edge; timeout, compile failure or an unrelated/earlier assertion is not detection. Assertions are falsifiable: each names observable signals or counters that differ between the correct and mutated design. Report assertion hit counts and require each named stimulus to occur. In addition an independent runner control produces the exact expected transcript but a nonzero exit; the outer runner must fail. Normal suite PASS requires every trace, all designated mutations detected, the runner control detected, nonzero/error statuses handled, and trace/tool/source identity recorded. A finite PASS makes no claim beyond these synthetic assumptions.

## 7. R1 finding disposition (R2 review)

1. X2/X3 combined injections: split into X2a/X2b and X3a/X3b; separate mutations M09–M12.
2. C4 vacuous storage check: `sw` counter; C4 edge 10 asserts `grant==0 && sw==3`.
3. X7 replay assertion: asserts `rej==0 && acc==1 && iss==1` at edge 2.
4. X7 prose variant: literal X7b.
5. Default-event collisions: no implicit schedule (§1).
6. Untested obligations: traces added (C5a–d, C6, X10a/b, X11, X12, X16, X1 ack of stale caps) or removed from claims (§3, §5).
7. Contradictory terminal payload: restored (§2(e), X10).
8. Stale sink intent after non-reset cancellation sets F: explicit in §2(b).
9. X6 recording after overrun: frozen as "continues" (§5, M16).
10. Fixture Q: loaded directly; C1's final state is cross-checked equal to Q but does not produce it.

## 7c. R4 review disposition (R5)

M36 moved to X9 edge 17, where the stale capability was captured from an existing unread rejection (R1), which was then replaced. The mutant bypasses exactly: explicit capability invalidation, the serial match and the generation comparison; it keeps only "capability exists and record unread". The earlier X1 placement could not isolate those checks, because an independent "snapshot held no rejection" check would also keep `uR` set. X1 edge 6 `ackR(4)` remains as a consistency check and is not a mutation point for the rejection channel.

## 7b. R3 review disposition (R4)

1. M36 redefined as removal of the complete rejection stale-ack protection (explicit invalidation and serial match). Removing only the explicit invalidation on the rejection channel is an equivalent mutant, because the serial check still rejects, and is not claimed. M18 stays discriminating: a terminal update leaves the transaction serial unchanged, so only explicit invalidation protects the transaction channel.
2. SUCCESS publication wording scoped (§2).
3. F is a harness probe; host-visible behavior is timeout, UNKNOWN, reset (§2).

## 7a. R2 review disposition (R3)

1. Effect/transaction lifetimes separated and fault rules reclassified (§2).
2. X5 counter substitutions frozen per block.
3. C2 pending-sink cancellation is a defined exception (§3); non-failed submissions while pending stay unclaimed.
4. F freezes existing work (§2); tested by X12 edge 6 (engine) and C7 (sink); M37, M38.
5. X7 heading corrected; M18 split into M18 (transaction caps) and M36 (rejection caps).

## 8. Remaining assumptions and holds

Truthful unreused epoch tags; fake units obey the gates; real SPI CDC and timing, physical reset observability, H0 canonical masks, production generation/identity widths, real SET-N/SET-R configuration, A31 refusal, source QR commit timing, protected-path inventory, actual FPGA resources, and all items listed as "not claimed" in §3 and §5 remain HOLD or unclaimed. No production feature or ISA semantics is introduced.
