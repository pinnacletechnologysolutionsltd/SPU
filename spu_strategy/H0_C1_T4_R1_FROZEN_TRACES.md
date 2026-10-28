# H0-C1-T4-R1 — Frozen independent expected traces

**Disposition: READY FOR INDEPENDENT REVIEW**, not an implementation or simulation authorization. Companion: `/tmp/H0_C1_T4_R1_CONTRACT.md`. These manually specified traces are the independent expected outputs; they were not generated from a controller or simulator. All scenarios and their assertions are finite and synthetic. Production H0-C1 and NUM-SOM-4 Phase B remain HOLD.

## Trace notation and fixtures

Each row `edge: inputs -> expected` gives all changed state at the edge; everything not mentioned is unchanged, every absent input/event is low. All counters are modulo four. Hex values have no production encoding. `Tg/id/state/outcome/v/payload`, `Rg/kind`, `Ag/kind`, and `P` mean transaction, rejection, configuration acknowledgement and active pending ID; `/`-separated fields are literal. `uT,uR,uA` are unread bits; `oT,oR,oA` overrun bits; `F` fault; `e` fake architectural effect counter; `pair,single` committed fake sink storage; `s,p,L` are staged flag, committed progress and lifecycle. `cap` denotes a valid one-shot snapshot capability; `ackT(c)` etc acknowledges that channel only. `sn(c)` captures the full pre-edge state with capability c; interruption `intr(c)` invalidates the response/cap, not storage/records. A changed-generation record invalidates the old capability for that channel.

**Fixture Z:** Immediately after reset, epoch E=1, L=CONFIG,p=0,s=0,P=NONE,T=R=A=NONE, all generations 0, serials 0, all unread/overrun bits 0,F=0, pair=0000,single=00,e=0, no valid request or outstanding cap. All identities allocated afresh from 1; config attempt=1. Reset edges elsewhere use E=2. A request on an edge is a one-edge pulse unless explicitly held. A supplied `stage(k)`, `paircommit(k)`, `singlecommit(k)`, `issue(id)`, `effect(id)` or `terminal(id,...)` is the fake unit's tagged acknowledgement/commit intent on that edge. Correctly matched sink/engine commit intent must have grant=1; blocked/stale intent must have grant=0. Fake effects and stored data change only when granted. Engine terminal has no grant and never directly changes storage.

**Fixture Q:** This is the literal post-edge state after the C1 trace below plus its final acknowledgement: E=1,L=READY,p=2,s=0,P=NONE,T=NONE,R=NONE,A=3/COMMITTED,uT=uR=uA=0,oT=oR=oA=0,F=0,pair=1234,single=56,e=0; transaction/rejection generations and serials=0, cfg-ack generation/serial=3; no request/cap; next transaction id=1 and next snapshot capability=4. Cases based on Q have independently checked this fixture by running C1; it is not seeded from the implementation under test. Every case resets and reruns C1, except C1/N1 which begin at Z. A statement `low` means the relevant request-valid is sampled low for an edge.

## Independent normal and directed-fault cases

### N1 — not ready; Z

1: `I(OK)` -> no acceptance/issue, `R1/NOT_READY`,uR=1,L=CONFIG,P=NONE,e=0,F=0.
2: `low,sn(1)` -> snapshot R1, uR=1; cap1.
3: `ackR(1)` -> uR=0; cap1 consumed for R. Assert exactly one rejection and zero engine/sink grants.

### C1 — staged versus committed configuration; Z

1: `C(LOW,12,id1)` -> sink PENDING id1, no ack, L=CONFIG,p=0,s=0.
2: `stage(id1)` -> grant1; stage=(attempt1,12), `A1/STAGED`,uA=1,p=0,s=1, pair=0000,L=CONFIG.
3: `low,sn(1)` -> snapshot A1 and p0,s1, cap1.
4: `ackA(1)` -> uA=0.
5: `C(HIGH,34,id2)` -> sink PENDING id2; p0,s1; no ack or storage write.
6: `paircommit(id2)` -> grant1; pair=1234,s=0,p=1, `A2/COMMITTED`,uA=1,L=CONFIG.
7: `low,sn(2)` -> snapshot A2,p1; cap2.
8: `ackA(2)` -> uA=0.
9: `C(SINGLE,56,id3)` -> sink PENDING id3; L=CONFIG,p1.
10: `singlecommit(id3)` -> grant1; single=56,p=2,L=READY, `A3/COMMITTED`,uA=1.
11: `low,sn(3)` -> snapshot A3,p2,READY; cap3.
12: `ackA(3)` -> uA=0; final state Q. Assert no fake write at request acceptance and one write per granted commit.

### C2 — failure cancels pending HIGH, committed prior storage remains; Z

1: `C(LOW,12,id1)` -> sink pending1.
2: `stage(id1)` -> grant1,A1/STAGED,uA=1,s=1,p=0.
3: `low,sn(1)` -> cap1.
4: `ackA(1)` -> uA=0.
5: `C(HIGH,34,id2)` -> sink pending2.
6: `low` -> pending2 remains.
7: `C(bad frame,id3),paircommit(id2)` -> invalidation wins: grant0, R1/BAD_FRAME,uR=1,L=CONFIG,p=0,s=0,pair=0000; pending2 CANCELLED; no A2.
8: `low,paircommit(id2)` -> grant0,pair=0000,p=0,F=1 (stale intent); no new A. Reset recovery is necessary.
9: `reset(E=2)` -> F=0, records NONE,L=CONFIG,p=s=0; committed storage remains pair=0000. Re-run literal C1 with epoch 2 and new attempt; pair=1234 and READY only after its edge 10. This demonstrates a failed submission forces complete replay.

### C3 — interrupted read is not a failed write; Z

1: `C(LOW,12,id1)` -> pending1.
2: `stage(id1)` -> grant1,A1/STAGED,uA=1,p0,s1.
3: `low,sn(1)` -> snapshot A1,cap1.
4: `intr(1)` -> response/cap1 invalid, L=CONFIG,p0,s1,uA=1,F=0; host outcome UNKNOWN.
5: `reset(E=2)` -> A=NONE,p0,s0,L=CONFIG; storage unchanged. Host replays C1 under E2; no retry before reset.

### C4 — already committed data survives, delayed old HIGH cannot corrupt new sequence; Z

1–6: same as C1 edges 1–6 -> pair=1234,A2/COMMITTED,p1.
7: `reset(E=2)` -> pair remains 1234; L=CONFIG,p=s=0; no valid config record.
8: `C(LOW,12,id1,attempt1,E2)` -> new sink pending.
9: `stage(id1,E2)` -> grant1,s=1,p0,A1/STAGED; pair remains 1234.
10: `paircommit(old id2,E1)` -> grant0,pair remains 1234,p0,L=CONFIG,F=1; old HIGH is not authorized against new LOW. An injection with a different old HIGH value must likewise not mutate pair. Reset before full replay. Assert current storage is never taken as proof of READY.

### S1 — normal success, commit before terminal; Q

1: `I(OK)` -> accepted id1,T1/1/EXEC/—/0/—,uT=1,P=1,e0.
2: `low,issue(1)` -> engine pending1, acknowledged at t=2.
3: no input -> P1,e0,T EXEC.
4: `effect(1,E1)` -> grant1,e=1,T EXEC (no terminal, no SUCCESS).
5: `terminal(1,SUCCESS,5A,E1)` -> P=NONE,T1/1/COMPLETE/SUCCESS/1/5A,e1,F0, exactly one completion.
6: `sn(4)` -> pre-edge T1 COMPLETE,cap4.
7: `ackT(4)` -> uT=0. Assert exactly one issue, effect and completion.

### S2 — delayed success, terminal before commit; Q

1: `I(DELAY)` -> T1/1/EXEC,P1.
2: `low,issue(1)` -> pending engine, t=2.
3: no input -> EXEC,e0.
4: `terminal(1,SUCCESS,3C,E1)` -> still T EXEC,result-valid0,e0; terminal retained internally.
5–6: no input -> still EXEC,e0.
7: `effect(1,E1)` -> grant1,e1,P=NONE,T1/1/COMPLETE/SUCCESS/1/3C, exactly one completion. Assert no success at edge 4.

### R1 — old result is historical on refusal; Q

1–5: same as S1 edges 1–5 -> T1/1 COMPLETE SUCCESS 5A,e1.
6: `sn(4)` -> cap4 captures T1.
7: `ackT(4)` -> uT0.
8: `I(REFUSE)` -> T2/2/EXEC/—/0/—,P2; physically retained payload 5A is not valid for id2.
9: `low,issue(2)` -> pending2, t=9.
10–11: no input -> EXEC,e1.
12: `terminal(2,REFUSED,no-payload,E1)` -> T2/2/COMPLETE/REFUSED/0/—,P=NONE,e1,F0. Exactly one completion, no grant/effect for id2.

### U1 — unsupported; Q

1: `I(UNSUPPORTED)` -> T1/1/COMPLETE/UNSUPPORTED/0/—,P=NONE,uT1,e0, issue count0,F0.
2: `low` -> no second completion; e0.

### X1 — completion plus rejection plus coherent pre-edge snapshot; Q

1–4: same as S1 edges 1–4 -> T1/1 EXEC,P1,e1.
5: `terminal(1,SUCCESS,5A),I(OK),sn(4)` -> T1/1 COMPLETE SUCCESS 5A,P=NONE and R1/BUSY,uR1. Snapshot cap4 contains pre-edge T1 EXEC, R=NONE, P1,e1; not the new completed/rejection records. No new accept or second issue; cap4 transaction channel is invalidated by terminal state update and cannot acknowledge COMPLETE.
6: `low,sn(5)` -> snapshot T1 COMPLETE and R1 BUSY,cap5.
7: `ackT(5),ackR(5)` -> uT=uR=0. Assert both updates survive the same edge.

### X2 — duplicate terminal and duplicate effect cannot duplicate architectural effect; Q

1–5: S1 -> e1, T1 COMPLETE SUCCESS, one completion.
6: `terminal(1,SUCCESS,5A),effect(1)` -> grant0,e1,T unchanged,F1; no second completion.
7: `reset(E=2)` -> F0, records NONE, e remains 1. Assert both duplicate detections and counter unchanged.

### X3 — cancellation across reset; Q

1: `I(DELAY)` -> T1 EXEC,P1.
2: `low,issue(1)` -> engine pending1.
3: `reset(E2),effect(1,E1),terminal(1,SUCCESS,3C,E1)` -> reset wins, grant0,e0,T=NONE,F0,L=CONFIG; engine work CANCELLED.
4: `effect(1,E1),terminal(1,SUCCESS,3C,E1)` -> grant0,e0,T NONE,F1; no completion/telemetry.
5: `reset(E3)` -> F0. Assert no effect at either 3 or 4.

### X4 — reset before or after irreversible sink commit; Z

1: `C(LOW,12,id1)` -> pending1.
2: `reset(E2),stage(id1,E1)` -> grant0, no stage, no A, p0,s0,F0.
3: `stage(id1,E1)` -> grant0,F1, no stage/storage change.
4: `reset(E3)` -> F0.
5–10: replay C1 edges 1–6 under E3 -> pair=1234 and p1.
11: `reset(E4)` -> pair remains 1234, p0,s0,L CONFIG, A NONE. Assert already committed storage is retained but unauthorized.

### X5 — generation wrap with valid serialized host; Q

For each of five transactions i=1..5, run S1 edges 1–7 as a seven-edge block, substituting id=i and transaction generation `i mod 4`, resetting neither hardware nor storage, and incrementing e by one at each effect. The five blocks respectively capture and consume distinct caps 4,5,6,7,8 before the next. Literal completed sequence by block: `(edge5,T1/id1,e1)`, `(edge12,T2/id2,e2)`, `(edge19,T3/id3,e3)`, `(edge26,T0/id4,e4)`; each terminal is SUCCESS/1/5A, all overruns0, each following ack clears uT. Use blocks **1–7, 8–14, 15–21, 22–28, 29–35**. The complete sequence is edges **5,12,19,26,33** with ids **1,2,3,4,5**, gens **1,2,3,0,1**, counters **1,2,3,4,5**; corresponding snapshot edges 6,13,20,27,34, ack edges 7,14,21,28,35. Each block's engine issue is block edge2, commit block edge4, terminal block edge5. This wrap is accepted only because every prior completion was observed and acknowledged, not because gen1 alone is unique.

### X6 — unread rejection overrun and stale acknowledgement after generation wrap; Q

1: `I(OK)` -> T1/id1 EXEC,uT1,P1.
2: `low,issue(1)` -> engine pending; the fake engine is deliberately delayed for this adversarial case and has no terminal or effect before edge12.
3: `I(OK)` -> R1/BUSY,uR1; active id1 unchanged.
4: `low,sn(4)` -> cap4 captures R1/BUSY,uR1; intentionally do not ack.
5: `I(OK)` -> R2/BUSY,uR1,oR1; cap4 invalidated for R. Host must treat this overrun as UNKNOWN and recover; this adversarial stimulus intentionally continues before recovery.
6: `low,ackR(4)` -> stale ack inert; uR1,oR1.
7: `I(OK)` -> R3/BUSY,uR1,oR1.
8: `low` -> unchanged.
9: `I(OK)` -> R0/BUSY,uR1,oR1.
10: `low` -> unchanged.
11: `I(OK)` -> R1/BUSY,uR1,oR1, now the same 2-bit generation as cap4.
12: `low,ackR(4)` -> stale ack inert despite generation match; uR1,oR1. The real host has been in UNKNOWN/recovery since edge5; these are deliberate hostile requests, not the normal host discipline.
13: `reset(E2)` -> oR0, records NONE, id1 cancelled. If the controller chooses to stop recording further rejections once overrun is set, this trace requires an explicit review and revision; it must not silently pass without showing the wrap.

### X9 — stale capability after fully acknowledged wrap, without overrun; Q

The fake engine is delayed until after edge17 to keep id1 busy; no engine completion or effect occurs in this case. This trace uses compliant acknowledgements until its intentional final stale-ack injection.

1: `I(OK)` -> T1/id1 EXEC,P1.
2: `low,issue(1)` -> engine pending.
3: `I(OK)` -> R1/BUSY,uR1,oR0.
4: `low,sn(4)` -> cap4 captures R1, leave cap4 unused.
5: `sn(5)` -> cap5 also captures R1.
6: `ackR(5)` -> uR0; cap4 remains unused but is invalidated on next replacement.
7: `I(OK)` -> R2/BUSY,uR1,oR0; cap4 invalid for R.
8: `low,sn(6)` -> cap6 captures R2.
9: `ackR(6)` -> uR0.
10: `I(OK)` -> R3/BUSY,uR1,oR0.
11: `low,sn(7)` -> cap7 captures R3.
12: `ackR(7)` -> uR0.
13: `I(OK)` -> R0/BUSY,uR1,oR0.
14: `low,sn(8)` -> cap8 captures R0.
15: `ackR(8)` -> uR0.
16: `I(OK)` -> R1/BUSY,uR1,oR0, generation equals cap4's old generation but serial differs.
17: `low,ackR(4)` -> stale ack inert, uR1,oR0. Assert replacement invalidates cap4 independently of overrun gating.
18: `reset(E2)` -> records NONE, id1 cancelled.

### X7 — held valid and payload stability; Q

The harness suppresses the default engine schedule for edges 3–4 to isolate the held-request protocol violation; no commit intent is presented on those edges.
1: `I(OK,valid=1)` -> accept id1,P1, one issue.
2: `I(OK,valid=1),issue(1)` -> no new accept/issue/reject.
3: `I(OK,valid=1)` -> still one acceptance; no fault.
4: `I(REFUSE,valid=1)` -> payload changed without low: F1, no second acceptance/issue; pending1 is not automatically committed by this event.
5: `reset(E2)` -> F0,P=NONE. Separately, repeat edges 1–3 with stable valid then sampled low and normal engine schedule; expect one acceptance and eventual one completion. This isolates replay from payload-change detection.

### X8 — stale result and interrupted snapshot; Q

1–5: S1 -> T1 COMPLETE SUCCESS 5A,e1.
6: `sn(4)` -> pre-edge T1 valid,cap4.
7: `intr(4),ackT(4)` -> interruption wins, cap invalid, ack inert,uT1,T unchanged; host UNKNOWN.
8: `reset(E2)` -> T NONE,result-valid0; e remains1 and historical 5A is not a new result.

### L1 — indistinguishable mistagged stale event is an assumption limit; Q

1: `I(OK)` -> current E1,id1 accepted.
2: `low,issue(1)` -> current pending id1.
3: harness injects an obsolete terminal mislabeled exactly `(E1,id1,SUCCESS,5A)` -> observationally identical to an early valid terminal; contract cannot require stale detection. Current record remains EXEC because effect absent. Record this limitation explicitly; do not count injection as stale-event rejection coverage.
4: `effect(1,E1)` -> grant1,e1; since falsely trusted terminal is indistinguishable, controller publishes SUCCESS under these assumptions. This is a demonstrated attribution limitation, not a safety PASS for mis-tagged events or a statement about physical hardware. The controller must not be claimed to detect it.

## Mutation controls and precise required assertions

Each mutation compiles/runs against the same traces and MUST fail the named assertion on the named edge; an unrelated failure or timeout is not detection.

| Mutation | Required failing assertion |
|---|---|
| Mark STAGED as committed/READY | C1 edge2: `p==0 && L==CONFIG` |
| Preserve authorization/progress on bad frame | C2 edge7: `p==0 && s==0 && L==CONFIG` |
| Let old sink commit after cancellation | C2 edge7 or C4 edge10: `grant==0 && pair unchanged` |
| Treat interrupted read as failed write | C3 edge4: `s==1 && p==0` |
| Publish terminal before effect | S2 edge4: `state==EXEC && result_valid==0` |
| Reuse historical payload as refusal result | R1 edge12: `outcome==REFUSED && result_valid==0` |
| Suppress simultaneous busy rejection | X1 edge5: `R==R1/BUSY` while completion is present |
| Ignore duplicate effect | X2 edge6: `grant==0 && e==1 && F==1` |
| Grant cancelled old effect | X3 edge4: `grant==0 && e==0 && T==NONE` |
| Suppress overrun | X6 edge5: `oR==1` |
| ACK checks only 2-bit generation, ignoring capability invalidation and record serial | X9 edge17: `uR==1 && oR==0` |
| Replay held valid | X7 edge3: `accept_count==1 && issue_count==1` |
| Ignore held-valid payload change | X7 edge4: `F==1 && accept_count==1` |
| Reset loses priority to sink write | X4 edge2: `grant==0 && stage absent` |

An independent runner control must produce the exact expected transcript but exit nonzero; the runner must itself fail. L1 is a limitation demonstration and has no mutation that claims reliable stale detection. Every expected F transition is intentional where stated and must clear only on reset.
