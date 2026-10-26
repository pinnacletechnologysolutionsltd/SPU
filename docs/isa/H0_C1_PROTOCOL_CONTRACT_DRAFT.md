# H0-C1 — Minimum host-driven execution protocol: contract draft

**Status:** NON-NORMATIVE DRAFT for independent review. Nothing here is implemented, ratified or an encoding. Normative ratification and RTL implementation **HOLD**.
**Baseline identity:** `dev/next` at `b682ee825401ee61171ef4d8fa4957aba9214981` (clean). Existing VM, assembler and RTL sources are unchanged from public RC2 `b063280`.
**Scope:** the smallest transaction contract needed to qualify the existing Artix-7 SPU-13 host-driven execution engine (profile **H0**, see [`ISA_V02_STATE1_FINDINGS.md`](ISA_V02_STATE1_FINDINGS.md)). No instruction-set or mathematical semantic change; no queue; no autonomous program counter; no unified FLAGS register; no fixed counter width and no new SPI encoding is prescribed.
**Language:** MUST/SHALL mark requirements of this *proposed* contract, not properties of the current design.

## 1. Evidence base

| Source | What it establishes (as built) |
|---|---|
| [`ISA_V02_STATE1_FINDINGS.md`](ISA_V02_STATE1_FINDINGS.md) | The core acknowledges unsupported opcodes with `inst_done` and no effect; the RTL has no PC, fault state or success/refusal signal. |
| [`ISA_V02_H0TRANSPORT1_FINDINGS.md`](ISA_V02_H0TRANSPORT1_FINDINGS.md) | SPI `0xB1` yields a one-cycle strobe with no queue, sequence number or acknowledgement; `inst_done` is not host-visible; silent drops (CS drop, deadman, boot-not-ready); `0xAE` valid is sticky with no freshness. |
| [`ISA_V02_H0V1_FINDINGS.md`](ISA_V02_H0V1_FINDINGS.md) | Simulation at core level: 40 unsupported opcodes acknowledged without effect; overlapping strobes can swallow an instruction or lose an in-flight ROTC result; boot-not-ready strobes lost; repeated identical instructions have no identity; the Padé sidecar rejects a busy request correctly. |
| [`ISA_V02_A31R2_FINDINGS.md`](ISA_V02_A31R2_FINDINGS.md) | Simulation: after an A31 inversion refusal the ordinary pipeline and core bridge publish the previous result (or `x` after reset) with valid indications; the Padé sidecar suppresses the commit. |

## 2. Central invariant and vocabulary

> **Every accepted instruction has exactly one observable terminal outcome. No refused or unsupported instruction may publish a fresh valid result.**

| Term | Definition (proposed) |
|---|---|
| **Submitted** | A frame carrying an instruction word reached the ingress. |
| **Transport-rejected** | Submitted but not delivered to the engine: CRC failure, aborted or malformed frame. Not a refusal of an instruction. |
| **Rejected at acceptance** | Delivered but not taken: engine not READY (boot), or an instruction already outstanding (busy). Not a refusal; no effect on any transaction. |
| **Accepted** | Execution ownership transferred to the engine. From this point exactly one terminal outcome SHALL occur (subject to §7 reset and fatal rules). |
| **Completed** | The transaction reached its terminal outcome and its record is published. |
| **Succeeded** | Completed with outcome SUCCESS: the instruction's specified effects were committed. |
| **Refused** | Completed with outcome REFUSED: execution ended without publishing an invalid result (for example A31 inversion of a zero divisor, or an operand-validity fault of a supported opcode). |
| **Unsupported** | Completed with outcome UNSUPPORTED: the opcode is outside the supported subset of the running bitstream; no effect. |
| **Result-valid** | The transaction produced a fresh result payload. Independent of completion: only a SUCCESS of a result-producing instruction is result-valid. |

`inst_done` MUST NOT be read as success. The existing pulse MAY remain as an internal compatibility signal; it carries no outcome.

## 3. Transaction lifecycle

| State | Entered when | Hardware obligation | Host observation required |
|---|---|---|---|
| **IDLE** | Reset exit after boot READY, or after the previous record is published and the engine is free | Accept the next instruction | READY / not-busy |
| **FRAME** | A `0xB1` frame is in progress | Validate CRC; no engine effect yet | none required beyond the frame itself |
| **TRANSPORT-REJECTED** | CRC failure, CS drop or deadman abort | Discard; no acceptance; no effect on any outstanding transaction | CRC failure visible (existing sticky); an aborted frame MUST NOT advance the acceptance indication |
| **REJECTED-NOT-READY** | Valid frame while the engine is not READY | Discard; no acceptance | Reason distinguishable from busy and from CRC; boot FAULT distinguishable from HYDRATING |
| **REJECTED-BUSY** | Valid frame while a transaction is outstanding | Discard; the outstanding transaction MUST be unaffected (not swallowed, not starved) | Reason visible; MUST NOT be mistaken for the outstanding transaction's outcome |
| **ACCEPTED / EXECUTING** | Valid frame, READY, not busy | Classify the opcode; dispatch or select UNSUPPORTED; mark busy | Acceptance indication advances; busy visible |
| **COMPLETED(outcome)** | The unit reports its terminal outcome | Publish one record atomically with any result; release busy only after publication | The record (§5) |

Only one transaction is outstanding at a time across the **whole** engine (core and every sidecar behind the ingress). Outstanding runs from acceptance until the record is published, not merely until a completion pulse.

## 4. Safety invariants (proposed)

1. **INV-1 Exactly one terminal outcome** per accepted instruction (no zero, no two).
2. **INV-2 Single outstanding.** A second instruction is rejected visibly while one is outstanding; hardware enforces this independent of host behavior.
3. **INV-3 No swallow, no starvation.** A rejected instruction never alters, delays or discards an in-flight operation's step or result (H0-V1: ROTC result loss, QLDI swallowed during `qsub_active`, swallows on the `rplu2_result_valid` and `rote_done_tdm` cycles).
4. **INV-4 No fresh-valid on refusal.** A REFUSED or UNSUPPORTED transaction never raises a result-valid, a commit, or a commit-telemetry update, and never presents the previous transaction's result or an undefined (`x`) value as fresh (A31-R2).
5. **INV-5 Unsupported is a terminal outcome, not a success.** Classification of opcodes against the bitstream's supported subset happens in the hardware; host preflight alone is insufficient (§8).
6. **INV-6 Rejection is visible and distinct.** CRC, abort, not-ready and busy rejections are distinguishable from each other and from any accepted transaction's outcome.
7. **INV-7 Distinct consecutive transactions.** The record of transaction N is distinguishable from that of N+1 even when results are identical (H0-V1: two identical QLDI/Padé completions are indistinguishable today).
8. **INV-8 Record stability.** A published record is stable and readable until the next acceptance or reset, and its fields are mutually coherent (no tearing).
9. **INV-9 Transport status is separate from arithmetic status.** CRC and rejection indications do not share bits or meaning with SUCCESS/REFUSED/UNSUPPORTED.

## 5. Host-visible record: requirements (no encoding)

For each accepted transaction the host MUST be able to read, coherently and non-destructively:

| Item | Requirement |
|---|---|
| Transaction identity | A value that changes on every acceptance (a monotonic count or an equivalent tag). Width and wrap are a design choice (§11); it MUST suffice, with a single outstanding transaction and the host's polling discipline, to tell consecutive transactions apart. |
| State | Whether the transaction is executing or completed. |
| Terminal outcome | SUCCESS, REFUSED or UNSUPPORTED. |
| Result-valid | Whether a fresh result accompanies this transaction. |
| Result association | When result-valid, the payload is tied to this transaction (the record carries it, or the existing `0xAE` content is guaranteed to correspond to the record while result-valid). |
| Last rejection | The reason of the most recent rejection (CRC/abort, not-ready, busy), kept separate from the transaction record. |
| Busy / ready | Whether a submission would now be rejected. |

**Lifetime.** The record persists from publication until the next acceptance or reset; reading it MUST NOT clear it. Legacy clear-on-read behavior of `0xAC` (CRC sticky, ratio-valid) is preserved for existing hosts and is not reused for the record. Fields are captured atomically when the record is published; a read during an update MUST return either the old or the new coherent record.

**Host polling discipline (proposed).** Submit; read until the record shows the new identity as completed (with a documented timeout); then submit the next. A host that cannot observe completion cannot enforce one-outstanding, which is why the record is part of the contract.

## 6. Outcome semantics

- **SUCCESS:** specified effects committed; for result-producing instructions result-valid is true.
- **REFUSED:** terminal, no commit; includes arithmetic refusal (A31 zero-divisor via `flags_v`, with the consumer classifying `pade_done && !flags_v` versus `pade_done && flags_v`) and operand-validity faults of supported opcodes (the existing ROTC bad-angle and IROTC guard paths are candidates; their mapping is to be established, not assumed).
- **UNSUPPORTED:** terminal, no effect, no commit. Includes opcodes whose feature is disabled in the bitstream.
- Completion is independent of result-valid: a refusal completes without result-valid.
- A refusal MAY leave physical registers holding old data; that data is never associated with the new transaction nor flagged valid.

## 7. Busy, boot, malformed transport and reset

- **Busy:** a submission while a transaction is outstanding is rejected (REJECTED-BUSY) and visible. There is no queue.
- **Boot-not-ready:** a submission before READY is rejected visibly and is not replayed; boot FAULT is distinguishable from HYDRATING.
- **Malformed transport:** CRC failure is a transport rejection (existing sticky retained). A partial frame (CS drop, deadman) is an abort: no acceptance, no effect, and the acceptance indication does not advance. Whether aborts also need their own indication, or whether the unchanged acceptance indication is sufficient, is open (§11).
- **Reset during execution:** reset aborts the outstanding transaction; no record claims it completed; after reset the record is in a defined "no transaction" state and boot gating applies. The host treats a transaction in flight at reset as not completed.
- **Fatal / non-terminating execution** (for example a unit that never completes): the contract requires a documented bound, either a hardware watchdog that completes the transaction with a terminal outcome, or a host timeout followed by reset. Which is a design choice (§11); today ROTC with math disabled can hang (conformance record, not re-derived).

## 8. Enforcement boundary for unsupported instructions

Host preflight validation (a driver that only sends supported opcodes) is a convenience, not an enforcement mechanism. An incorrectly configured or untrusted host can send any 64-bit word. The hardware therefore SHALL classify every accepted opcode against the bitstream's supported subset and terminate unsupported ones with UNSUPPORTED. The supported subset is a property of the named bitstream/profile and MUST be enumerable; it is not decided here. Opcodes disabled by a feature parameter are UNSUPPORTED in that bitstream.

## 9. Relationship to existing SPI commands

| Command | Treatment (proposed) |
|---|---|
| `0xB1` | Frame, CRC and big-endian word unchanged. CRC success is **necessary but not sufficient** for acceptance. The one-cycle strobe becomes an internal request that the engine accepts or rejects; it is never silently dropped. |
| `0xAC` | Existing field meanings unchanged for current hosts. The spin-dependent debug meanings (see H0-TRANSPORT-1) are not reused as completion/outcome. Spare zero bits exist in byte 3, but reusing them without versioning would change a published response; whether to use them is open. |
| `0xAE` | Unchanged "last commit" content. Its valid byte stays sticky and legacy. It MUST NOT be the only freshness evidence. |
| Record read | An **additive** mechanism (for example a new read-only command) is the compatibility-preserving direction; no command value or layout is chosen here. |

## 10. Real SPI timing: UNVERIFIED

The H0-V1 collisions are core-level results under supplied one-cycle strobes. A `0xB1` frame is at least 80 SCK bit periods, but the relationship between SCK, `clk_fast` (`A7_CLK_DIV_LOG2`, spin dividers) and the SPI slave's synchronizer limit was not established. This draft assumes no ratio and claims no collision window is reachable on the board. The contract therefore requires hardware rejection (INV-2, INV-3) independent of whether a particular window is reachable, and the buffering decision (none proposed) is to be revisited only if measured timing shows a need.

## 11. Unresolved design choices (for review)

1. **Do acceptance and completion need separate records?** With one outstanding transaction, a single record with a state field (executing/completed) and an identity may suffice. Which is simpler and race-free?
2. **Where the record lives:** SPI slave, Artix-7 top, or core; and how a single owner learns completion from the core and from each sidecar without a new control layer.
3. **Identity width and wrap**, and whether a 1-bit alternating tag is enough under the polling discipline.
4. **Atomic publication and clearing:** how a record and its result payload are captured coherently, how reads race with updates, and when `0xAE` content is guaranteed to correspond to the record.
5. **Opcode classification location** (ingress or core) and how the supported-subset table is kept consistent with the instruction FSM.
6. **Operand-validity refusals:** which existing fault paths (ROTC angle, IROTC guards, others) map to REFUSED.
7. **Watchdog versus host timeout** (§7).
8. **Abort indication** (§7) and the representation of rejection reasons.
9. **Legacy `inst_done`:** retained internally as a completion pulse feeding the record, or removed.
10. **Existing sidecars:** Lucas, SU3 and the live-evaluator sidecar were not audited for this contract; the Padé sidecar's busy rejection and commit gating are a positive control, but its pulses (`error`, `qr_commit_valid`) must be turned into the record.
11. **Real SPI timing** (§10).

## 12. Verification acceptance criteria (proposed)

Each criterion is a directed test with fixed expected outcomes; the H0-V1 and A31-R2 probes are the starting fixtures.

| ID | Criterion |
|---|---|
| AC-1 | Each supported instruction alone: one acceptance, one completion record with SUCCESS and the expected result-valid and state. |
| AC-2 | Each tested unsupported or feature-disabled opcode (the 40 in H0-V1): accepted, exactly one record with UNSUPPORTED, no commit, no state change. |
| AC-3 | A second instruction at every gap in the H0-V1 overlap windows (including `qsub_active`, `rote_done_tdm`, `rplu2_result_valid`): rejected visibly as busy; the outstanding transaction completes with its correct result and exactly one record. |
| AC-4 | A31 refusal after a success and first after reset, on the pipeline, the core bridge, the live-evaluator path and the sidecar: REFUSED, no result-valid, no commit, no stale or `x` value presented as fresh; a following valid transaction succeeds. |
| AC-5 | Consecutive identical instructions: the two records are distinguishable by identity. |
| AC-6 | Boot-not-ready: rejected visibly with a not-ready reason, not replayed; boot FAULT distinguishable from HYDRATING. |
| AC-7 | Bad CRC and aborted frames: no acceptance, no effect, correct transport indication; existing `0xAC` CRC sticky behavior unchanged. |
| AC-8 | Record stability: repeated reads (including across CS toggles) return the same coherent record until the next acceptance; no field tearing under concurrent completion. |
| AC-9 | Reset during execution: no record claims completion; defined post-reset state. |
| AC-10 | `0xAC` and `0xAE` compatibility: existing responses unchanged for existing hosts. |
| AC-11 | Every item above repeated at each qualified SCK and `clk_fast` combination, with the timing margin measured (§10). |
| AC-12 | Synthesis and timing of the exact Artix-7 image, then the same fixtures executed over SPI on the target board; the named H0 profile is the qualified scope. Physical results are reported separately from simulation. |

## 13. Out of scope

New instructions or mathematical changes; a queue or sequencer; a unified FLAGS register (see SNAP-1); A31 arithmetic redesign (the repair is validity propagation, not arithmetic); choice of SPI encodings, counter widths or buffering; the SPU-4 profile.
