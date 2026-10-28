# H0-C1-T4-R3 — Frozen independent expected traces

**Disposition: REVISED FOR INDEPENDENT RE-REVIEW (R3)**, not an implementation or simulation authorization. Companion: `spu_strategy/H0_C1_T4_R3_CONTRACT.md`. These manually specified traces were not generated from a controller or simulator. All scenarios are finite and synthetic. Production H0-C1 and the isolated RTL prototype remain HOLD.

## Notation and fixtures

Each row `edge: inputs -> expected` gives all changed state; everything not mentioned is unchanged; every absent input/event is low and **no engine or sink event occurs unless listed**. Generations are modulo four. `Tg/id/state/outcome/v/payload`, `Rg/kind`, `Ag/kind` are the transaction, rejection and config-ack records; `P` is the active pending id. `uT,uR,uA` unread, `oT,oR,oA` overrun, `F` fault, `e` effect counter, `pair,single` fake sink storage, `s,p,L` staged flag, progress, lifecycle. Counters `sw,acc,iss,rej,cmp` are defined in the contract §1 and are never cleared by reset; a row mentions only counters it asserts. `grant=0/1` is the controller's commit grant for an intent on that edge. `ackT(c)`, `ackR(c)`, `ackA(c)` acknowledge that channel with capability c; `sn(c)` snapshots pre-edge state, minting cap c for each channel; `intr(c)` interrupts that snapshot. `low` means request-valid sampled low. `sched` rows list engine events by name: `issue(id)`, `effect(id,E)`, `terminal(id,outcome,payload,E)`; sink events `stage(id)`, `paircommit(id)`, `singlecommit(id)` with optional `E`. Omitted `E` means the current epoch.

**Fixture Z (harness-loaded):** E=1, L=CONFIG, p=s=0, P=NONE, T=R=A=NONE, all generations and serials 0, all unread/overrun 0, F=0, pair=0000, single=00, e=0, sw=0, acc=iss=rej=cmp=0, no request, no capability; ids from 1; first config attempt 1.

**Fixture Q (harness-loaded, not produced by the design under test):** E=1, L=READY, p=2, s=0, P=NONE, T=NONE, R=NONE, A=3/COMMITTED, uT=uR=uA=0, oT=oR=oA=0, F=0, pair=1234, single=56, e=0, sw=3, acc=iss=rej=cmp=0; transaction and rejection generations and serials 0; cfg-ack generation and serial 3; no request or capability; next transaction id 1; next snapshot capability 4. Consistency check on the C1 trace: its final row equals Q. Rows of Q-based cases are numbered from 1 and each case begins from a fresh load of Q.

## Configuration cases (start at Z)

### N1 — not ready
1: `I(OK)` -> acc=0,iss=0, R1/NOT_READY, uR=1, rej=1, L=CONFIG, e=0, F=0.
2: `low,sn(1)` -> cap1 captures R1/NOT_READY, uR=1.
3: `ackR(1)` -> uR=0. Assert rej=1 and zero grants.

### C1 — staged versus committed configuration
1: `C(LOW,12,id1)` -> sink PENDING id1, no ack, L=CONFIG, p=0, s=0, sw=0.
2: `stage(id1)` -> grant=1; stage=(attempt1,12), A1/STAGED, uA=1, p=0, s=1, pair=0000, L=CONFIG, sw=1.
3: `low,sn(1)` -> cap1 captures A1/STAGED, p0, s1.
4: `ackA(1)` -> uA=0.
5: `C(HIGH,34,id2)` -> sink PENDING id2; p0, s1; no ack; sw=1.
6: `paircommit(id2)` -> grant=1; pair=1234, s=0, p=1, A2/COMMITTED, uA=1, L=CONFIG, sw=2.
7: `low,sn(2)` -> cap2 captures A2, p1.
8: `ackA(2)` -> uA=0.
9: `C(SINGLE,56,id3)` -> sink PENDING id3; L=CONFIG, p1; sw=2.
10: `singlecommit(id3)` -> grant=1; single=56, p=2, L=READY, A3/COMMITTED, uA=1, sw=3.
11: `low,sn(3)` -> cap3 captures A3, p2, READY.
12: `ackA(3)` -> uA=0. Final state equals Q. Assert: no write at acceptance edges 1, 5, 9; exactly one `sw` increment per granted commit.

### C2 — failure cancels pending HIGH; prior committed storage remains; F blocks config
1–4: as C1 edges 1–4 (sw=1 after edge 2; A1/STAGED acked).
5: `C(HIGH,34,id2)` -> sink PENDING id2.
6: `low` -> pending2 remains.
7: `C(bad frame,id3),paircommit(id2)` -> invalidation wins: grant=0, R1/BAD_FRAME, uR=1, rej=1, L=CONFIG, p=0, s=0, pair=0000, sw=1, F=0; pending2 CANCELLED; no A2.
8: `low,paircommit(id2)` -> grant=0, pair=0000, p=0, sw=1, **F=1** (stale intent, no matching pending); no new A.
9: `C(LOW,12,id4)` -> ignored under F: sink_pending=NONE, rej=1 (unchanged), R1/BAD_FRAME unchanged, sw=1, p=0, s=0.
10: `low,reset(E=2)` -> F=0, records NONE, L=CONFIG, p=s=0; pair=0000, sw=1.
11–22: replay C1 edges 1–12 under E=2 with attempt 2, ids from 1, starting from pair=0000, sw=1. Row 11+k-1 equals C1 edge k except every `sw` is C1's value +1. Row 22 (C1 edge 12): pair=1234, single=56, p=2, L=READY, A3/COMMITTED, uA=0, sw=4. This demonstrates complete replay after failure.

### C3 — interrupted read is not a failed write
1: `C(LOW,12,id1)` -> pending1.
2: `stage(id1)` -> grant=1, A1/STAGED, uA=1, p0, s1, sw=1.
3: `low,sn(1)` -> cap1 captures A1.
4: `intr(1)` -> cap1 invalid, L=CONFIG, p=0, s=1, uA=1, F=0; host outcome UNKNOWN.
5: `reset(E=2)` -> A=NONE, p=0, s=0, L=CONFIG; storage unchanged, sw=1. No retry before reset.

### C4 — committed data survives; old HIGH cannot act on a new sequence
1–6: as C1 edges 1–6 -> pair=1234, A2/COMMITTED, p=1, sw=2.
7: `reset(E=2)` -> pair=1234, sw=2, L=CONFIG, p=s=0, A=NONE, F=0.
8: `C(LOW,12,id1,attempt1)` under E=2 -> new sink PENDING id1; sw=2.
9: `stage(id1,E=2)` -> grant=1, s=1, p=0, A1/STAGED, pair=1234 (retained), sw=3.
10: `paircommit(id2,E=1)` -> **grant=0, sw=3**, p=0, s=1, pair=1234, L=CONFIG, F=1. The old HIGH rewrites the value already stored; only `grant` and `sw` (and p) show the write, so the assertion is on those. Reset follows before any replay.
11: `reset(E=3)` -> F=0, p=s=0. Storage pair=1234 is retained but never taken as proof of READY.

### C5a — wrong order
1: `C(HIGH,34,id1)` -> R1/WRONG_ORDER, uR=1, rej=1, no sink pending, sw=0, p=0, s=0, F=0.

### C5b — wrong value
1: `C(LOW,13,id1)` -> R1/WRONG_VALUE, uR=1, rej=1, no sink pending, sw=0, p=0, s=0, F=0.

### C5c — wrong target
1: `C(MID,12,id1)` -> R1/WRONG_TARGET, uR=1, rej=1, no sink pending, sw=0, p=0, s=0, F=0.

### C5d — duplicate after STAGED invalidates
1: `C(LOW,12,id1)` -> pending1.
2: `stage(id1)` -> grant=1, A1/STAGED, uA=1, s=1, p=0, sw=1.
3: `low` -> no change.
4: `C(LOW,12,id2)` -> R1/DUPLICATE, uR=1, rej=1, s=0, p=0, L=CONFIG, no sink pending, sw=1 (the earlier stage write remains committed), F=0.

### C6 — config-ack overrun
1: `C(LOW,12,id1)` -> pending1.
2: `stage(id1)` -> grant=1, A1/STAGED, uA=1, sw=1.
3: `C(HIGH,34,id2)` -> pending2 (A1 not acknowledged).
4: `paircommit(id2)` -> grant=1, pair=1234, p=1, A2/COMMITTED, uA=1, **oA=1**, sw=2.
5: `reset(E=2)` -> oA=0, A=NONE, pair=1234, sw=2.

## Transaction cases (start at Q)

### S1 — commit before terminal
1: `I(OK)` -> accept id1, T1/1/EXEC/—/0/—, uT=1, P=1, acc=1, e=0.
2: `low,issue(1)` -> engine pending1, iss=1.
3: (no input) -> P=1, e=0, T EXEC.
4: `effect(1,E1)` -> grant=1, e=1, T EXEC, cmp=0 (no SUCCESS before terminal).
5: `terminal(1,SUCCESS,5A,E1)` -> P=NONE, T1/1/COMPLETE/SUCCESS/1/5A, cmp=1, e=1, F=0.
6: `sn(4)` -> cap4 captures T1 COMPLETE.
7: `ackT(4)` -> uT=0. Assert exactly one issue, effect and completion.

### S2 — terminal before commit
1: `I(DELAY)` -> T1/1/EXEC, P=1, acc=1.
2: `low,issue(1)` -> pending, iss=1.
3: (no input) -> EXEC, e=0.
4: `terminal(1,SUCCESS,3C,E1)` -> T still EXEC, result_valid=0, cmp=0, e=0; terminal retained internally.
5–6: (no input) -> EXEC, e=0.
7: `effect(1,E1)` -> grant=1, e=1, P=NONE, T1/1/COMPLETE/SUCCESS/1/3C, cmp=1. No success at edge 4.

### R1 — refusal carries no historical payload
1–5: as S1 edges 1–5 -> T1 COMPLETE SUCCESS 5A, e=1, cmp=1.
6: `sn(4)` -> cap4 captures T1.
7: `ackT(4)` -> uT=0.
8: `I(REFUSE)` -> T2/2/EXEC/—/0/—, P=2, acc=2; retained 5A is not valid for id2.
9: `low,issue(2)` -> pending2, iss=2.
10–11: (no input) -> EXEC, e=1.
12: `terminal(2,REFUSED,none,E1)` -> T2/2/COMPLETE/REFUSED/0/—, P=NONE, cmp=2, e=1, F=0. No grant or effect for id2.

### U1 — unsupported
1: `I(UNSUPPORTED)` -> T1/1/COMPLETE/UNSUPPORTED/0/—, P=NONE, uT=1, acc=1, iss=0, cmp=1, e=0, F=0.
2: `low` -> no second completion; cmp=1.

### X1 — completion plus rejection plus pre-edge snapshot; caps invalidated by update
1–4: as S1 edges 1–4 -> T1/1 EXEC, P=1, e=1.
5: `terminal(1,SUCCESS,5A,E1),I(OK),sn(4)` -> T1/1 COMPLETE SUCCESS 5A, P=NONE, cmp=1; R1/BUSY, uR=1, rej=1; acc=1, iss=1 (no new accept or issue). cap4 captured pre-edge T1 EXEC and R=NONE, P=1; the terminal update invalidates cap4 for T and the new rejection invalidates cap4 for R.
6: `low,sn(5),ackT(4),ackR(4)` -> both acks inert: uT=1, uR=1, F=0. cap5 captures T1 COMPLETE and R1 BUSY.
7: `ackT(5),ackR(5)` -> uT=0, uR=0. Both updates survive the same edge.

### X2a — duplicate effect alone
1–5: as S1 edges 1–5 -> e=1, cmp=1.
6: `effect(1,E1)` -> grant=0, e=1, T unchanged, cmp=1, F=1.
7: `reset(E=2)` -> F=0, records NONE, e=1.

### X2b — duplicate terminal alone
1–5: as S1 edges 1–5 -> e=1, cmp=1.
6: `terminal(1,SUCCESS,5A,E1)` -> e=1, T unchanged, cmp=1 (no second completion), F=1.
7: `reset(E=2)` -> F=0, records NONE, e=1.

### X3a — cancelled effect across reset
1: `I(DELAY)` -> T1 EXEC, P=1.
2: `low,issue(1)` -> pending1.
3: `reset(E=2),effect(1,E1)` -> reset wins: grant=0, e=0, T=NONE, L=CONFIG, F=0; engine work CANCELLED.
4: `effect(1,E1)` -> grant=0, e=0, T=NONE, F=1.
5: `reset(E=3)` -> F=0, e=0.

### X3b — cancelled terminal across reset
1–2: as X3a edges 1–2.
3: `reset(E=2),terminal(1,SUCCESS,3C,E1)` -> reset wins: T=NONE, cmp=0, F=0.
4: `terminal(1,SUCCESS,3C,E1)` -> T=NONE, cmp=0, F=1.
5: `reset(E=3)` -> F=0.

### X4 — reset before or after irreversible sink commit (Z)
1: `C(LOW,12,id1)` -> pending1.
2: `reset(E=2),stage(id1,E1)` -> grant=0, no stage, no A, p=0, s=0, sw=0, F=0.
3: `stage(id1,E1)` -> grant=0, sw=0, F=1.
4: `reset(E=3)` -> F=0.
5–10: replay C1 edges 1–6 under E=3 (attempt 2, ids from 1, from pair=0000, sw=0; rows equal C1 edges 1–6 with the same sw values). Row 10: pair=1234, p=1, sw=2, A2/COMMITTED.
11: `reset(E=4)` -> pair=1234, sw=2, p=0, s=0, L=CONFIG, A=NONE. Committed storage retained but unauthorized.

### X5 — generation wrap with a valid serialized host (Q)
Five seven-edge blocks, each equal to S1 edges 1–7 with id = i and transaction generation = i mod 4 (the S1 literal `T1/1` becomes `T(i mod 4)/i`), no reset between blocks, e incrementing by one at each effect. **Counter substitution (frozen):** wherever S1 states a cumulative counter value `acc`, `iss`, `cmp` or `e`, block i states that value plus (i−1); `rej` stays 0. Block i therefore asserts, in order: edge 1 `acc=i`; edge 2 `iss=i`; edge 4 `e=i, cmp=i−1`; edge 5 `cmp=i, e=i, F=0`; edge 7 `uT=0`; and `acc=iss=cmp=e=i` at the end of the block. Block i occupies edges 7(i−1)+1 … 7i; within a block: accept edge 1, issue edge 2, effect edge 4, terminal edge 5, snapshot edge 6, ack edge 7; snapshot caps are 4,5,6,7,8 for blocks 1–5.

| block | edges | id | gen | completion edge | e after | cap |
|---|---|---|---|---|---|---|
| 1 | 1–7 | 1 | 1 | 5 | 1 | 4 |
| 2 | 8–14 | 2 | 2 | 12 | 2 | 5 |
| 3 | 15–21 | 3 | 3 | 19 | 3 | 6 |
| 4 | 22–28 | 4 | 0 | 26 | 4 | 7 |
| 5 | 29–35 | 5 | 1 | 33 | 5 | 8 |

Each terminal is SUCCESS/1/5A; all overrun bits stay 0; every ack edge clears uT. Block 5 repeats generation 1 but is fresh only because every prior completion was observed and acknowledged.

### X6 — unread rejection overrun; stale ack after wrap (Q)
1: `I(OK)` -> T1/id1 EXEC, uT=1, P=1.
2: `low,issue(1)` -> pending; the engine is held silent through edge 13 (no effect or terminal).
3: `I(OK)` -> R1/BUSY, uR=1; id1 unchanged.
4: `low,sn(4)` -> cap4 captures R1/BUSY, uR=1; deliberately not acknowledged.
5: `I(OK)` -> R2/BUSY, uR=1, **oR=1**; cap4 invalid for R. Host must treat this as UNKNOWN; the stimulus continues only as an adversarial case.
6: `low,ackR(4)` -> inert; uR=1, oR=1.
7: `I(OK)` -> **R3/BUSY** (recording continues under overrun), uR=1, oR=1.
8: `low` -> unchanged.
9: `I(OK)` -> R0/BUSY.
10: `low` -> unchanged.
11: `I(OK)` -> R1/BUSY, same 2-bit generation as cap4.
12: `low,ackR(4)` -> inert despite generation match; uR=1, oR=1.
13: `reset(E=2)` -> oR=0, records NONE, id1 cancelled.

### X7 — held valid and payload stability (Q; the only engine event is `issue(1)` at edge 2)
1: `I(OK,valid=1)` -> accept id1, P=1, acc=1.
2: `I(OK,valid=1),issue(1)` -> acc=1, iss=1, rej=0, F=0 (no replay).
3: `I(OK,valid=1)` -> acc=1, iss=1, rej=0, F=0.
4: `I(REFUSE,valid=1)` -> payload changed without a low: F=1, acc=1, rej=0; pending1 not committed.
5: `reset(E=2)` -> F=0, P=NONE.

### X7b — stable held valid, then low, normal completion (Q; engine events as listed)
1: `I(OK,valid=1)` -> accept id1, acc=1.
2: `I(OK,valid=1),issue(1)` -> acc=1, iss=1, rej=0.
3: `I(OK,valid=1)` -> acc=1, rej=0, F=0.
4: `low` -> acc=1, iss=1, rej=0, F=0.
5: `effect(1,E1)` -> grant=1, e=1, T EXEC.
6: `terminal(1,SUCCESS,5A,E1)` -> T1/1/COMPLETE/SUCCESS/1/5A, cmp=1, P=NONE, F=0.

### X8 — interrupted snapshot makes ack inert (Q)
1–5: as S1 edges 1–5 -> T1 COMPLETE SUCCESS 5A, e=1.
6: `sn(4)` -> cap4 captures T1 COMPLETE.
7: `intr(4),ackT(4)` -> interruption wins: ack inert, uT=1, T unchanged; host UNKNOWN.
8: `reset(E=2)` -> T=NONE, result_valid=0; e=1; the historical 5A is not a new result.

### X9 — stale capability after fully acknowledged wrap, no overrun (Q)
The engine stays silent through edge 18.
1: `I(OK)` -> T1/id1 EXEC, P=1.
2: `low,issue(1)` -> pending.
3: `I(OK)` -> R1/BUSY, uR=1, oR=0.
4: `low,sn(4)` -> cap4 captures R1; left unused.
5: `sn(5)` -> cap5 captures R1.
6: `ackR(5)` -> uR=0; cap4 unconsumed.
7: `I(OK)` -> R2/BUSY, uR=1, oR=0; cap4 invalid for R.
8: `low,sn(6)` -> cap6 captures R2.
9: `ackR(6)` -> uR=0.
10: `I(OK)` -> R3/BUSY, uR=1.
11: `low,sn(7)` -> cap7 captures R3.
12: `ackR(7)` -> uR=0.
13: `I(OK)` -> R0/BUSY, uR=1.
14: `low,sn(8)` -> cap8 captures R0.
15: `ackR(8)` -> uR=0.
16: `I(OK)` -> R1/BUSY, uR=1; same generation as cap4's capture, different serial.
17: `low,ackR(4)` -> inert: **uR=1, oR=0**.
18: `reset(E=2)` -> records NONE, id1 cancelled.

### X10a — contradictory terminal: REFUSED with payload (Q)
1: `I(REFUSE)` -> accept id1, P=1, acc=1.
2: `low,issue(1)` -> pending1.
3: `terminal(1,REFUSED,payload=77,E1)` -> F=1, T stays EXEC, P=1, cmp=0, e=0.
4: `reset(E=2)` -> F=0.

### X10b — contradictory terminal: SUCCESS without payload (Q)
1: `I(OK)` -> accept id1, P=1, acc=1.
2: `low,issue(1)` -> pending1.
3: `terminal(1,SUCCESS,none,E1)` -> F=1, T stays EXEC, P=1, cmp=0, e=0.
4: `reset(E=2)` -> F=0.

### X11 — ack of an EXECUTING record is inert (Q; engine silent)
1: `I(OK)` -> T1/1/EXEC, uT=1, P=1.
2: `low,issue(1)` -> pending.
3: `sn(4)` -> cap4 captures T1 EXEC, uT=1.
4: `ackT(4)` -> inert: uT=1, F=0, T EXEC (cap4 not consumed).
5: `reset(E=2)` -> records NONE.

### X12 — F blocks new instruction (Q)
1: `I(OK)` -> accept id1, P=1, acc=1.
2: `low,issue(1)` -> pending, iss=1.
3: `effect(1,E1)` -> grant=1, e=1, T EXEC.
4: `effect(1,E1)` -> grant=0, e=1, F=1.
5: `I(OK)` -> ignored under F: acc=1, iss=1, rej=0, T1/1 EXEC unchanged, P=1.
6: `terminal(1,SUCCESS,5A,E1)` -> frozen under F: T1/1 stays EXEC, P=1, cmp=0, F=1, e=1 (valid terminal for the still-active transaction is not published).
7: `reset(E=2)` -> F=0, records NONE, e=1.

### C7 — F freezes pending sink work (Z)
1: `C(LOW,12,id1)` -> sink PENDING id1.
2: `stage(id9)` -> no matching pending: grant=0, F=1; pending id1 unchanged, sw=0.
3: `stage(id1)` -> frozen under F: grant=0, sw=0, s=0, no A, F=1.
4: `reset(E=2)` -> F=0, records NONE, sw=0.

### X16 — transaction overrun (Q; engine events only as listed)
1–5: as S1 edges 1–5 -> T1 COMPLETE SUCCESS 5A, uT=1 (never acknowledged), e=1, cmp=1.
6: `I(OK)` -> accept id2, T2/2/EXEC/—/0/—, P=2, uT=1, **oT=1**, acc=2; no issue acknowledgement follows.
7: `reset(E=2)` -> oT=0, records NONE, e=1.

### L1 — indistinguishable mistagged stale event is an assumption limit (Q)
1: `I(OK)` -> accept id1, current E=1.
2: `low,issue(1)` -> pending id1.
3: harness injects an obsolete terminal mislabeled exactly `(E1,id1,SUCCESS,5A)` -> observationally identical to an early valid terminal: retained, T EXEC, cmp=0, F=0. The contract cannot require stale detection; not counted as rejection coverage.
4: `effect(1,E1)` -> grant=1, e=1; the controller publishes T1/1/COMPLETE/SUCCESS/1/5A, cmp=1, P=NONE, F=0. This documents the attribution limit under truthful-tag assumptions; it is not a safety PASS for mistagged events. No further engine events (the true terminal is not injected).

## Mutation controls

Each mutation compiles/runs the same traces and MUST fail exactly the named assertion at the named edge; an earlier or unrelated failure, compile error or timeout is not detection. Edge numbers refer to the case's own rows.

| ID | Mutation | Case, edge | Failing assertion |
|---|---|---|---|
| M01 | STAGED marked committed/READY | C1 e2 | `p==0 && L==CONFIG && s==1` |
| M02 | Bad frame preserves authorization/progress | C2 e7 | `p==0 && s==0 && L==CONFIG` |
| M03 | Old sink commit granted after cancellation | C2 e8 | `grant==0 && sw==1` |
| M04 | Old HIGH granted against new LOW | C4 e10 | `grant==0 && sw==3` |
| M05 | Interrupted read treated as failed write | C3 e4 | `s==1 && p==0` |
| M06 | Terminal published before effect | S2 e4 | `state==EXEC && result_valid==0` |
| M07 | Historical payload reused on refusal | R1 e12 | `outcome==REFUSED && result_valid==0` |
| M08 | Simultaneous busy rejection suppressed | X1 e5 | `R==R1/BUSY && cmp==1` |
| M09 | Duplicate effect ignored | X2a e6 | `grant==0 && e==1 && F==1` |
| M10 | Duplicate terminal ignored | X2b e6 | `cmp==1 && F==1` |
| M11 | Cancelled old effect granted | X3a e4 | `grant==0 && e==0 && F==1` |
| M12 | Cancelled old terminal accepted | X3b e4 | `T==NONE && cmp==0 && F==1` |
| M13 | Reset loses priority to sink write | X4 e2 | `grant==0 && sw==0` |
| M14 | Reset loses priority to engine effect | X3a e3 | `grant==0 && e==0 && F==0` |
| M15 | Rejection overrun suppressed | X6 e5 | `oR==1` |
| M16 | Rejection recording stops under overrun | X6 e7 | `R==R3/BUSY` |
| M17 | Ack checks only 2-bit generation | X9 e17 | `uR==1 && oR==0` |
| M18 | Terminal update does not invalidate transaction caps | X1 e6 | `uT==1` |
| M19 | Held valid replayed | X7 e2 | `rej==0 && acc==1 && iss==1` |
| M20 | Held-valid payload change ignored | X7 e4 | `F==1 && rej==0 && acc==1` |
| M21 | Interruption does not void ack | X8 e7 | `uT==1` |
| M22 | Transaction overrun suppressed | X16 e6 | `oT==1` |
| M23 | Config-ack overrun suppressed | C6 e4 | `oA==1` |
| M24 | Ack of EXECUTING accepted | X11 e4 | `uT==1` |
| M25 | F does not block new instruction | X12 e5 | `acc==1 && iss==1 && rej==0` |
| M26 | F does not block configuration | C2 e9 | `sink_pending==NONE && rej==1` |
| M27 | REFUSED-with-payload terminal accepted | X10a e3 | `F==1 && cmp==0 && state==EXEC` |
| M28 | SUCCESS-without-payload terminal accepted | X10b e3 | `F==1 && cmp==0 && state==EXEC` |
| M29 | Wrong-order submission accepted | C5a e1 | `R==R1/WRONG_ORDER && sw==0` |
| M30 | Wrong-value submission accepted | C5b e1 | `R==R1/WRONG_VALUE && sw==0` |
| M31 | Wrong-target submission accepted | C5c e1 | `R==R1/WRONG_TARGET && sw==0` |
| M32 | Duplicate preserves STAGED | C5d e4 | `R==R1/DUPLICATE && s==0 && p==0` |
| M33 | UNSUPPORTED issued to engine | U1 e1 | `iss==0 && state==COMPLETE` |
| M34 | NOT_READY request accepted | N1 e1 | `acc==0 && R==R1/NOT_READY` |
| M35 | SUCCESS published on commit alone | S1 e4 | `state==EXEC && cmp==0` |
| M36 | New rejection does not invalidate rejection caps | X1 e6 | `uR==1` |
| M37 | F does not freeze a valid terminal | X12 e6 | `cmp==0 && state==EXEC` |
| M38 | F does not freeze pending sink commit | C7 e3 | `grant==0 && sw==0` |

Runner control RC1: produces the exact expected transcript but exits nonzero; the outer runner must fail. L1 is a limitation demonstration and has no mutation that claims reliable stale detection. Every expected F transition is intentional where stated and clears only on reset.
